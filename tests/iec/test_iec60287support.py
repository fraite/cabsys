import unittest

import cabsys.data_classes.auto_cable
import cabsys.data_classes.auto_install
import cabsys.iec.iec_constants as iec
import cabsys.quantity.quantity_constants as ds
import cabsys.iec.iec60287support as support
from cabsys.data_classes.auto_cable import AutoCable
import cabsys
from cabsys import CableState, Log


class TestSupport(unittest.TestCase):

    def test_get_parameter(self):
        """get parameter case 2: dc resistance overridden"""
        cab = AutoCable(name='my_cable')
        cab.conductor.dc_resistance20 = 7.2e-6
        cab.conductor.alpha20 = 3.93e-3
        # placed_cable_results.set_attr('dc_resistance20', 8.88e-6, 'ohm/m')
        result = support.get_parameter(cab.conductor, 'dc_resistance20', log=Log())
        self.assertEqual(round(7.2e-6, 11), round(result.value, 11), 'get parameter, set as attribute')

    def test_get_parameter_none(self):
        """get parameter case 3: dc resistance overridden"""
        cab = AutoCable(name='my_cable')
        # cab.conductor.dc_resistance20 = 7.2e-6
        cab.conductor.alpha20 = 3.93e-3
        result = support.get_parameter(cab.conductor, 'dc_resistance20', log=Log())
        self.assertEqual(None, result, 'get parameter, not set')

    def test_get_cond_temp_overridden(self):
        """get conductor temperature case 1: result overridden"""
        cab = AutoCable(name='my_cable')
        cab.conductor.dc_resistance20 = 7.2e-6
        cab.conductor.alpha20 = 3.93e-3
        cab.max_cond_temp = 77.7
        cable_state = CableState()
        cable_state.set_quantity('cond_temp', 88.8, '°C', source=ds.ATTR_USER_SET)
        result = support.get_cond_temp(cab, state=cable_state, log=Log())
        self.assertEqual(round(88.8, 11), round(result.value, 11), 'get conductor temperature, result overridden')

    def test_get_cond_temp(self):
        """get conductor temperature case 2: result set as parameter"""
        cab = AutoCable(name='my_cable')
        cab.conductor.dc_resistance20 = 7.2e-6
        cab.conductor.alpha20 = 3.93e-3
        cab.max_cond_temp = 77.7
        # cable_state = CableState()
        # cable_state.set_attr('cond_temp', 88.8, '°C')
        result = support.get_cond_temp(cab)
        self.assertEqual(round(77.7, 11), round(result.value, 11), 'get conductor temperature, set as parameter')

    def test_get_cond_temp_default(self):
        """get conductor temperature case 3: default"""
        cab = AutoCable(name='my_cable')
        cab.conductor.dc_resistance20 = 7.2e-6
        cab.conductor.alpha20 = 3.93e-3
        # cab.max_cond_temp = 77.7
        # cable_state = CableState()
        # cable_state.set_attr('cond_temp', 88.8, '°C')
        result = support.get_cond_temp(cab)
        self.assertEqual(round(90.0, 11), round(result.value, 11), 'get parameter, result overridden')

    def test_find_cond_number(self):
        cab = AutoCable(name='my_cable')
        cab.number_cores = iec.SINGLE_CORE
        pc1 = cabsys.AutoPlacedCable()
        pc1.cable = cab
        pc2 = cabsys.AutoPlacedCable()
        pc2.cable = cab
        pc3 = cabsys.AutoPlacedCable()
        pc3.cable = cab
        cab_set = cabsys.AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.f = 50.0
        cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE
        result = cab_set.find_no_cores(0, log=Log())
        self.assertEqual(iec.SINGLE_CORE, result, 'get number of cores: OK')

    def test_find_cond_number_error(self):
        cab = AutoCable(name='my_cable')
        cab.number_cores = iec.THREE_CORE
        pc1 = cabsys.AutoPlacedCable()
        pc1.cable = cab
        pc2 = cabsys.AutoPlacedCable()
        pc2.cable = cab
        pc3 = cabsys.AutoPlacedCable()
        pc3.cable = cab
        cab_set = cabsys.AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.f = 50.0
        cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE
        with self.assertRaises(Exception):
            cab_set.find_no_cores(0, log=Log())

    def test_find_cable_number(self):
        cab = AutoCable(name='my_cable')
        cab.number_cores = iec.SINGLE_CORE
        pc1 = cabsys.AutoPlacedCable()
        pc1.cable = cab
        pc2 = cabsys.AutoPlacedCable()
        pc2.cable = cab
        pc3 = cabsys.AutoPlacedCable()
        pc3.cable = cab
        cab_set = cabsys.AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.f = 50.0
        cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE
        result = cab_set.find_no_cables(log=Log())
        self.assertEqual(3, result, 'get number of cores: OK')

    def test_sheath_screen_dia(self):
        cab = AutoCable(name='my_cable')
        cab.number_cores = iec.SINGLE_CORE
        cab.serving.material = iec.SERVING_PVC
        cab.serving.dia = 99.7
        cab.wire_screen.material = iec.COPPER
        cab.wire_screen.dia = 87.8
        cab.sheath.material = iec.LEAD
        cab.sheath.dia_under_sheath = 87.9
        cab.sheath.thickness = 0.1
        cab.sheath.dia = 88.7
        cab.tape.material = iec.COPPER
        cab.tape.dia = 91.3
        pc1 = cabsys.AutoPlacedCable()
        pc1.cable = cab
        pc2 = cabsys.AutoPlacedCable()
        pc2.cable = cab
        pc3 = cabsys.AutoPlacedCable()
        pc3.cable = cab
        cab_set = cabsys.AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.f = 50.0
        cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE
        cab.sheath_type = iec.CWS_TAPE_SHEATH
        result = support.calc_sheath_screen_diameter(cab, log=Log()).value
        self.assertEqual(91.3, result, 'get sheath/screen tape dia')
        cab.sheath_type = iec.PB_SHEATH
        cab.tape.material = iec.NONE
        result = support.calc_sheath_screen_diameter(cab, log=Log()).value
        self.assertEqual(88.7, result, 'get sheath/screen sheath dia')
        cab.sheath_type = iec.CWS_SHEATH
        cab.sheath.material = iec.NONE
        result = support.calc_sheath_screen_diameter(cab, log=Log()).value
        self.assertEqual(87.8, result, 'get sheath/screen cws dia')
        cab.sheath_type = iec.CAS_SHEATH
        result = support.calc_sheath_screen_diameter(cab, log=Log()).value
        self.assertEqual(88.4, result, 'get sheath/screen CAS dia')
        # check raise exception if no sheath type specified
        cab.sheath_type = None
        cab.wire_screen.material = None
        with self.assertRaises(Exception):
            support.calc_sheath_screen_diameter(cab, log=Log())

    def test_cable_external_dia(self):
        cab = AutoCable(name='my_cable')
        cab.number_cores = iec.SINGLE_CORE
        cab.serving.material = iec.SERVING_PVC
        cab.serving.dia = 99.7
        cab.sheath.material = iec.LEAD
        cab.sheath.dia = 88.7
        pc1 = cabsys.AutoPlacedCable()
        pc1.cable = cab
        pc2 = cabsys.AutoPlacedCable()
        pc2.cable = cab
        pc3 = cabsys.AutoPlacedCable()
        pc3.cable = cab
        cab_set = cabsys.AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.f = 50.0
        cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE
        result = cab.calc_outer_diameter(log=Log())
        self.assertEqual(99.7, result, 'get cable external dia')
        cab.serving.material = iec.NONE
        result = cab.calc_outer_diameter(log=Log())
        self.assertEqual(88.7, result, 'get cable external dia')
        cab.sheath.material = None
        with self.assertRaises(Exception):
            cab.calc_outer_diameter(log=Log())
        cab.sheath.material = iec.NONE
        with self.assertRaises(Exception):
            cab.calc_outer_diameter(log=Log())

    def test_formation_spacing(self):
        cab = cabsys.AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_1000MM2
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
        cab.number_cores = iec.THREE_CORE
        cab.core.spacing = 66.5
        cab.max_cond_temp = 90.0
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 99.9

        pc1 = cabsys.AutoPlacedCable()
        pc1.cable = cab
        pc1.x = 0.0
        pc1.y = -900.0
        pc2 = cabsys.AutoPlacedCable()
        pc2.cable = cab
        pc2.x = -300.0
        pc2.y = -900.0
        pc3 = cabsys.AutoPlacedCable()
        pc3.cable = cab
        pc3. x = 300.0
        pc3.y = -900.0

        # only one cable
        cab_set = cabsys.AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.f = 50.0
        cab_set.cct_type = iec.THREE_PHASE_THREE_CORE

        result = cab_set.calc_formation_spacing()
        self.assertEqual((iec.NA, 66.5, iec.NA, iec.NA, iec.NA), result, 'get spacing for 3/C cable')
        cab.number_cores = iec.TWO_CORE
        cab_set.cct_type = iec.TWO_PHASE_TWO_CORE
        result = cab_set.calc_formation_spacing()
        self.assertEqual((iec.NA, 66.5, iec.NA, iec.NA, iec.NA), result, 'get spacing for 2/C cable')

        # two phase single core
        cab.number_cores = iec.SINGLE_CORE
        cab_set.cct_type = iec.TWO_PHASE_SINGLE_CORE
        result = cab_set.calc_formation_spacing()
        self.assertEqual((iec.FLAT, 300.0, iec.NA, iec.SPACED, iec.HORIZONTAL), result,
                         'get spacing for 2 phase 1/C cable, horizontal spaced')
        pc2.x = 0.0
        pc2.y = -800.0
        pc3. x = 0.0
        pc3.y = -1000.0
        result = cab_set.calc_formation_spacing()
        self.assertEqual((iec.FLAT, 100.0, iec.NA, iec.TOUCHING, iec.VERTICAL), result,
                         'get spacing for 2 phase 1/C cable, vertical touching')

        # three phase single core
        cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE
        result = cab_set.calc_formation_spacing()
        self.assertEqual((iec.FLAT, 100.0, iec.EQUAL, iec.TOUCHING, iec.VERTICAL), result,
                         'get spacing for 3 phase 1/C cable, horizontal touching')
        pc2.x = -300.0
        pc2.y = -900.0
        pc3. x = 300.0
        pc3.y = -900.0
        result = cab_set.calc_formation_spacing()
        self.assertEqual((iec.FLAT, 300.0, iec.EQUAL, iec.SPACED, iec.HORIZONTAL), result,
                         'get spacing for 3 phase 1/C cable, horizontal spaced')
        pc2.x = -400.0
        pc2.y = -900.0
        pc3. x = 100.0
        pc3.y = -900.0
        result = cab_set.calc_formation_spacing()
        self.assertEqual((iec.FLAT, 200.0, iec.UNEQUAL, iec.SOME_TOUCHING, iec.HORIZONTAL), result,
                         'get spacing for 3 phase 1/C cable, horizontal some touching')
        pc2.x = 0.0
        pc2.y = -800.0
        pc3. x = 0.0
        pc3.y = -1000.0
        result = cab_set.calc_formation_spacing()
        self.assertEqual((iec.FLAT, 100.0, iec.EQUAL, iec.TOUCHING, iec.VERTICAL), result,
                         'get spacing for 3 phase 1/C cable, vertical touching')

    def test_calc_clearance(self):
        """test calc_clearance"""
        cab = AutoCable(name='my_cable')
        cab.wire_screen.dia_under_wire = 90.0
        cab.sheath.dia_under_sheath = 100.0
        cab.tape.dia_under_tape = 110.0
        cab.sheath_type = iec.CWS_PB_SHEATH
        result = support.calc_clearance_dia(cab)
        self.assertEqual(90.0, result.value, 'clearance cws+pb')
        cab.sheath_type = iec.PB_SHEATH
        result = support.calc_clearance_dia(cab)
        self.assertEqual(100.0, result.value, 'clearance pb')
        cab.sheath_type = iec.TAPE_SHEATH
        result = support.calc_clearance_dia(cab)
        self.assertEqual(110.0, result.value, 'clearance pb')

    def test_calc_mean_diameter(self):
        """test mean diameter"""
        cab = AutoCable(name='my_cable')
        cab.wire_screen.dia_under_wire = 90.0
        cab.wire_screen.dia = 92.0
        cab.sheath.dia_under_sheath = 100.0
        cab.sheath.dia = 102.0
        cab.tape.dia_under_tape = 110.0
        cab.tape.dia = 111.0
        cab.sheath_type = iec.CWS_PB_SHEATH
        result = support.calc_sheath_screen_mean_diameter(cab)
        self.assertEqual((91.0 + 101.0)/2, result.value, 'mean sheath dia: cws+pb')
        result = support.calc_sheath_screen_mean_diameter(cab, ignore_csw_tape=True)
        self.assertEqual(101.0, result.value, 'mean sheath dia: cws+pb, ignore cws')
        cab.sheath_type = iec.PB_SHEATH
        result = support.calc_sheath_screen_mean_diameter(cab)
        self.assertEqual(101.0, result.value, 'mean sheath dia: pb')
        cab.sheath_type = iec.PB_TAPE_SHEATH
        result = support.calc_sheath_screen_mean_diameter(cab)
        self.assertEqual(105.75, result.value, 'mean sheath dia: pb+tape')
        cab.sheath_type = iec.PB_TAPE_SHEATH
        result = support.calc_sheath_screen_mean_diameter(cab, ignore_csw_tape=True)
        self.assertEqual(101.0, result.value, 'mean sheath dia: pb+tape, ignore tape')
        cab.sheath_type = iec.TAPE_SHEATH
        result = support.calc_sheath_screen_mean_diameter(cab)
        self.assertEqual(110.5, result.value, 'mean sheath dia: tape')

    def test_tape_lay_length(self):
        cable = AutoCable(name='my_cable')
        cable.tape.number_layers = 1
        cable.tape.angle = 5.0
        result = support.calc_tape_lay_length(cable.tape)
        self.assertEqual(support.TAPE_LAY_LONG, result.value, 'long lay length')
        cable.tape.number_layers = 1
        cable.tape.angle = 55.0
        result = support.calc_tape_lay_length(cable.tape)
        self.assertEqual(support.TAPE_LAY_54, result.value, '54° length')
        cable.tape.number_layers = 1
        cable.tape.angle = 75.0
        result = support.calc_tape_lay_length(cable.tape)
        self.assertEqual(support.TAPE_LAY_SHORT, result.value, 'short lay length')
        cable.tape.number_layers = 2
        cable.tape.angle = 75.0
        result = support.calc_tape_lay_length(cable.tape)
        self.assertEqual(support.TAPE_LAY_MULTIPLE_LAYERS, result.value, 'short multiple lay length')

        with self.assertRaises(Exception):
            cable.tape.number_layers = 2
            cable.tape.angle = 55.0
            result = support.calc_tape_lay_length(cable.tape)
            self.assertEqual(support.TAPE_LAY_MULTIPLE_LAYERS, result.value, 'long lay length')

    def test_sheath_thickness(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.PB_TAPE_SHEATH
        cable.sheath.thickness = 2.2
        result = support.calc_sheath_screen_thickness(cable, ignore_csw_tape=True)
        self.assertEqual(2.2, result.value, 'lead sheath with tape thickness')

        with self.assertRaises(Exception):
            result = support.calc_sheath_screen_thickness(cable)
            self.assertEqual(2.2, result.value, 'lead sheath with tape thickness')

    def test_tape_resistance(self):
        cable = AutoCable(name='my_cable')
        cable.tape.number_layers = 1
        cable.tape.angle = 54.0
        cable.tape.number_tapes = 2
        cable.tape.material = iec.BRONZE
        cable.tape.tape_width = 20.0
        cable.tape.tape_thickness = 0.2
        result = support.calc_tape_resistance(cable.tape, 75.1355)
        self.assertEqual(round(5.99383e-3, 5), round(result.value, 5), 'tape resistance')

    def test_wire_screen_resistance(self):
        cable = AutoCable(name='my_cable')
        cable.wire_screen.number_wires = 100
        cable.wire_screen.wire_size = 1.8
        cable.wire_screen.material = iec.COPPER
        result = support.calc_wire_resistance(cable.wire_screen, 73.6367)
        self.assertEqual(round(8.20346e-5, 9), round(result.value, 9), 'wire resistance')

    def test_sheath_resistance(self):
        cable = AutoCable(name='my_cable')
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM
        result = support.calc_sheath_resistance(cable.sheath, 73.792)
        self.assertEqual(round(7.74572e-5, 9), round(result.value, 9), 'sheath resistance')

    def test_sheath_screen_resistance(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM
        result = support.calc_sheath_screen_resistance(cable, 73.792)
        self.assertEqual(round(7.74572e-5, 9), round(result.value, 9), 'screen resistance (sheath)')

        cable.sheath_type = iec.PB_TAPE_SHEATH
        cable.sheath.dia = 93.7
        cable.sheath.dia_under_sheath = 86.5
        cable.sheath.thickness = 3.6
        cable.sheath.material = iec.LEAD
        cable.tape.number_layers = 1
        cable.tape.angle = 54.0
        cable.tape.number_tapes = 2
        cable.tape.material = iec.BRONZE
        cable.tape.tape_width = 20.0
        cable.tape.tape_thickness = 0.15
        result = support.calc_sheath_screen_resistance(cable, 59.525)
        self.assertEqual(round(0.000235736, 9), round(result.value, 9), 'screen resistance (sheath)')

    def test_sheath_screen_resistivity(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.material = iec.ALUMINIUM
        result = support.calc_sheath_screen_resistivity(cable, 73.7928)
        self.assertEqual(round(3.45567e-8, 13), round(result.value, 13), 'sheath resistivity (sheath)')
        cable.sheath.resistivity = 2.8e-8
        result = support.calc_sheath_screen_resistivity(cable, 73.7928)
        self.assertEqual(round(3.4070e-8, 13), round(result.value, 13), 'sheath resistivity (sheath)')
        cable.sheath.alpha20 = 0.004
        result = support.calc_sheath_screen_resistivity(cable, 73.7928)
        self.assertEqual(round(3.402479e-8, 13), round(result.value, 13), 'sheath resistivity (sheath)')

        cable.sheath_type = iec.PB_TAPE_SHEATH
        cable.sheath.material = iec.LEAD
        result = support.calc_sheath_screen_resistivity(cable, 73.7928)
        self.assertEqual(round(3.402479e-8, 13), round(result.value, 13), 'sheath resistivity (sheath)')

        cable.sheath_type = iec.CWS_TAPE_SHEATH
        cable.wire_screen.material = iec.COPPER
        result = support.calc_sheath_screen_resistivity(cable, 80.0)
        self.assertEqual(round(2.130643e-8, 13), round(result.value, 13), 'wire screen resistivity')
        cable.wire_screen.resistivity = 1.7e-8
        result = support.calc_sheath_screen_resistivity(cable, 80.0)
        self.assertEqual(round(2.10086e-8, 13), round(result.value, 13), 'wire screen resistivity')
        cable.wire_screen.alpha20 = 0.003
        result = support.calc_sheath_screen_resistivity(cable, 80.0)
        self.assertEqual(round(2.006e-8, 13), round(result.value, 13), 'wire screen resistivity')

        cable.sheath_type = iec.TAPE_SHEATH
        cable.tape.material = iec.COPPER
        result = support.calc_sheath_screen_resistivity(cable, 80.0)
        self.assertEqual(round(2.130643e-8, 13), round(result.value, 13), 'tape screen resistivity')
        cable.tape.resistivity = 1.7e-8
        result = support.calc_sheath_screen_resistivity(cable, 80.0)
        self.assertEqual(round(2.10086e-8, 13), round(result.value, 13), 'tape screen resistivity')
        cable.tape.alpha20 = 0.003
        result = support.calc_sheath_screen_resistivity(cable, 80.0)
        self.assertEqual(round(2.006e-8, 13), round(result.value, 13), 'tape screen resistivity')

    def test_calc_central_cable(self):
        cab = cabsys.AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_1000MM2
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
        cab.number_cores = iec.THREE_CORE
        cab.core.spacing = 66.5
        cab.max_cond_temp = 90.0
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 99.9

        pc1 = cabsys.AutoPlacedCable()
        pc1.cable = cab
        pc1.x = 0.0
        pc1.y = -900.0
        pc2 = cabsys.AutoPlacedCable()
        pc2.cable = cab
        pc2.x = -300.0
        pc2.y = -900.0
        pc3 = cabsys.AutoPlacedCable()
        pc3.cable = cab
        pc3. x = 300.0
        pc3.y = -900.0

        cab_set = cabsys.AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.f = 50.0
        cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE

        result = support.calc_centre_cable(cab_set)
        self.assertEqual(0, result.value, 'calculate centre cable')

        pc1.x = 0.0
        pc1.y = -100.0
        result = support.calc_centre_cable(cab_set)
        self.assertEqual(3, result.value, 'calculate centre cable, but 2 cables closest to centre')

    def test_calc_cable_phase(self):
        cab = cabsys.AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_1000MM2
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
        cab.number_cores = iec.THREE_CORE
        cab.core.spacing = 66.5
        cab.max_cond_temp = 90.0
        cab.serving.material = iec.SERVING_PE
        cab.serving.dia = 99.9

        pc1 = cabsys.AutoPlacedCable()
        pc1.cable = cab
        pc1.x = 0.0
        pc1.y = -900.0
        pc1.phase = iec.YELLOW
        pc2 = cabsys.AutoPlacedCable()
        pc2.cable = cab
        pc2.x = -300.0
        pc2.y = -900.0
        pc2.phase = iec.RED
        pc3 = cabsys.AutoPlacedCable()
        pc3.cable = cab
        pc3. x = 300.0
        pc3.y = -900.0
        pc3.phase = iec.BLUE

        cab_set = cabsys.AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.f = 50.0
        cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE

        result = support.calc_cable_phase_wrt_centre(cab_set, 0)
        self.assertEqual(iec.YELLOW, result.value, 'calculate centre cable')
        result = support.calc_cable_phase_wrt_centre(cab_set, 1)
        self.assertEqual(iec.RED, result.value, 'calculate centre cable')
        result = support.calc_cable_phase_wrt_centre(cab_set, 2)
        self.assertEqual(iec.BLUE, result.value, 'calculate centre cable')

        pc1.x = 0.0
        pc1.y = -100.0
        with self.assertRaises(Exception):
            _result = support.calc_cable_phase_wrt_centre(cab_set, 0)


if __name__ == '__main__':
    unittest.main()
