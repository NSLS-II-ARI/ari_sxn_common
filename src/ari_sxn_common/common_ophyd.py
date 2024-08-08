from collections import defaultdict, namedtuple
from nslsii.devices import TwoButtonShutter
from ophyd import (Component, Device, EpicsMotor)
from ophyd.areadetector.base import ADComponent
from ophyd.areadetector.cam import ProsilicaDetectorCam
from ophyd.areadetector.detectors import ProsilicaDetector
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.quadem import NSLS_EM, QuadEMPort
from ophyd.signal import Signal, EpicsSignalRO, EpicsSignal
import re


# noinspection PyUnresolvedReferences,PyProtectedMember
class PrettyStrForDevices:
    """
    A class that provides a better print and tab-to-complete functionality`

    This class has a custom `__str__()` method that returns a formatted string
    that includes the device name as well as child signals grouped by the
    `signal._ophyd_labels_` list.

    This class also has a custom `__dir__()` method that returns a list of
    attribute names giving the required options when using tab-to-complete. This
    list contains all of the signals found in `self._signals.keys()` as well as
    the `read()` method.

    Methods
    -------
    __str__() :
        Returns a formatted string indicating it's name and all of the child
        signals grouped by their `_ophyd_labels_`.
    __dir__() :
        Returns a list of attribute name strings to be used to define what
        options are available when doing tab-to-complete.
    """
    def __str__(self):
        """
        Updates the __str__() method to provide the formatted string described
        in the class definition.

        Returns
        -------
        output : str
            A formatted string that should be printed when using print(self)
        """
        signals = defaultdict(list)
        if hasattr(self, '_signals'):
            for signal in self.component_names:
                try:
                    labels = list(getattr(self, signal)._ophyd_labels_)
                except IndexError:
                    labels = {'unknown', }
                for label in labels:
                    signals[label].append(
                        getattr(self, signal).__str__().replace(
                            f'{self.name}_', ''))

        try:
            self_label = self._ophyd_labels_
        except IndexError:
            self_label = {'unknown', }

        output = f'\n{self.name} ({str(self_label)[1:-1]})'
        for label, names in signals.items():
            output += f'\n  "{label}s":'
            for name in names:
                output += f'    {re.sub(r'\(.*\)', '', 
                                        name.replace('\n', '\n    '))}'

        return output

    def __dir__(self):
        """
        Used to limit the number of options when using tab to complete.

        This method is used to give the list of options when using pythons tab
        to complete process. It gives all of the signal attributes (motors and
        detectors) as well as the 'read' method.

        Returns
        -------
        attribute_list : list[str]
            A list of attribute names to be included when using tab-to-complete
        """
        attribute_list = ['read']
        attribute_list.extend([key for key in self.component_names])

        return attribute_list


# noinspection PyUnresolvedReferences
class PrettyStrForSignal:
    """
    A class that provides a better string when using `print(PrettyStr)`

    This class has a custom `__str__()` method that returns a formatted string
    that includes the device name as well as the `signal._ophyd_labels_` list.
    It is designed for use with the `PrettyStrForDevices` class but on the
    lowest level signals that should be accessed by users.

    This class also has a custom `__dir__()` method that returns a list of
    attribute names giving the required options when using tab-to-complete. This
    list contains only the `read()` method.

    Methods
    -------
    __str__() :
        Returns a formatted string indicating it's name and it's
        `_ophyd_labels_`.
    __dir__() :
        Returns a list of attribute name strings to be used to define what
        options are available when doing tab-to-complete.
    """

    def __str__(self):
        """
        Updating the __str__ function to return 'name (label)'

        Returns
        -------
        output : str
            A formatted string that should be printed when using print(self)
        """

        try:
            self_label = self._ophyd_labels_
        except IndexError:
            self_label = {'unknown', }
        return f'{self.name} ({str(self_label)[1:-1]})'

    def __dir__(self):
        """
        Used to limit the number of options when using tab to complete.

        This method is used to give the list of options when using pythons tab
        to complete process. It gives only the 'read' method.

        Returns
        -------
        attribute_list : list[str]
            A list of attribute names to be included when using tab-to-complete
        """
        attribute_list = ['read']

        return attribute_list


# noinspection PyUnresolvedReferences
class ID29EpicsMotor(PrettyStrForSignal, EpicsMotor):
    """
    Updates ophyd.EpicsMotor with a str method from PrettyStrForSignal

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent 'EpicsMotor' class
    **kwargs : keyword arguments
        The keyword arguments passed to the parent 'EpicsMotor' class

    Attributes
    ----------
    *attrs : many
        The attributes of the parent `EpicsMotor` class.

    Methods
    -------
    *methods : many
        The methods of the parent `PrettyStrForSignal` and `EpicsMotor`
        classes.
    __init__(*args, **kwargs) :
        Runs the parent `EpicsMotor` __init__() method and then updates the
        'kind' attribute on a few attributes.
    """
    def __init__(self, *args, **kwargs):
        """
        Modifies the kind of some signals to match the 29ID requirements
        """
        super().__init__(*args, **kwargs)
        self.user_setpoint.kind = 'normal'
        self.user_readback.kind = 'hinted'


# noinspection PyUnresolvedReferences
class ID29EpicsSignalRO(PrettyStrForSignal, EpicsSignalRO):
    """
    Updates ophyd.EpicsSignalRO with a str method from PrettyStrForSignal

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent `EpicsSignalRO` class
    **kwargs : keyword arguments
        The keyword arguments passed to the parent 'EpicsSignalRO' class

    Attributes
    ----------
    *attrs : many
        The attributes of the parent `EpicsSignalRO` class.

    Methods
    -------
    *methods : many
        The methods of the parent `PrettyStrForSignal` and `EpicsSignalRO`
        classes.
    """


class ID29EM(PrettyStrForSignal, NSLS_EM):
    """
    A 29-ID specific version of the NSLS_EM quadEM device.

    The main difference between this and the ophyd standard is adjusting
    the 'kind' of the signals to match what is required at 29-ID.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent 'NSLS_EM' class
    **kwargs : keyword arguments
        The keyword arguments passed to the parent 'NSLS_EM' class

    Attributes
    ----------
    *attrs : many
        The attributes of the parent `NSLS_EM` class.
    conf : QuadEMPort
        updates the QuadEMport component of the `NSLS_EM` parent with a new
        port name.

    Methods
    -------
    *methods : many
        The methods of the parent `NSLS_EM` and PrettyStrForSignal classes.
    __init__(*args, **kwargs) :
        Runs the parent `NSLS_EM` __init__() method and then updates the
        'kind' attribute on a few attributes.
    """
    conf = Component(QuadEMPort, port_name='EM180', kind='config')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Generate a list of signals and sub-devices for this qem
        signals_list = [(signal.dotted_name, signal.item)
                        for signal in self.walk_signals()
                        if '.' not in signal.dotted_name]
        devices_list = [(name, device)
                        for (name, device) in self.walk_subdevices()]
        for (name, device) in signals_list + devices_list:
            if name in ['current1', 'current2', 'current3', 'current4']:
                device.kind = 'hinted'  # Hint this signal for proper readback
                device.nd_array_port.put('EM180')  # Set the correct port.
            elif name in ['values_per_read', 'averaging_time',
                          'integration_time', 'num_average', 'num_acquire',
                          'em_range']:
                device.kind = 'config'  # Set signal to 'config' for readback
            elif hasattr(device, 'kind'):
                device.kind = 'omitted'  # set signal to 'omitted'.


class ID29TwoButtonShutter(PrettyStrForSignal, TwoButtonShutter):
    """
    An nslsii.devices.TwoButtonShutter class that adds the `__str__` and
    `__dir__` methods from PrettyStrForSignal
    """


class Prosilica(PrettyStrForSignal, SingleTrigger, ProsilicaDetector):
    """
    Adds the `cam1.array_data` attribute required when not image saving.

    This class adds the `self.cam.array_data` attribute used when not saving
    images, the cam attribute and an updated `self.__str__()` method that
    matches that used for the `PrettyStr` class. In this case however it does
    not include any child signals, as this is the lowest level device that users
    are likely to interact with.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent 'ProsilicaDetector' class
    **kwargs : keyword arguments
        The keyword arguments passed to the parent 'ProsilicaDetector' class

    Attributes
    ----------
    *attrs : many
        The attributes of the parent `SingleTrigger` and `ProsilicaDetector`
        classes.
    cam : ProsilicaCam
        The cam attribute for this area-detector.

    Methods
    -------
    *methods : many
        The methods of the parent ``PrettyStrForSignal`, SingleTrigger` and
        `ProsilicaDetector` classes.
    __init__(*args, **kwargs) :
        Runs the parent `ProsilicaDetector` __init__() method and then updates
        the 'kind' attribute on a few attributes.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cam.kind = 'normal'
        self.cam.array_data.kind = 'normal'

    class ProsilicaCam(ProsilicaDetectorCam):
        """
        A `ProsillicaDetectorCam` class that adds some extra attributes

        Parameters
        ----------
        *args : arguments
            The arguments passed to the parent 'ProsilicaDetectorCam' class
        **kwargs : keyword arguments
            The keyword arguments passed to the parent 'ProsilicaDetectorCam'
            class

        Attributes
        ----------
        *attrs : many
            The attributes of the parent `ProsilicaDetectorCam` class.
        array_data : ID29EpicsSignalRO
            An attribute that holds the array data for this camera.
        array_counter : EpicsSignal
            An attribute that is used to indicate how far through the trigger
            process the detector is.

        Methods
        -------
        *methods : many
            The methods of the parent `ProsilicaDetectorCam` class.
        __init__(*args, **kwargs) :
            Runs the parent `ProsilicaDetector` __init__() method and then
            updates the 'kind' attribute on a few attributes.
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        array_data = ADComponent(ID29EpicsSignalRO, "ArrayData",
                                 kind='normal')
        array_counter = ADComponent(EpicsSignal, 'ArrayCounter',
                                    kind='config', timeout=10)

    cam = Component(ProsilicaCam, "cam1:", kind='normal')


class DeviceWithLocations(PrettyStrForDevices, Device):
    """
    A child of ophyd.Device that adds a 'location' functionality.

    The location functionality adds new properties (self._locations_data, a new
    child signal (self.locations), a new signal (self.available_locations) and a
     new method (self.set_location). These allow for a collection of 'locations'
      to be defined which can be:
        * set via `self.locations.set('...')`
        * read via `self.locations.read()`
        * A list of available locations is returned from
          `self.locations.available()`

    It also includes the new `self.__str__()` method defined in the
    `PrettyStrForDevices` class.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent 'Device' class
    locations_data : {str: {str:(float, float), ...}, ...}, optional.
        A dictionary mapping the names of 'locations' to a dictionary mapping
        the 'signal name' to a (location position, location precision) tuple for
        the corresponding location. These are used in the 'set_location' method
        on the diagnostic device to quickly move between locations/setups for
        the diagnostic. 'location position' is the value that the corresponding
        'signal name' axis should be set to when moving to 'location'.
        'location precision' is used to determine if the device is in 'location'
         by seeing if the 'signal name's 'current position' is within +/-
         'location precision' of 'location position'. For str or int signals
         this value is ignored but should be set as 'None'.
    **kwargs : keyword arguments
        The keyword arguments passed to the parent 'Device' class

    Attributes
    ----------
    *attrs : many
        The attributes of the parent `Device` and `PrettyStrForDevices` classes.
    _locations_data : Dict
        A dictionary containing the information on the locations as passed into
        the self.__init__() method via locations_data.
    locations : LocationSignal
        The signal that contains the methods used for setting and reading
        the devices location(s).

    Methods
    -------
    *methods : many
        The methods of the parent `Device` and `PrettyStrForDevices` class.
    __init__(*args, **kwargs) :
        Runs the parent `Device` __init__() method and then adds the
        `_locations_data` attribute.
    """

    # noinspection PyUnresolvedReferences
    class LocationSignal(PrettyStrForSignal, Signal):
        """
        An InternalSignal class to be used for updating the 'location' signal

        This `ophyd.signal.Signal` child class is used to provide a
        signal that can be set, via self.set('...'), to one of the pre-set
        'locations' from `self.parent._locations_data.keys()`, The 'set' will
        move the attributes of the parent `DeviceWithLocations` Device to the
        corresponding positions defined in `self.parent._locations_data`
        associated with the 'location' key. When 'read' using `self.get()` or
        self.read() this signal returns a list of locations (keys from the
        `self.parent._locations_data`) that the parent is currently in. It also
        has a `self.available()` method that returns a list of pre-set
        'locations' that it can be set too.

        NOTE: It is an inner class of DeviceWithLocations as it relies on the
        parent having attributes defined by DeviceWithLocations. It updates
        the ```self.get()``` method to update its value before calling
        ```super().get()```, the self.set(...) method to move to the pre-set
        location and the self.available() method.

        Parameters
        ----------
        *args : arguments
            The arguments passed to the parent 'Signal' class
        **kwargs : keyword arguments
            The keyword arguments passed to the parent 'Signal' class

        Attributes
        ----------
        *attrs : many
            The attributes of the parent `Signal` class.

        Methods
        -------
        *methods : many
            The methods of the parent `Signal` class.
        get() :
            Returns a list of locations the parent device is currently 'in'.
        set(location) :
            Sets the 'location' of the parent device to location.
        available() :
            returns a list of possible 'locations' that the parent device can
            be set to.
        """

        def get(self, **kwargs):
            """
            Method that returns a list of 'locations' that the device is 'in'

            This is a modified get method that looks through
            self.parent._locations_data to check if the device is 'in' each of
            the locations and then 'puts' a list of locations where this is
            true. After this it returns super().get(**kwargs) to ensure that
            any important information is not lost.

            Note, the put at the end is done during the 'get' instead of during
            the 'set' as each of the motors/signals could be independently
            moved without passing through the 'set' function. This does result
            in the case where using 'locations.value' does not guarantee an
            up-to-date value so take care.

            Parameters
            ----------
            **kwargs : keyword arguments
                kwargs passed through to super().get(**kwargs)

            Returns
            -------
            super().get(**kwargs) :
                Returns the result of super().get(**kwargs)
            """
            # Determine the locations we are currently 'in'.
            locations = {}
            # Note the next line gives an 'accessing a protected member,
            # _locations_data' warning in my editor. I accept the risk !-).
            for location, location_data in self.parent._locations_data.items():
                value_check = []
                for signal_name, data in location_data.items():
                    # note below tries signal.position and then signal.get() to
                    # work with 'positioners' and 'signals'.
                    signal = getattr(self.parent, signal_name)
                    # EpicsMotor.get() returns a tuple not it's position
                    if hasattr(signal, 'position'):
                        value = getattr(signal, 'position')
                    elif hasattr(signal, 'get'):
                        value = getattr(signal, 'get')()
                    else:
                        raise AttributeError(f'during a call to '
                                             f'{self.parent}.locations.get() a '
                                             f'signal ({signal_name}) from '
                                             f'{self.parent.name}'
                                             f'._location_data was found to not'
                                             f' have a supported attribute. '
                                             f'Presently supported attributes '
                                             f'are '
                                             f'{self.parent.name}{signal_name}.'
                                             f'position and '
                                             f'{self.parent.name}{signal_name}.'
                                             f'get()')

                    if isinstance(value, float):  # for float values
                        value_check.append(data[0] - data[1] < value <
                                           data[0] + data[1])
                    elif isinstance(getattr(self.parent, signal_name),
                                    type(self)):
                        # This implies the signal is a child DeviceWithLocation
                        # LocationSignal
                        value_check.append(data[0] in value)
                    elif isinstance(value, (int, str)):  # for string/int values
                        value_check.append(data[0] == value)
                    else:
                        raise ValueError(f'during a call to {self.parent.name}.'
                                         f'locations.get()'
                                         f'a value ({value}) from '
                                         f'{self.parent.name}._location_data '
                                         f'was found to be a non-supported '
                                         f'data-type. Presently supported '
                                         f'data-types are floats, ints and '
                                         f'strings or lists from '
                                         f'DeviceWithLocations '
                                         f'LocationSignal signals')
                if all(value_check):
                    locations[location] = True
                else:
                    locations[location] = False
            # Set the value at read time.
            self.put(self.parent._LocationsTuple(**locations))

            return super().get(**kwargs)  # run the parent get function.

        def set(self, value, **kwargs):
            """
            A set method that moves all specified signals to a 'location'

            This method extracts location data using value as a key of
            the self.parent._locations_data dictionary and then uses
            this location data to move all necessary signals to their
            desired locations.

            Parameters
            ----------
            value : str,
                The name of the location that the parent device should
                be moved to.
            kwargs : dict
                The kwargs to be passed through to the super().set()
                method.

            Returns
            -------
            output_status : Status
                The combined status object for all the required sets.
            """
            try:
                location_data = self.parent._locations_data[value]
            except KeyError as exc:  # more helpful traceback message
                traceback_str = (f'A call to {self.name}.set() expected input,'
                                 f' {value}, to be in '
                                 f'{list(self.parent._locations_data.keys())}')
                raise KeyError(traceback_str) from exc

            # Move all the required 'axes' to their locations in parallel.
            status_list = [super().set(value, **kwargs)]
            for signal, data in location_data.items():
                status_list.append(status_list[-1] &
                                   getattr(self.parent, signal).set(data[0]))

            status_list[0].set_finished()  # The super().set() never completes!
            output_status = status_list[-1]

            return output_status

        def available(self):
            """
            Method that returns the list of available locations.

            Returns
            -------
            self.parent._locations_data.keys() : list
                The list of 'locations' that this device has defined.
            """

            return list(self.parent._locations_data.keys())

    def __init__(self, *args, locations_data=None, **kwargs):
        """
        Initializes the DeviceWithLocations device class, passing *args
        and **kwargs through to parent.__init__(...) and adding some child
        class specific attributes. See the class doc-string for parameter
        descriptions.
        """
        super().__init__(*args, **kwargs)
        if locations_data is None:
            locations_data = {}
        self._locations_data = locations_data

        self._LocationsTuple = namedtuple('Locations',
                                         self._locations_data.keys())

    locations = Component(LocationSignal, name='locations',
                          kind='config', labels=('position',))


# noinspection PyUnresolvedReferences
class Diagnostic(DeviceWithLocations):
    """
    DeviceWithLocations ophyd Device used for ARI & SXN 'Diagnostic' units.

    The ARI & SXN diagnostic units consist of a movable blade that
    holds a number of diagnostic elements (e.g. a YaG screen, a photo-diode,
    a multilayer mirror, ...) as well as an additional movable filter (e.g.
    with an Al coated YaG screen for use with the multilayer mirror). They
    also have a camera, for viewing the image on the filter or blade YaG
    screens. Optionally, via the `photodiode` kwarg, a photodiode can also
    be included. It also has a 'locations' attribute that is an ophyd signal
    that returns a list of 'locations' that the device is currently 'in'
    when read and can be 'set' to any one of the locations predefined in
    the kwarg locations_data.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent 'DeviceWithLocations' class
    photodiode : bool
        A boolean indicating if the diagnostic contains a photodiode or not
    **kwargs : keyword arguments
        The keyword arguments passed to the parent 'Device' class

    Attributes
    ----------
    *attrs : many
        The attributes of the parent `DeviceWithLocations` class.

    Methods
    -------
    *methods : many
        The methods of the parent `DeviceWithLocations` class.
    __init__(*args, **kwargs) :
        Runs the parent `DeviceWithLocations` __init__() method, adds some
        symlinks to, and renames, existing attributes and then updates the
        'kind' attribute on a few attributes.
    trigger() :
        Calls the parent `DeviceWithLocations` trigger method, the child camera
        trigger method, and the child currents trigger method and returns a
        combined status object.
    """

    def __init__(self, *args, photodiode=False, **kwargs):
        super().__init__(*args, **kwargs)
        # Update the 'name' of the self.camera.cam.array_data
        getattr(self, 'camera.cam.array_data').name = f'{self.name}_camera'

        if photodiode:
            current_signals = {'current2': 'photodiode'}
        else:
            current_signals = {}
        # the list of ```currents.current*``` attributes
        current_names = ['current1', 'current2', 'current3', 'current4']
        currents = getattr(self, 'currents')  # ```self.currents``` attr.

        # for each of the current*.mean_value attrs (* = 1,2,3, or 4)
        for current_name in current_names:
            current = getattr(currents, current_name)
            if current_name in current_signals.keys():
                current.mean_value.name = (f'{self.name}_'
                                           f'{current_signals[current_name]}')
                setattr(self, current_signals[current_name], current)
            else:
                current.mean_value.kind = 'omitted'  # Omit unused currents

    blade = Component(ID29EpicsMotor, 'multi_trans', name='blade',
                      kind='normal', labels=('motor',))
    filter = Component(ID29EpicsMotor, 'yag_trans', name='filter',
                       kind='normal', labels=('motor',))

    camera = Component(Prosilica, 'Camera:', name='camera', kind='normal',
                       labels=('detector',))

    # This is added to allow for the mirror current even if no photodiode exists
    currents = Component(ID29EM, 'Currents:', name='currents',
                         kind='normal', labels=('detector',))

    def trigger(self):
        """
        A trigger functions that also triggers the currents quad_em and camera
        """

        # resolves a connection time-out error, but I have no idea why.
        _ = self.camera.cam.array_counter.read()
        # trigger the child components that need it
        camera_status = self.camera.trigger()
        currents_status = self.currents.trigger()
        # Call the parent trigger
        super_status = super().trigger()

        output_status = camera_status & currents_status & super_status

        return output_status


class BaffleSlit(DeviceWithLocations):
    """
    A DeviceWithLocations ophyd Device used for ARI & SXN 'Baffle Slit' units.

    The ARI & SXN baffle slit units consist of four movable blades that can be
    used to 'trim' the beam. The current to ground can be read from each of
    these blades as well which gives a way to determine the 'position' of the
    beam at the baffle slit location in real time. The baffle slit units also
    have a 'set_location' method that allows the user to quickly move to the
    locations defined by the 'locations' argument, this could be used to quickly
    move the blades to the pre-determined 'operation' position. The 'location'
    attribute is a read-only ophyd signal that returns a list of 'locations'
    that the device is currently 'in'.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the grandparent 'Device' class
    **kwargs : keyword arguments
        The keyword arguments passed to the grandparent 'Device' class

    Attributes
    ----------
    *attrs : many
        The attributes of the parent `DeviceWithLocations` class.

    Methods
    -------
    *methods : many
        The methods of the parent `DeviceWithLocations` class.
    __init__(*args, **kwargs) :
        Runs the parent `DeviceWithLocations` __init__() method, adds some
        symlinks to, and renames, existing attributes and then updates the
        'kind' attribute on a few attributes.
    trigger() :
        Calls the parent `DeviceWithLocations` trigger method and the child
        currents trigger method and returns a combined status object.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # names to give the ```currents.current*.mean_value``` components
        current_signals = {'current1': 'top', 'current2': 'bottom',
                           'current3': 'inboard', 'current4': 'outboard'}
        # the list of ```currents.current*``` attributes
        current_names = ['current1', 'current2', 'current3', 'current4']
        currents = getattr(self, 'currents')  # ```self.currents``` attr.

        # for each of the current*.mean_value attrs (* = 1,2,3, or 4)
        for current_name in current_names:
            current = getattr(currents, current_name)
            if current_name in current_signals.keys():
                current.mean_value.name = (f'{self.name}_currents_'
                                           f'{current_signals[current_name]}')
                setattr(currents, current_signals[current_name], current)
            else:
                current.mean_value.kind = 'omitted'

    # The 4 blade motor components
    top = Component(ID29EpicsMotor, 'Top', name='top', kind='normal',
                    labels=('motor',))
    bottom = Component(ID29EpicsMotor, 'Bottom', name='bottom',
                       kind='normal', labels=('motor',))
    inboard = Component(ID29EpicsMotor, 'Inboard', name='inboard',
                        kind='normal', labels=('motor',))
    outboard = Component(ID29EpicsMotor, 'Outboard', name='outboard',
                         kind='normal', labels=('motor',))
    # The current read-back of the 4 blades.
    currents = Component(ID29EM, 'Currents:', name='currents',
                         kind='normal', labels=('detector',))

    def trigger(self):
        """
        A trigger functions that includes a call to trigger the currents quad_em
        """

        currents_status = self.currents.trigger()
        super_status = super().trigger()

        output_status = currents_status & super_status
        return output_status
