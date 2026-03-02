import unittest

import cabsys.iec.iec_constants as iec
import cabsys.quantity.quantity_constants as dc
import cabsys.iec.iec60287_2_1 as iec60287_2_1w
from cabsys.data_classes.auto_cable import AutoCable
from cabsys import InstallState
from cabsys.data_classes.auto_install import AutoCableSet, AutoPlacedCable, AutoInstall
# from cabsys.data_classes.project import Project


class TestIEC60287p1p1(unittest.TestCase):

    def test_t1_4_1_2(self):
        """calculate T1 for single core cables"""
        cab = AutoCable(name='my_cable')
        cab.sheath_type = iec.WELDED_AL_SHEATH
        cab.conductor.dia.value = 66.0
        cab.sheath.dia_under_sheath = 128.0
        cab.core.insulation_material = iec.INS_XLPE_UNFILLED
        cab.design_volts = 220.0
        cab.number_cores = iec.SINGLE_CORE
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 138.2

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcr.x = 0.0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcy.x = -500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cab
        pcb.x = 500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        install = AutoInstall(name='my install')
        install.cable_sets.append(cs)
        install.kind = iec.BURIED

        result = iec60287_2_1w.calc_t1(install, 0, 0)
        self.assertEqual(round(0.36897118, 5), round(result.value, 5), 'T1 flat spaced')

    def test_t1_4_1_2_1_single_core(self):
        """calculate T1 for single core cables"""
        cab = AutoCable(name='my_cable')
        cab.sheath_type = iec.WELDED_AL_SHEATH
        cab.conductor.dia.value = 66.0
        cab.sheath.dia_under_sheath = 128.0
        cab.core.insulation_material = iec.INS_XLPE_UNFILLED
        cab.design_volts = 220.0
        cab.number_cores = iec.SINGLE_CORE
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 138.2

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcr.x = 0.0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcy.x = -500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cab
        pcb.x = 500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        install = AutoInstall(name='my install')
        install.cable_sets.append(cs)
        install.kind = iec.BURIED

        result = iec60287_2_1w.calc_t1_4_1_2_1(install, 0, 0)
        self.assertEqual(round(0.36897118, 5), round(result.value, 5), 'T1 flat spaced')

        pcr.x = 0.0
        pcr.y = 969.1
        pcy.x = -69.1
        pcy.y = 1088.8
        pcb.x = 69.1
        pcb.y = 1088.8

        result = iec60287_2_1w.calc_t1_4_1_2_1(install, 0, 0)
        self.assertEqual(round(0.36897118, 5), round(result.value, 5), 'T1 trefoil 100% coverage')

        cab.design_volts = 220.0
        cab.number_cores = iec.SINGLE_CORE
        cab.sheath_type = iec.CWS_SHEATH
        cab.conductor.dia.value = 66.0
        cab.core.insulation_material = iec.INS_XLPE_UNFILLED
        cab.wire_screen.dia_under_wire = 128.2
        cab.wire_screen.dia = 131.8
        cab.wire_screen.wire_size = 1.8
        cab.wire_screen.number_wires = 100
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 142.0

        pcr.x = 0.0
        pcr.y = 971.0
        pcy.x = -71.0
        pcy.y = 1094.0
        pcb.x = 71.0
        pcb.y = 1094.0

        install.config.non_metal_screen_isotherm = False
        result = iec60287_2_1w.calc_t1_4_1_2_1(install, 0, 0)
        self.assertEqual(round(0.42902, 5), round(result.value, 5), 'T1 trefoil 44% coverage, not strict IEC')

        # check if strict IEC, that exception raised as IEC does not include voltage > 76 kV
        install.config.non_metal_screen_isotherm = True
        self.assertRaises(Exception, iec60287_2_1w.calc_t1_4_1_2_1, install, 0, 0)

        cab.design_volts = 76.0
        install.config.non_metal_screen_isotherm = True
        result = iec60287_2_1w.calc_t1_4_1_2_1(install, 0, 0)
        self.assertEqual(round(0.42902, 5), round(result.value, 5), 'T1 trefoil 44% coverage, U0 = 76 kV')

        cab.design_volts = 18.0
        result = iec60287_2_1w.calc_t1_4_1_2_1(install, 0, 0)
        self.assertEqual(round(0.3957297, 5), round(result.value, 5), 'T1 trefoil 44% coverage, U0 = 18 kV')

        cab.wire_screen.number_wires = 25
        result = iec60287_2_1w.calc_t1_4_1_2_1(install, 0, 0)
        self.assertEqual(round(0.369841, 5), round(result.value, 5),
                         'T1 trefoil 11% coverage, U0 = 18 kV, strict_IEC')

        install.config.non_metal_screen_isotherm = False
        cab.wire_screen.number_wires = 25
        result = iec60287_2_1w.calc_t1_4_1_2_1(install, 0, 0)
        self.assertEqual(round(0.369841*1.07, 5), round(result.value, 5),
                         'T1 trefoil 11% coverage, U0 = 18 kV, not strict_IEC')

    def test_t1_thermal_thickness(self):
        """Calculate thermal thickness t1"""
        cab = AutoCable(name='my_cable')
        cab.number_cores = iec.SINGLE_CORE
        cab.conductor.dia.value = 20.0
        cab.sheath_type = iec.PB_SHEATH
        cab.sheath.dia_under_sheath = 30.0
        # cable_state = CableState()
        # cable_state.set_attr('r_dash', 8.88e-6, 'ohm/m')
        result = iec60287_2_1w.calc_t1_thermal_thickness(cab)
        self.assertEqual(round(5.0, 11), round(result.value, 11), 't1 thickness')

    def test_t3_thermal_thickness(self):
        """Calculate thermal thickness t3"""
        cab = AutoCable(name='my_cable')
        cab.number_cores = iec.SINGLE_CORE
        cab.conductor.dia.value = 20.0
        cab.sheath_type = iec.PB_SHEATH
        cab.sheath.dia_under_sheath = 30.0
        cab.sheath.dia = 33.0
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 43.2

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcr.x = 0.0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcy.x = -500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cab
        pcb.x = 500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        install = AutoInstall(name='my install')
        install.cable_sets.append(cs)
        install.kind = iec.BURIED
        # cable_state = CableState()
        # cable_state.set_attr('r_dash', 8.88e-6, 'ohm/m')
        result = iec60287_2_1w.calc_t3_thermal_thickness(install, 1, 1)
        self.assertEqual(round(5.1, 11), round(result.value, 11), 't3 thickness')

    def test_t3_4_1_4(self):
        """calculate T3"""
        cab = AutoCable(name='my_cable')
        cab.sheath_type = iec.WELDED_AL_SHEATH
        cab.conductor.dia.value = 66.0
        cab.sheath.dia_under_sheath = 128.0
        cab.sheath.dia = 130.2
        cab.core.insulation_material = iec.INS_XLPE_UNFILLED
        cab.design_volts = 220.0
        cab.number_cores = iec.SINGLE_CORE
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 138.2
        cab.armour = iec.NONE

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcr.x = 0.0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcy.x = -500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cab
        pcb.x = 500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        install = AutoInstall(name='my install')
        install.cable_sets.append(cs)
        install.kind = iec.BURIED

        result = iec60287_2_1w.calc_t3(install, 0, 0)
        self.assertEqual(round(0.033217, 5), round(result.value, 5), 'T1 flat spaced')

    def test_t1_4_1_4_1_single_core(self):
        """calculate T3 for single core cables"""
        cab = AutoCable(name='my_cable')
        cab.sheath_type = iec.WELDED_AL_SHEATH
        cab.conductor.dia.value = 66.0
        cab.sheath.dia_under_sheath = 128.0
        cab.sheath.dia = 130.2
        cab.core.insulation_material = iec.INS_XLPE_UNFILLED
        cab.design_volts = 220.0
        cab.number_cores = iec.SINGLE_CORE
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 138.2
        cab.armour = iec.NONE

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcr.x = 0.0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcy.x = -500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cab
        pcb.x = 500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        install = AutoInstall(name='my install')
        install.cable_sets.append(cs)
        install.kind = iec.BURIED

        result = iec60287_2_1w.calc_t3_4_1_5_1(install, 0, 0)
        self.assertEqual(round(0.033217, 5), round(result.value, 5), 'T3 flat spaced')

        pcr.x = 0.0
        pcr.y = 969.1
        pcy.x = -69.1
        pcy.y = 1088.8
        pcb.x = 69.1
        pcb.y = 1088.8

        result = iec60287_2_1w.calc_t3_4_1_5_1(install, 0, 0)
        self.assertEqual(round(0.0531456, 5), round(result.value, 5), 'T3 trefoil 100% coverage')

        cab.design_volts = 220.0
        cab.number_cores = iec.SINGLE_CORE
        cab.sheath_type = iec.CWS_SHEATH
        cab.conductor.dia.value = 66.0
        cab.core.insulation_material = iec.INS_XLPE_UNFILLED
        cab.wire_screen.dia_under_wire = 128.2
        cab.wire_screen.dia = 131.8
        cab.wire_screen.wire_size = 1.8
        cab.wire_screen.number_wires = 100
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 141.8

        pcr.x = 0.0
        pcr.y = 971.0
        pcy.x = -71.0
        pcy.y = 1094.0
        pcb.x = 71.0
        pcb.y = 1094.0

        result = iec60287_2_1w.calc_t3_4_1_5_1(install, 0, 0)
        self.assertEqual(round(0.065180, 5), round(result.value, 5), 'T3 trefoil 44% coverage, not strict IEC')

        # check if strict IEC, that exception raised as IEC does not include voltage > 76 kV
        # self.assertRaises(Exception, iec60287_2_1w.calc_t1_4_1_2_1, install, 0, 0, True)

        cab.design_volts = 76.0
        install.config.non_metal_screen_isotherm = True
        result = iec60287_2_1w.calc_t3_4_1_5_1(install, 0, 0)
        self.assertEqual(round(0.065180, 5), round(result.value, 5), 'T3 trefoil 44% coverage, U0 = 76 kV')

        cab.wire_screen.number_wires = 25
        result = iec60287_2_1w.calc_t3_4_1_5_1(install, 0, 0)
        self.assertEqual(round(0.040737, 5), round(result.value, 5),
                         'T3 trefoil 11% coverage, U0 = 18 kV, strict_IEC')

        install.config.non_metal_screen_isotherm = False
        cab.wire_screen.number_wires = 25
        result = iec60287_2_1w.calc_t3_4_1_5_1(install, 0, 0)
        self.assertEqual(round(0.065180, 5), round(result.value, 5),
                         'T3 trefoil 11% coverage, U0 = 18 kV, not strict_IEC')

    # tables

    def test_rho_t_insu(self):
        """find thermal resistivity of material"""
        cable = AutoCable(name='my_cable')
        cable.core.insulation_material.value = iec.INS_EPR
        cable.design_volts.value = 76.0
        result = iec60287_2_1w.find_insulation_rho_1(cable.core.insulation_material, cable.design_volts)
        self.assertEqual(round(5.0, 11), round(result.value, 11), 'calculated insulation resistance')
        cable.design_volts.value = 2.0
        result = iec60287_2_1w.find_insulation_rho_1(cable.core.insulation_material, cable.design_volts)
        self.assertEqual(round(3.5, 11), round(result.value, 11), 'calculated insulation resistance')

    def test_rho_t_serving(self):
        """find thermal resistivity of material"""
        cable = AutoCable(name='my_cable')
        cable.serving.material = iec.SERVING_PVC
        cable.design_volts = 76.0
        result = iec60287_2_1w.find_serving_rho_t(cable)
        self.assertEqual(round(6.0, 11), round(result.value, 11), 'calculated serving resistance')
        cable.design_volts = 2.0
        result = iec60287_2_1w.find_serving_rho_t(cable)
        self.assertEqual(round(5.0, 11), round(result.value, 11), 'calculated serving resistance')
        cable.sheath_type = iec.CAS_SHEATH
        result = iec60287_2_1w.find_serving_rho_t(cable)
        self.assertEqual(round(6.0, 11), round(result.value, 11), 'calculated serving resistance')

    def test_air_arrangement(self):
        cable = AutoCable(name='my_cable')
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 50.0

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.phase = iec.YELLOW
        pcr.x = 0
        pcr.y = 900.0
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.phase = iec.RED
        pcy.x = 500.0
        pcy.y = 900.0
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.phase = iec.BLUE
        pcb.x = -500.0
        pcb.y = 900.0
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        result = iec60287_2_1w.calc_air_arrangement(cs, 0)
        self.assertEqual(iec.AIR_SINGLE_CABLE, result.value, "flat spaced")

        pcy.x = 50.0
        pcb.x = -50.0
        result = iec60287_2_1w.calc_air_arrangement(cs, 0)
        self.assertEqual(iec.AIR_THREE_CABLES_TOUCHING_HORIZONTAL, result.value, "flat touching")

        pcy.x = 0.0
        pcb.x = -0.0
        pcy.y = 850.0
        pcb.y = 950.0
        result = iec60287_2_1w.calc_air_arrangement(cs, 0)
        self.assertEqual(iec.AIR_THREE_CABLES_TOUCHING_VERTICAL, result.value, "vertical touching")

        pcy.x = 0.0
        pcb.x = -0.0
        pcy.y = 800.0
        pcb.y = 1000.0
        result = iec60287_2_1w.calc_air_arrangement(cs, 0)
        self.assertEqual(iec.AIR_THREE_CABLES_SPACED_DE_VERTICAL, result.value, "vertical spaced")

    def test_h(self):
        cable = AutoCable(name='my_cable')
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.phase = iec.YELLOW
        pcr.x = 0
        pcr.y = 900.0
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.phase = iec.RED
        pcy.x = 500.0
        pcy.y = 900.0
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.phase = iec.BLUE
        pcb.x = -500.0
        pcb.y = 900.0
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        result = iec60287_2_1w.calc_h_4_2_1_1(cs, 0)
        self.assertEqual(round(4.628517, 6), round(result.value, 6), "flat spaced")

        pcy.x = 138.2
        pcb.x = -138.2
        result = iec60287_2_1w.calc_h_4_2_1_1(cs, 0)
        self.assertEqual(round(2.966868, 6), round(result.value, 6), "flat spaced")

        pcy.x = 0.0
        pcb.x = -0.0
        pcy.y = 900.0 - 138.2
        pcb.y = 900.0 + 138.2
        result = iec60287_2_1w.calc_h_4_2_1_1(cs, 0)
        self.assertEqual(round(2.8117967, 6), round(result.value, 6), "vertical touching")

        pcy.x = 0.0
        pcb.x = -0.0
        pcy.y = 900.0 - 276.4
        pcb.y = 900.0 + 276.4
        result = iec60287_2_1w.calc_h_4_2_1_1(cs, 0)
        self.assertEqual(round(3.94612032, 6), round(result.value, 6), "vertical spaced")

    def test_k_a(self):
        cable = AutoCable(name='my_cable')
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2
        cable.number_cores = iec.SINGLE_CORE

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcb = AutoPlacedCable()
        pcb.cable = cable
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        install = AutoInstall(name='my_install')
        install.cable_sets = [cs]

        install_state = InstallState(install)
        cable_set_state = install_state.cable_set_states[0]
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('h', 4.628516685, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_1', 0.115261894, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_2', 0.0, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('T_1', 0.36897118, 'mm',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('T_2', 0.0, 'mm',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('T_3', 0.0332165335, 'mm',
                                                                        source=dc.ATTR_USER_STATE_SET)
        result = iec60287_2_1w.calc_k_a_4_2_1_1(install, 0, 0, 90.0, 47.48417, state=install_state)
        self.assertEqual(round(0.73158767, 6), round(result.value, 6), "k_a flat spaced")

    def test_theta_d(self):
        cable = AutoCable(name='my_cable')
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2
        cable.number_cores = iec.SINGLE_CORE

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcb = AutoPlacedCable()
        pcb.cable = cable
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        install = AutoInstall(name='my_install')
        install.cable_sets = [cs]

        install_state = InstallState(install)
        cable_set_state = install_state.cable_set_states[0]
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('wd', 4.11976986691, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_1', 0.115261894, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_2', 0.0, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('T_1', 0.36897118, 'mm',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('T_2', 0.0, 'mm',
                                                                        source=dc.ATTR_USER_STATE_SET)
        result = iec60287_2_1w.calc_delta_theta_d_4_2_1_1(install, 0, 0, 90.0, 47.48417, state=install_state)
        self.assertEqual(round(0.6029388674, 6), round(result.value, 6), "delta theta_d flat spaced")

    def test_theta_s_t4(self):
        cable = AutoCable(name='my_cable')
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2
        cable.number_cores = iec.SINGLE_CORE

        pcr = AutoPlacedCable()
        pcr.cable = cable
        # pcr.ambient_theta = 15.0
        pcy = AutoPlacedCable()
        pcy.cable = cable
        # pcy.ambient_theta = 15.0
        pcb = AutoPlacedCable()
        pcb.cable = cable
        # pcb.ambient_theta = 15.0
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        install = AutoInstall(name='my_install')
        install.cable_sets = [cs]
        install.auto_ambient_theta = 15.0

        install_state = InstallState(install)
        cable_set_state = install_state.cable_set_states[0]
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('wd', 4.11976986691, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_1', 0.115261894, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_2', 0.0, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('T_1', 0.36897118, 'mm',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('T_2', 0.0, 'mm',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('h', 4.628516685, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('T_3', 0.0332165335, 'mm',
                                                                        source=dc.ATTR_USER_STATE_SET)
        result = iec60287_2_1w.calc_delta_theta_s_4_2_1_1(install, 0, 0, 90.0, 47.48417)
        self.assertEqual(round(2.30353848, 6), round(result.value, 6), "delta theta_s flat spaced")

        result = iec60287_2_1w.calc_t4_4_2_1_1(install, 0, 0, 90.0, 47.48417, state=install_state)
        self.assertEqual(round(0.216025381, 6), round(result.value, 6), "T4 air protected flat spaced")


if __name__ == '__main__':
    unittest.main()
