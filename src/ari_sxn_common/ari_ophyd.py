from common_ophyd import (BaffleSlit, Diagnostic, DeviceWithLocations)
from ophyd import (Component, EpicsMotor)
from ophyd.signal import EpicsSignalRO


class M1(DeviceWithLocations):
    """
    The ophyd `Device` that is used to talk to the ARI M1 mirror section.

    The ARI M1 mirror section consists of the M1 mirror chamber, the beam
    -pipe, the associated Diagnostic and BaffleSlit sub-devices and the
    motors, detectors and vacuum signals for these. It is designed to
    provide an intuitive, tab-to-complete based, interface to find all
    the components associated with the M1 mirror.
    """
    def __init__(self, *args, **kwargs):
        """
        A new __init__ method that links photocurrent to the self.diag quadem
        """
        super().__init__(*args, **kwargs)
        self.diag.currents.current1.mean_value.name = f'{self.name}_photocurrent'
        self.diag.currents.current1.mean_value.kind = 'normal'
        setattr(self, 'photocurrent', self.diag.currents.current1.mean_value)

    # Mirror motor axes
    Ry_coarse = Component(EpicsMotor, 'Ry_coarse', name='Ry_coarse',
                          kind='normal', labels=('motor',))
    Ry_fine = Component(EpicsMotor, 'Ry_fine', name='Ry_fine',
                        kind='normal', labels=('motor',))
    Rz = Component(EpicsMotor, 'Rz', name='Rz', kind='normal',
                   labels=('motor',))
    x = Component(EpicsMotor, 'x', name='x', kind='normal', labels=('motor',))
    y = Component(EpicsMotor, 'y', name='y', kind='normal', labels=('motor',))

    # Mirror chamber vacuum axes
    ccg = Component(EpicsSignalRO, "ccg", name='ccg', kind='config',
                    labels=('detector',))
    tcg = Component(EpicsSignalRO, "tcg", name='tcg', kind='config',
                    labels=('detector',))
    ip = Component(EpicsSignalRO, "ip", name='ip', kind='config',
                   labels=('detector',))

    # baffle slit sub-device
    slits = Component(BaffleSlit, "baffle:", name='slits', kind='normal',
                      labels=('device',),
                      locations_data={'in': {'top': (-12.7, 0.1),
                                             'bottom': (12.7, 0.1),
                                             'inboard': (12.7, 0.1),
                                             'outboard': (-12.7, 0.1)},
                                      'centre': {'top': (0, 0.1),
                                                 'bottom': (0, 0.1),
                                                 'inboard': (0, 0.1),
                                                 'outboard': (0, 0.1)},
                                      'nominal': {'top': (12.7, 0.1),
                                                  'bottom': (-12.7, 0.1),
                                                  'inboard': (-12.7, 0.1),
                                                  'outboard': (12.7, 0.1)},
                                      'out': {'top': (28, 0.1),
                                              'bottom': (-28, 0.1),
                                              'inboard': (-28, 0.1),
                                              'outboard': (28, 0.1)}})

    # diagnostic sub-device
    diag = Component(Diagnostic, "diag:", name='diag', kind='normal',
                     labels=('device',),
                     locations_data={'Out': {'blade': (0, 1)},
                                     'YaG': {'blade': (-31.75, 1),
                                             'filter': (0, 1)},
                                     'ML250': {'blade': (-63.5, 1),
                                               'filter': (-25, 1)},
                                     'ML700': {'blade': (-95.25, 1),
                                               'filter': (-25, 1)}})

    def trigger(self):
        """
        A trigger function that adds triggering of the baffleslit and diagnostic
        """

        # This appears to resolve a connection time-out error, but I have no idea why.
        _ = self.diag.camera.cam.array_counter.read()

        super_status = super().trigger()

        # trigger the child components that need it
        baffle_status = self.slits.trigger()
        diag_status = self.diag.trigger()

        # Not sure why but status = status & status & status fails to complete
        child_status = baffle_status & diag_status
        output_status = child_status & super_status

        return output_status

    def test_structure(self):
        """
        Test method add later
        """

        output = {i: (getattr(self, i).test_structure
                      if hasattr(getattr(self, i), 'test_structure')
                      else None)
                  for i in self._signals.keys()}

        return output
