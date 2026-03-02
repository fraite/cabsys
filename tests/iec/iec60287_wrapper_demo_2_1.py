import cabsys.data_classes.auto_install
import cabsys.data_classes.state
import cabsys.iec.iec60287_2_1 as iec60287_2_1wrapper
# import cabsys.iec.iec60287support as iec60287support
import cabsys
from cabsys.data_classes.cabsys_data_viewer import cabsys_data_show
from cabsys.quantity.log import Log
import cabsys.iec.iec_constants as iec
import cabsys.data_classes.cable_constants as cc
from cabsys.quantity.log_viewer import log_show


def clearance_calc():
    cable = cabsys.AutoCable()
    cable.auto_design()
    cable.set_auto_design(True)

    cabsys_data_show(cable, is_auto_design=True)
    log = Log()
    # cable_set_state = cabsys.data_classes.install.CableSetState(cable_set)
    t1 = iec60287_2_1wrapper.calc_t1_thermal_thickness(cable, log=log)
    print(t1)
    # data_store_show(cable_set_state)
    log_show(log)


def t1_single_core_calc():
    install = cabsys.AutoInstall()
    install.auto_design()
    install.set_auto_design(True)
    cabsys_data_show(install, is_auto_design=True)
    log = Log()
    # cable_set_state = cabsys.data_classes.install.CableSetState(cable_set)
    t1 = iec60287_2_1wrapper.calc_t1_4_1_2_1(install, 0, 0, log=log)
    print(t1)
    # data_store_show(cable_set_state)
    log_show(log)

    install.cable_sets[0].auto_formation = cc.TREFOIL_TOUCHING
    install.auto_design()
    cabsys_data_show(install, is_auto_design=True)
    log = Log()
    # cable_set_state = cabsys.data_classes.install.CableSetState(cable_set)
    t1 = iec60287_2_1wrapper.calc_t1_4_1_2_1(install, 0, 0, log=log)
    print(t1)
    # data_store_show(cable_set_state)
    log_show(log)

    install.cable_sets[0].placed_cables[0].cable.sheath_type = iec.CWS_SHEATH
    install.auto_design()
    cabsys_data_show(install, is_auto_design=True)
    log = Log()
    # cable_set_state = cabsys.data_classes.install.CableSetState(cable_set)
    t1 = iec60287_2_1wrapper.calc_t1_4_1_2_1(install, 0, 0, strict_iec=True, log=log)
    print(t1)
    # data_store_show(cable_set_state)
    log_show(log)


def t1_calc():
    install = cabsys.AutoInstall()
    install.auto_design()
    install.set_auto_design(True)
    cabsys_data_show(install, is_auto_design=True)
    log = Log()
    install_state = cabsys.data_classes.state.InstallState(install)
    cabsys_data_show(install_state)
    install.config.non_metal_screen_isotherm = False
    t1 = iec60287_2_1wrapper.calc_t1(install, 0, 0, state=install_state, log=log)
    print(t1)
    # data_store_show(install_state)
    log_show(log)
    log = Log()
    cabsys_data_show(install_state)
    t1 = iec60287_2_1wrapper.calc_t1(install, 0, 0, state=install_state, log=log)
    print(t1)
    cabsys_data_show(install_state)
    log_show(log)


if __name__ == '__main__':

    # demonstrate clearance calculations
    # clearance_calc()

    # demonstrate T1 calculations
    #t1_single_core_calc()

    # demonstrate T1 calculations
    t1_calc()