from ophyd import (Component, Device, EpicsMotor)
from ophyd.areadetector.base import ADComponent
from ophyd.areadetector.cam import ProsilicaDetectorCam
from ophyd.areadetector.detectors import ProsilicaDetector
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.quadem import NSLS_EM, QuadEMPort
from ophyd.signal import InternalSignal, EpicsSignalRO
from ophyd.status import wait


class ID29EM(NSLS_EM):
    """
    A 29-ID specific version of the NSLS_EM quadEM device.

    The main difference between this and the ophyd standard is adjusting
    the 'kind' of the signals to match what is required at 29-ID.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent 'Device' class
    **kwargs : keyword arguments
            The keyword arguments passed to the parent 'Device' class
    """
    conf = Component(QuadEMPort, port_name='EM180', kind='config')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove acquire check from staging as this causes a problem with 'self.unstage()'.
        self.stage_sigs.pop('acquire')
        # Generate a list of signals and sub-devices for this qem
        signals_list = [(signal.dotted_name, signal.item)
                        for signal in self.walk_signals()
                        if '.' not in signal.dotted_name]
        devices_list = [(name, device) for (name, device) in self.walk_subdevices()]
        for (name, device) in signals_list+devices_list:  # step through all attributes
            if name in ['current1', 'current2', 'current3', 'current4']:
                device.kind = 'hinted'  # Hint this signal for proper readback
                device.nd_array_port.put('EM180')  # Set the correct port for this value.
            elif name in ['values_per_read', 'averaging_time', 'integration_time',
                          'num_average', 'num_acquire', 'em_range']:
                device.kind = 'config'  # Set signal to 'config' for proper readback
            elif hasattr(device, 'kind'):
                device.kind = 'omitted'  # set signal to 'omitted' for proper readback


class Prosilica(SingleTrigger, ProsilicaDetector):
    """
    This is a class which adds the cam1.array_data attribute required when not
    image saving.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cam.kind = 'normal'
        self.cam.array_data.kind = 'normal'

    class ProsilicaCam(ProsilicaDetectorCam):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        array_data = ADComponent(EpicsSignalRO, "ArrayData", kind='normal')

    cam = Component(ProsilicaCam, "cam1:", kind='normal')


class DeviceWithLocations(Device):
    # noinspection GrazieInspection
    """
        A child of ophyd.Device that adds a 'location' functionality.

        The location functionality adds new properties (self._locations_data,
        self.available_locations), a new child signal (self.locations) and
        a new method (self.set_location). These allow for a collection of
        'locations' to be defined which can be:
        * set via ```self.set_location(location)```
        * read via ```self.locations.read()```

        The list of available locations to use in the ```self.set_location()```
        method can be found with the ```self.available_locations``` property.
        As the 'locations' attribute is a read-only ophyd component that returns
        a list of 'locations' that the device is currently 'in' this is set to
        ```kind='config'``` by default so that it will be read using
        ```read_configuration()``` and hence recorded in a plans metadata.

        Parameters
        ----------
        *args : arguments
            The arguments passed to the parent 'Device' class
        locations_data : {str: {str:(float, float), ...}, ...}, optional.
            A dictionary mapping the names of 'locations' to a dictionary mapping
            the 'motor name' to a (location position, location precision) tuple for
            the corresponding location. These are used in the 'set_location'
            method on the diagnostic device to quickly move between locations/
            setups for the diagnostic. 'location position' is the value that the
            corresponding 'motor name' axis should be set to when moving to
            'location'. 'location precision' is used to determine if the device
            is in 'location' by seeing if the 'motor name's 'current position'
            is within +/- 'location precision' of 'location position'
        **kwargs : keyword arguments
            The keyword arguments passed to the parent 'Device' class
        """

    class LocationSignal(InternalSignal):
        """
        An InternalSignal class to be used for updating the 'location' signal

        This ophyd.signal.InternalSignal child class is used to provide a
        read only signal that returns a list of locations a
        DeviceWithLocations Device is currently in.

        NOTE: It is an inner class of DeviceWithLocations as it relies on the
        parent having attributes defined by DeviceWithLocations. It updates
        the ```self.get(...)``` method to update its value before calling
        ```super().get(...)```.
        """

        def get(self, **kwargs):
            # Determine the locations we are currently 'in'.
            locations = []
            # Note the next line gives an 'accessing a protected member, _locations_data'
            # warning in my editor. I am accepting the risk !-).
            for location, location_data in self.parent._locations_data.items():
                if all([(data[0] - data[1] < getattr(self.parent, motor).position <
                         data[0] + data[1])
                        for motor, data in location_data.items()]):
                    locations.append(location)
            self.put(locations, internal=True)  # Set the value at read time.

            return super().get(**kwargs)  # run the parent get function.

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

    @property  # An attribute that returns what locations are available.
    def available_locations(self):
        return list(self._locations_data.keys())

    def set_location(self, location):
        """
        A method that will move the device to 'location' if location is
        in self.available_locations.
        """
        try:
            location_data = self._locations_data[location]
        except KeyError as exc:  # raise KeyError with a more helpful traceback message
            traceback_str = (f'A call to {self.name}.set_location expected '
                             f'input, {location}, to be in '
                             f'{list(self._locations_data.keys())}')
            raise KeyError(traceback_str) from exc

        # Move all the required 'axes' to their locations in parallel.
        status_list = []
        for motor, data in location_data.items():
            status_list.append(getattr(self, motor).set(data[0]))
        # Note I am not sure why but wait(*status_list) doesn't work.
        for status in status_list:  # Wait for each move to finish
            wait(status)

    locations = Component(LocationSignal, value=[], name='locations',
                          kind='config')


# noinspection PyUnresolvedReferences
class Diagnostic(DeviceWithLocations):
    """
    A DeviceWithLocations ophyd Device used for ARI & SXN 'Diagnostic' units.

    The ARI & SXN diagnostic units consist of a movable blade that
    holds a number of diagnostic elements (e.g. a YaG screen, a photo-diode,
    a multilayer mirror, ...) as well as an additional movable filter (e.g.
    with an Al coated YaG screen for use with the multilayer mirror). They
    also have a camera, for viewing the image on the filter or blade YaG
    screens, and an electrometer for measuring the current on the photo-diode.
    The diagnostic also has a 'set_location' method that allows the user to quickly
    move to the locations defined by the 'locations' argument. The 'locations'
    attribute is a read-only ophyd signal that returns a list of 'locations' that
    the device is currently 'in'.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent 'DeviceWithLocations' class
    **kwargs : keyword arguments
        The keyword arguments passed to the parent 'Device' class
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update the 'name' of the self.camera.cam.array_data to something more useful
        getattr(self, 'camera.cam.array_data').name = f'{self.name}_camera'
        # names to give the ```currents.current*.mean_value``` in self.read*() dicts.
        current_signals = {'current2': 'photodiode'}
        # the list of ```currents.current*``` attributes
        current_names = ['current1', 'current2', 'current3', 'current4']
        currents = getattr(self, 'currents')  # ```self.currents``` attr.

        # for each of the current*.mean_value attrs (* = 1,2,3, or 4)
        for current_name in current_names:
            current = getattr(currents, current_name)
            if current_name in current_signals.keys():
                current.mean_value.name = f'{self.name}_{current_signals[current_name]}'  # Adjust the name
                setattr(self, current_signals[current_name], current)  # Create a sym-link
            else:
                current.mean_value.kind = 'omitted'  # Omit from reading any currents not used.

    blade = Component(EpicsMotor, 'multi_trans', name='blade',
                      kind='normal')
    filter = Component(EpicsMotor, 'yag_trans', name='filter',
                       kind='normal')

    currents = Component(ID29EM, 'Currents:', name='currents', kind='normal')

    camera = Component(Prosilica, 'Camera:', name='camera', kind='normal')

    def trigger(self):
        '''
        A trigger functions that also triggers the currents quad_em and camera
        '''

        # This appears to resolve a connection time-out error but I have no idea why.
        counter_value = self.camera.cam.array_counter.read()
        # trigger the child components that need it
        currents_status = self.currents.trigger()
        camera_status = self.camera.trigger()
        super_status = super().trigger()

        output_status = currents_status & camera_status & super_status

        return output_status


class BaffleSlit(DeviceWithLocations):
    """
    A DeviceWithLocations ophyd Device used for ARI & SXN 'Baffle Slit' units.

    The ARI & SXN baffle slit units consist of four movable blades that can be used
    to 'trim' the beam. The current to ground can be read from each of these blades
    as well which gives a way to determine the 'position' of the beam at the baffle
    slit location in real time. The baffle slit units also have a 'set_location'
    method that allows the user to quickly move to the locations defined by the
    'locations' argument, this could be used to quickly move the blades to the
    pre-determined 'operation' position. The 'location' attribute is a read-only
    ophyd signal that returns a list of 'locations' that the device is currently
    'in'.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the grandparent 'Device' class
    **kwargs : keyword arguments
        The keyword arguments passed to the grandparent 'Device' class
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # names to give the ```currents.current*.mean_value``` in self.read*() dicts.
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
                                           f'{current_signals[current_name]}')  # Adjust the name
                setattr(currents, current_signals[current_name], current)  # Create a sym-link
            else:
                current.mean_value.kind = 'omitted'  # Omit from reading any currents not used.

    # The 4 blade motor components
    top = Component(EpicsMotor, 'Top', name='top', kind='normal')
    bottom = Component(EpicsMotor, 'Bottom', name='bottom', kind='normal')
    inboard = Component(EpicsMotor, 'Inboard', name='inboard', kind='normal')
    outboard = Component(EpicsMotor, 'Outboard', name='outboard', kind='normal')
    # The current read-back of the 4 blades.
    currents = Component(ID29EM, 'Currents:', name='currents', kind='normal')

    def trigger(self):
        '''
        A trigger functions that includes a call to trigger the currents quad_em
        '''

        currents_status = self.currents.trigger()
        super_status = super().trigger()

        output_status = currents_status & super_status
        return output_status