import math
import cabsys.iec.iec_constants as iec
import cabsys.data_classes.current_curve_const as tc
import cabsys.cigre.cigre_constants as cigre_consts
from cabsys.data_classes.auto_cable import AutoCable
from cabsys.data_classes.auto_install import AutoInstall, AutoCableSet, AutoPlacedCable
from cabsys.data_classes.auto_current_curve import AutoCurrentCurve, TransientCurrentPoint
from cabsys.quantity.log import Log
# from cabsys.gui.log_viewer import log_show


def default_install() -> AutoInstall:
    cab = AutoCable(name='my_cable')
    cab.set_auto_design(False)
    cab.sheath_type = iec.WELDED_AL_SHEATH
    cab.armour = iec.NONE
    cab.number_cores = iec.SINGLE_CORE
    cab.design_volts = 220.0
    cab.conductor.dia = 66.0
    cab.conductor.size = iec.IEC_2500MM2_2005
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
    cab.core.cond_screen_dia = 70.6
    cab.core.insu_dia = 124.2
    cab.core.insulation_material = iec.INS_XLPE_UNFILLED
    cab.core.bedding_dia = 127.8
    cab.sheath.material = iec.ALUMINIUM
    cab.sheath.dia_under_sheath = 128.0
    cab.sheath.thickness = 1.1
    cab.sheath.dia = 130.2
    cab.sheath.binder_dia = 130.2
    cab.serving.material = iec.SERVING_PE
    cab.serving.dia = 138.2
    cab.pipe_type = False
    pc1 = AutoPlacedCable()
    pc1.x = 0.0
    pc1.y = -969.1
    pc1.phase = iec.YELLOW
    pc1.u_pe = 400.0*1000 / math.sqrt(3)
    # pc1.ambient_theta = 15.0
    pc2 = AutoPlacedCable()
    pc2.x = -500.0
    pc2.y = -969.1
    pc2.phase = iec.RED
    pc2.u_pe = 400.0*1000 / math.sqrt(3)
    # pc2.ambient_theta = 15.0
    pc3 = AutoPlacedCable()
    pc3.x = 500.0
    pc3.y = -969.1
    pc3.phase = iec.BLUE
    pc3.u_pe = 400.0*1000 / math.sqrt(3)
    # pc3.ambient_theta = 15.0
    pc1.cable = pc2.cable = pc3.cable = cab
    cab_set = AutoCableSet()
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.desired_I = 1000.0
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE
    cab_set.bonding = iec.CROSS_BONDED
    cab_set.transposed = True
    cab_set.length1 = cab_set.length2 = 1000.0
    cab_set.length3 = 1200.0
    inst = AutoInstall(name='my_install')
    inst.set_auto_design(False)
    inst.cable_sets = [cab_set]
    inst.kind = iec.BURIED
    inst.auto_ambient_theta = 15.0
    inst.scenarios[install.selected_scenario.value].buried.ground_tr.set_value(1.2, unit='K.m/W')
    inst.config.elt87_config.elt87_boundary_accuracy = 0.1    # °C
    inst.config.elt87_config.elt87_boundary_accuracy2 = 3
    return inst


def default_current_curve_ng() -> AutoCurrentCurve:
    cc = AutoCurrentCurve(name='my_current_curve')
    cc.set_auto_design(False)
    cc.cyclic = True
    cc.preload_type = tc.PRELOAD_AVE_LOSS
    cc.preload_volts = True
    cc.normalise_curve = True
    p0 = TransientCurrentPoint()
    p0.time = 0.0
    p0.current = 1.0
    p1 = TransientCurrentPoint()
    p1.time = 6.0 * 60.0 * 60.0
    p1.current = 0.6
    cc.points = [p0, p1]
    return cc


def elt087_w2_install() -> AutoInstall:
    """Electra 87 Worked Example 2 Install

    An installation that matches the worked examples of Electra 87, transient ratings. This install is targeted at
    the worked example using the second (independent program) example.

    :return: Electra 87 worked example Install
    """

    # cable
    cab = AutoCable(name='elt087_cable')
    cab.set_auto_design(False)
    cab.sheath_type = iec.PB_SHEATH
    cab.armour = iec.NONE
    cab.number_cores = iec.SINGLE_CORE
    cab.design_volts = 220.0
    cab.conductor.dc_resistance20 = 8.95e-6
    cab.conductor.alpha20 = 0.00393
    cab.conductor.dia = 57.5
    cab.conductor.ks = 0.435
    cab.conductor.kp = 0.37
    cab.conductor.conductor_volume = 2040.0
    cab.conductor.duct_dia = 0.0
    cab.conductor.size = iec.IEC_2000MM2
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
    cab.core.cond_screen_dia = 59.0
    cab.core.insu_dia = 105.0
    cab.core.insulation_material = iec.INS_PAPER_SCOF
    cab.core.permittivity = 3.3
    cab.core.tan_d = 0.0025
    cab.core.rho_1 = 5.0
    cab.core.v_s_heat = 2.0e6
    cab.core.bedding_dia = 106.0
    cab.sheath.material = iec.LEAD
    cab.sheath.dc_resistance20 = 154.8e-6
    cab.sheath.alpha20 = 0.004
    cab.sheath.dia_under_sheath = 106.0
    cab.sheath.thickness = 4.0
    cab.sheath.dia = 114.0
    cab.sheath.binder_dia = 114.0
    cab.sheath.v_s_heat = 1.45e6
    # next layers are needed as SCOF lead sheath cables always have tape reinforcement
    cab.tape.material = iec.BRONZE
    cab.tape.dia_under_tape = 114.0
    cab.tape.number_tapes = 2
    cab.tape.tape_width = 20.0
    cab.tape.tape_thickness = 0.001
    cab.tape.magnetic = False
    cab.tape.angle = 54.0
    cab.tape.number_layers = 1
    cab.tape.dia = 114.0
    # back to Electra 87 data
    cab.serving.material = iec.SERVING_PE
    cab.serving.dia = 122.0
    cab.serving.rho_t = 3.5
    cab.serving.v_s_heat = 2.4e6
    cab.pipe_type = False

    # placed cable
    pc1 = AutoPlacedCable()
    pc1.x = 0.0
    pc1.y = -1000.0
    pc1.phase = iec.YELLOW
    pc1.u_pe = 400.0*1000 / math.sqrt(3)
    # pc1.ambient_theta = 10.0
    pc2 = AutoPlacedCable()
    pc2.x = -700.0
    pc2.y = -1000.0
    pc2.phase = iec.RED
    pc2.u_pe = 400.0*1000 / math.sqrt(3)
    # pc2.ambient_theta = 10.0
    pc3 = AutoPlacedCable()
    pc3.x = 700.0
    pc3.y = -1000.0
    pc3.phase = iec.BLUE
    pc3.u_pe = 400.0*1000 / math.sqrt(3)
    # pc3.ambient_theta = 10.0
    pc1.cable = pc2.cable = pc3.cable = cab

    #  cable set
    cab_set = AutoCableSet()
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.desired_I = 1796.3
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE
    cab_set.bonding = iec.CROSS_BONDED
    cab_set.transposed = True
    cab_set.duct_layout = iec.NO_DUCTS
    cab_set.length1 = cab_set.length2 = 1000.0
    cab_set.length3 = 1150.0
    cab_set.preload_type = iec.PRELOAD_CONST_CURRENT
    cab_set.preload_current = 0.0

    # install
    elt087_install = AutoInstall(name='elt087_install')
    q_rating_type = elt087_install.scenarios[elt087_install.selected_scenario.value].rating_type
    q_rating_type.set_value(iec.RATING_TRANSIENT)
    elt087_install.set_auto_design(False)
    elt087_install.cable_sets = [cab_set]
    elt087_install.kind = iec.BURIED
    elt087_install.auto_ambient_theta = 10.0
    elt087_install.scenarios[install.selected_scenario.value].buried.ground_tr.set_value(1.0, unit='K.m/W')
    elt087_install.scenarios[install.selected_scenario.value].buried.ground_v_s_heat.set_value(2e6, unit='J/K/m³')
    elt087_install.scenarios[elt087_install.selected_scenario.value].end_time = 4.0 * 60.0 * 60.0
    # config
    elt087_install.config.memorise = True
    elt087_install.config.solver_continuous = iec.CALC_TRANSIENT_ELT_87
    elt087_install.config.auto_calc = False
    elt087_install.config.max_log_count = 500000
    elt087_install.config.log_level = 30
    elt087_install.config.non_metal_screen_isotherm = True
    elt087_install.config.stop_warn = True
    elt087_install.config.always_calc_wd = True
    elt087_install.config.always_calc_c_gs = True
    elt087_install.config.always_calc_delta = True
    # config.elt87_config
    elt087_install.config.elt87_config.elt87_boundary_accuracy = 0.1    # °C
    elt087_install.config.elt87_config.elt87_boundary_accuracy2 = 3     # number of decimal points
    elt087_install.config.elt87_config.elt87_max_delta_theta = 0.5
    elt087_install.config.elt87_config.elt87_time_step = 1800.0
    elt087_install.config.elt87_config.vary_time_step = cigre_consts.TIME_STEP_USER_VARY
    elt087_install.config.elt87_config.time_step1 = 60.0
    elt087_install.config.elt87_config.time_period1 = 600.0
    elt087_install.config.elt87_config.time_step2 = 300.0
    elt087_install.config.elt87_config.time_period2 = 3600.0

    return elt087_install


def elt087_current_curve() -> AutoCurrentCurve:
    cc = AutoCurrentCurve(name='elt087_current_curve')
    cc.set_auto_design(False)
    cc.emergency = False
    cc.cyclic = False
    cc.normalise_curve = False
    p0 = TransientCurrentPoint()
    p0.time = 0.0
    p0.current = 3600.0
    cc.points = [p0]
    return cc


if __name__ == '__main__':

    install = default_install()
    log = Log()
