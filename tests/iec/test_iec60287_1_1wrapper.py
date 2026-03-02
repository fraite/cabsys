import unittest

import cabsys.iec.iec_constants as iec
import cabsys.quantity.quantity_constants as dc
import cabsys.iec.iec60287_1_1 as iec60287_1_1w
from cabsys.data_classes.auto_cable import AutoCable
from cabsys import CableState, CableSetState, InstallState
from cabsys.data_classes.auto_install import AutoCableSet, AutoPlacedCable
from cabsys.data_classes.project import AutoInstall
from cabsys.quantity.log import Log
# from cabsys.gui.log_viewer import log_show
# from cabsys.gui.data_store_viewer import data_store_show


class TestIEC60287p1p1(unittest.TestCase):

    def test_dc_res_overridden(self):
        """Calculate dc resistance case 1: dc resistance overridden"""
        cab = AutoCable(name='my_cable')
        cab.conductor.dc_resistance20 = 7.2e-6
        cab.conductor.alpha20 = 3.93e-3
        cab.max_cond_temp = 90.0
        cable_results = CableState()
        cable_results.set_quantity('r_dash', 8.88e-6, 'ohm/m', source=dc.ATTR_USER_SET)
        result = iec60287_1_1w.calc_r_dash(cab, state=cable_results)
        self.assertEqual(round(8.88e-6, 11), round(result.value, 11), 'calculated dc resistance overridden')

    def test_dc_res_case3(self):
        """Calculate dc resistance case 3: conductor temperature overridden, dc resistance set in cable,
         alpha20 set in cable"""
        cab = AutoCable(name='my_cable')
        cab.conductor.dc_resistance20 = 14.9e-6
        cab.conductor.alpha20 = 4.03e-3
        cab.max_cond_temp = 105.0
        cable_results = CableState()
        # cable_results.set_attr('cond_temp', 100, attr_unit='ohm/m', top=dc.USER_SET)
        cable_results.set_quantity('cond_temp', 100.0, attr_unit='°C', source=dc.ATTR_USER_SET)
        # data_store_show(cable_results)
        log = Log()
        result = iec60287_1_1w.calc_r_dash(cab, state=cable_results, log=log)
        # log_show(log)

        self.assertEqual(round(19.7038e-6, 10), round(result.value, 10), 'calculated dc resistance: case 3')

    def test_dc_res_case4(self):
        """Calculate dc resistance case 4: conductor temperature set in cable, dc resistance set in cable,
         alpha20 set in cable"""
        cab = AutoCable(name='my_cable')
        cab.conductor.dc_resistance20 = 14.9e-6
        cab.conductor.alpha20 = 4.03e-3
        cab.max_cond_temp = 105.0
        result = iec60287_1_1w.calc_r_dash(cab)
        self.assertEqual(round(20.004e-6, 10), round(result.value, 10), 'calculated dc resistance: case 4')

    def test_dc_res_case5(self):
        """Calculate dc resistance case 5: default temperature, for given conductor size and description"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_2500MM2_2005
        cab.conductor.material = iec.COPPER
        # have to pass an empty PlacedCableResults() otherwise test suit picks up an old version
        result = iec60287_1_1w.calc_r_dash(cab)
        self.assertEqual(round(9.18072e-6, 11), round(result.value, 11), 'calculated dc resistance: case5')

    def test_ys_overridden(self):
        """Calculate ys resistance at 90 °C for given conductor description xs<=2.8, result overridden"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_1000MM2
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
        cab.max_cond_temp = 90.0

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f = 50.0

        cable_set_state = CableSetState(cs)
        # cable_set_state.set_quantity('ys', 0.22222, '')
        cs.ys = 0.22222
        _result = iec60287_1_1w.calc_ys(cs, 0, state=cable_set_state)
        # not possible to override ys
        # self.assertEqual(round(0.22222, 4), round(result.value, 4), 'calculated ys2 for XLPE cable: overridden ys')

    def test_ys_case2(self):
        """Calculate ys resistance at 90 °C for given conductor description case2: xs<=2.8"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_1000MM2
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
        cab.max_cond_temp = None

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        cable_set_state = CableSetState(cs)
        result = iec60287_1_1w.calc_ys(cs, 0, state=cable_set_state)
        self.assertEqual(round(0.14444, 4), round(result.value, 4), 'calculated ys2 for XLPE cable case 2: xs<=2.8')

    def test_ys_case3(self):
        """Calculate ys resistance at 90 °C for given conductor description case3: 2.8<xs<=3.8"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_2000MM2
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.ROUND_MILLIKEN_BARE_BI_EXTRUDED
        # cab.max_cond_temp = 90.0

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        cable_set_state = CableSetState(cs)
        result = iec60287_1_1w.calc_ys(cs, 0, state=cable_set_state)
        self.assertEqual(round(0.30481, 4), round(result.value, 4), 'calculated ys2 for XLPE cable case 2: 2.8<xs<=3.8')

    def test_ys_case4(self):
        """Calculate ys resistance at 50 °C for given conductor description case4: xs>3.8"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_2500MM2_2005
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cab.max_cond_temp = 50.0
        cab.conductor.ks = 1.0

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f = 50.0

        cable_set_state = CableSetState(cs)
        result = iec60287_1_1w.calc_ys(cs, 0, state=cable_set_state)
        self.assertEqual(round(0.665751, 4), round(result.value, 4),
                         'calculated ys2 for XLPE cable case 2: 2.8<xs<=3.8')

    def test_ys_case5(self):
        """Calculate ys resistance at 50 °C for given conductor description case5: conductor set as argument"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_2500MM2_2005
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cab.conductor.ks = 1.0

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f = 50.0

        cable_set_state = CableSetState(cs)
        result = iec60287_1_1w.calc_ys(cs, 0, cond_temp=50.0, state=cable_set_state)
        self.assertEqual(round(0.665751, 4), round(result.value, 4),
                         'calculated ys2 for XLPE cable case 2: 2.8<xs<=3.8')

    def test_xs2_xlpe(self):
        """Calculate xs2 resistance at 90 °C for given conductor description"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size.value = iec.IEC_1000MM2
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.ROUND_STRANDED_EXTRUDED
        cab.max_cond_temp.value = 90.0

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        result = iec60287_1_1w.calc_xs2(cs, 0)
        self.assertEqual(round(result.value, 4), round(5.599548, 4), 'calculated xs2 for XLPE cable')

    def test_xs2_oil_filled_1000mm2(self):
        """Calculate xs2 resistance at 90 °C for given conductor description"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size.value = iec.IEC_1000MM2
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.HOLLOW_KEYSTONE_IMPREGNATED
        cab.max_cond_temp.value = 90.0
        cab.conductor.duct_dia.value = 12.0
        cab.conductor.dia.value = 38.4

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        result = iec60287_1_1w.calc_xs2(cs, 0)
        self.assertEqual(round(result.value, 4), round(4.471188, 4), 'calculated xs2 for oil filled cable')

    def test_xs2_oil_filled_1000mm2_80degc(self):
        """Calculate xs2 resistance at 80 °C for given conductor description"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size.value = iec.IEC_1000MM2
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.HOLLOW_KEYSTONE_IMPREGNATED
        cab.conductor.duct_dia.value = 12.0
        cab.conductor.dia.value = 38.4

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        cable_set_state = CableSetState(cs)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('cond_temp', 80.0, '°C',
                                                                        source=dc.ATTR_USER_SET)
        result = iec60287_1_1w.calc_xs2(cs, 0, state=cable_set_state)
        self.assertEqual(round(result.value, 4), round(4.61338, 4), 'calculated xs2 for oil filled cable at 80 °C')

    def test_xs2_xlpe_ks(self):
        """Calculate xs2 resistance at 90 °C for given conductor description with ks specified"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_1000MM2
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
        cab.conductor.ks = 0.9

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f = 50.0

        result = iec60287_1_1w.calc_xs2(cs, 0)
        self.assertEqual(round(result.value, 4), round(5.03959, 4), 'calculated xs2 for XLPE cable with ks specified')

    def test_ks_oil_filled_1000mm2(self):
        """Calculate ks ducted given conductor description"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_1000MM2
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.HOLLOW_KEYSTONE_IMPREGNATED
        cab.conductor.duct_dia = 12.0
        cab.conductor.dia = 38.4

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f = 50.0

        result = iec60287_1_1w.calc_ks_ducted(cab)
        self.assertEqual(round(result.value, 5), round(0.798491, 5), 'calculated ks for oil filled ducted conductor')

    def test_ks_oil_filled_oval(self):
        """Calculate ks ducted given conductor description"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size.value = iec.IEC_400MM2
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.OVAL_STRANDED_IMPREGNATED

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        result = iec60287_1_1w.find_ks(cab)
        self.assertEqual(round(result.value, 5), round(1.0000, 5), 'calculated ks for oil filled ducted conductor')

    def test_ks_oil_filled_1000mm2_compaction(self):
        """Calculate ks ducted conductor description and specified compaction"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size = iec.IEC_1000MM2
        cab.conductor.material = iec.COPPER
        cab.conductor.makeup = iec.HOLLOW_KEYSTONE_IMPREGNATED
        cab.conductor.duct_dia = 12.0
        cab.conductor.dia = 38.4
        cab.conductor.compaction = 90.0

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f = 50.0

        result = iec60287_1_1w.calc_ks_ducted(cab)
        self.assertEqual(round(result.value, 5), round(0.7872431, 5),
                         'calculated ks for conductor with specified compaction')

    def test_xp2_xlpe(self):
        """Calculate xp2 resistance at 90 °C for given conductor description"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size.value = iec.IEC_2500MM2_2005
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cab.max_cond_temp.value = 90.0

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        cable_set_results = CableSetState(cs)
        result = iec60287_1_1w.calc_xp2(cs, 0, state=cable_set_results)
        self.assertEqual(round(result.value, 4), round(2.73757, 4), 'calculated xp2 for XLPE cable')

    def test_xp2_case1(self):
        """Calculate xp2 resistance case 1: xp2 overridden"""
        cab = AutoCable(name='my_cable')
        cab.conductor.size.value = iec.IEC_2500MM2_2005
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cab.max_cond_temp.value = 90.0

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        cable_set_results = CableSetState(cs)
        cable_set_results.placed_cable_states[0].cable_state.set_quantity('xp2', 1.11111, '-')
        _result = iec60287_1_1w.calc_xp2(cs, 0, state=cable_set_results)
        # no longer possible to override xp
        # self.assertEqual(round(result.value, 4), round(1.11111, 4), 'calculated xp2 for XLPE cable')

    def test_xp2_case2(self):
        """Calculate xp2 case 2: kp given in cable object"""
        cab = AutoCable(name='my_cable')
        cab.conductor.kp = 0.5
        cab.conductor.size.value = iec.IEC_2500MM2_2005
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cab.max_cond_temp.value = 90.0

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        result = iec60287_1_1w.calc_xp2(cs, 0)
        self.assertEqual(round(result.value, 4), round(6.84389, 4), 'calculated xp2 for XLPE cable')

    def test_yp(self):
        cab = AutoCable(name='my_cable')
        cab.pipe_type.value = False
        cab.number_cores.value = iec.SINGLE_CORE
        cab.common_sheath = True
        cab.conductor.size.value = iec.IEC_400MM2
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.ROUND_STRANDED_EXTRUDED
        cab.conductor.dia.value = 23.1
        cab.serving.dia.value = 63.9
        cab.serving.material.value = iec.SERVING_PE
        cab.pipe.material.value = None
        pc1 = AutoPlacedCable()
        pc1.cable = cab
        pc1.x.value = 0.0
        pc1.y.value = -900.0
        pc2 = AutoPlacedCable()
        pc2.cable = cab
        pc2.x.value = 500.0
        pc2.y.value = -900.0
        cab_set = AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2]
        cab_set.f.value = 50.0
        cab_set.cct_type.value = iec.TWO_PHASE_SINGLE_CORE

        cable_set_state = CableSetState(cab_set)
        result = iec60287_1_1w.calc_yp(cab_set, 0, state=cable_set_state)
        self.assertEqual(round(result.value, 8), round(1.39198e-4, 8), 'calculated yp for 2 phase 2 single core cables')

        cab.number_cores.value = iec.TWO_CORE
        cab_set.cct_type.value = iec.TWO_PHASE_TWO_CORE
        cab.core.spacing.value = 65.0
        result = iec60287_1_1w.calc_yp(cab_set, 0, state=cable_set_state)
        self.assertEqual(round(result.value, 8), round(0.008236549, 8), 'calculated yp for 2 phase cable')

        cab.number_cores.value = iec.SINGLE_CORE
        cab.conductor.size.value = iec.IEC_2500MM2_2005
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cab.conductor.dia.value = 66.0
        cab.serving.dia.value = 138.2
        pc3 = AutoPlacedCable()
        pc3.cable = cab
        pc3.x.value = -500.0
        pc3.y.value = -900.0
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.cct_type.value = iec.THREE_PHASE_SINGLE_CORE
        result = iec60287_1_1w.calc_yp(cab_set, 0, state=cable_set_state)
        self.assertEqual(round(result.value, 8), round(0.00253149, 8), 'calculated yp for 3 single core cables')

        cab.number_cores.value = iec.THREE_CORE
        cab.conductor.size.value = iec.IEC_2500MM2_2005
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cab.conductor.dia.value = 66.0
        cab.serving.dia.value = 150.0
        cab.core.spacing.value = 118.2
        pc3 = AutoPlacedCable()
        pc3.cable = cab
        pc3.x.value = -500.0
        pc3.y.value = -900.0
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.cct_type.value = iec.THREE_PHASE_THREE_CORE
        result = iec60287_1_1w.calc_yp(cab_set, 0, state=cable_set_state)
        self.assertEqual(round(result.value, 8), round(0.0463821097, 8), 'calculated yp for 3 core circular cable')

        cab.number_cores.value = iec.THREE_CORE
        cab.conductor.size.value = iec.IEC_400MM2
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.SECTOR_SHAPED_EXTRUDED
        cab.conductor.effective_dia.value = 23.1
        cab.serving.dia.value = 60.0
        cab.core.spacing.value = 63.9
        pc3 = AutoPlacedCable()
        pc3.cable = cab
        pc3.x.value = -500.0
        pc3.y.value = -900.0
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.cct_type.value = iec.THREE_PHASE_THREE_CORE
        result = iec60287_1_1w.calc_yp(cab_set, 0, state=cable_set_state)
        self.assertEqual(round(result.value, 8), round(0.011976047, 8), 'calculated yp for 3 core shaped cable')

        cab.number_cores.value = iec.THREE_CORE
        cab.conductor.size.value = iec.IEC_400MM2
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.OVAL_STRANDED_IMPREGNATED
        cab.conductor.minor_dia.value = 20.0
        cab.conductor.major_dia.value = 26.6805
        cab.serving.dia.value = 60.0
        cab.core.spacing.value = 63.9
        pc3 = AutoPlacedCable()
        pc3.cable = cab
        pc3.x.value = -500.0
        pc3.y.value = -900.0
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.cct_type.value = iec.THREE_PHASE_THREE_CORE
        result = iec60287_1_1w.calc_yp(cab_set, 0, state=cable_set_state)
        self.assertEqual(round(result.value, 8), round(0.00792946, 8), 'calculated yp for 3 core shaped cable')

    def test_r_ac(self):
        cab = AutoCable(name='my_cable')
        cab.pipe_type.value = False
        cab.number_cores.value = iec.SINGLE_CORE
        cab.separate_sheath.value = False
        cab.conductor.size.value = iec.IEC_2500MM2_2005
        cab.conductor.material.value = iec.COPPER
        cab.conductor.makeup.value = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cab.conductor.dia.value = 66.0
        cab.serving.dia.value = 138.2
        cab.serving.material.value = iec.SERVING_PE
        cab.pipe.material.value = None
        pc1 = AutoPlacedCable()
        pc1.cable = cab
        pc1.x.value = 0.0
        pc1.y.value = -900.0
        pc2 = AutoPlacedCable()
        pc2.cable = cab
        pc2.x.value = 500.0
        pc2.y.value = -900.0
        pc3 = AutoPlacedCable()
        pc3.cable = cab
        pc3.x.value = -500.0
        pc3.y.value = -900.0
        cab_set = AutoCableSet(name='my_cable_set')
        cab_set.placed_cables = [pc1, pc2, pc3]
        cab_set.f.value = 50.0
        cab_set.cct_type.value = iec.THREE_PHASE_SINGLE_CORE

        result = iec60287_1_1w.calc_r_ac(cab_set, 0)
        self.assertEqual(round(result.value, 11), round(1.02056067e-5, 11), 'calculated r_ac')

    def test_c(self):
        """Calculate c case 1: default 2500mm2 cable"""
        cab = AutoCable(name='my_cable')
        cab.core.insu_dia.value = 124.2
        cab.core.cond_screen_dia.value = 70.6
        cab.core.insulation_material.value = iec.INS_XLPE_UNFILLED
        cab.design_volts.value = iec.IEC_400KV

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]

        install = AutoInstall()
        install.cable_sets = [cs]

        result = iec60287_1_1w.calc_c(install, cable_set_num=0, cable_num=0)
        self.assertEqual(round(result.value, 14), round(2.4588e-10, 14), 'calculated c for XLPE cable')

        cab.core.permittivity = 2.0

        result = iec60287_1_1w.calc_c(install, cable_set_num=0, cable_num=0)
        self.assertEqual(round(result.value, 14), round(1.967e-10, 14),
                         'calculated c for XLPE cable but permittivity changed to 2.0')

    def test_wd(self):
        """Calculate Wd case 1: default 2500mm2 cable"""
        cab = AutoCable(name='my_cable')
        cab.core.insu_dia.value = 124.2
        cab.core.cond_screen_dia.value = 70.6
        cab.core.insulation_material.value = iec.INS_XLPE_UNFILLED
        cab.design_volts.value = iec.IEC_400KV

        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcr.u_pe = 400000 / 3**0.5
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcy.u_pe = 400000 / 3**0.5
        pcb = AutoPlacedCable()
        pcb.cable = cab
        pcb.u_pe = 400000 / 3**0.5
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.auto_voltage.value = 400
        install = AutoInstall(name='my_install')
        install.cable_sets = [cs]
        install.config.always_calc_wd.set_value(True)

        result = iec60287_1_1w.calc_wd(install, cable_set_num=0, cable_num=0)
        self.assertEqual(round(result.value, 4), round(4.1198, 4), 'calculated c for XLPE cable')

        result = iec60287_1_1w.calc_wd(install, cable_set_num=0, cable_num=0, u_pe=200000)
        self.assertEqual(round(result.value, 4), round(3.0898, 4), 'calculated c for XLPE cable') #3.08983

        cab.core.tan_d = 0.005
        result = iec60287_1_1w.calc_wd(install, cable_set_num=0)
        self.assertEqual(round(result.value, 4), round(20.5988, 4), 'calculated c for XLPE cable, tand = 0.005')

        cab.core.insu_dia.value = 68.4
        cab.core.cond_screen_dia.value = 36.9
        cab.core.insulation_material.value = iec.INS_XLPE_UNFILLED
        cab.design_volts.value = iec.IEC_132KV
        cs.auto_voltage.value = 132
        pcr.u_pe = pcb.u_pe = pcy.u_pe = 132000 / 3**0.5
        cab.core.tan_d = 0.001
        result = iec60287_1_1w.calc_wd(install, cable_set_num=0)
        self.assertEqual(round(result.value, 4), round(0.0, 4), 'calculated c for XLPE cable, 132kV default to zero')

        result = iec60287_1_1w.calc_wd(install, cable_set_num=0)
        self.assertEqual(round(result.value, 4), round(0.4106, 4),
                         'calculated c for XLPE cable, 132kV force calculation')

        state = InstallState(install)
        result = iec60287_1_1w.calc_wd(install, cable_set_num=0, state=state)
        self.assertEqual(round(result.value, 4), round(0.4106, 4),
                         'calculated c for XLPE cable, 132kV force calculation with blank state')

        state = InstallState(install)
        # cable_set_state.placed_cable_states[0].cable_state.set_quantity('wd', 1.111, source=dc.ATTR_USER_SET)
        result = iec60287_1_1w.calc_wd(install, cable_set_num=0, state=state)
        self.assertEqual(round(1.111, 4), round(result.value, 4),
                         'calculated c for XLPE cable, 132kV set state')

    def test_theta_sc(self):
        """Calculate sheath temperature: default 2500mm2 cable"""
        cab = AutoCable(name='my_cable')
        pcr = AutoPlacedCable()
        pcr.cable = cab
        pcy = AutoPlacedCable()
        pcy.cable = cab
        pcb = AutoPlacedCable()
        pcb.cable = cab
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.auto_voltage.value = 400
        install = AutoInstall(name='my_install')
        install.cable_sets.append(cs)

        install_state = InstallState(install)
        cable_set_state = install_state.cable_set_states[0]
        cable_state = cable_set_state.placed_cable_states[0].cable_state
        cable_state.set_quantity('R', 10.205607E-6, attr_unit='ohm/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('wd', 4.11977, attr_unit='W/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('T_1', 0.3689712, attr_unit='°Cm/W', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('cond_temp', 90.0, attr_unit='W/m', source=dc.ATTR_USER_STATE_SET)
        cable_set_state.set_quantity('current', 2025.387, attr_unit='A', source=dc.ATTR_USER_STATE_SET)

        install.config.always_calc_wd = True
        result = iec60287_1_1w.calc_theta_sc(install, 0, 0, 2025.387, 90.0, state=install_state)
        self.assertEqual(round(73.79284, 4), round(result.value, 4),
                         'calculated sheath temperature for default 400 kV 2500mm² XLPE cable')

    def test_sheath_screen_reactance_trefoil(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2
        cable.number_cores = iec.SINGLE_CORE

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.x = 0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.x = 69.1
        pcy.y = 1088.784
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.x = -69.1
        pcb.y = 1088.784
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.auto_voltage.value = 400
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE
        install = AutoInstall(name='my_install')
        install.cable_sets.append(cs)

        result = iec60287_1_1w.calc_x_5_3_2(cs, 0)
        self.assertEqual(round(4.783149e-5, 9), round(result.value, 9), 'screen resistance (sheath)')

        cs.placed_cables[2].y = 2000.0
        with self.assertRaises(Exception):
            _result = iec60287_1_1w.calc_x_5_3_2(cs, 0)

        cs.cct_type = iec.TWO_PHASE_SINGLE_CORE
        result = iec60287_1_1w.calc_x_5_3_2(cs, 0)
        self.assertEqual(round(4.783149e-5, 9), round(result.value, 9), 'screen resistance (sheath)')

        cable.core.bedding_dia = 96.6
        cable.core.spacing = 96.6
        cable.sheath.dia = 99.0
        cable.sheath.dia_under_sheath = 96.8
        cable.serving.dia = 219.3
        cable.number_cores = iec.THREE_CORE
        cable.separate_sheath = True

        cs.cct_type = iec.THREE_PHASE_THREE_CORE
        with self.assertRaises(Exception):
            result = iec60287_1_1w.calc_x_5_3_2(cs, 0)
            self.assertEqual(round(4.27118e-5, 9), round(result.value, 9), 'screen resistance (sheath)')

        cable.separate_sheath = False

        with self.assertRaises(Exception):
            _result = iec60287_1_1w.calc_x_5_3_2(cs, 0)

    def test_2_core_lambda1_d(self):

        cable = AutoCable(name='my_cable')
        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcb = AutoPlacedCable()
        pcb.cable = cable
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]

        cable_set_state = CableSetState(cs)
        cable_state = cable_set_state.placed_cable_states[0].cable_state
        # cable_state.X = 4.783149e-5
        cable_state.set_quantity('X', 4.783149e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R', 1.0491787e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R_s', 8.03915e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)

        result = iec60287_1_1w.calc_lambda_1_s5_3_2(cs, 0, state=cable_set_state)
        self.assertEqual(round(2.003311, 6), round(result.value, 6), 'screen resistance (sheath)')

    def test_sheath_screen_reactance_flat_transposed(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2
        cable.number_cores = iec.SINGLE_CORE

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.x = 0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.x = 500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.x = -500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.auto_voltage.value = 400
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE
        cs.transposed = True
        install = AutoInstall(name='my_install')
        install.cable_sets.append(cs)

        result = iec60287_1_1w.calc_x1_2_3_2(cs, 0)
        self.assertEqual(round(1.4314460e-4, 9), round(result.value, 9), 'screen resistance (sheath)')

    def test_3_core_flat_transposed_lambda1_d(self):

        cable = AutoCable(name='my_cable')
        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcb = AutoPlacedCable()
        pcb.cable = cable
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]

        cable_set_state = CableSetState(cs)
        cable_state = cable_set_state.placed_cable_states[0].cable_state
        # cable_state.X = 4.783149e-5
        cable_state.set_quantity('X1', 1.43144598e-4, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R', 1.0205607e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R_s', 8.0673710e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)

        result = iec60287_1_1w.calc_lambda_1_s5_3_3(cs, 0, state=cable_set_state)
        self.assertEqual(round(5.999313, 6), round(result.value, 6), 'lambda_1_dash flat transposed (sheath)')

    def test_sheath_screen_reactance_flat_not_transposed(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2
        cable.number_cores = iec.SINGLE_CORE

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.x = 0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.x = 500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.x = -500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.auto_voltage.value = 400
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE
        cs.transposed = True
        install = AutoInstall(name='my_install')
        install.cable_sets.append(cs)

        with self.assertRaises(Exception):
            result = iec60287_1_1w.calc_x_5_3_4(cs, 0)
            self.assertEqual(round(1.4314460e-4, 9), round(result.value, 9), 'screen resistance (sheath) X')

        cs.transposed = False
        result = iec60287_1_1w.calc_x_5_3_4(cs, 0)
        self.assertEqual(round(1.2862736e-4, 9), round(result.value, 9), 'screen resistance (sheath) X')

        result = iec60287_1_1w.calc_xm_5_3_4(cs)
        self.assertEqual(round(4.355172e-5, 9), round(result.value, 9), 'screen resistance (sheath) Xm')

    def test_p_q(self):

        cable = AutoCable(name='my_cable')
        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcb = AutoPlacedCable()
        pcb.cable = cable
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f = 50.0

        cable_set_state = CableSetState(cs)
        cable_state = cable_set_state.placed_cable_states[0].cable_state
        # cable_state.X = 4.783149e-5
        cable_state.set_quantity('X', 1.28627358e-4, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        # cable_state.set_quantity('Xm', 4.355172181e-4, 'Ω/m', top=dc.ATTR_USER_STATE_SET)

        result = iec60287_1_1w.calc_cp_5_3_4(cs, 0, state=cable_set_state)
        self.assertEqual(round(1.7217908e-4, 9), round(result.value, 9), 'P')

        result = iec60287_1_1w.calc_cq_5_3_4(cs, 0, state=cable_set_state)
        self.assertEqual(round(1.1411012e-4, 9), round(result.value, 9), 'Q')

    def test_3_core_flat_not_transposed_lambda1_d(self):

        cable = AutoCable(name='my_cable')
        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcb = AutoPlacedCable()
        pcb.cable = cable
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f = 50.0

        cable_set_state = CableSetState(cs)
        cable_state = cable_set_state.placed_cable_states[0].cable_state
        # cable_state.X = 4.783149e-5
        # cable_state.set_quantity('Xm', 4.35517218e-5, 'Ω/m', top=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('phase', iec.YELLOW, '', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('X', 1.28627358e-4, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R', 1.0205456e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R_s', 8.0635638e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)

        result = iec60287_1_1w.calc_lambda_1dash_s5_3_4(cs, 0, state=cable_set_state)
        self.assertEqual(round(5.26976630, 6), round(result.value, 6), 'screen resistance (sheath)')

        cable_state.set_quantity('phase', iec.RED, '', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('X', 1.28627358e-4, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R', 9.984043617e-6, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R_s', 7.8437866e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)

        result = iec60287_1_1w.calc_lambda_1dash_s5_3_4(cs, 0, state=cable_set_state)
        self.assertEqual(round(5.3263285, 6), round(result.value, 6), 'screen resistance (sheath)')

        cable_state.set_quantity('phase', iec.BLUE, '', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('X', 1.28627358e-4, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R', 1.01927596e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)
        cable_state.set_quantity('R_s', 8.05098796e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)

        result = iec60287_1_1w.calc_lambda_1dash_s5_3_4(cs, 0, state=cable_set_state)
        self.assertEqual(round(7.0713343, 6), round(result.value, 6), 'screen resistance (sheath)')

    def test_m_n_f_trefoil(self):
        cable = AutoCable(name='my_cable')
        cable.conductor.kp = 0.2
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2
        cable.number_cores = iec.SINGLE_CORE

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.x = 0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.x = 69.1
        pcy.y = 1088.78471
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.x = -69.1
        pcb.y = 1088.78471
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.auto_voltage.value = 400
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE
        install = AutoInstall(name='my_install')
        install.cable_sets.append(cs)

        cable_set_state = CableSetState(cs)
        cable_state = cable_set_state.placed_cable_states[0].cable_state
        cable_state.set_quantity('R_s', 8.0391514e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)

        result = iec60287_1_1w.calc_cm1_s5_3_6a(cs, 0, sheath_screen_temperature=85.2297477)
        self.assertEqual(round(1.6807236, 5), round(result.value, 5), 'M trefoil')

        result = iec60287_1_1w.calc_cm1_s5_3_6a(cs, 0, state=cable_set_state)
        self.assertEqual(round(1.6807236, 5), round(result.value, 5), 'M trefoil')

        result = iec60287_1_1w.calc_cn_s5_3_6a(cs, 0, sheath_screen_temperature=85.2297477)
        self.assertEqual(round(1.6807236, 5), round(result.value, 5), 'N trefoil')

        result = iec60287_1_1w.calc_cn_s5_3_6a(cs, 0, state=cable_set_state)
        self.assertEqual(round(1.6807236, 5), round(result.value, 5), 'N trefoil')

        # test F

        cable.conductor.kp = 0.8
        result = iec60287_1_1w.calc_f_c_s5_3_6(install, cs, 0, sheath_screen_temperature=85.2297477)
        self.assertEqual(round(0.0, 5), round(result.value, 5), 'F trefoil, not Milliken')

        cable.conductor.kp = 0.2
        cs.cct_type = iec.TWO_PHASE_SINGLE_CORE
        result = iec60287_1_1w.calc_f_c_s5_3_6(install, cs, 0, state=cable_set_state)
        self.assertEqual(round(0.738551, 5), round(result.value, 5), 'F two phase, Milliken')

        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE
        result = iec60287_1_1w.calc_f_c_s5_3_6(install, cs, 0, sheath_screen_temperature=85.2297477)
        self.assertEqual(round(0.738551, 5), round(result.value, 5), 'F trefoil')

    def test_m_n_flat(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2
        cable.number_cores = iec.SINGLE_CORE

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.x = 0.0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.x = 500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.x = -500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.auto_voltage.value = 400
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE
        install = AutoInstall(name='my_install')
        install.cable_sets.append(cs)

        cable_set_state = CableSetState(cs)
        cable_state = cable_set_state.placed_cable_states[0].cable_state
        cable_state.set_quantity('R_s', 8.067371e-5, 'Ω/m', source=dc.ATTR_USER_STATE_SET)

        result = iec60287_1_1w.calc_cm1_s5_3_6b(cs, 0, sheath_screen_temperature=86.3298)
        self.assertEqual(round(0.468545, 6), round(result.value, 6), 'M flat')

        result = iec60287_1_1w.calc_cm1_s5_3_6b(cs, 0, state=cable_set_state)
        self.assertEqual(round(0.468545, 6), round(result.value, 6), 'M flat')

        result = iec60287_1_1w.calc_cn_s5_3_6b(cs, 0, sheath_screen_temperature=86.3298)
        self.assertEqual(round(0.70698122, 6), round(result.value, 6), 'screen resistance (sheath)')

        result = iec60287_1_1w.calc_cn_s5_3_6b(cs, 0, state=cable_set_state)
        self.assertEqual(round(0.70698122, 6), round(result.value, 6), 'screen resistance (sheath)')

        cable.conductor.kp = 0.2
        result = iec60287_1_1w.calc_f_c_s5_3_6(install, cs, 0, sheath_screen_temperature=86.32976)
        self.assertEqual(round(0.2488643, 6), round(result.value, 6), 'F trefoil')

    def test_gs(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.material = iec.ALUMINIUM
        cable.sheath.dia = 130.2
        cable.sheath.thickness = 1.1

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.x = 0.0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.x = 500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.x = -500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        result = iec60287_1_1w.calc_cgs_5_3_7_1(cs, 0, 73.792848)
        self.assertEqual(round(1.0030415, 6), round(result.value, 6), 'gs')

        cable.sheath_type = iec.PB_SHEATH
        cable.sheath.material = iec.LEAD
        result = iec60287_1_1w.calc_cgs_5_3_7_1(cs, 0, 73.792848, always_calc_c_gs=False)
        self.assertEqual(round(1.00, 6), round(result.value, 6), 'gs')

        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.material = iec.ALUMINIUM
        result = iec60287_1_1w.calc_cgs_5_3_7_1(cs, 0, 73.792848, always_calc_c_gs=False)
        self.assertEqual(round(1.0030415, 6), round(result.value, 6), 'gs')

        cable.sheath.dia = 69.0
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.material = iec.ALUMINIUM
        result = iec60287_1_1w.calc_cgs_5_3_7_1(cs, 0, 73.792848, always_calc_c_gs=False)
        self.assertEqual(round(1.00, 6), round(result.value, 6), 'gs')

    def test_beta1(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.material = iec.ALUMINIUM

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.x = 0.0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.x = 500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.x = -500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        result = iec60287_1_1w.calc_beta1_5_3_7_1(cs, 0, 73.792848)
        self.assertEqual(round(106.884257, 4), round(result.value, 4), 'beta1')

    def test_m(self):
        cable = AutoCable(name='my_cable')
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.x = 0.0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.x = 500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.x = -500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0

        result = iec60287_1_1w.calc_m_5_3_7_1(cs, 0, 73.792848)
        self.assertEqual(round(0.4055892, 6), round(result.value, 6), 'beta1')

    def test_lambda0_trefoil(self):
        cable = AutoCable(name='my_cable')
        cable.number_cores = iec.SINGLE_CORE
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.x = 0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.x = 69.1
        pcy.y = 1088.78471
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.x = -69.1
        pcb.y = 1088.78471
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        result = iec60287_1_1w.calc_lambda0_5_3_7_1(cs, 0, 81.53631074144)
        self.assertEqual(round(0.08850649, 6), round(result.value, 6), 'lambda0')
        result = iec60287_1_1w.calc_delta1_5_3_7_1(cs, 0, 81.53631074144)
        self.assertEqual(round(0.09585777, 6), round(result.value, 6), 'delta1')
        result = iec60287_1_1w.calc_delta2_5_3_7_1(cs, 0, 81.53631074144)
        self.assertEqual(round(0.0, 6), round(result.value, 6), 'delta2')

    def test_lambda0_flat(self):
        cable = AutoCable(name='my_cable')
        cable.number_cores = iec.SINGLE_CORE
        cable.sheath_type = iec.PB_SHEATH
        cable.sheath.dia = 57.1
        cable.sheath.dia_under_sheath = 51.9
        cable.sheath.thickness = 2.6
        cable.sheath.material = iec.LEAD
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 63.7

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.phase = iec.YELLOW
        pcr.x = 0
        pcr.y = 931.85
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.phase = iec.RED
        pcy.x = 300.0
        pcy.y = 931.85
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.phase = iec.BLUE
        pcb.x = -300.0
        pcb.y = 931.85
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE

        result = iec60287_1_1w.calc_m_5_3_7_1(cs, 0, 71.17142)
        self.assertEqual(round(0.0542480, 6), round(result.value, 6), 'm')
        result = iec60287_1_1w.calc_lambda0_5_3_7_1(cs, 0, 71.1714212)
        self.assertEqual(round(0.00014525454, 8), round(result.value, 8), 'lambda0')
        result = iec60287_1_1w.calc_delta1_5_3_7_1(cs, 0, 71.1714212)
        self.assertEqual(round(1.690631e-5, 9), round(result.value, 9), 'delta1')
        result = iec60287_1_1w.calc_delta2_5_3_7_1(cs, 0, 71.1714212)
        self.assertEqual(round(0.0, 6), round(result.value, 6), 'delta2')

        result = iec60287_1_1w.calc_delta1_5_3_7_1(cs, 0, 71.17070, always_calc_delta=False)
        self.assertEqual(round(0.0, 6), round(result.value, 6), 'delta1 with always_calc_delta=False')
        result = iec60287_1_1w.calc_delta2_5_3_7_1(cs, 0, 71.17070, always_calc_delta=False)
        self.assertEqual(round(0.0, 6), round(result.value, 6), 'delta1 with always_calc_delta=False')

        result = iec60287_1_1w.calc_m_5_3_7_1(cs, 1, 66.256723)
        self.assertEqual(round(0.0551477, 6), round(result.value, 6), 'm')
        result = iec60287_1_1w.calc_lambda0_5_3_7_1(cs, 1, 66.256723)
        self.assertEqual(round(3.752478e-5, 9), round(result.value, 9), 'lambda0')
        result = iec60287_1_1w.calc_delta1_5_3_7_1(cs, 1, 66.256723)
        self.assertEqual(round(0.00499420, 7), round(result.value, 7), 'delta1')
        result = iec60287_1_1w.calc_delta2_5_3_7_1(cs, 1, 66.256723)
        self.assertEqual(round(6.50923e-9, 11), round(result.value, 11), 'delta2')
        result = iec60287_1_1w.calc_m_5_3_7_1(cs, 2, 66.255987)
        self.assertEqual(round(0.0551477, 6), round(result.value, 6), 'm')
        result = iec60287_1_1w.calc_lambda0_5_3_7_1(cs, 2, 66.256723)
        self.assertEqual(round(3.752478e-5, 9), round(result.value, 9), 'lambda0')
        result = iec60287_1_1w.calc_delta1_5_3_7_1(cs, 2, 66.256723)
        self.assertEqual(round(-0.013796733, 7), round(result.value, 7), 'delta1')
        result = iec60287_1_1w.calc_delta2_5_3_7_1(cs, 2, 66.256723)
        self.assertEqual(round(1.46717107e-7, 11), round(result.value, 11), 'delta2')

    def test_lambda1_d_d(self):
        cable = AutoCable(name='my_cable')
        cable.pipe_type = False
        cable.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cable.conductor.material = iec.COPPER
        cable.conductor.size = iec.IEC_2500MM2_2005
        cable.conductor.dia = 66.0
        cable.number_cores = iec.SINGLE_CORE
        cable.sheath_type = iec.WELDED_AL_SHEATH
        cable.sheath.dia = 130.2
        cable.sheath.dia_under_sheath = 128.0
        cable.sheath.thickness = 1.1
        cable.sheath.material = iec.ALUMINIUM
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 138.2

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.phase = iec.YELLOW
        pcr.x = 0
        pcr.y = 969.1
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.phase = iec.RED
        pcy.x = 500.0
        pcy.y = 969.1
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.phase = iec.BLUE
        pcb.x = -500.0
        pcb.y = 969.1
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE
        install = AutoInstall()
        install.cable_sets = [cs]

        result = iec60287_1_1w.calc_lambda1_dash_dash_5_3_7_1(install, 0, 0, 90.0, sheath_screen_temperature=73.792848)
        self.assertEqual(round(0.1080916, 6), round(result.value, 6), "lambda1''")

        cable.sheath_type = iec.CWS_SHEATH
        cable.wire_screen.material = iec.COPPER
        cable.wire_screen.number_wires = 41
        cable.wire_screen.wire_size = 1.05
        result = iec60287_1_1w.calc_lambda1_dash_dash_5_3_7_1(install, 0, 0, 90.0, sheath_screen_temperature=73.792848)
        self.assertEqual(round(0.0, 6), round(result.value, 6), "lambda1'' for CWS")

    def test_lambda1_d_d_lead(self):
        cable = AutoCable(name='my_cable')
        cable.pipe_type = False
        cable.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
        cable.conductor.material = iec.COPPER
        cable.conductor.size = iec.IEC_2500MM2_2005
        cable.conductor.dia = 66.0
        cable.number_cores = iec.SINGLE_CORE
        cable.sheath_type = iec.PB_SHEATH
        cable.sheath.dia = 137.0
        cable.sheath.dia_under_sheath = 127.4
        cable.sheath.thickness = 4.8
        cable.sheath.material = iec.LEAD
        cable.serving.material = iec.SERVING_PE
        cable.serving.dia = 145.0

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.phase = iec.YELLOW
        pcr.x = 0
        pcr.y = 972.5
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.phase = iec.RED
        pcy.x = 500.0
        pcy.y = 972.5
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.phase = iec.BLUE
        pcb.x = -500.0
        pcb.y = 972.5
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE
        install = AutoInstall()
        install.cable_sets = [cs]

        result = iec60287_1_1w.calc_lambda1_dash_dash_5_3_7_1(install, 0, 0, 90.0, sheath_screen_temperature=73.5405446)
        self.assertEqual(round(0.07574188, 6), round(result.value, 6), "lambda1''")
        result = iec60287_1_1w.calc_lambda1_dash_dash_5_3_7_1(install, 0, 0, 90.0, sheath_screen_temperature=73.5405446)
        self.assertEqual(round(0.07363, 6), round(result.value, 6), "lambda1''")

    def test_rcc(self):
        cable = AutoCable(name='my_cable')

        pcr = AutoPlacedCable()
        pcr.cable = cable
        pcr.phase = iec.YELLOW
        pcr.x = 0
        pcr.y = 972.5
        pcy = AutoPlacedCable()
        pcy.cable = cable
        pcy.phase = iec.RED
        pcy.x = 500.0
        pcy.y = 972.5
        pcb = AutoPlacedCable()
        pcb.cable = cable
        pcb.phase = iec.BLUE
        pcb.x = -500.0
        pcb.y = 972.5
        cs = AutoCableSet(name='my_cable_set')
        cs.placed_cables = [pcr, pcy, pcb]
        cs.f.value = 50.0
        cs.cct_type = iec.THREE_PHASE_SINGLE_CORE
        cs.length1 = 1000.0
        cs.length2 = 1000.0
        cs.length3 = 1000.0

        result = iec60287_1_1w.calc_rcc_5_3_7_2(cs)
        self.assertEqual(round(0.0, 6), round(result.value, 6), "rcc")

        cs.length1 = 1200.0
        result = iec60287_1_1w.calc_rcc_5_3_7_2(cs)
        self.assertEqual(round(0.003906, 6), round(result.value, 6), "rcc")

        cs.length1 = 1000.0
        cs.length2 = 1200.0
        result = iec60287_1_1w.calc_rcc_5_3_7_2(cs)
        self.assertEqual(round(0.003906, 6), round(result.value, 6), "rcc")

        cs.length2 = 1000.0
        cs.length3 = 1200.0
        result = iec60287_1_1w.calc_rcc_5_3_7_2(cs)
        self.assertEqual(round(0.003906, 6), round(result.value, 6), "rcc")

    def test_lambda1(self):
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
        cable_set_state.set_quantity('rcc', 0.00390625, '', source=dc.ATTR_USER_STATE_SET)
        cable_set_state.set_quantity('F', 0.234702, '', source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_1_dash', 5.873404, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_1_dash_dash', 0.107905, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        result = iec60287_1_1w.calc_lambda_1(install, 0, 0, 90.0, 73.7928481, state=install_state)
        self.assertEqual(round(0.13084805, 6), round(result.value, 6), "lambda1")

        cs.bonding = iec.SINGLE_POINT_BONDED
        cable_set_state = install_state.cable_set_states[0]
        cable_set_state.set_quantity('rcc', 0.00390625, '', source=dc.ATTR_USER_STATE_SET)
        cable_set_state.set_quantity('F', 0.234702, '', source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_1_dash', 5.873404, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_1_dash_dash', 0.107905, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        result = iec60287_1_1w.calc_lambda_1(install, 0, 0, 90.0, 73.7928481, state=install_state)
        self.assertEqual(round(0.107905, 6), round(result.value, 6), "lambda1")

        cs.bonding = iec.SOLID_BONDED
        cable_set_state.set_quantity('rcc', None, '', source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('F', 0.7385218, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_1_dash', 2.0033822, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        cable_set_state.placed_cable_states[0].cable_state.set_quantity('lambda_1_dash_dash', 0.730003, '',
                                                                        source=dc.ATTR_USER_STATE_SET)
        result = iec60287_1_1w.calc_lambda_1(install, 0, 0, 90.0, 73.7928481, state=install_state)
        self.assertEqual(round(2.54250509, 6), round(result.value, 6), "lambda1")


if __name__ == '__main__':
    unittest.main()
