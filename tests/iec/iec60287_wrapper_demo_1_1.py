import cabsys.data_classes.auto_install
import cabsys.data_classes.state
import cabsys.iec.iec60287_1_1 as iec60287_1_1wrapper
import cabsys
from cabsys.gui import data_store_show
from cabsys.quantity.log import Log
import cabsys.iec.iec_constants as iec
import cabsys.quantity.quantity_constants as dc
from cabsys.quantity.log_viewer import log_show


def cond_temperature_change_calcs():

    print('\nCalculate dc resistance by setting conductor temperature in different ways')

    print('\ncalculate values using cable class - input temperature set by program')
    cab = cabsys.AutoCable(name='my_cable')
    cab.max_cond_temp = 100.0
    # cab.conductor.dc_resistance20 = 17.6e-6
    cab.conductor.size = iec.IEC_1000MM2
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
    print('show cable using gui')
    data_store_show(cab)
    log = Log()
    cable_state = cabsys.data_classes.state.CableState()
    dc_resistance = iec60287_1_1wrapper.calc_r_dash(cab, cond_temp=88.0, cond_temp_source='passed as argument',
                                                    state=cable_state, log=log)
    print(dc_resistance)
    data_store_show(cable_state)
    log_show(log)

    print('\ncalculate values using cable class - input set by result')
    cab = cabsys.AutoCable(name='my_cable')
    cab.max_cond_temp = 100.0
    cab.conductor.dc_resistance20 = 17.6e-6
    cab.conductor.alpha20 = 3.93e-3
    print('show cable using gui')
    data_store_show(cab)
    log = Log()
    cable_state = cabsys.data_classes.state.CableState()
    cable_state.set_quantity('cond_temp', 91.0, '°C', source=dc.ATTR_USER_STATE_SET, symbol='θ_c')
    dc_resistance = iec60287_1_1wrapper.calc_r_dash(cab, state=cable_state, log=log)
    print(dc_resistance)
    data_store_show(cable_state)
    log_show(log)

    print('\ncalculate values using cable class - input set by cable parameter')
    cab = cabsys.AutoCable(name='my_cable')
    cab.max_cond_temp = 89.0
    cab.conductor.dc_resistance20 = 17.6e-6
    cab.conductor.alpha20 = 3.93e-3
    print('show cable using gui')
    data_store_show(cab)
    log = Log()
    cable_state = cabsys.data_classes.state.CableState()
    dc_resistance = iec60287_1_1wrapper.calc_r_dash(cab, state=cable_state, log=log)
    print(dc_resistance)
    data_store_show(cable_state)
    log_show(log)

    print('\ncalculate values using cable class - calculate default value for conductor temperature')
    cab = cabsys.AutoCable(name='my_cable')
    cab.conductor.dc_resistance20 = 17.6e-6
    cab.conductor.set_source('dc_resistance20', dc.ATTR_USER_SET)
    cab.conductor.alpha20 = 3.93e-3
    cab.conductor.set_source('alpha20', dc.ATTR_USER_SET)
    print('show cable using gui')
    data_store_show(cab)
    log = Log()
    cable_state = cabsys.data_classes.state.CableState()
    dc_resistance = iec60287_1_1wrapper.calc_r_dash(cab, state=cable_state, log=log)
    print(dc_resistance)
    data_store_show(cable_state)
    log_show(log)


def dc_res_calcs():

    print('\ncalculate values using cable class - cable object defines dc_resistance20')
    cab = cabsys.AutoCable(name='my_cable')
    cab.conductor.dc_resistance20 = 17.6e-6
    # cab.conductor.set_source('dc_resistance20', dc.USER_CABSYS_SET) <-- not needed as set automatically
    cab.conductor.alpha20 = 3.93e-3
    # cab.conductor.set_source('alpha20', dc.USER_CABSYS_SET) <-- not needed as set automatically
    print('show cable using gui')
    data_store_show(cab)
    log = Log()
    cable_results = cabsys.data_classes.state.CableState()
    dc_resistance = iec60287_1_1wrapper.calc_r_dash(cab, state=cable_results, log=log)
    print(dc_resistance)
    data_store_show(cable_results)
    log_show(log)

    print('\ncalculate values using cable class - dc_resistance worked out using size and material')
    cab2 = cabsys.AutoCable(name='my_cable')
    cab2.conductor.size = iec.IEC_1000MM2
    cab2.conductor.material = iec.COPPER
    print('show cable using gui')
    data_store_show(cab2)
    log2 = Log()
    cable_results = cabsys.data_classes.state.CableState()
    dc_resistance2 = iec60287_1_1wrapper.calc_r_dash(cab2, state=cable_results, log=log2)
    print(dc_resistance2)
    data_store_show(cable_results)
    # print(log2.text(iec.VERSION))
    log_show(log2)


def simple_calcs_missing_parameters():

    cabsys.QuantityStore.ask_if_missing = dc.CONSOLE
    print(cabsys.QuantityStore.ask_if_missing)

    print('\ncalculate values using cable class')
    cab2 = cabsys.AutoCable(name='my_cable')
    # cab2.conductor.size = constants.IEC_1000MM2
    cab2.conductor.material = iec.COPPER
    # print('show cable using gui')
    data_store_show(cab2)
    log2 = Log()
    cable_results = cabsys.data_classes.state.CableState()
    dc_resistance2 = iec60287_1_1wrapper.calc_r_dash(cab2, cond_temp=90.0, state=cable_results, log=log2)
    print(dc_resistance2)
    # print(log2.text(iec.VERSION))
    data_store_show(cable_results)
    log_show(log2)


def ys_calc():

    print('\ncalculate values using cable class')
    cab2 = cabsys.AutoCable(name='my_cable')
    cab2.conductor.size = iec.IEC_1000MM2
    cab2.conductor.material = iec.COPPER
    cab2.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
    # cab2.max_cond_temp = 90.0
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab2
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab2
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab2
    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0

    data_store_show(cab_set)
    log1 = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    ys = iec60287_1_1wrapper.calc_ys(cab_set, 0, state=cable_set_state, log=log1)
    print(ys)
    data_store_show(cable_set_state)
    log_show(log1)

    print('\ncalculate values using cable class - ks set to 0.7')
    log1 = Log()
    cab2.conductor.ks = 0.7
    data_store_show(cab_set)
    ys = iec60287_1_1wrapper.calc_ys(cab_set, 0, state=cable_set_state, log=log1)
    print(ys)
    data_store_show(cable_set_state)
    log_show(log1)

    print("\ncalculate values using cable class - with R' result override")
    log1 = Log()
    cable_set_state.placed_cable_states[0].cable_state.set_quantity("r_dash", 10e-6)
    data_store_show(cable_set_state)
    ys = iec60287_1_1wrapper.calc_ys(cab_set, 0, state=cable_set_state, log=log1)
    print(ys)
    data_store_show(cable_set_state)
    log_show(log1)


def ys_calc_oval():

    print('\ncalculate values using cable class')
    cab2 = cabsys.AutoCable(name='my_cable')
    cab2.conductor.size = iec.IEC_400MM2
    cab2.conductor.material = iec.COPPER
    cab2.conductor.makeup = iec.OVAL_STRANDED_IMPREGNATED
    # cab2.max_cond_temp = 90.0
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab2
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab2
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab2
    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0

    data_store_show(cab_set)
    log1 = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    ys = iec60287_1_1wrapper.calc_ys(cab_set, 0, state=cable_set_state, log=log1)
    print(ys)
    data_store_show(cable_set_state)
    log_show(log1)


def xs_duct_calc():

    print('\ncalculate values using cable class')
    cab2 = cabsys.AutoCable(name='my_cable')
    cab2.conductor.size = iec.IEC_1000MM2
    cab2.conductor.material = iec.COPPER
    cab2.conductor.makeup = iec.HOLLOW_KEYSTONE_IMPREGNATED
    cab2.conductor.duct_dia.value = 12.0
    cab2.conductor.dia.value = 38.4
    cab2.max_cond_temp = 90.0
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab2
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab2
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab2
    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0

    data_store_show(cab_set)
    log2 = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    result = iec60287_1_1wrapper.calc_xs2(cab_set, 0, state=cable_set_state, log=log2)
    print(result)
    data_store_show(cable_set_state)
    log_show(log2)

    print('\ncalculate values using cable class - compaction set to 95%')
    cab2.conductor.compaction = 95.0
    data_store_show(cab_set)
    log2 = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    result = iec60287_1_1wrapper.calc_xs2(cab_set, 0, state=cable_set_state, log=log2)
    print(result)
    data_store_show(cable_set_state)
    log_show(log2)

    print('\ncalculate values using cable class - dc_dash_dia = 35.5 mm')
    cab2.conductor.compaction = 95.0
    cab2.conductor.dc_dash_dia = 35.5
    data_store_show(cab_set)
    log2 = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    result = iec60287_1_1wrapper.calc_xs2(cab_set, 0, state=cable_set_state, log=log2)
    print(result)
    data_store_show(cable_set_state)
    log_show(log2)


def xp_calc():

    print('\ncalculate values using cable class')
    cab2 = cabsys.AutoCable(name='my_cable')
    cab2.conductor.size = iec.IEC_2500MM2_2005
    cab2.conductor.material = iec.COPPER
    cab2.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab2
    pc1.x = 0.0
    pc1.y = -900.0
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab2
    pc2.x = 300.0
    pc2.y = -900.0
    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2]
    cab_set.f = 50.0

    print('show cable set using gui')
    data_store_show(cab_set)
    log2 = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    result = iec60287_1_1wrapper.calc_xp2(cab_set, 0, state=cable_set_state, log=log2)
    print(result)
    log_show(log2)
    data_store_show(cable_set_state)


def yp_calc():

    print('\ncalculate yp')
    cab = cabsys.AutoCable(name='my_cable')
    cab.pipe_type = False
    cab.number_cores = iec.SINGLE_CORE
    cab.conductor.size = iec.IEC_2500MM2_2005
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
    cab.conductor.dia.value = 66.0
    cab.serving.dia = 138.2
    cab.serving.material = iec.SERVING_PE
    cab.pipe.material = None
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab
    pc1.x = 0.0
    pc1.y = -900.0
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab
    pc2.x = 500.0
    pc2.y = -900.0
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab
    pc3.x = -500.0
    pc3.y = -900.0

    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE

    data_store_show(cab_set)
    log = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    yp = iec60287_1_1wrapper.calc_yp(cab_set, 0, state=cable_set_state, log=log)
    print(yp)
    data_store_show(cable_set_state)
    log_show(log)

    print('\ncalculate yp oval')
    cab = cabsys.AutoCable(name='my_cable')
    cab.pipe_type = False
    cab.number_cores = iec.THREE_CORE
    cab.common_sheath = True
    cab.conductor.size = iec.IEC_400MM2
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.OVAL_STRANDED_IMPREGNATED
    cab.conductor.minor_dia = 20.0
    cab.conductor.major_dia = 26.6805
    cab.core.spacing = 63.9
    cab.serving.material = iec.SERVING_PE
    cab.pipe.material = None
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab
    pc1.x = 0.0
    pc1.y = -900.0
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab
    pc2.x = 500.0
    pc2.y = -900.0
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab
    pc3.x = -500.0
    pc3.y = -900.0

    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_THREE_CORE

    data_store_show(cab_set)
    log = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    yp = iec60287_1_1wrapper.calc_yp(cab_set, 0, state=cable_set_state, log=log)
    print(yp)
    data_store_show(cable_set_state)
    log_show(log)


def r_ac_calc():

    print('\ncalculate R')
    cab = cabsys.AutoCable(name='my_cable')
    cab.pipe_type = False
    cab.number_cores = iec.SINGLE_CORE
    cab.conductor.size = iec.IEC_2500MM2_2005
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
    cab.conductor.dia.value = 66.0
    cab.serving.dia = 138.2
    cab.serving.material = iec.SERVING_PE
    cab.pipe.material = None
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab
    pc1.x = 0.0
    pc1.y = -900.0
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab
    pc2.x = 500.0
    pc2.y = -900.0
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab
    pc3.x = -500.0
    pc3.y = -900.0

    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE

    data_store_show(cab_set)
    log = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    r_ac = iec60287_1_1wrapper.calc_r_ac(cab_set, 0, 90, None, cable_set_state, log)
    # r_ac = iec60287_1_1wrapper.calc_r_ac(cab_set, 0, 90, 'set by line')
    print(r_ac)
    data_store_show(cable_set_state)
    log_show(log)

    print('\ncalculate R oval')
    cab = cabsys.AutoCable(name='my_cable')
    cab.pipe_type = False
    cab.number_cores = iec.THREE_CORE
    cab.conductor.size = iec.IEC_400MM2
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.OVAL_STRANDED_IMPREGNATED
    cab.conductor.minor_dia = 20.0
    cab.conductor.major_dia = 26.6805
    cab.core.spacing = 63.9
    cab.serving.material = iec.SERVING_PE
    cab.pipe.material = None
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab
    pc1.x = 0.0
    pc1.y = -900.0
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab
    pc2.x = 500.0
    pc2.y = -900.0
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab
    pc3.x = -500.0
    pc3.y = -900.0

    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_THREE_CORE

    data_store_show(cab_set)
    log = Log()
    cable_set_state = cabsys.data_classes.state.CableSetState(cab_set)
    r_ac = iec60287_1_1wrapper.calc_r_ac(cab_set, 0, state=cable_set_state, log=log)
    print(r_ac)
    data_store_show(cable_set_state)
    log_show(log)


def c_calc():
    # cable_set = cabsys.AutoCableSet()
    # cable_set.auto_design()
    install = cabsys.AutoInstall()
    install.auto_design()

    data_store_show(install)
    log = Log()
    # cable_state = cabsys.data_classes.state.CableState()
    install_state = cabsys.data_classes.state.InstallState()
    c = iec60287_1_1wrapper.calc_c(install, cable_set_num=0, cable_num=0, state=install_state, log=log)
    print(c)
    # wd = iec60287_1_1wrapper.calc_wd(project, cable_set, 0, placed_cable_results, log=log)
    # print(wd)
    data_store_show(install_state)
    log_show(log)


def wd_calc():
    # cable_set = cabsys.AutoCableSet()
    # cable_set.auto_design()
    install = cabsys.AutoInstall()
    install.auto_design()

    data_store_show(install)
    log = Log()
    # cable_set_state = cabsys.data_classes.state.CableSetState(cable_set)
    install_state = cabsys.data_classes.state.InstallState(install)
    wd = iec60287_1_1wrapper.calc_wd(install, cable_set=0, cable_num=0, state=install_state, log=log)
    print(wd)
    data_store_show(install_state)
    log_show(log)


def theta_sc_calc():

    install = cabsys.AutoInstall(name='my_install')

    cable_set = cabsys.AutoCableSet()
    cable_set.auto_design()
    install.cable_sets.append(cable_set)
    install.auto_design()

    data_store_show(install)
    log = Log()
    install_state = cabsys.data_classes.state.InstallState(install)
    cable_set_state = install_state.cable_set_states[0]
    cable_set_state.set_quantity('current', 1000.0, 'A', description='current in cable set', source='assumed rating',
                                 symbol='I')
    theta_sc = iec60287_1_1wrapper.calc_theta_sc(install, 0, 0, state=install_state, log=log)
    print(theta_sc)
    data_store_show(install_state)
    log_show(log)


if __name__ == '__main__':

    # change top of conductor temperature to calculate d.c. resistance at operating temperature
    # cond_temperature_change_calcs()

    # check simple calc
    # dc_res_calcs()

    # missing parameter calculations
    # simple_calcs_missing_parameters()

    # calculate ys
    # ys_calc()

    # calculate ys
    # ys_calc_oval()

    # calculate xs for ducted stranded conductors
    # xs_duct_calc()

    # calc xp
    # xp_calc()

    # demonstrate yp calculations
    # yp_calc()

    # demonstrate R calculations
    # r_ac_calc()

    # demonstrate Wd calculations
    # c_calc()

    # demonstrate Wd calculations
    # wd_calc()

    # demonstrate theta_sc calculations
    theta_sc_calc()
