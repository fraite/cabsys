"""IEC 60287-1-1: 2023 Alternative current rating equations and calculation of losses - General

In addition to the function returning a result, the result can be returned in the State object. A bespoke logger
(different to the standard Python logger) can also be used.

Some of the equations have been modified. The logger notes where the changes have been made.
"""

import math
from typing import Tuple, Optional

from cabsys import IEC60287Exception
from cabsys.data_classes.install import CableSet
import cabsys.data_classes.state
from cabsys.quantity.quantity_store import QFloat
from cabsys.quantity.log import Log, LogSection
from cabsys.data_classes.cable import Cable
from cabsys import CableState, CableSetState, InstallState
from cabsys.data_classes.install import Install
from cabsys.data_classes.auto_install import AutoCableSet, AutoInstall
import cabsys.iec.iec60287support as iec60287support
from cabsys.data_classes.state import UseState
import cabsys.iec.iec60287_2_1 as iec60287_2_1w
import cabsys.iec.iec_constants as iec
import cabsys.iec.iec60287_2_1alt as iec60287_2_1alt
import cabsys.iec.iec60287_1_1 as iec60287_1_1
import cabsys.quantity.quantity_constants as dc


@LogSection('Δθ buried no dry out')
def calc_delta_theta_4_2_1(install: AutoInstall, cable_set_num: int, cable_num: int,
                           current: float, cond_temp: float,
                           u_pe: float = None,
                           state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the rise in conductor temperature for buried cables without soil dry out, or in air

    Calculate the rise in conductor temperature of buried cables without soil dry out or in air cables for a given
    conductor current. As the sheath temperature is not know but is required an iterative process is required, where
    this function is repeatedly called. An assumed conductor temperature has to be given, from which the metal sheath
    temperature is calculated and the resulting temperature rise is returned. The returned temperature rise will only
    be correct if the input conductor temperature is correct.

    The phase to earth voltage is normally taken from the PlacedCable object but can be overridden by supplying a value.

    :param install: cable installation
    :param cable_set_num: cable set number in install
    :param cable_num: cable number in cable_set
    :param current: current in cable conductor (A)
    :param cond_temp: conductor temperature (°C)
    :param u_pe: phase to earth voltages for cable (V)
    :param state: install set state
    :param log: logger used to store results
    :return: current rating of cable
    """

    if install.config.iec_60287_1_1_ver.value in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 4.2.1'
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 1.4.1.1'
    else:
        raise IEC60287Exception(f'trying to calculate the conductor temperature rise IEC 60287-1-1 Section 4.2.1'
                                f' but {install.config.iec_60287_1_1_ver} in install config not recognised')

    cable_set = install.cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable

    if state is not None:
        cable_set_state = state.cable_set_states[cable_set_num]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    log.add_line('I', current, 'A', 'set or calculated previously')
    r_ac = iec60287_1_1.calc_r_ac(cable_set, cable_num, cond_temp,
                                  iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                  state=cable_set_state, log=log)
    always_calc_wd = install.config.always_calc_wd.get_value(unit='', log=log)
    wd = iec60287_1_1.calc_wd(install, cable_set_num, cable_num, u_pe=u_pe, state=state, log=log)

    # calculate metal sheath/screen temperatures

    theta_sc_w, theta_sc_s, theta_sc_t = calc_theta_sc(install, cable_set_num, cable_num,
                                                       current, cond_temp,
                                                       state=state, log=log)
    sheath_temp = (theta_sc_w.value, theta_sc_s.value, theta_sc_t.value)

    # calculate metal sheath/screen losses
    lambda_1 = calc_lambda_1(install, cable_set_num, cable_num, cond_temp, sheath_temp,
                             state=state, log=log)
    lambda_1c = lambda_1[0]
    lambda_1w = lambda_1[1]
    lambda_1s = lambda_1[2]

    lambda_2 = iec60287_1_1.calc_lambda_2(install, cable_set_num, cable_num, state=state, log=log)
    t1 = iec60287_2_1w.calc_t1(install, cable_set_num, cable_num, state=state, log=log)
    t_ws = iec60287_2_1alt.calc_t_ws(install.cable_sets[cable_set_num].placed_cables[cable_num].cable, log=log)
    t_st = iec60287_2_1alt.calc_t_st(install.cable_sets[cable_set_num].placed_cables[cable_num].cable, log=log)
    t2 = iec60287_2_1w.calc_t2(cable, state=cable_state, log=log)
    t3 = iec60287_2_1w.calc_t3(install, cable_set_num, cable_num, state=state, log=log)

    if cable_set.duct_layout.value == iec.NO_DUCTS:
        duct_air_temp = None
    else:
        duct_air_temp = iec60287_1_1.calc_theta_m(install, cable_set_num, cable_num, current, cond_temp, sheath_temp,
                                                  state=state, log=log).value
    t4 = iec60287_2_1w.calc_t4(install, cable_set_num, cable_num, cond_temp,
                               sheath_temperature=sheath_temp,
                               duct_air_temp=duct_air_temp,
                               state=state, log=log)
    n = cable_set.find_no_cores(cable_num, as_int=True, log=log)

    delta_theta = ((current ** 2 * r_ac.value + 0.5 * wd.value) * t1.value +
                   (current ** 2 * r_ac.value * (1 + lambda_1w.value) + wd.value) * t_ws.value +
                   (current ** 2 * r_ac.value * (1 + lambda_1w.value + lambda_1s.value) + wd.value) * t_st.value +
                   (current ** 2 * r_ac.value * (1 + lambda_1c.value) + wd.value) * n * t2.value +
                   (current ** 2 * r_ac.value *
                    (1 + lambda_1c.value + lambda_2.value) + wd.value) * n * (t3.value + t4.value))

    return QFloat(delta_theta, '°C', f'{source}: conductor temperature',
                  description='conductor temperature buried no dry out, or air', symbol='Δθ')


@LogSection('Δθ_d buried no dry out')
def calc_delta_theta_d_4_2_1(install: AutoInstall, cable_set_num: int, cable_num: int,
                             current: float, cond_temp: float,
                             u_pe: float = None,
                             state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate rise in conductor temperature due to dielectric loss for buried cables without soil dry out, or in air

    Calculate the rise in conductor temperature due to dielectric loss of buried cables without soil dry out or in air
    cables for a given conductor current. As the sheath temperature is not know but is required an iterative process is
    required, where this function is repeatedly called. An assumed conductor temperature has to be given, from which the
    metal sheath temperature is calculated and the resulting temperature rise is returned. The returned temperature rise
    will only be correct if the input conductor temperature is correct.

    The phase to earth voltage is normally taken from the PlacedCable object but can be overridden by supplying a value.

    :param install: cable installation
    :param cable_set_num: cable set number in install
    :param cable_num: cable number in cable_set
    :param current: current in cable conductor (A)
    :param cond_temp: conductor temperature (°C)
    :param u_pe: phase to earth voltages for cable (V)
    :param state: install set state
    :param log: logger used to store results
    :return: current rating of cable
    """

    if install.config.iec_60287_1_1_ver.value in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 4.2.1'
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 1.4.1.1'
    else:
        raise IEC60287Exception(f'trying to calculate the conductor temperature rise IEC 60287-1-1 Section 4.2.1'
                                f' but {install.config.iec_60287_1_1_ver} in install config not recognised')

    cable_set = install.cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable

    if state is not None:
        cable_set_state = state.cable_set_states[cable_set_num]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    log.add_line('I', current, 'A', 'set or calculated previously')
    # always_calc_wd = install.config.always_calc_wd.get_value(unit='', log=log)
    wd = iec60287_1_1.calc_wd(install, cable_set_num, cable_num, u_pe=u_pe, state=state, log=log)

    # calculate metal sheath/screen temperatures

    theta_sc_w, theta_sc_s, theta_sc_t = calc_theta_sc(install, cable_set_num, cable_num,
                                                       current, cond_temp,
                                                       state=state, log=log)
    sheath_temp = (theta_sc_w.value, theta_sc_s.value, theta_sc_t.value)

    t1 = iec60287_2_1w.calc_t1(install, cable_set_num, cable_num, state=state, log=log)
    t_ws = iec60287_2_1alt.calc_t_ws(install.cable_sets[cable_set_num].placed_cables[cable_num].cable, log=log)
    t_st = iec60287_2_1alt.calc_t_st(install.cable_sets[cable_set_num].placed_cables[cable_num].cable, log=log)
    t2 = iec60287_2_1w.calc_t2(cable, state=cable_state, log=log)
    t3 = iec60287_2_1w.calc_t3(install, cable_set_num, cable_num, state=state, log=log)

    if cable_set.duct_layout.value == iec.NO_DUCTS:
        duct_air_temp = None
    else:
        duct_air_temp = iec60287_1_1.calc_theta_m(install, cable_set_num, cable_num, current, cond_temp, sheath_temp,
                                                  state=state, log=log).value
    t4 = iec60287_2_1w.calc_t4(install, cable_set_num, cable_num, cond_temp,
                               sheath_temperature=sheath_temp,
                               duct_air_temp=duct_air_temp,
                               state=state, log=log)
    n = cable_set.find_no_cores(cable_num, as_int=True, log=log)

    delta_theta = (0.5 * wd.value * t1.value +
                   wd.value * t_ws.value +
                   wd.value * t_st.value +
                   wd.value * n * t2.value +
                   wd.value * n * (t3.value + t4.value))

    return QFloat(delta_theta, '°C', f'{source}: conductor temperature',
                  description='conductor temperature due to dielectric loss buried no dry out, or air', symbol='Δθ_d')


@UseState(('theta_sc_w', 'theta_sc_s', 'theta_sc_t'), level=cabsys.data_classes.state.CABLE)
@LogSection('sheath_temp_multi')
def calc_theta_sc(install: AutoInstall, cable_set_num: int, cable_num: int,
                  current: float, conductor_temp: float, u_pe: float = None,
                  state: InstallState = None, log: Log = None) -> Tuple[QFloat, QFloat, QFloat]:
    """Calculate the sheath temperature for a given load current. (°C)

    The sheath temperature is calculated from the inputs. If the cable voltage is not given the voltage defined
    in the placed cable object is used.

    IEC 60287-1-1 Section 5.3.1 alternative version

    :param install: object containing cable_set
    :param cable_set_num: index number of cable set in the installation
    :param cable_num: index number of the cable in the cable set
    :param current: current flowing through cable (A)
    :param conductor_temp: conductor temperature of cable (°C)
    :param u_pe: phase to earth voltage of cable (V)
    :param state: install set state, used to get and set other calculations
    :param log: logger used to store results
    :return: sheath temperature for given cable current (°C)
    """

    if install.config.combi_sheath_iec.value:
        raise IEC60287Exception('trying to calculated multi sheath/screen but install.config.combi_sheath_iec '
                                'set to True')

    theta_sc = calc_theta_sc_lambda(install, cable_set_num, cable_num,
                                    current, conductor_temp,
                                    lambda_1w=0.0, lambda_1s=0.0,
                                    u_pe=u_pe,
                                    state=state, log=log)
    old_theta_sc = calc_theta_sc_lambda(install, cable_set_num, cable_num,
                                        current, conductor_temp,
                                        lambda_1w=1.0, lambda_1s=1.0,
                                        u_pe=u_pe,
                                        state=state, log=log)

    log.add_line('multi sheath accuracy', install.config.multi_sheath_accuracy.value, '°C',
                 'install.config.multi_sheath_accuracy.value')

    while abs(theta_sc[2].value - old_theta_sc[2].value) > install.config.multi_sheath_accuracy.value:
        old_theta_sc = theta_sc

        sheath_temperature = (theta_sc[0].value, theta_sc[1].value, theta_sc[2].value)
        lambda_1 = calc_lambda_1(install, cable_set_num, cable_num,
                                 conductor_temp, sheath_temperature,
                                 log=log)
        theta_sc = calc_theta_sc_lambda(install, cable_set_num, cable_num,
                                        current, conductor_temp,
                                        lambda_1w=lambda_1[1].value, lambda_1s=lambda_1[2].value,
                                        u_pe=u_pe,
                                        state=state, log=log)

    return theta_sc


@LogSection('sheath_temp_multi_iteration')
def calc_theta_sc_lambda(install: AutoInstall, cable_set_num: int, cable_num: int,
                         current: float, conductor_temp: float,
                         lambda_1w: float, lambda_1s: float,
                         u_pe: float = None,
                         state: InstallState = None, log: Log = None) -> Tuple[QFloat, QFloat, QFloat]:
    """Calculate the sheath temperature for a given load current and metal sheath/screen loss. (°C)

    The sheath temperature is calculated from the inputs. If the cable voltage is not given the voltage defined
    in the placed cable object is used.

    IEC 60287-1-1 Section 5.3.1 alternative version

    :param install: object containing cable_set
    :param cable_set_num: index number of cable set in the installation
    :param cable_num: index number of the cable in the cable set
    :param current: current flowing through cable (A)
    :param conductor_temp: conductor temperature of cable (°C)
    :param lambda_1w: wire screen loss factor
    :param lambda_1s: metal sheath loss factor
    :param u_pe: phase to earth voltage of cable (V)
    :param state: install set state, used to get and set other calculations
    :param log: logger used to store results
    :return: sheath temperature for given cable current (°C)
    """

    if state is not None:
        cable_set_state = state.cable_set_states[cable_set_num]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    source = 'IEC 60287-1-1 ED3 Section 5.3.1alt'

    if install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT,
                                                  iec.IEC60287_1_1_ED2]:
        if log is not None:
            log.add_warning('multiple sheath temperatures used')
    elif install.config.iec_60287_1_1_ver.value in [None, iec.CIGRE_TB880_2022]:
        pass
    else:
        raise IEC60287Exception(f'trying to calculate metal sheath temperature (IEC 60287-1-1 ED3 Section 5.3.1) but'
                                f' IEC 60287-1-1 version "{install.config.iec_60287_1_1_ver.value}" in install config'
                                f' not recognised')

    cable_set = install.cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable

    if conductor_temp is None:
        conductor_temp = iec60287support.get_cond_temp(cable, state=cable_state, log=log).value
    elif log is not None:
        log.add_line('θ', conductor_temp, '°C', 'set or calculated previously')
    theta_c = conductor_temp
    r_ac = iec60287_1_1.calc_r_ac(cable_set, cable_num, theta_c,
                                  iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                  state=cable_set_state, log=log)
    always_calc_wd = install.config.always_calc_wd.value
    wd = iec60287_1_1.calc_wd(install, cable_set_num, cable_num, u_pe=u_pe, state=state, log=log)
    t1 = iec60287_2_1w.calc_t1(install, cable_set_num, cable_num, state=state, log=log)

    theta_sc_w = theta_c - (current**2 * r_ac.value + wd.value / 2) * t1.value

    log.add_line("lambda_1w", lambda_1w, '', 'previously calculated (IEC 60287-1-1 alt)')
    log.add_line("lambda_1s", lambda_1s, '', 'previously calculated (IEC 60287-1-1 alt)')

    t_ws = iec60287_2_1alt.calc_t_ws(install.cable_sets[cable_set_num].placed_cables[cable_num].cable, log=log)
    theta_sc_s = theta_sc_w - (current**2 * r_ac.value * (1 + lambda_1w) + wd.value) * t_ws.value

    t_st = iec60287_2_1alt.calc_t_st(install.cable_sets[cable_set_num].placed_cables[cable_num].cable, log=log)
    theta_sc_t = theta_sc_s - (current**2 * r_ac.value * (1 + lambda_1w + lambda_1s) + wd.value) * t_st.value

    q_theta_sc_w = QFloat(theta_sc_w, '°C', source=source, symbol='θ_sc_w')
    q_theta_sc_s = QFloat(theta_sc_s, '°C', source=source, symbol='θ_sc_s')
    q_theta_sc_t = QFloat(theta_sc_t, '°C', source=source, symbol='θ_sc_t')

    return q_theta_sc_w, q_theta_sc_s, q_theta_sc_t


# TODO: remove single resistance return and single temperature input?
# TODO: remove bespoke sheath and log sections and use below decorators.
# @UseState('R_s_multi')
# @LogSection('R_s_multi')
def calc_sheath_screen_resistance(cable: Cable,
                                  theta_sc: Tuple[float, float, float],
                                  ignore_csw_tape: bool = False,
                                  iec_60287_1_1_ver: str = None,
                                  state: CableState = None,
                                  log: cabsys.Log = None) -> Tuple[Optional[QFloat], Optional[QFloat],
                                                                   Optional[QFloat], Optional[QFloat]]:
    """Calculate the metal sheath / screen resistance for multiple sheaths/screens (ohm/m)

    The sheath / screen resistance for each sheath or screen is calculated, and the total for all sheaths / screens is
    then calculated. If ignore_cws_tape is set to True then the wire screen and tape layers are ignored, as required for
    specially bonded cables.

    :param cable: cable with sheath or screen
    :param theta_sc: temperature of sheath/screen (°C)
    :param ignore_csw_tape: if True then result does not include the wire screen
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable state, used to get and set other calculations
    :param log: logger
    :return: sheath/screen resistance (ohm/m)
    """

    if theta_sc is None:
        raise Exception('trying to calculate sheath/screen resistance but no sheath/screen temperature given')

    if state is not None:
        if state.get_source('R_s_c') in dc.ATTR_FIXED_INPUTS or (state.get_memorise() and
                                                                 state.get_quantity('R_s_c') is not None):
            resistance = state.get_quantity('R_s_c', log=log)
            wire_resistance = state.get_quantity('R_s_w', log=log)
            sheath_resistance = state.get_quantity('R_s_s', log=log)
            tape_resistance = state.get_quantity('R_s_t', log=log)
            return resistance, wire_resistance, sheath_resistance, tape_resistance

    source = 'IEC 60287-1-1 ED3 Section 5.3.1alt'

    if isinstance(theta_sc, tuple):
        theta_sc_w, theta_sc_s, theta_sc_t = theta_sc
    else:
        theta_sc_w = theta_sc_s = theta_sc_t = theta_sc

    if log is not None:
        log.start_section('R_s', source)

    inv_sheath_screen_resistance = 0

    if cable.wire_screen.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating sheath/screen resistance: wire screen material has not been defined')
    if cable.wire_screen.material.get_value(unit='') != iec.NONE:
        if ignore_csw_tape:
            if log is not None:
                log.add_line(f'wire screen resistance ignored', '-', '-', source)
            wire_resistance = math.inf
        else:
            wire_resistance = iec60287support.calc_wire_resistance(cable.wire_screen, theta_sc_w, log=log).value
            inv_sheath_screen_resistance = inv_sheath_screen_resistance + 1 / wire_resistance
    else:
        wire_resistance = math.inf

    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating sheath/screen resistance: metal sheath material has not been defined')
    if cable.sheath.material.get_value(unit='') != iec.NONE:
        sheath_resistance = iec60287support.calc_sheath_resistance(cable.sheath, theta_sc_s, log=log).value
        inv_sheath_screen_resistance = inv_sheath_screen_resistance + 1 / sheath_resistance
        # warn if corrugated and CIGRE TB 880 used that "important" correction is not made for corrugation
        dia = cable.sheath.dia.get_value(unit='mm')
        dia_under_sheath = cable.sheath.dia_under_sheath.get_value(unit='mm')
        thickness = cable.sheath.thickness.get_value(unit='mm')
        if (dia - dia_under_sheath) / 2 != thickness and iec_60287_1_1_ver == iec.CIGRE_TB880_2022:
            log.add_warning('TB 880 GP30: correction for corrugated metal sheath resistance not implemented')
    else:
        sheath_resistance = math.inf

    if cable.tape.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating sheath/screen resistance: screen tape material has not been defined')
    if cable.tape.material.get_value(unit='') != iec.NONE:
        if ignore_csw_tape:
            if log is not None:
                log.add_line(f'tape screen resistance ignored', '-', '-', source)
            tape_resistance = math.inf
        else:
            tape_resistance = iec60287support.calc_tape_resistance(cable.tape, theta_sc_t, log=log).value
            inv_sheath_screen_resistance = inv_sheath_screen_resistance + 1 / tape_resistance
    else:
        tape_resistance = math.inf

    resistance = 1 / inv_sheath_screen_resistance

    if log is not None:
        if isinstance(theta_sc, tuple):
            log.end_section('R_s', f'{resistance * 1e6:.5f}: '
                                   f'{wire_resistance * 1e6:.5f}, '
                                   f'{sheath_resistance * 1e6:.5f}, '
                                   f'{tape_resistance * 1e6:.5f}, ',
                            'μΩ/m', source)
        else:
            log.end_section('R_s', f'{resistance * 1e6:.5f}: ', 'μΩ/m', source)

    if state is not None:
        state.set_quantity('R_s_c', resistance, 'Ω/m', source=source, symbol='R_s')
        state.set_quantity('R_s_w', wire_resistance, 'Ω/m', source=source, symbol='R_s_w')
        state.set_quantity('R_s_s', sheath_resistance, 'Ω/m', source=source, symbol='R_s_s')
        state.set_quantity('R_s_t', tape_resistance, 'Ω/m', source=source, symbol='R_s_t')

    q_resistance = QFloat(resistance, 'Ω', source=source, symbol="R_s")
    q_wire_resistance = QFloat(wire_resistance, 'Ω', source=source, symbol="R_s_w")
    q_sheath_resistance = QFloat(sheath_resistance, 'Ω', source=source, symbol="R_s_s")
    q_tape_resistance = QFloat(tape_resistance, 'Ω', source=source, symbol="R_s_t")

    return q_resistance, q_wire_resistance, q_sheath_resistance, q_tape_resistance


@UseState(('lambda_1', 'lambda_1w', 'lambda_1s', 'lambda_1t'), level=cabsys.data_classes.state.CABLE)
@LogSection('λ_1 multi')
def calc_lambda_1(install: AutoInstall, cable_set_num: int, cable_num: int,
                  conductor_temperature: float,
                  sheath_temperature: Tuple[float, float, float],
                  state: InstallState = None, log: Log = None) -> Tuple[QFloat, QFloat, QFloat, QFloat]:
    """Calculate the metal sheath/screen loss (multiple sheath temperatures)

    Calculates the metal sheath/screen loss (lambda_1). The metal sheath/screen resistance is based on the metal
    sheath/screen temperature given as an argument.

    IEC 60287-1-1 alternative clause 5.3.1

    :param install: object containing cable_set
    :param cable_set_num: index number of cable set in the installation
    :param cable_num: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param state: install set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    if state is not None:
        cable_set_state = state.cable_set_states[cable_set_num]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    if install.config.iec_60287_1_1_ver.value in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 alt Section 5.3.1'
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2]:
        source = 'IEC 60287-1-1 ED2 alt Section 2.3'
    elif install.config.iec_60287_1_1_ver.value in [iec.CIGRE_TB880_2022]:
        source = 'CIGRE TB 880 2022 Guidance Point [missing]'
    else:
        raise IEC60287Exception(f'trying to calculate the sheath loss (IEC 60287-1-1 alt ED3 Section 5.3.1) but'
                                f' IEC 60287-1-1 version "{install.config.iec_60287_1_1_ver.value}" in install config'
                                f' not recognised')

    cable_set = install.cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable

    warn = False
    for other_placed_cable in cable_set.placed_cables:
        if cable.sheath != other_placed_cable.cable.sheath:
            warn = True
    if warn:
        log.add_warning('cable sheaths are not the same in cable set')

    if cable.number_cores.value == iec.SINGLE_CORE:
        bonding = cable_set.bonding.get_value('', log=log)
        number_cables = cable_set.find_no_cables(log=log)
        if number_cables == 1:
            raise IEC60287Exception('calculating sheath loss but only 1 single core cable')
        elif number_cables == 2:
            if bonding == iec.SOLID_BONDED:
                lambda1 = calc_lambda_1d(cable_set, cable_num, conductor_temperature,
                                         sheath_temperature=sheath_temperature,
                                         iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                         state=cable_set_state, log=log).value
                raise IEC60287Exception('2 singel core cables not yet implemented')
                # Todo: add correction factor for Milliken conductors
            else:
                # Todo: add sheath loss for 2 single core cables specially bonded
                raise IEC60287Exception('calculating sheath loss but 2 single core cables specially bonded')
        elif number_cables == 3:
            if bonding == iec.SOLID_BONDED:
                lambda1dash = calc_lambda_1d(cable_set, cable_num, conductor_temperature,
                                             sheath_temperature=sheath_temperature,
                                             iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                             state=cable_set_state, log=log)
                r_s = calc_sheath_screen_resistance(cable, sheath_temperature,
                                                    iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                                    state=cable_state, log=log)
                c_f = iec60287_1_1.calc_f_c_s5_3_6(install, cable_set, cable_num,
                                                   sheath_screen_resistance=r_s[0].value,
                                                   state=cable_set_state, log=log)
                if c_f.value > 0:
                    lambda1_dash_dash = iec60287_1_1.calc_lambda1_dash_dash_5_3_7_1(install, cable_set_num, cable_num,
                                                                                    conductor_temperature,
                                                                                    sheath_temperature[1],
                                                                                    state=state, log=log)
                else:
                    lambda1_dash_dash = QFloat(0.0)
                lambda1 = lambda1dash[0].value + c_f.value * lambda1_dash_dash.value
                lambda1w = lambda1dash[1].value
                lambda1s = lambda1dash[2].value + c_f.value * lambda1_dash_dash.value
                lambda1t = lambda1dash[3].value

            else:
                if bonding == iec.CROSS_BONDED:
                    transposed = cable_set.transposed.get_value(unit='')
                    if not transposed:
                        raise IEC60287Exception('IEC 60287-1-1: circuit is cross bonded but not transposed')
                if bonding == iec.SINGLE_POINT_BONDED:
                    c_i = QFloat(0.0)
                else:
                    c_i = iec60287_1_1.calc_rcc_5_3_7_2(cable_set,
                                                        iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                                        state=cable_set_state, log=log)
                if c_i.value > 0.0:
                    lambda1dash = calc_lambda_1d(cable_set, cable_num, conductor_temperature,
                                                 sheath_temperature=sheath_temperature,
                                                 iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                                 state=cable_set_state, log=log)
                else:
                    lambda1dash = [QFloat(0.0), QFloat(0.0), QFloat(0.0), QFloat(0.0)]
                lambda1_dash_dash = iec60287_1_1.calc_lambda1_dash_dash_5_3_7_1(install, cable_set_num, cable_num,
                                                                                conductor_temperature,
                                                                                sheath_temperature[1],
                                                                                state=state, log=log)
                lambda1 = c_i.value * lambda1dash[0].value + lambda1_dash_dash.value
                lambda1w = c_i.value * lambda1dash[1].value
                lambda1s = c_i.value * lambda1dash[2].value + lambda1_dash_dash.value
                lambda1t = c_i.value * lambda1dash[3].value
        else:
            raise IEC60287Exception('calculating sheath loss factor but more than 3 single core cables given')
    else:
        raise IEC60287Exception('calculating sheath loss factor but only single core cables implemented')

    q_lambda1 = QFloat(lambda1, '', source=source, symbol="λ_1")
    q_lambda1w = QFloat(lambda1w, '', source=source, symbol="λ_1w")
    q_lambda1s = QFloat(lambda1s, '', source=source, symbol="λ_1s")
    q_lambda1t = QFloat(lambda1t, '', source=source, symbol="λ_1t")

    return q_lambda1, q_lambda1w, q_lambda1s, q_lambda1t


@UseState(("lambda_1d", "lambda_1dw", "lambda_1ds", "lambda_1dt"), level=cabsys.data_classes.state.CABLE)
@LogSection("λ_1' multi")
def calc_lambda_1d(cable_set: AutoCableSet, cable_num: int,
                   conductor_temperature: float,
                   sheath_temperature: Tuple[float, float, float],
                   iec_60287_1_1_ver: str = None,
                   state: CableSetState = None, log: Log = None) -> Tuple[QFloat, QFloat, QFloat, QFloat]:
    """Calculate the circulating loss for  metal sheath/screen (with  multiple metal sheath/screens)

    Calculates the metal sheath/screen loss (lambda_1') due to circulating currents.

    IEC 60287-1-1 Ed 3 alternative clause 5.3.1

    :param cable_set: cable_set
    :param cable_num: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    cable = cable_set.placed_cables[cable_num].cable

    number_cores = cable.number_cores.get_value('', log=log)

    if number_cores == iec.SINGLE_CORE:
        number_cables = cable_set.find_no_cables(log=log)
        transposed = cable_set.transposed.get_value('', log=log)
        formation = iec60287support.calc_cable_formation(cable_set, log=log)
        if number_cables == 1:
            raise IEC60287Exception('calculating X but only 1 single core cable in cable set')
        elif number_cables == 2 or (number_cables == 3 and formation == iec.TREFOIL):
            lambda_1d = calc_lambda_1_s5_3_2(cable_set, cable_num, conductor_temperature,
                                             sheath_temperature=sheath_temperature,
                                             iec_60287_1_1_ver=iec_60287_1_1_ver,
                                             state=state, log=log)
        elif number_cables == 3 and formation == iec.FLAT and transposed:
            lambda_1d = calc_lambda_1_s5_3_3(cable_set, cable_num, conductor_temperature,
                                             sheath_temperature=sheath_temperature,
                                             iec_60287_1_1_ver=iec_60287_1_1_ver,
                                             state=state, log=log)
        elif number_cables == 3 and formation == iec.FLAT and not transposed:
            lambda_1d = calc_lambda_1dash_s5_3_4(cable_set, cable_num, conductor_temperature,
                                                 sheath_temperature=sheath_temperature,
                                                 iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                 state=state, log=log)
        else:
            raise IEC60287Exception(f'trying to calculate lambda but {number_cables} S/C cables installed in'
                                    f' {formation} formation not recognised')
    else:
        raise IEC60287Exception('not yet implemented')

    return lambda_1d


@LogSection("λ'_1 multi: 2 phase/trefoil")
def calc_lambda_1_s5_3_2(cable_set: AutoCableSet, cable_no: int,
                         conductor_temperature: float,
                         sheath_temperature: Tuple[float, float, float],
                         iec_60287_1_1_ver: str = None,
                         state: CableSetState = None, log: Log = None) -> Tuple[QFloat, QFloat, QFloat, QFloat]:
    """Calculate the circulating loss for metal sheath/screen loss solidly bonded 2 phase systems

    Calculates the metal sheath/screen loss (lambda_1') due to circulating currents for 2 phase and 3 phase trefoil
    systems.

    IEC 60287-1-1 alt clause 5.3.2

    :param cable_set: cable_set
    :param cable_no: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param iec_60287_1_1_ver: IEC 60287_1_1 version used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.2 alt'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.1 alt'
    else:
        raise IEC60287Exception(f'trying to calculate the 2 phase or trefoil solidly bonded sheath loss'
                                f' (IEC 60287-1-1 ED3 Section 5.3.2)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    cable = cable_set.placed_cables[cable_no].cable
    if state is not None:
        cable_state = state.placed_cable_states[cable_no].cable_state
    else:
        cable_state = None

    x = iec60287_1_1.calc_x_5_3_2(cable_set, cable_no, iec_60287_1_1_ver=iec_60287_1_1_ver, state=state, log=log)
    r_s = calc_sheath_screen_resistance(cable, sheath_temperature,
                                        ignore_csw_tape=False,
                                        iec_60287_1_1_ver=iec_60287_1_1_ver,
                                        state=cable_state, log=log)
    r_c = iec60287_1_1.calc_r_ac(cable_set, cable_no, conductor_temperature,
                                 iec_60287_1_1_ver=iec_60287_1_1_ver,
                                 state=state, log=log)

    lambda_1_dash = r_s[0].value / r_c.value * (1 / (1 + (r_s[0].value / x.value) ** 2))
    lambda_1_dash_w = lambda_1_dash * r_s[0].value / r_s[1].value
    lambda_1_dash_s = lambda_1_dash * r_s[0].value / r_s[2].value
    lambda_1_dash_t = lambda_1_dash * r_s[0].value / r_s[3].value

    q_lambda_1_dash = QFloat(lambda_1_dash, '', source=source, symbol="λ_1'")
    q_lambda_1_dash_w = QFloat(lambda_1_dash_w, '', source=source, symbol="λ_1w'")
    q_lambda_1_dash_s = QFloat(lambda_1_dash_s, '', source=source, symbol="λ_1s'")
    q_lambda_1_dash_t = QFloat(lambda_1_dash_t, '', source=source, symbol="λ_1t'")

    return q_lambda_1_dash, q_lambda_1_dash_w, q_lambda_1_dash_s, q_lambda_1_dash_t


@LogSection("λ'_1 flat transposed")
def calc_lambda_1_s5_3_3(cable_set: AutoCableSet, cable_no: int,
                         conductor_temperature: float,
                         sheath_temperature: Tuple[float, float, float],
                         iec_60287_1_1_ver: str = None,
                         state: CableSetState = None, log: Log = None) -> Tuple[QFloat, QFloat, QFloat, QFloat]:
    """Calculate circulating loss for metal sheath/screen solidly bonded 3 phase systems in flat transposed formation

    Calculates the metal sheath/screen loss (lambda_1') due to circulating currents for 3 phase flat transposed cable
    systems.

    IEC 60287-1-1 alt clause 5.3.3

    :param cable_set: cable_set
    :param cable_no: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.3 alt'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.2 alt'
    else:
        raise IEC60287Exception(f'trying to calculate the 3 phase flat formation transposed solidly bonded sheath loss'
                                f' (IEC 60287-1-1 ED3 Section 5.3.3 alt)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    cable = cable_set.placed_cables[cable_no].cable

    if state is not None:
        cable_state = state.placed_cable_states[cable_no].cable_state
    else:
        cable_state = None

    x = iec60287_1_1.calc_x1_5_3_3(cable_set, cable_no, iec_60287_1_1_ver=iec_60287_1_1_ver, state=state, log=log)
    r_c = iec60287_1_1.calc_r_ac(cable_set, cable_no, conductor_temperature,
                                 iec_60287_1_1_ver=iec_60287_1_1_ver,
                                 state=state, log=log)

    r_s = calc_sheath_screen_resistance(cable, sheath_temperature,
                                        ignore_csw_tape=False,
                                        iec_60287_1_1_ver=iec_60287_1_1_ver,
                                        state=cable_state, log=log)

    lambda_1_dash = r_s[0].value / r_c.value * (1 / (1 + (r_s[0].value / x.value) ** 2))
    lambda_1_dash_w = lambda_1_dash * r_s[0].value / r_s[1].value
    lambda_1_dash_s = lambda_1_dash * r_s[0].value / r_s[2].value
    lambda_1_dash_t = lambda_1_dash * r_s[0].value / r_s[3].value

    q_lambda_1_dash = QFloat(lambda_1_dash, '', source=source, symbol="λ_1'")
    q_lambda_1_dash_w = QFloat(lambda_1_dash_w, '', source=source, symbol="λ_1w'")
    q_lambda_1_dash_s = QFloat(lambda_1_dash_s, '', source=source, symbol="λ_1s'")
    q_lambda_1_dash_t = QFloat(lambda_1_dash_t, '', source=source, symbol="λ_1t'")

    return q_lambda_1_dash, q_lambda_1_dash_w, q_lambda_1_dash_s, q_lambda_1_dash_t


@LogSection("λ'_1 flat not transposed")
def calc_lambda_1dash_s5_3_4(cable_set: AutoCableSet, cable_no: int,
                             conductor_temperature: float,
                             sheath_temperature: Tuple[float, float, float],
                             iec_60287_1_1_ver: float = None,
                             state: CableSetState = None, log: Log = None) -> Tuple[QFloat, QFloat, QFloat, QFloat]:
    """Calculate circulating loss for metal sheath/screen solidly bonded 3 phase systems in flat un-transposed formation

    Calculates the metal sheath/screen loss (lambda_1') due to circulating currents for 3 phase flat un-transposed cable
    systems.

    IEC 60287-1-1 clause 5.3.4 alt

    :param cable_set: cable_set
    :param cable_no: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.4 alt'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.3 alt'
    else:
        raise IEC60287Exception(f'trying to calculate the 3 phase flat formation un-transposed solidly bonded'
                                f' sheath loss (IEC 60287-1-1 ED3 Section 5.3.4 alt)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    cable = cable_set.placed_cables[cable_no].cable
    if state is not None:
        cable_state = state.placed_cable_states[cable_no].cable_state
    else:
        cable_state = None

    xm = iec60287_1_1.calc_xm_5_3_4(cable_set, iec_60287_1_1_ver=iec_60287_1_1_ver, state=state, log=log).value
    r_s_s = calc_sheath_screen_resistance(cable, sheath_temperature,
                                          ignore_csw_tape=False,
                                          iec_60287_1_1_ver=iec_60287_1_1_ver,
                                          state=cable_state, log=log)
    r_c = iec60287_1_1.calc_r_ac(cable_set, cable_no, conductor_temperature,
                                 iec_60287_1_1_ver=iec_60287_1_1_ver,
                                 state=state, log=log).value
    c_p = iec60287_1_1.calc_cp_5_3_4(cable_set, cable_no, iec_60287_1_1_ver=iec_60287_1_1_ver,
                                     state=state, log=log).value
    c_q = iec60287_1_1.calc_cq_5_3_4(cable_set, cable_no, state=state, log=log).value
    phase = iec60287support.calc_cable_phase_wrt_centre(cable_set, cable_no, state=state, log=log)

    r_s = r_s_s[0].value
    if phase.value == iec.BLUE:
        lambda_1_dash = r_s / r_c * (0.75 * c_p ** 2 / (r_s ** 2 + c_p ** 2) + 0.25 * c_q ** 2 / (r_s ** 2 + c_q ** 2) +
                                     2 * r_s * c_p * c_q * xm /
                                     (math.sqrt(3) * (r_s ** 2 + c_p ** 2) * (r_s ** 2 + c_q ** 2)))
        symbol = "λ'11"
    elif phase.value == iec.RED:
        lambda_1_dash = r_s / r_c * (0.75 * c_p ** 2 / (r_s ** 2 + c_p ** 2) + 0.25 * c_q ** 2 / (r_s ** 2 + c_q ** 2) -
                                     2 * r_s * c_p * c_q * xm /
                                     (math.sqrt(3) * (r_s ** 2 + c_p ** 2) * (r_s ** 2 + c_q ** 2)))
        symbol = "λ'12"
    else:
        lambda_1_dash = r_s / r_c * (c_q ** 2 / (r_s ** 2 + c_q ** 2))
        symbol = "λ'1m"

    lambda_1_dash_w = lambda_1_dash * r_s_s[0].value / r_s_s[1].value
    lambda_1_dash_s = lambda_1_dash * r_s_s[0].value / r_s_s[2].value
    lambda_1_dash_t = lambda_1_dash * r_s_s[0].value / r_s_s[3].value

    q_lambda_1_dash = QFloat(lambda_1_dash, '', source=source, symbol=symbol)
    q_lambda_1_dash_w = QFloat(lambda_1_dash_w, '', source=source, symbol=symbol + "w")
    q_lambda_1_dash_s = QFloat(lambda_1_dash_s, '', source=source, symbol=symbol + "s")
    q_lambda_1_dash_t = QFloat(lambda_1_dash_t, '', source=source, symbol=symbol + "t")

    return q_lambda_1_dash, q_lambda_1_dash_w, q_lambda_1_dash_s, q_lambda_1_dash_t
