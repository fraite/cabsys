import unittest

import cabsys.iec.iec_constants as iec
import cabsys.quantity.quantity_constants as dc
import cabsys.iec.iec_extra as iec_extra
from cabsys.data_classes.auto_cable import AutoCable
from cabsys.data_classes.auto_install import AutoInstall, AutoPlacedCable, AutoCableSet
from cabsys import InstallState
from tests.test_objects import default_install


class TestExtra(unittest.TestCase):

    def test_w_cable(self):
        """test losses"""

        cable = AutoCable(name='my_cable')
        cable.number_cores = iec.SINGLE_CORE

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcb = AutoPlacedCable()
        pcb.cable = cable
        cs = AutoCableSet(name='my_cable_set')
        cs.bonding = iec.CROSS_BONDED
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        install = AutoInstall()
        install.cable_sets = [cs]

        install_state = InstallState(install)

        cable_set_state = install_state.cable_set_states[0]
        cable_state = cable_set_state.placed_cable_states[0].cable_state
        cable_state.set_quantity('R', 10.2056653e-6, 'ohm/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('wd', 4.1197699, 'W/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('sheath_temp', 73.7044, '', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('lambda_1', 0.108114, '', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('lambda_2', 0.0, '', source=dc.ATTR_USER_STATE_SET)
        result = iec_extra.calc_w_cable(install, 0, 0, 2031.2526, state=install_state)
        self.assertEqual(round(50.7807258, 6), round(result.value, 6), "heat loss of cable")

        install = default_install()
        result = iec_extra.calc_w_cable(install, 0, 0, 2014.606)
        self.assertEqual(round(50.96627, 5), round(result.value, 5), "heat loss of cable")