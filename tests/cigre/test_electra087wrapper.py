import unittest
# import math
import cabsys.iec.iec_constants as iec
import cabsys.cigre.cigre_constants as cigre_consts
import cabsys.cigre.electra087wrapper as elt087wrapper
# import cabsys.iec.iec_extra as iec_extra
from cabsys.data_classes.auto_cable import AutoCable
# from cabsys.data_classes.install import Install, CableSet, PlacedCable
from tests.test_objects import default_install, default_current_curve_ng, elt087_w2_install, elt087_current_curve
from cabsys.quantity.log import Log
from cabsys.data_classes.state import InstallState
# from cabsys.gui.log_viewer import log_show


class TestIEC60287p1p1(unittest.TestCase):

    def test_cond_temp(self):
        install = elt087_w2_install()
        cc = elt087_current_curve()
        install.cable_sets[0].current_curve = cc
        install.cable_sets[0].desired_I = 3600.0
        install.cable_sets[0].desired_I_change = False

        log = Log()
        state = InstallState(install)
        result = elt087wrapper.solve_calc_temperature(install, state=state, log=log)
        # log_show(log)
        self.assertEqual(round(112.44817867263689,6), round(result[1][0][0], 6), "transient conductor temperature")

        install.config.log_level = 30
        install.config.elt87_config.elt87_time_step = 30.0
        install.config.elt87_config.vary_time_step.set_value(cigre_consts.TIME_STEP_CONSTANT)
        log = Log()
        state = InstallState(install)
        result = elt087wrapper.solve_calc_temperature(install, state=state, log=log)
        # log_show(log)
        self.assertEqual(round(116.152933,6), round(result[1][0][0], 6), "transient conductor temperature")

    def test_w_i(self):
        install = default_install()
        install.cable_sets[0].desired_I = 2014.53
        cc = default_current_curve_ng()
        install.cable_sets[0].current_curve = cc

        install.cable_sets[0].preload_type.set_value(iec.PRELOAD_AVE_LOSS)
        log = Log()
        result = elt087wrapper.calc_w_i(install, 0, 0, log=log)
        # log_show(log)
        self.assertEqual(round(30.010887, 6), round(result.value, 6), "change of heat loss of cable")

        install.cable_sets[0].preload_type.set_value(iec.PRELOAD_OFF)
        log = Log()
        result = elt087wrapper.calc_w_i(install, 0, 0, log=log)
        # log_show(log)
        self.assertEqual(round(50.962727, 6), round(result.value, 6), "change of heat loss of cable")

        install.cable_sets[0].preload_type.set_value(None)
        log = Log()
        result = elt087wrapper.calc_w_i(install, 0, 0, log=log)
        # log_show(log)
        self.assertEqual(round(50.962727, 6), round(result.value, 6), "change of heat loss of cable")

        install.cable_sets[0].preload_type.set_value(iec.PRELOAD_CONST_CURRENT)
        install.cable_sets[0].preload_current.set_value(200.0, unit='A')
        log = Log()
        result = elt087wrapper.calc_w_i(install, 0, 0, log=log)
        # log_show(log)
        self.assertEqual(round(46.382579, 6), round(result.value, 6), "change of heat loss of cable")

    def test_theta_r_t(self):
        install = default_install()
        install.cable_sets[0].desired_I = 2014.53
        install.scenarios[install.selected_scenario.value].end_time = 24.0 * 60.0 * 60.0
        q_rating_type = install.scenarios[install.selected_scenario.value].rating_type
        q_rating_type.set_value(iec.RATING_TRANSIENT)
        cc = default_current_curve_ng()
        install.cable_sets[0].current_curve = cc
        install.cable_sets[0].preload_type.set_value(iec.PRELOAD_AVE_LOSS)
        log = Log()
        result = elt087wrapper.calc_theta_r_t(install, 0, 0, 0.1, log=log)
        # log_show(log)
        self.assertEqual(round(6.076246836, 6), round(result.value, 6), "temperature rise")

        result = elt087wrapper.calc_theta_r_t(install, 0, 0, 0.558198, log=log)
        # log_show(log)
        self.assertEqual(round(0.099099, 6), round(result.value, 6), "temperature rise")

        install.scenarios[install.selected_scenario.value].buried.ground_thermal_diffusivity.set_value(5e-7)
        log = Log()
        result = elt087wrapper.calc_theta_r_t(install, 0, 0, 0.1, log=log)
        # log_show(log)
        self.assertEqual(round(6.67559711, 6), round(result.value, 6), "temperature rise")

    def test_r(self):
        install = default_install()
        q_rating_type = install.scenarios[install.selected_scenario.value].rating_type
        q_rating_type.set_value(iec.RATING_TRANSIENT)
        install.cable_sets[0].desired_I = 2014.53
        install.scenarios[install.selected_scenario.value].end_time = 24.0 * 60.0 * 60.0
        install.cable_sets[0].preload_type.value = iec.PRELOAD_OFF
        cc = default_current_curve_ng()
        install.cable_sets[0].current_curve = cc
        log = Log()
        result = elt087wrapper.calc_d_t(install, 0, 0, log=log)
        # log_show(log)
        self.assertEqual(round(0.605, 3), round(result.value, 3), "boundary radius")

        install.scenarios[install.selected_scenario.value].end_time = 365.0 * 24.0 * 60.0 * 60.0
        log = Log()
        result = elt087wrapper.calc_d_t(install, 0, 0, log=log)
        # log_show(log)
        self.assertEqual(round(2.2018195, 6), round(result.value, 6), "boundary radius for long transient")

    def test_ni_10(self):
        """Calculate ni case 1: 10 layers"""
        cab = AutoCable(name='my_cable')
        cab.number_cores = iec.SINGLE_CORE
        cab.conductor.dia = 50.0
        cab.sheath_type = iec.WELDED_AL_SHEATH
        cab.sheath.dia = 72.0
        cab.sheath.thickness = 1.0
        cab.sheath.dia_under_sheath = 70.0
        # cable_state = CableState()
        # cable_state.set_quantity('r_dash', 8.88e-6, 'ohm/m', top=dc.ATTR_USER_SET_SET)
        result = elt087wrapper.calc_ni(cab)
        self.assertEqual(10, result.value, 'calculated number of insulation layers: 10')

    def test_ni_5(self):
        """Calculate ni case 2: 4 layers"""
        cab = AutoCable(name='my_cable')
        cab.number_cores = iec.SINGLE_CORE
        cab.conductor.dia = 50.0
        cab.sheath_type = iec.WELDED_AL_SHEATH
        cab.sheath.dia = 61.0
        cab.sheath.thickness = 1.0
        cab.sheath.dia_under_sheath = 59.0
        # cable_state = CableState()
        # cable_state.set_quantity('r_dash', 8.88e-6, 'ohm/m', top=dc.ATTR_USER_SET_SET)
        result = elt087wrapper.calc_ni(cab)
        self.assertEqual(4, result.value, 'calculated number of layers')

    def test_ns(self):
        install = default_install()
        q_rating_type = install.scenarios[install.selected_scenario.value].rating_type
        q_rating_type.set_value(iec.RATING_TRANSIENT)
        install.cable_sets[0].desired_I = 2014.53
        install.cable_sets[0].preload_type = iec.PRELOAD_OFF
        install.scenarios[install.selected_scenario.value].end_time = 24.0 * 60.0 * 60.0
        cc = default_current_curve_ng()
        install.cable_sets[0].current_curve = cc
        log = Log()
        result = elt087wrapper.calc_ns(install, 0, 0, log=log)
        # log_show(log)
        self.assertEqual(round(25, 6), round(result.value, 6), "number of soil layers")

        install.scenarios[install.selected_scenario.value].end_time = 365.0 * 24.0 * 60.0 * 60.0
        log = Log()
        result = elt087wrapper.calc_ns(install, 0, 0, log=log)
        # log_show(log)
        self.assertEqual(round(97, 6), round(result.value, 6), "boundary radius for long transient")

        install = elt087_w2_install()
        cc = elt087_current_curve()
        install.cable_sets[0].current_curve = cc
        install.cable_sets[0].desired_I = 3200.0
        install.cable_sets[0].desired_I_change = False
        log = Log()
        result = elt087wrapper.calc_ns(install, 0, 0, log=log)
        # log_show(log)
        self.assertEqual(round(117, 6), round(result.value, 6), "number of soil layers")

    def test_exp_int(self):
        """Calculate the exponential integral"""
        x = -1.0
        self.assertRaises(Exception, elt087wrapper.calc_exponential_integral, x)

        x = 0.0
        self.assertRaises(Exception, elt087wrapper.calc_exponential_integral, x)

        x = 0.1
        result = elt087wrapper.calc_exponential_integral(x)
        self.assertEqual(round(1.8229238, 5), round(result.value, 5), f'exponential integral {x}')

        x = 0.5
        result = elt087wrapper.calc_exponential_integral(x)
        self.assertEqual(round(0.5597735, 5), round(result.value, 5), f'exponential integral {x}')

        x = 2.0
        result = elt087wrapper.calc_exponential_integral(x)
        self.assertEqual(round(0.04890292, 7), round(result.value, 7), f'exponential integral {x}')

        x = 5.0
        result = elt087wrapper.calc_exponential_integral(x)
        self.assertEqual(round(0.0011482401, 7), round(result.value, 7), f'exponential integral {x}')


if __name__ == '__main__':
    unittest.main()
