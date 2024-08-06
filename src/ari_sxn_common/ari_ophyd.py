from common_ophyd import (BaffleSlit, Diagnostic, DeviceWithLocations,
                          ID29EpicsMotor, ID29EpicsSignalRO,
                          ID29TwoButtonShutter)
from ophyd import Component



class M1(DeviceWithLocations):
    """
    The ophyd `Device` that is used to talk to the ARI M1 mirror section.

    The ARI M1 mirror section consists of the M1 mirror chamber, the beam
    -pipe, the associated Diagnostic and BaffleSlit sub-devices and the
    motors, detectors and vacuum signals for these. It is designed to
    provide an intuitive, tab-to-complete based, interface to find all
    the components associated with the M1 mirror.

    Parameters
    ----------
    *args : arguments
        The arguments passed to the parent `DeviceWithLocations` class
    **kwargs : keyword arguments
        The keyword arguments passed to the parent `DeviceWithLocations` class

    Attributes
    ----------
    *attrs : many
        The attributes of the parent `DeviceWithLocations` class.
    Ry_coarse : ID29EpicsMotor
        The motor for coarse mirror rotation around the y axis.
    Ry_fine : ID29EpicsMotor
        The motor for fine mirror rotation around the y axis.
    Rz : ID29EpicsMotor
        The motor for mirror rotation around the z axis.
    x : ID29EpicsMotor
        The motor for mirror motion along the x axis.
    y : ID29EpicsMotor
        The motor for mirror motion along the y axis.
    ccg : ID29EpicsSignalRO
        The cold cathode gauge reading in the mirror chamber
    tcg : ID29EpicsSignalRO
        The thermo-couple (Pirani) gauge reading in the mirror chamber
    ip : ID29EpicsSignalRO
        The ion pump reading in the mirror chamber
    slits : BaffleSlit
        The baffle slit downstream of the mirror chamber
    diag : Diagnostic
        The diagnostic device downstream of the mirror chamber

    Methods
    -------
    *methods : many
        The methods of the parent `DeviceWithLocations` class.
    trigger() :
        Runs the trigger methods from the parent `DeviceWithLocations` class,
        the child `BaffleSlit` class, and the child `Diagnostic` class and
        returns a combination of all of the status objects.
    """
    def __init__(self, *args, **kwargs):
        """
        A new __init__ method that links photocurrent to the self.diag quadem
        """
        super().__init__(*args, **kwargs)
        self.diag.currents.current1.mean_value.name = (f'{self.name}'
                                                       f'_photocurrent')
        self.diag.currents.current1.mean_value.kind = 'hinted'
        setattr(self, 'photocurrent', self.diag.currents.current1.mean_value)

    # Mirror motor axes
    Ry_coarse = Component(ID29EpicsMotor, 'Ry_coarse', name='Ry_coarse',
                          kind='normal', labels=('motor',))
    Ry_fine = Component(ID29EpicsMotor, 'Ry_fine', name='Ry_fine',
                        kind='normal', labels=('motor',))
    Rz = Component(ID29EpicsMotor, 'Rz', name='Rz', kind='normal',
                   labels=('motor',))
    x = Component(ID29EpicsMotor, 'x', name='x', kind='normal',
                  labels=('motor',))
    y = Component(ID29EpicsMotor, 'y', name='y', kind='normal',
                  labels=('motor',))

    # Mirror chamber vacuum axes
    ccg = Component(ID29EpicsSignalRO, "ccg", name='ccg', kind='config',
                    labels=('detector',))
    tcg = Component(ID29EpicsSignalRO, "tcg", name='tcg', kind='config',
                    labels=('detector',))
    ip = Component(ID29EpicsSignalRO, "ip", name='ip', kind='config',
                   labels=('detector',))
    gv = Component(ID29TwoButtonShutter, "gv:", name='gv', kind='config',
                   labels=('position',))


    # baffle slit sub-device
    slits = Component(BaffleSlit, "baffle:", name='slits', kind='normal',
                      labels=('device',),
                      locations_data={'all_in': {'top': (-12.7, 0.1),
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
                                      'all_out': {'top': (28, 0.1),
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

        super_status = super().trigger()

        # trigger the child components that need it
        baffle_status = self.slits.trigger()
        diag_status = self.diag.trigger()

        output_status = baffle_status & super_status & diag_status

        return output_status
