from ophyd import (Component, Device, EpicsMotor, EpicsSignalRO)
from ophyd.quadem import NSLS_EM, QuadEMPort
from ophyd.signal import InternalSignal
from ophyd.status import wait


class ID29EM(NSLS_EM):
    conf = Component(QuadEMPort, port_name='EM180', kind='hinted')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([(self.acquire_mode, 'Single')])
        signals_list = [(signal.dotted_name, signal.item)
                        for signal in self.walk_signals()
                        if '.' not in signal.dotted_name]
        devices_list = [(name, device) for (name, device) in self.walk_subdevices()]
        for (name, device) in signals_list+devices_list:  # step through all attrs
            if name in ['current1', 'current2', 'current3', 'current4']:
                device.kind = 'normal'
                device.nd_array_port.put('EM180')
            elif name in ['values_per_read', 'averaging_time', 'integration_time',
                          'num_average', 'num_acquire', 'em_range']:
                device.kind = 'config'
            elif hasattr(device, 'kind'):
                device.kind = 'omitted'

    def trigger(self):
        """
        Trigger one acquisition. This is here to resolve an issue
        whereby the built-in quadEM._status object defined by
        quadEM.self._status_type(quadEM) never completes. will need
        to circle back to why that doesn't work at a later date.
        """
        # This is to remove with trigger later when the issue is resolved
        from ophyd.device import Staged
        import time as ttime
        if self._staged != Staged.yes:
            raise RuntimeError(
                "This detector is not ready to trigger."
                "Call the stage() method before triggering."
            )

        # self._status = self._status_type(self)
        self._status = self._acquisition_signal.set(1)
        self.generate_datum(self._image_name, ttime.time(), {})
        return self._status


class DeviceWithLocations(Device):
    # noinspection GrazieInspection
    """
        A child of ophyd.Device that adds a 'location' functionality.

        The location functionality adds new properties (self._locations_data,
        self.available_locations), a new child signal (self.locations) and
        a new method (self.set_location). These allow for a collection of
        'locations' to be defined which can be:
        set via
        ```self.set_location(location)```
        read via
        ```self.locations.read()```
        The list of available locations to use in the ```self.set_location()```
        method can be found with the ```self.available_locations``` property.

        Parameters
        ----------
        *args : arguments
            The arguments passed to the parent 'Device' class
        locations_data : {str: {str:(float, float), ...}, ...}
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
            for location, location_data in self.parent._locations_data.items():
                if all([(data[0] - data[1] < getattr(self.parent, motor).position <
                         data[0] + data[1])
                        for motor, data in location_data.items()]):
                    locations.append(location)
            self.put(locations, internal=True)  # Set the value at read time.

            return super().get(**kwargs)  # run the parent get function.

    def __init__(self, *args, locations_data, **kwargs):
        """
        Initializes the DeviceWithLocations device class, passing *args
        and **kwargs through to parent.__init__(...) and adding some child
        class specific attributes. See the class doc-string for parameter
        descriptions.
        """
        super().__init__(*args, **kwargs)
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
        for status in status_list:  # Wait for each move to finish
            wait(status)

    locations = Component(LocationSignal, value=[], name='locations',
                          kind='normal')


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
    move to the locations defined by the 'locations' argument.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent 'DeviceWithLocations' class
    locations_data : {str: {str:(float, float), ...}, ...}
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
    blade = Component(EpicsMotor, ':multi_trans', name='blade',
                      kind='normal')
    filter = Component(EpicsMotor, ':yag_trans', name='filter',
                       kind='normal')
    photodiode = Component(EpicsSignalRO, ':photodiode',
                           name='photodiode', kind='normal')
    # camera = TO BE ADDED
