
from cabsys.quantity.quantity_store import QFloat
from cabsys.quantity.log import Log, LogSection
from cabsys import InstallState
from cabsys.data_classes.auto_install import AutoInstall
import cabsys.iec.iec60287support as iec60287support
import cabsys.iec.iec60287_1_1 as iec60287_1_1wrapper


@LogSection('W_cable')
def calc_w_cable(install: AutoInstall, cable_set_no: int, cable_no: int,
                 current: float, cond_temp: float = None,
                 u_pe: float = None,
                 state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the heat loss of a cable (W/m).

    Calculates the heat loss of a cable. If the conductor temperature is missing, the maximum conductor temperature
    is assumed.

    IEC extra equations

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no: cable number in cable_set
    :param current: current in the conductor of the cable (A)
    :param cond_temp: conductor temperature (°C)
    :param u_pe: phase to earth voltage applied to cable (V)
    :param state: cable set state
    :param log: logger used to store results
    :return: heat loss of cable (W/m)
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    if state is not None:
        cable_set_state = state.cable_set_states[cable_set_no]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_no].cable_state
    else:
        cable_state = None

    if log is not None:
        log.add_line('current', current, 'A', 'set by program')

    if cond_temp is None:
        cond_temp = iec60287support.get_max_cond_temp(cable, log=log).value
    rac = iec60287_1_1wrapper.calc_r_ac(cable_set, cable_no, cond_temp,
                                        iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                        state=cable_set_state, log=log).value
    always_calc_wd = install.config.always_calc_wd.get_value(unit='', log=log)
    wd = iec60287_1_1wrapper.calc_wd(install, cable_set_no, cable_no, u_pe=u_pe, state=state, log=log).value

    sheath_temp = iec60287_1_1wrapper.calc_theta_sc(install, cable_set_no, cable_no,
                                                    current, cond_temp, state=state, log=log).value

    lambda_1 = iec60287_1_1wrapper.calc_lambda_1(install, cable_set_no, cable_no, cond_temp,
                                                 sheath_temperature=sheath_temp,
                                                 state=state, log=log).value
    lambda_2 = iec60287_1_1wrapper.calc_lambda_2(install, cable_set_no, cable_no, state=state, log=log).value

    w_cable = current**2 * rac * (1 + lambda_1 + lambda_2) + wd

    return QFloat(w_cable, 'W/m', 'IEC extra', description='heat loss of cable',
                  symbol='W_cable')