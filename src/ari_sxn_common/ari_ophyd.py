from common_ophyd import BaffleSlit, Diagnostic
from ophyd import (Component, Device, EpicsMotor)
from ophyd.signal import EpicsSignalRO

class M1(Device):
    """
    The ophyd `Device` that is used to talk to the ARI M1 mirror section.

    The ARI M1 mirror section consists of the M1 mirror chamber, the beam
    -pipe, the associated Diagnostic and BaffleSlit sub-devices and the
    motors, detectors and vacuum signals for these. It is designed to
    provide an intuitive, tab-to-complete based, interface to find all of
    the components associated with the M1 mirror.
    """

    # Mirror motor axes
    Ry_coarse = Component(EpicsMotor, 'Ry_coarse', name='Ry_coarse',
                          kind='config')
    Ry_fine = Component(EpicsMotor, 'Ry_fine', name='Ry_fine',
                        kind='config')
    Rz = Component(EpicsMotor, 'Rz', name='Rz', kind='config')
    x = Component(EpicsMotor, 'x', name='x', kind='config')
    y = Component(EpicsMotor, 'y', name='y', kind='config')

    # Mirror chamber vacuum axes
    ccg = Component(EpicsSignalRO, "ccg", name='ccg', kind='config')
    tcg = Component(EpicsSignalRO, "tcg", name='tcg', kind='config')
    ip = Component(EpicsSignalRO, "ip", name='ip', kind='config')

    # baffle slit sub-device
    baffle = Component(BaffleSlit, "baffle", name='baffle', kind='normal')

    # diagnostic sub-device
    diag = Component(Diagnostic, "diag", name='diag', kind='normal')

    def trigger(self):
        '''
        A trigger function that adds triggering of the baffleslit and diagnostic
        '''

        # trigger the child components that need it
        baffle_status = self.baffle.trigger()
        diag_status = self.diag.trigger()
        super_status = super().trigger()

        output_status = baffle_status & diag_status & super_status

        return output_status


