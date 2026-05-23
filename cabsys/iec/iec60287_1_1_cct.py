"""IEC 60287-1-1: 2023 Current rating equations and calculation of losses - General

The equations found in IEC 60287-1-1 are implemented. The inputs to the functions are given as Install and Cable
objects, where sometimes the cable set number or cable number is given as an input also. Each function has the
IEC 60287-1-1 section number in the function name.

In addition to the function returning a result, the result can be returned in the State object. A bespoke logger
(different to the standard Python logger) can also be used.

Some of the equations have been modified. The logger notes where the changes have been made.
"""

import math
from typing import Tuple, Union, Optional, List

from cabsys import IEC60287Exception
from cabsys.data_classes.install import CableSet
# import cabsys.data_classes.state_cct
from cabsys.quantity.quantity_store import QFloat
from cabsys.quantity.log import Log, LogSection, no_log
from cabsys.data_classes.cable import Cable, CableConductor
from cabsys.data_classes.state_cct import CableState, CableSetState, InstallState
from cabsys.data_classes.install import Install
from cabsys.data_classes.state_cct import UseState
import cabsys.iec.iec60228
import cabsys.iec.iec60287support as iec60287support
import cabsys.iec.iec60287_2_1_cct as iec60287_2_1
import cabsys.iec.iec_constants as iec
# import cabsys.iec.iec60287_2_1alt as iec60287_2_1alt
import cabsys.iec.iec60287_1_1alt_cct as iec60287_1_1alt


def calc_delta_theta(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
                     current: float | List[float],
                     cond_temp: float | List[float],
                     u_pe: Optional[float| List[float]] = None,
                     state: Optional[InstallState] = None,
                     log: Optional[Log] = None) -> QFloat:
    """Calculate the rise in conductor temperature for buried cables without soil dry out, or in air

    Calculate the rise in conductor temperature of buried cables without soil dry out or in air cables for a given
    conductor current. As the sheath temperature is not know but is required an iterative process is required, where
    this function is repeatedly called. An assumed conductor temperature has to be given, from which the metal sheath
    temperature is calculated and the resulting temperature rise is returned. The returned temperature rise will only
    be correct if the input conductor temperature is correct.

    The phase to earth voltage is normally taken from the PlacedCable object but can be overridden by supplying a value.

    :param install: cable installation
    :param circuit_num: circuit number in the installation
    :param cable_set_num: cable set number in install
    :param cable_num: cable number in cable_set
    :param current: current in cable conductor (A)
    :param cond_temp: conductor temperature (°C)
    :param u_pe: phase to earth voltages for cable (V)
    :param state: install set state
    :param log: logger used to store results
    :return: current rating of cable
    """

    if install.config.multi_sheath_lambda.value:
        delta_theta = iec60287_1_1alt.calc_delta_theta_4_2_1(install, circuit_num, cable_set_num, cable_num,
                                                             current, cond_temp,
                                                             u_pe=u_pe,
                                                             state=state, log=log)
    else:
        delta_theta = calc_delta_theta_4_2_1(install, circuit_num, cable_set_num, cable_num,
                                             current, cond_temp,
                                             u_pe=u_pe,
                                             state=state, log=log)
    return delta_theta


@LogSection('Δθ buried no dry out')
def calc_delta_theta_4_2_1(install: Install, circuit_num, cable_set_num: int, cable_num: int,
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
    :param circuit_num: circuit number in the installation
    :param cable_set_num: cable set number in install
    :param cable_num: cable number in cable_set
    :param current: current in cable conductor (A)
    :param cond_temp: conductor temperature (°C)
    :param u_pe: phase to earth voltages for cable (V)
    :param state: install set state
    :param log: logger used to store results
    :return: current rating of cable
    """

    if log is None:
        log = no_log

    if install.config.iec_60287_1_1_ver.value in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 4.2.1'
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 1.4.1.1'
    else:
        raise IEC60287Exception(f'trying to calculate the conductor temperature rise IEC 60287-1-1 Section 4.2.1'
                                f' but {install.config.iec_60287_1_1_ver} in install config not recognised')

    cable_set = install.install_circuits[circuit_num].cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable

    if state is not None:
        install_circuit_state = state.install_circuit_states[circuit_num]
        cable_set_state = install_circuit_state.cable_set_states[cable_set_num]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    log.add_line('I', current, 'A', 'set or calculated previously')
    r_ac = calc_r_ac(cable_set, cable_num, cond_temp,
                     iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                     state=cable_set_state, log=log)
    wd = calc_wd(install, circuit_num, cable_set_num, cable_num, u_pe=u_pe, state=state, log=log)

    sheath_temp = calc_theta_sc(install, circuit_num, cable_set_num, cable_num,
                                current, cond_temp, state=state, log=log).get_value2()

    lambda_1 = calc_lambda_1(install, circuit_num, cable_set_num, cable_num, cond_temp, sheath_temp, state=state, log=log)
    lambda_2 = calc_lambda_2(install, circuit_num, cable_set_num, cable_num, state=state, log=log)
    t1 = iec60287_2_1.calc_t1(install, circuit_num, cable_set_num, cable_num, state=state, log=log)
    t2 = iec60287_2_1.calc_t2(cable, state=cable_state, log=log)
    t3 = iec60287_2_1.calc_t3(install, circuit_num, cable_set_num, cable_num,
                              state=state, log=log).get_value2(unit='K.m/W')

    if cable_set.duct_layout.value == iec.NO_DUCTS:
        duct_air_temp = None
    else:
        duct_air_temp = calc_theta_m(install, circuit_num, cable_set_num, cable_num, current, cond_temp, sheath_temp,
                                     state=state, log=log).value
    t4 = iec60287_2_1.calc_t4(install, circuit_num, cable_set_num, cable_num, cond_temp,
                              sheath_temperature=sheath_temp,
                              duct_air_temp=duct_air_temp,
                              state=state, log=log).get_value2(unit='K.m/W')
    n = cable_set.find_no_cores(cable_num, as_int=True, log=log)

    delta_theta = ((current**2 * r_ac.value + 0.5 * wd.value) *
                   t1.value + (current**2 * r_ac.value * (1 + lambda_1.value) + wd.value) * n * t2.value +
                   (current ** 2 * r_ac.value *
                    (1 + lambda_1.value + lambda_2.value) + wd.value) * n * (t3 + t4))

    return QFloat(delta_theta, '°C', f'{source}: conductor temperature',
                  description='conductor temperature buried no dry out, or air', symbol='Δθ')


def calc_delta_theta_d(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
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
    :param circuit_num: circuit number
    :param cable_set_num: cable set number in install
    :param cable_num: cable number in cable_set
    :param current: current in cable conductor (A)
    :param cond_temp: conductor temperature (°C)
    :param u_pe: phase to earth voltages for cable (V)
    :param state: install set state
    :param log: logger used to store results
    :return: current rating of cable
    """

    if install.config.multi_sheath_lambda.value:
        delta_theta = iec60287_1_1alt.calc_delta_theta_d_4_2_1(install, circuit_num, cable_set_num, cable_num,
                                                             current, cond_temp,
                                                             u_pe=u_pe,
                                                             state=state, log=log)
    else:
        delta_theta = calc_delta_theta_d_4_2_1(install, circuit_num, cable_set_num, cable_num,
                                             current, cond_temp,
                                             u_pe=u_pe,
                                             state=state, log=log)
    return delta_theta


@LogSection('Δθ_d buried no dry out')
def calc_delta_theta_d_4_2_1(install: Install, circuit_num:int, cable_set_num: int, cable_num: int,
                             current: float, cond_temp: float,
                             u_pe: float = None,
                             state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate rise in conductor temperature due to dielectric loss for buried cables without soil dry out, or in air

    Calculate the rise in conductor temperature of buried cables due to dielectric loss without soil dry out or in air
    cables for a given conductor current. As the sheath temperature is not know but is required an iterative process is required, where
    this function is repeatedly called. An assumed conductor temperature has to be given, from which the metal sheath
    temperature is calculated and the resulting temperature rise is returned. The returned temperature rise will only
    be correct if the input conductor temperature is correct.

    The phase to earth voltage is normally taken from the PlacedCable object but can be overridden by supplying a value.

    :param install: cable installation
    :param circuit_num: circuit number
    :param cable_set_num: cable set number in install
    :param cable_num: cable number in cable_set
    :param current: current in cable conductor (A)
    :param cond_temp: conductor temperature (°C)
    :param u_pe: phase to earth voltages for cable (V)
    :param state: install set state
    :param log: logger used to store results
    :return: current rating of cable
    """

    if log is None:
        log = no_log

    if install.config.iec_60287_1_1_ver.value in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 4.2.1'
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 1.4.1.1'
    else:
        raise IEC60287Exception(f'trying to calculate the conductor temperature rise IEC 60287-1-1 Section 4.2.1'
                                f' but {install.config.iec_60287_1_1_ver} in install config not recognised')

    cable_set = install.install_circuits[circuit_num].cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable

    if state is not None:
        install_circuit_state = state.install_circuit_states[circuit_num]
        cable_set_state = install_circuit_state.cable_set_states[cable_set_num]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    log.add_line('I', current, 'A', 'set or calculated previously')
    wd = calc_wd(install, circuit_num, cable_set_num, cable_num, u_pe=u_pe, state=state, log=log).get_value2(unit='W/m')

    sheath_temp = calc_theta_sc(install, circuit_num, cable_set_num, cable_num, current,
                                cond_temp, state=state, log=log).get_value2(unit='°C')

    t1 = iec60287_2_1.calc_t1(install, circuit_num, cable_set_num, cable_num,
                              state=state, log=log).get_value2(unit='K.m/W')
    t2 = iec60287_2_1.calc_t2(cable, state=cable_state, log=log).get_value2(unit='K.m/W')
    t3 = iec60287_2_1.calc_t3(install, circuit_num, cable_set_num, cable_num,
                              state=state, log=log).get_value2(unit='K.m/W')

    if cable_set.duct_layout.value == iec.NO_DUCTS:
        duct_air_temp = None
    else:
        duct_air_temp = calc_theta_m(install, circuit_num, cable_set_num, cable_num, current, cond_temp, sheath_temp,
                                     state=state, log=log).value
    t4 = iec60287_2_1.calc_t4(install, circuit_num, cable_set_num, cable_num, cond_temp,
                              sheath_temperature=sheath_temp,
                              duct_air_temp=duct_air_temp,
                              state=state, log=log).get_value2(unit='K.m/W')
    n = cable_set.find_no_cores(cable_num, as_int=True, log=log)

    delta_theta = wd * (0.5 * t1 + n * t2 + n * (t3 + t4))

    return QFloat(delta_theta, '°C', f'{source}: conductor temperature',
                  description='conductor temperature due to dielectric loss buried no dry out, or air', symbol='Δθ_d')


@LogSection('I buried no dry out')
def calc_i_4_2_1(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
                 ambient_temperature,
                 cond_temp: float = None,
                 sheath_temperature: float = None,
                 duct_air_temperature: float = None,
                 delta_theta_p: float = None,
                 u_pe: float = None,
                 state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate I, the permissible current for buried cables without soil dry out or in air

    Calculate the current rating of buried cables without soil dry out or in air cables.

    :param install: cable installation
    :param circuit_num: circuit number
    :param cable_set_num: cable set number in install
    :param cable_num:  cable number in cable_set
    :param ambient_temperature: ambient temperature of installation at cable location
    :param cond_temp: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param duct_air_temperature: average duct air temperature (°C)
    :param delta_theta_p: temperature rise of cable due to other cables (°C)
    :param u_pe: phase to earth voltage of the cable (V)
    :param state: install set state
    :param log: logger used to store results
    :return: current rating of cable
    """

    if install.config.iec_60287_1_1_ver.value in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 4.2.1'
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 1.4.1.1'
    else:
        raise IEC60287Exception(f'trying to calculate current rating (IEC 60287-1-1 ED3 Section 4.2.1) but'
                                f' IEC 60287-1-1 version "{install.config.iec_60287_1_1_ver.value}" in install config'
                                f' not recognised')

    cable_set = install.install_circuits[circuit_num].cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable

    if state is not None:
        install_circuit_state = state.install_circuit_states[circuit_num]
        cable_set_state = install_circuit_state.cable_set_states[cable_set_num]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    if cond_temp is None:
        cond_temp = iec60287support.get_cond_temp(cable, state=cable_state, log=log).get_value2()
    elif log is not None:
        log.add_line('θ', cond_temp, '°C', 'set or calculated previously')
    if delta_theta_p is None:
        delta_theta = cond_temp - ambient_temperature
    else:
        if log is not None:
            log.add_line('Δθ_p', delta_theta_p, '°C', 'set or calculated previously')
        delta_theta = cond_temp - ambient_temperature - delta_theta_p

    r_ac = calc_r_ac(cable_set, cable_num, cond_temp,
                     iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                     state=cable_set_state, log=log)
    wd = calc_wd(install, circuit_num, cable_set_num, cable_num, u_pe=u_pe, state=state, log=log)
    lambda_1 = calc_lambda_1(install, circuit_num, cable_set_num, cable_num, cond_temp,
                             sheath_temperature=sheath_temperature,
                             state=state, log=log).get_value2(unit='')
    lambda_2 = calc_lambda_2(install, circuit_num, cable_set_num, cable_num,
                             state=state, log=log).get_value2(unit='')
    t1 = iec60287_2_1.calc_t1(install, circuit_num, cable_set_num, cable_num,
                              state=state, log=log).get_value2(unit='K.m/W')
    t2 = iec60287_2_1.calc_t2(cable, state=cable_state, log=log).get_value2(unit='K.m/W')
    t3 = iec60287_2_1.calc_t3(install, circuit_num, cable_set_num, cable_num,
                              state=state, log=log).get_value2(unit='K.m/W')
    t4 = iec60287_2_1.calc_t4(install, circuit_num, cable_set_num, cable_num, cond_temp,
                              sheath_temperature=sheath_temperature,
                              duct_air_temp=duct_air_temperature,
                              state=state, log=log).get_value2(unit='K.m/W')
    n = cable_set.find_no_cores(cable_num, as_int=True, log=log)

    i = math.sqrt((delta_theta - wd.value * (0.5 * t1 + n * (t2 + t3 + t4))) /
                  (r_ac.value * t1 + n * r_ac.value * (1 + lambda_1) * t2 +
                   n * r_ac.value * (1 + lambda_1 + lambda_2) * (t3 + t4)))

    return QFloat(i, 'A', f'{source}: current rating',
                  description='current rating buried no dry out, or air', symbol='I')


# TODO: Section 4.2.2 DC cables up to 5 kV
# TODO: Sections 4.3, 4.4, 4.5


@UseState('R_C', level=cabsys.data_classes.state_cct.CABLE)
@LogSection('R_C')
def calc_r_ac(cable_set: CableSet, cable_num: int, cond_temp: float = None,
              iec_60287_1_1_ver: str = None,
              state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate R_C, the AC resistance of a conductor (Ω/m)

    Calculate the AC resistance of the conductor, see IEC 60287-1-1 Section 5.1. Note within the program this parameter
    is called r_ac to comply with Python naming recommendations.

    :param cable_set: the cable_set containing the cable
    :param cable_num:  cable number in the cable_set
    :param state: object holding results relating to cables
    :param cond_temp: conductor temperature (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param log: logger used to store results
    :return: the AC resistance of a conductor (Ω/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.1'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.1'
    else:
        raise IEC60287Exception(f'trying to calculate conductor AC resistance (IEC 60287-1-1 ED3 Section 5.1) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" (probably in install config)'
                                f' not recognised')

    if state is None:
        cable_state = None
    else:
        placed_cable_state = state.placed_cable_states[cable_num]
        cable_state = placed_cable_state.cable_state

    cable = cable_set.placed_cables[cable_num].cable
    r_dash = calc_r_dash(cable, cond_temp=cond_temp,
                         iec_60287_1_1_ver=iec_60287_1_1_ver,
                         state=cable_state, log=log).get_value2()
    ys = calc_ys(cable_set, cable_num, cond_temp,
                 iec_60287_1_1_ver=iec_60287_1_1_ver,
                 state=state, log=log).get_value2()
    yp = calc_yp(cable_set, cable_num, cond_temp,
                 iec_60287_1_1_ver=iec_60287_1_1_ver,
                 state=state, log=log).get_value2()

    r_ac = r_dash * (1.0 + ys + yp)

    return QFloat(r_ac, 'Ω/m', f'{source}: AC conductor resistance',
                  description='ac resistance of conductor', symbol='R')


@UseState('r_dash', level=cabsys.data_classes.state_cct.CABLE)
@LogSection("R'")
def calc_r_dash(cable: Cable, cond_temp: float = None,
                iec_60287_1_1_ver: str = None,
                state: CableState = None, log: Log = None) -> QFloat:
    """Calculate dc resistance of phase conductor at operating temperature (Ω/m)

    If the conductor temperature is missing, the conductor temperature will be set using the following (in order of
    preference):
      * cable_state object if cond_temp top is set to dc.USER
      * cable object if cable.parameters.max_cond_temp top is set to dc.USER
      * calculated value (90.0 °C)

    IEC 60287-1-1 clause 5.1.2

    :param cable: the cable with the conductor being considered
    :param state: results and intermediate results
    :param cond_temp: conductor temperature of the conductor (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param log: calculation log
    :return: dc resistance of conductor at specified temperature (Ω/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.1.2'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.1.1'
    else:
        raise IEC60287Exception(f'trying to calculate conductor DC resistance (IEC 60287-1-1 ED3 Section 5.1.2) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" (probably in install config)'
                                f' not recognised')

    if cond_temp is None:
        cond_temp = iec60287support.get_cond_temp(cable, state=state, log=log).get_value2(unit='°C')
    elif log is not None:
        log.add_line('θ', cond_temp, '°C', 'set or calculated previously')

    r0 = iec60287support.get_q_parameter(cable.conductor.dc_resistance20, log=log)
    if r0 is None:
        r0 = cabsys.iec.iec60228.find_r0(cable, log=log).get_value2()

    alpha20 = iec60287support.get_q_parameter(cable.conductor.alpha20, log=log)
    if alpha20 is None:
        alpha20 = find_alpha20(cable, log=log).get_value2()

    r_dash = r0 * (1.0 + alpha20 * (cond_temp - 20.0))

    return QFloat(r_dash, 'Ω/m', f'{source}: DC conductor resistance',
                  description='conductor dc resistance at operating temperature', symbol="R'")


@LogSection("y_s")
def calc_ys(cable_set: CableSet, cable_num: int, cond_temp: float = None,
            iec_60287_1_1_ver: str = None,
            state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate ys2, the skin effect factor

    Calculate the skin effect factor ys, to IEC 60287-1-1 clause 5.1.3.

    :param cable_set: the cable set containing the cable
    :param cable_num: the cable number in the cable_set
    :param cond_temp: conductor temperature (°C)
    :param iec_60287_1_1_ver: IEC 60287-1-1 version to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: ys2, the skin effect factor
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.1.3'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.1.2'
    else:
        raise IEC60287Exception(f'trying to calculate conductor y_s (IEC 60287-1-1 ED3 Section 5.1.3) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" (probably in install config)'
                                f' not recognised')

    xs2 = calc_xs2(cable_set, cable_num, cond_temp,
                   iec_60287_1_1_ver=iec_60287_1_1_ver,
                   state=state, log=log).get_value2(unit='')

    xs = math.sqrt(xs2)
    if xs <= 2.8:
        ys = xs2 * xs2 / (192 + 0.8 * xs2 * xs2)
    elif xs <= 3.8:
        ys = -0.136 - 0.0177 * xs + 0.0563 * xs2
    else:
        ys = 0.354 * xs - 0.733

    return QFloat(ys, '-', f'{source}, skin effect factor',
                  description='skin effect factor', symbol='y_s')


@LogSection("x_s^2")
def calc_xs2(cable_set: CableSet, cable_num: int, cond_temp: float = None,
             iec_60287_1_1_ver: str = None,
             state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate xs2

    Calculate the xs2 factor, used to calculate the skin effect factor ys for a cable. If the conductor temperature is
    not given the maximum conductor temperature is used as defined in the Cable object (in cable_set).

    See IEC 60287-1-1 Section 5.1.3

    :param cable_set: the cable set containing the cable
    :param cable_num: the cable number in the cable set
    :param cond_temp: conductor temperature (°C)
    :param iec_60287_1_1_ver: IEC 60287-1-1 version to be used
    :param state: object holding results relating to cables
    :param log: logging object used to track results
    :return: xs2
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.1.3'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.1.2'
    else:
        raise IEC60287Exception(f'trying to calculate conductor x_s^2 (IEC 60287-1-1 ED3 Section 5.1.3) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" (probably in install config)'
                                f' not recognised')

    f = cable_set.f.get_value(unit='Hz', log=log)

    if state is None:
        cable_state = None
    else:
        cable_state = state.placed_cable_states[cable_num].cable_state
    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')
    r_dash = calc_r_dash(cable, cond_temp=cond_temp,
                         iec_60287_1_1_ver=iec_60287_1_1_ver,
                         state=cable_state, log=log).value

    # ks = cable.conductor.ks
    ks = iec60287support.get_q_parameter(cable.conductor.ks, log=log)
    if ks is None:
        ks = find_ks(cable, log=log).value

    xs2 = 8.0 * math.pi * f / r_dash * 1E-7 * ks

    return QFloat(xs2, '', f'{source}, skin effect factor',
                  description='skin effect factor', symbol='x_s^2')


@LogSection("x_p^2")
def calc_xp2(cable_set: CableSet, cable_num: int, cond_temp: float = None,
             iec_60287_1_1_ver: str = None,
             state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate xp2

    Calculate the xp2 factor, used to calculate the skin effect factor yp for a cable. If the conductor temperature is
    not given the maximum conductor temperature is used as defined in the Cable object (in cable_set).

    See IEC 60287-1-1 Section 5.1.4

    :param cable_set: the cable set containing the cable
    :param state: object holding results relating to cables
    :param cable_num: the cable number in the cable set
    :param cond_temp: conductor temperature (°C)
    :param iec_60287_1_1_ver: IEC 60287-1-1 version to be used
    :param log: logging used to store results
    :return: xp2
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.1.4'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.1.3'
    else:
        raise IEC60287Exception(f'trying to calculate conductor x_p^2 (IEC 60287-1-1 ED3 Section 5.1.4) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" (probably in install config)'
                                f' not recognised')

    f = cable_set.f.get_value(unit='Hz', log=log)

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is None:
        cable_state = None
    else:
        cable_state = state.placed_cable_states[cable_num].cable_state

    r_dash = calc_r_dash(cable, cond_temp=cond_temp,
                         iec_60287_1_1_ver=iec_60287_1_1_ver,
                         state=cable_state, log=log).value
    kp = iec60287support.get_q_parameter(cable.conductor.kp, log=log)
    if kp is None:
        kp = find_kp(cable, log=log).value

    xp2 = 8.0 * math.pi * f / r_dash * 1E-7 * kp

    return QFloat(xp2, '', f'{source}, proximity effect factor',
                  description='proximity effect factor', symbol='x_p^2')


@LogSection("y_p")
def calc_yp(cable_set: CableSet, cable_num: int, cond_temp: float = None,
            iec_60287_1_1_ver: str = None,
            state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the proximity effect factor, yp

    Calculate the proximity effect factor, yp. IEC 60287-1-1 clause 5.1.4 to clause 5.1.5

    :param cable_set: the cable set containing the cable
    :param cable_num: cable number in the cable_set
    :param state: object holding results relating to cables
    :param cond_temp: conductor temperature (°C)
    :param iec_60287_1_1_ver: IEC 60287-1-1 version to be used
    :param log: logger used to store results
    :return: proximity effect factor, yp
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.1.4 - 5.1.5'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.1.3 - 2.1.4'
    else:
        raise IEC60287Exception(f'trying to calculate conductor y_p (IEC 60287-1-1 ED3 Section 5.1.4 or 5.1.5) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" (probably in install config)'
                                f' not recognised')

    xp2 = calc_xp2(cable_set, cable_num, cond_temp,
                   iec_60287_1_1_ver=iec_60287_1_1_ver,
                   state=state, log=log).get_value2(unit='')
    no_cores = cable_set.find_no_cores(cable_num, log=log)
    no_cables = cable_set.find_no_cables(log=log)
    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    conductor_shape = cable.find_conductor_shape(log)
    s = iec60287support.calc_cable_spacing(cable_set, log)

    cable_pipe_type = cable.pipe_type.get_value(unit='', log=log)
    if cable_pipe_type is None:
        raise IEC60287Exception('trying to calculate ys but cable.pipe_type is None')

    if ((no_cables == 1 and no_cores == iec.TWO_CORE) or
        (no_cables == 2 and no_cores == iec.SINGLE_CORE) and
            not cable_pipe_type and conductor_shape == iec.CIRCULAR):
        dc = cable.conductor.dia.get_value2('mm', log=log)
        xp = math.sqrt(xp2)
        if xp > 2.8:
            raise IEC60287Exception("trying to calculate yp according to IEC 60287-1-1 Section 2.1.3 but xp > 2.8")
        yp = xp2 ** 2.0 / (192.0 + 0.8 * xp2 ** 2.0) * (dc / s) ** 2.0 * 2.9

    elif ((no_cables == 1 and no_cores == iec.THREE_CORE and conductor_shape == iec.CIRCULAR) or
          (no_cables == 3 and no_cores == iec.SINGLE_CORE)) and not cable_pipe_type:
        dc = cable.conductor.dia.get_value2('mm', log=log)
        yp = calc_yp_2_1_4_1(xp2, dc, s)
    elif no_cables == 1 and no_cores == iec.THREE_CORE and conductor_shape == iec.SHAPED and not cable_pipe_type:
        dc = cable.conductor.effective_dia.get_value2(unit='mm', log=log)
        yp = calc_yp_2_1_4_1(xp2, dc, s)
    elif no_cables == 1 and no_cores == iec.THREE_CORE and conductor_shape == iec.OVAL and not cable_pipe_type:
        d_major = cable.conductor.major_dia.get_value2(unit='mm', log=log)
        d_minor = cable.conductor.minor_dia.get_value2(unit='mm', log=log)
        dc = math.sqrt(d_major*d_minor)
        if log is not None:
            log.add_line('dc', dc, 'mm', 'square root of major and minor dia')
            log.add_warning('yp method not included in IEC 60287-1-1 for oval conductors')
        yp = calc_yp_2_1_4_1(xp2, dc, s)
    else:
        raise IEC60287Exception('trying to calculate ys but cable number of cores and cable formation not supported')

    return QFloat(yp, '-', f'{source}, proximity effect factor',
                  description='proximity effect factor', symbol='y_p')


def calc_yp_2_1_4_1(xp2: float, dc: float, s: float) -> float:
    """Calculate the proximity effect factor, yp, for three core and three single
     core cables, with circular conductors.

    IEC 60287-1-1  clause 5.1.4
    xp2  proximity effect factor xp2
    dc   diameter of conductor (mm)
    s    axial spacing between cables (mm)
    """
    xp = math.sqrt(xp2)
    if xp > 2.8:
        raise IEC60287Exception("trying to calculate yp but xp > 2.8")
    yp_bit = xp2 ** 2.0 / (192.0 + 0.8 * xp2 ** 2.0)
    yp = yp_bit * (dc / s) ** 2.0 * (0.312 * (dc / s) ** 2.0 + 1.18 / (yp_bit + 0.27))
    return yp


@UseState('wd', level=cabsys.data_classes.state_cct.CABLE)
@LogSection("W_d")
def calc_wd(install: Install, circuit_num: int, cable_set_num: int, cable_num: int, u_pe: float = None,
            state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the dielectric loss of a cable, Wd

    Normally the phase to earth voltage is defined in the CableSet.PlacedCable object but this can be overridden by
    supplying a value as an argument.

    IEC 60287-1-1 clause 5.2

    :param install: the installation being considered
    :param circuit_num: the circuit number
    :param cable_set_num: the cable set number in the installation
    :param cable_num: the cable number in the cable_set
    :param u_pe: phase to earth voltage applied to cable (V)
    :param state: installation state
    :param log: logger used to store results
    :return: dielectric loss of a cable, Wd (W/m)
    """

    iec_60287_1_1_ver = install.config.iec_60287_1_1_ver.get_value(unit='')
    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.2'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.2'
    else:
        raise IEC60287Exception(f'trying to calculate dielectric loss W_d (IEC 60287-1-1 ED3 Section 5.2) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" (probably in install config)'
                                f' not recognised')

    cable_set = install.install_circuits[circuit_num].cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable

    always_calc_wd = install.config.always_calc_wd.get_value(unit='')
    if not always_calc_wd:
        if log is not None:
            log.start_section('U0 check', 'IEC 60287-1-1 Section 5.2, ignore Wd below U0')
        ins_mat = cable.core.insulation_material.get_value(unit='', log=log)
        ignore_volts = INSULATION_LOSS_IGNORE[ins_mat]
        volts = cable.design_volts.get_value(unit='kV', log=log)
        if log is not None:
            log.end_section('U0 check', ignore_volts, 'V', 'IEC 60287-1-1 Section 5.2, ignore Wd below U0')
            if iec_60287_1_1_ver == iec.CIGRE_TB880_2022:
                log.add_warning("W_d is ignored: not compliant with CIGRE TB 880 2022 GP7 (always_calc_wd is False)")
        if volts < ignore_volts:
            return QFloat(0.0, 'W/m', 'IEC 60287-1-1 Table 3: Ignore dielectric losses',
                          description='dielectric losses', symbol='W_d')

    f = cable_set.f.get_value(unit='Hz', log=log)
    if f is None:
        raise IEC60287Exception('Cable system frequency must be set')

    cable = cable_set.placed_cables[cable_num].cable
    c = calc_c(install, circuit_num, cable_set_num, cable_num, state=state, log=log).value

    if u_pe is None:
        u_pe = cable_set.placed_cables[cable_num].u_pe.get_value(unit='V', log=log)
    else:
        if log is not None:
            log.add_line('U_pe', u_pe, 'V', 'supplied by program')

    tan_d = iec60287support.get_q_parameter(cable.core.tan_d, log=log)
    if tan_d is None:
        tan_d = find_insulation_tan_d(cable, log=log).value

    wd = 2.0 * math.pi * f * c * u_pe ** 2 * tan_d

    return QFloat(wd, 'W/m', f'{source}, dielectric losses',
                  description='dielectric losses', symbol='W_d')


@UseState('c', level=cabsys.data_classes.state_cct.CABLE)
@LogSection("C")
def calc_c(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
           state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the capacitance of a cable

    IEC 60287-1-1 clause 5.2

    :param install: the installation being considered
    :param circuit_num: the circuit number being considered
    :param cable_set_num: the cable set number in the installation
    :param cable_num: the cable number in the cable set
    :param state: cable state
    :param log: logger used to store results
    :return: capacitance of cable (F/m)
    """

    # not needed but stops PyCharms complaining that state is not used (it is but in the UseState decorator)
    if state:
        pass

    cable = install.install_circuits[circuit_num].cable_sets[cable_set_num].placed_cables[cable_num].cable

    capacitance_2023 = install.config.capacitance_2023.get_value(unit='')
    iec_60287_1_1_ver = install.config.iec_60287_1_1_ver.get_value(unit='')
    if capacitance_2023:
        source = 'IEC 60287-1-1:2023 ED3 Section 5.2'
        if iec_60287_1_1_ver in [iec.CIGRE_TB880_2022, iec.IEC60287_1_1_ED2]:
            if log is not None:
                log.add_warning(f'iec_60287_1_1_ver is {iec_60287_1_1_ver} but formula from '
                                f'IEC 60287-1-1:2023')
    else:
        source = 'IEC 60287-1-1 ED2 Section 2.2'
        if iec_60287_1_1_ver not in [iec.CIGRE_TB880_2022, iec.IEC60287_1_1_ED2]:
            if log is not None:
                log.add_warning(f'iec_60287_1_1_ver is {iec_60287_1_1_ver} but formula from '
                                f'IEC 60287-1-1 ED2')

    e = iec60287support.get_q_parameter(cable.core.permittivity, log=log)
    if e is None:
        e = find_insulation_permittivity(cable, log=log).get_value2()

    di = cable.core.insu_dia.get_value2(unit='mm', log=log)
    dc = cable.core.cond_screen_dia.get_value2(unit='mm', log=log)

    if capacitance_2023:
        c = 2.0 * math.pi * 8.854e-12 * e / (math.log(di / dc))
    else:
        c = e / (18.0 * math.log(di / dc)) * 10 ** -9

    return QFloat(c, 'F/m', f'{source}, capacitance of cable',
                  description='capacitance of cable', symbol='C')


def calc_theta_sc(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
                  current: float, conductor_temp: float, u_pe: float = None,
                  state: InstallState = None, log: Log = None) -> Union[QFloat, Tuple[QFloat, QFloat, QFloat]]:
    """Calculate the sheath temperature for a given load current. (°C)

    The sheath temperature is calculated from the inputs. If the cable voltage is not given the voltage defined
    in the placed cable object is used.

    The method of calculation will depend on install.config.multi_sheath_lambda. If the config is True then the method
    used will not be to IEC but will calculate a sheath temperature for each

    IEC 60287-1-1 amd clause 5.3.1

    :param install: object containing cable_set
    :param circuit_num: circuit number
    :param cable_set_num: index number of cable set in the installation
    :param cable_num: index number of the cable in the cable set
    :param current: current flowing through cable (A)
    :param conductor_temp: conductor temperature of cable (°C)
    :param u_pe: phase to earth voltage of cable (V)
    :param state: install set state, used to get and set other calculations
    :param log: logger used to store results
    :return: sheath temperature for given cable current (°C)
    """

    if install.config.multi_sheath_lambda.value:
        theta_sc = iec60287_1_1alt.calc_theta_sc(install, circuit_num, cable_set_num, cable_num,
                                                 current, conductor_temp, u_pe=u_pe,
                                                 state=state, log=log)
    else:
        theta_sc = calc_theta_sc_5_3_1(install, circuit_num, cable_set_num, cable_num,
                                       current, conductor_temp, u_pe=u_pe,
                                       state=state, log=log)
    return theta_sc


@UseState('sheath_temp', level=cabsys.data_classes.state_cct.CABLE)
@LogSection('θ_sc')
def calc_theta_sc_5_3_1(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
                        current: float, conductor_temp: float, u_pe: float = None,
                        state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the sheath temperature for a given load current. (°C)

    The sheath temperature is calculated from the inputs. If the cable voltage is not given the voltage defined
    in the placed cable object is used.

    IEC 60287-1-1 clause 5.3.1

    :param install: object containing cable_set
    :param circuit_num: circuit number
    :param cable_set_num: index number of cable set in the installation
    :param cable_num: index number of the cable in the cable set
    :param current: current flowing through cable (A)
    :param conductor_temp: conductor temperature of cable (°C)
    :param u_pe: phase to earth voltage of cable (V)
    :param state: install set state, used to get and set other calculations
    :param log: logger used to store results
    :return: sheath temperature for given cable current (°C)
    """

    if install.config.multi_sheath_lambda.value:
        raise IEC60287Exception('trying to calculate sheath/screen temperature but config.multi_sheath_lambda'
                                ' set to True')

    if state is not None:
        install_circuit_state = state.install_circuit_states[circuit_num]
        cable_set_state = install_circuit_state.cable_set_states[cable_set_num]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    if install.config.iec_60287_1_1_ver.value in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.1'
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3'
    else:
        raise IEC60287Exception(f'trying to calculate metal sheath temperature (IEC 60287-1-1 ED3 Section 5.3.1) but'
                                f' IEC 60287-1-1 version "{install.config.iec_60287_1_1_ver.value}" in install config'
                                f' not recognised')

    cable_set = install.install_circuits[circuit_num].cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable
    # current = cable_set_state.get_quantity('current', log=log)
    if conductor_temp is None:
        conductor_temp = iec60287support.get_cond_temp(cable, state=cable_state, log=log).get_value2(unit='°C')
    elif log is not None:
        log.add_line('θ', conductor_temp, '°C', 'set or calculated previously')
    theta_c = conductor_temp
    r_ac = calc_r_ac(cable_set, cable_num, theta_c,
                     iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                     state=cable_set_state, log=log).get_value2(unit='Ω/m')
    wd = calc_wd(install, circuit_num, cable_set_num, cable_num, u_pe=u_pe, state=state, log=log).get_value2(unit='W/m')
    t1 = iec60287_2_1.calc_t1(install, circuit_num, cable_set_num, cable_num,
                              state=state, log=log).get_value2(unit='K.m/W')

    theta_sc = theta_c - (current**2 * r_ac + wd / 2) * t1

    return QFloat(theta_sc, '°C', f'{source}, sheath temperature',
                  description='sheath temperature', symbol='θ_sc')


@UseState('duct_air_temp', level=cabsys.data_classes.state_cct.CABLE)
@LogSection('θ_m')
def calc_theta_m(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
                 current: float, conductor_temp: float, sheath_temp: Union[float, Tuple[float, float, float]],
                 u_pe: float = None,
                 state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the average duct temperature for a given load current. (°C)

    The average duct air temperature is value is found in the following order: the value in cable state, otherwise it is
    calculated using the current in the cable_set state.

    IEC 60287-1-1 in line with clause 2.3 (modified)

    :param install: installation object containing cable_set
    :param circuit_num: circuit number
    :param cable_set_num: index number of cable set in the installation
    :param cable_num: index number of the cable in the cable set
    :param current: current flowing through cable (A)
    :param conductor_temp: conductor temperature of cable (°C)
    :param sheath_temp: sheath temperature of cable (°C)
    :param u_pe: phase to earth voltage of cable (V)
    :param state: install set state, used to get and set other calculations
    :param log: logger used to store results
    :return: sheath temperature for given cable current (°C)
    """

    if state is not None:
        install_circuit_state = state.install_circuit_states[circuit_num]
        cable_set_state = install_circuit_state.cable_set_states[cable_set_num]
        if cable_set_state is not None:
            cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
        else:
            cable_state = None
    else:
        cable_set_state = None
        cable_state = None


    if install.config.iec_60287_1_1_ver.value in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.1 (modified)'
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3 (modified)'
    else:
        raise IEC60287Exception(f'trying to calculate duct air temperature (IEC 60287-1-1 ED3 Section 5.3.1) but'
                                f' IEC 60287-1-1 version "{install.config.iec_60287_1_1_ver.value}" in install config'
                                f' not recognised')

    cable_set = install.install_circuits[circuit_num].cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable
    # current = cable_set_state.get_quantity('current', log=log)
    if conductor_temp is None:
        conductor_temp = iec60287support.get_cond_temp(cable, state=cable_state, log=log).get_value2(unit='°C')
    elif log is not None:
        log.add_line('θ', conductor_temp, '°C', 'set or calculated previously')
    theta_c = conductor_temp
    theta_a = install.ambient_theta.get_value2(unit='°C', log=log)
    r_ac = calc_r_ac(cable_set, cable_num, theta_c,
                     iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                     state=cable_set_state, log=log).get_value2(unit='Ω/m')
    wd = calc_wd(install, circuit_num, cable_set_num, cable_num, u_pe=u_pe,
                 state=state, log=log).get_value2(unit='W/m')
    lambda1 = calc_lambda_1(install, circuit_num, cable_set_num, cable_num, conductor_temp, sheath_temp,
                            state=state, log=log).get_value2(unit='')
    t1 = iec60287_2_1.calc_t1(install, circuit_num, cable_set_num, cable_num,
                              state=state, log=log).get_value2(unit='K.m/W')
    t2 = iec60287_2_1.calc_t2(cable, state=cable_state, log=log).get_value2(unit='K.m/W')
    t3 = iec60287_2_1.calc_t3(install, circuit_num, cable_set_num, cable_num,
                              state=state, log=log).get_value2(unit='K.m/W')

    n_d = cable_set.calc_num_cables_in_ducts(log).get_value()

    old_duct_temp = 0.0
    theta_m = (theta_c + theta_a) / 2
    count = 0
    max_iteration = install.config.max_duct_air_iteration.value
    while (abs(theta_m - old_duct_temp) > install.config.duct_air_accuracy.value and count < max_iteration and
           count < 10000 and theta_m > theta_a):
        count = count + 1
        if log is not None:
            log.add_line('θ_m estimate', theta_m, '°C')
        old_duct_temp = theta_m
        t4dash = iec60287_2_1.calc_t4dash_4_2_6_3(install, circuit_num, cable_set_num,
                                                  cable_num, theta_m, log=log).get_value2(unit='K.m/W')
        theta_m = (theta_c - (current**2 * r_ac + wd / 2) * t1 -
                   ((current**2 * r_ac)*(1 + lambda1) + wd) * t2 -
                   ((current**2 * r_ac)*(1 + lambda1) + wd) * (t3 + n_d * t4dash / 2))

    if count == max_iteration:
        raise IEC60287Exception(f'trying to calculate mean duct temperature but iterations > {max_iteration}')
    if count == 10000:
        raise IEC60287Exception(f'trying to calculate mean duct temperature but iterations > 10000')

    return QFloat(theta_m, '°C', f'{source}, average duct air temperature',
                  description='duct air temperature', symbol='θ_m')


def calc_lambda_1(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
                  conductor_temperature: float,
                  sheath_temperature: Union[float, Tuple[float, float, float]],
                  state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the metal sheath/screen loss

    Calculates the metal sheath/screen loss (lambda_1). The metal sheath/screen resistance is based on the metal
    sheath/screen temperature given as an argument.

    If the sheath temperature is a single number (float), then the sheath/screen loss calculated will be based on
    IEC 60287-1-1 equations that assume the same sheath/screen temperature for all sheaths and screens. If the sheath/
    screen temperature is a tuple of 3 temperatures then CIGRE TB 880 equations are used that calculate the losses for
    each sheath/screen. The cable sheath/screens must be in the order of a wire screen, metal sheath, and tape layer,
    although a sheath or screen may be missed out.

    IEC 60287-1-1 Section 5.3.1 as modified by IEC 60287-2-1 4.2.4.2.1

    :param install: object containing cable_set
    :param circuit_num: circuit number
    :param cable_set_num: index number of cable set in the installation
    :param cable_num: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param state: install set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    # decide to use single lambda_1 as per IEC 60287-2-1 or multiple lambda_1 T1 as per TB 880
    if isinstance(sheath_temperature, float) and not install.config.multi_sheath_lambda.value:
        lambda_1 = calc_lambda_1_c_5_4(install, circuit_num, cable_set_num, cable_num,
                                       conductor_temperature,
                                       sheath_temperature,
                                       state=state, log=log)
    elif install.config.multi_sheath_lambda.value:
        lambda_1_m = iec60287_1_1alt.calc_lambda_1(install, circuit_num, cable_set_num, cable_num,
                                                   conductor_temperature,
                                                   sheath_temperature,
                                                   state=state, log=log)
        lambda_1 = lambda_1_m[0]
    else:
        raise IEC60287Exception('trying to calculate lambda_1 but more than one sheath temperature given for'
                                ' IEC method')
    return lambda_1


@UseState('lambda_1', level=cabsys.data_classes.state_cct.CABLE)
@LogSection('λ_1')
def calc_lambda_1_c_5_4(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
                        conductor_temperature: float,
                        sheath_temperature: float,
                        state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the metal sheath/screen loss

    Calculates the metal sheath/screen loss (lambda_1). The metal sheath/screen resistance is based on the metal
    sheath/screen temperature given as an argument.

    IEC 60287-1-1 clause 5.3.1

    :param install: object containing cable_set
    :param circuit_num: circuit number
    :param cable_set_num: index number of cable set in the installation
    :param cable_num: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param state: install set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    if log is None:
        log = no_log

    if state is not None:
        install_circuit_state = state.install_circuit_states[circuit_num]
        cable_set_state = install_circuit_state.cable_set_states[cable_set_num]
    else:
        cable_set_state = None
    # if cable_set_state is not None:
    #     cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    # else:
    #     cable_state = None

    if install.config.iec_60287_1_1_ver.value in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.1'
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2]:
        source = 'IEC 60287-1-1 ED2 Section 2.3'
    elif install.config.iec_60287_1_1_ver.value in [iec.CIGRE_TB880_2022]:
        source = 'CIGRE TB 880 2022 Guidance Point 6 & 31'
    else:
        raise IEC60287Exception(f'trying to calculate the sheath loss (IEC 60287-1-1 ED3 Section 5.3.1) but'
                                f' IEC 60287-1-1 version "{install.config.iec_60287_1_1_ver.value}" in install config'
                                f' not recognised')

    cable_set = install.install_circuits[circuit_num].cable_sets[cable_set_num]
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
                                         state=cable_set_state, log=log).get_value2(unit='')
                # Todo: add correction factor for Milliken conductors
            else:
                # Todo: add sheath loss for 2 single core cables specially bonded
                raise IEC60287Exception('calculating sheath loss but 2 single core cables specially bonded')
        elif number_cables == 3:
            if bonding == iec.SOLID_BONDED:
                lambda1dash = calc_lambda_1d(cable_set, cable_num, conductor_temperature,
                                             sheath_temperature=sheath_temperature,
                                             iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                             state=cable_set_state, log=log).get_value2(unit='')
                c_f = calc_f_c_s5_3_6(install, cable_set, cable_num,
                                      sheath_screen_temperature=sheath_temperature,
                                      state=cable_set_state, log=log).get_value2(unit='')
                if c_f > 0:
                    lambda1_dash_dash = calc_lambda1_dash_dash_5_3_7_1(install, circuit_num, cable_set_num, cable_num,
                                                                       conductor_temperature,
                                                                       sheath_screen_temperature=sheath_temperature,
                                                                       state=state, log=log).get_value2(unit='')
                else:
                    lambda1_dash_dash = 0.0
                lambda1 = lambda1dash + c_f * lambda1_dash_dash
            else:
                if bonding == iec.CROSS_BONDED:
                    transposed = cable_set.transposed.get_value(unit='')
                    if not transposed:
                        raise IEC60287Exception('IEC 60287-1-1: circuit is cross bonded but not transposed')
                if bonding == iec.SINGLE_POINT_BONDED:
                    c_i = 0.0
                else:
                    c_i = calc_rcc_5_3_7_2(cable_set,
                                           iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                           state=cable_set_state, log=log).get_value2(unit='')
                if c_i > 0.0:
                    lambda1dash = calc_lambda_1d(cable_set, cable_num, conductor_temperature,
                                                 sheath_temperature=sheath_temperature,
                                                 iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                                 state=cable_set_state, log=log).get_value2(unit='')
                else:
                    lambda1dash = 0.0
                lambda1_dash_dash = calc_lambda1_dash_dash_5_3_7_1(install, circuit_num, cable_set_num, cable_num,
                                                                   conductor_temperature,
                                                                   sheath_screen_temperature=sheath_temperature,
                                                                   state=state, log=log).get_value2(unit='')
                lambda1 = c_i * lambda1dash + lambda1_dash_dash
        else:
            raise IEC60287Exception('calculating sheath loss factor but more than 3 single core cables given')
    else:
        raise IEC60287Exception('calculating sheath loss factor but only single core cables implemented')

    return QFloat(lambda1, '', f'{source}, sheath/screen loss factor',
                  description='sheath/screen loss factor', symbol='λ_1')


@UseState("lambda_1_dash", level=cabsys.data_classes.state_cct.CABLE)
@LogSection("λ_1'")
def calc_lambda_1d(cable_set: CableSet, cable_num: int,
                   conductor_temperature: float,
                   sheath_temperature: float,
                   iec_60287_1_1_ver: str = None,
                   state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the circulating loss for  metal sheath/screen

    Calculates the metal sheath/screen loss (lambda_1') due to circulating currents.

    IEC 60287-1-1 Ed 3 clause 5.3.1

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
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

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


@LogSection("λ'_1 2 phase/trefoil")
def calc_lambda_1_s5_3_2(cable_set: CableSet, cable_num: int,
                         conductor_temperature: float,
                         sheath_temperature: float,
                         iec_60287_1_1_ver: str = None,
                         state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the circulating loss for metal sheath/screen loss solidly bonded 2 phase systems

    Calculates the metal sheath/screen loss (lambda_1') due to circulating currents for 2 phase and 3 phase trefoil
    systems.

    IEC 60287-1-1 clause 5.3.2

    :param cable_set: cable_set
    :param cable_num: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param iec_60287_1_1_ver: IEC 60287_1_1 version used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.2'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.1'
    else:
        raise IEC60287Exception(f'trying to calculate the 2 phase or trefoil solidly bonded sheath loss'
                                f' (IEC 60287-1-1 ED3 Section 5.3.2)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is not None:
        cable_state = state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    x = calc_x_5_3_2(cable_set, cable_num, iec_60287_1_1_ver, state=state, log=log).get_value2(unit='Ω/m')
    r_s = iec60287support.calc_sheath_screen_resistance(cable, sheath_temperature,
                                                        ignore_csw_tape=False,
                                                        iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                        state=cable_state, log=log).get_value2(unit='Ω/m')
    r_c = calc_r_ac(cable_set, cable_num, conductor_temperature,
                    iec_60287_1_1_ver=iec_60287_1_1_ver,
                    state=state, log=log).get_value2(unit='Ω/m')

    lambda_1_dash = r_s / r_c * (1 / (1 + (r_s / x) ** 2))

    return QFloat(lambda_1_dash, '', f'{source}, 2 phase/trefoil solid sheath loss',
                  description='circulating sheath loss', symbol="λ1'")


@UseState("X", level=cabsys.data_classes.state_cct.CABLE)
@LogSection("X")
def calc_x_5_3_2(cable_set: CableSet, cable_num: int, iec_60287_1_1_ver: str = None,
                 state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the reactance for metal sheath/screen loss solidly bonded 2 phase systems (Ω/m)

    Calculates the metal sheath/screen reactance (X) due for 2 phase and 3 phase trefoil systems.

    IEC 60287-1-1 clause 5.3.2: reactance per unit length of sheath or screen per unit length of cable (Ω/m)

    :param cable_set: cable_set
    :param cable_num: index number of the cable in the cable set
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: reactance per unit length of sheath or screen per unit length of cable (Ω/m)
    """

    # state needed for decorator UseState, the following line fools PyCharm into thinking state is used
    if state:
        pass

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.2'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.1'
    else:
        raise IEC60287Exception(f'trying to calculate the 2 phase or trefoil solidly bonded sheath loss'
                                f' (IEC 60287-1-1 ED3 Section 5.3.2)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    f = cable_set.f.get_value2('Hz', log=log)
    s = iec60287support.calc_cable_spacing(cable_set, log=log)
    number_cores = cable.number_cores.get_value('', log=log)

    if number_cores == iec.SINGLE_CORE:
        # check that the cable set is 2 cables or 3 cables in trefoil
        number_cables = cable_set.find_no_cables(log=log)
        formation = iec60287support.calc_cable_formation(cable_set, log=log)
        if number_cables == 1:
            raise IEC60287Exception('calculating X but only 1 single core cable in cable set')
        if number_cables == 3 and not formation == iec.TREFOIL:
            raise IEC60287Exception(f'calculating X but 3 cables are in {formation} formation')
        d = iec60287support.calc_sheath_screen_mean_diameter(cable, ignore_csw_tape=False,
                                                             log=log).get_value2(unit='mm')
    else:
        raise IEC60287Exception(f'calculating X but do not recognise "{number_cores}" number of cores')

    x = 2 * 2 * math.pi * f * 10 ** -7 * math.log(2 * s / d)

    return QFloat(x, 'Ω/m', f'{source}, sheath/screen reactance',
                  description='sheath/screen reactance', symbol='X')


@LogSection("λ'_1 flat transposed")
def calc_lambda_1_s5_3_3(cable_set: CableSet, cable_num: int,
                         conductor_temperature: float = None,
                         sheath_temperature: float = None,
                         iec_60287_1_1_ver: str = None,
                         state: CableSetState = None, log: Log = None) -> Union[QFloat,
                                                                                Tuple[float, float, float, float]]:
    """Calculate circulating loss for metal sheath/screen solidly bonded 3 phase systems in flat transposed formation

    Calculates the metal sheath/screen loss (lambda_1') due to circulating currents for 3 phase flat transposed cable
    systems.

    IEC 60287-1-1 clause 5.3.3

    :param cable_set: cable_set
    :param cable_num: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.3'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.2'
    else:
        raise IEC60287Exception(f'trying to calculate the 3 phase flat formation transposed solidly bonded sheath loss'
                                f' (IEC 60287-1-1 ED3 Section 5.3.3)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is not None:
        cable_state = state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    x = calc_x1_5_3_3(cable_set, cable_num, iec_60287_1_1_ver=iec_60287_1_1_ver,
                      state=state, log=log).get_value2(unit='Ω/m')
    r_c = calc_r_ac(cable_set, cable_num, conductor_temperature,
                    iec_60287_1_1_ver=iec_60287_1_1_ver,
                    state=state, log=log).get_value2(unit='Ω/m')

    r_s = iec60287support.calc_sheath_screen_resistance(cable, sheath_temperature,
                                                        ignore_csw_tape=False,
                                                        iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                        state=cable_state, log=log).get_value2(unit='Ω/m')
    lambda_1_dash = r_s / r_c * (1 / (1 + (r_s / x) ** 2))
    return QFloat(lambda_1_dash, '', f'{source}', description='circulating sheath loss', symbol="λ1'")


@UseState("X1", level=cabsys.data_classes.state_cct.CABLE)
@LogSection("X1")
def calc_x1_5_3_3(cable_set: CableSet, cable_no: int,
                  iec_60287_1_1_ver: str = None,
                  state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the reactance for metal sheath/screen solidly bonded 3 phase flat transposed systems

    Calculates the metal sheath/screen reactance(X) for 3 phase flat transposed cable systems.

    IEC 60287-1-1 clause 2.3.2: reactance per unit length of sheath or screen per unit length of cable (Ω/m)

    :param cable_set: cable_set
    :param cable_no: index number of the cable in the cable set
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: reactance per unit length of sheath or screen per unit length of cable (Ω/m)
    """

    # state needed for decorator UseState, the following line fools PyCharm into thinking state is used
    if state:
        pass

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.3'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.2'
    else:
        raise IEC60287Exception(f'trying to calculate the 3 phase flat formation transposed solidly bonded sheath loss'
                                f' (IEC 60287-1-1 ED3 Section 5.3.3)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    cable = cable_set.placed_cables[cable_no].cable
    f = cable_set.f.get_value('Hz', log=log)
    s = iec60287support.calc_cable_spacing(cable_set, log=log)
    number_cores = cable.number_cores.get_value('', log=log)

    if number_cores == iec.SINGLE_CORE:
        # check that the cable set 3 cables in flat transposed
        number_cables = cable_set.find_no_cables(log=log)
        formation = iec60287support.calc_cable_formation(cable_set, log=log)
        transposed = cable_set.transposed.get_value('', log=log)
        if number_cables == 3 and formation == iec.FLAT and transposed:
            d = iec60287support.calc_sheath_screen_mean_diameter(cable, ignore_csw_tape=False, log=log).value
        else:
            raise IEC60287Exception(f'calculating X1 for 3 S/C flat transposed but {number_cables} cables '
                                    f'in {formation} formation and transposed: {transposed}')
    elif number_cores == iec.THREE_CORE or number_cores == iec.TWO_CORE:
        raise IEC60287Exception(f'calculating X for single core cable but cable has "{number_cores}" number of cores')
    else:
        raise IEC60287Exception(f'calculating X but do not recognise "{number_cores}" number of cores')

    x1 = 2.0 * 2.0 * math.pi * f * 10 ** -7 * math.log(2.0 * 2.0 ** (1.0 / 3.0) * s / d)

    return QFloat(x1, 'Ω/m', f'{source}, sheath/screen reactance',
                  description='sheath/screen reactance', symbol='X1')


@LogSection("λ'_1 flat not transposed")
def calc_lambda_1dash_s5_3_4(cable_set: CableSet, cable_num: int,
                             conductor_temperature: float = None,
                             sheath_temperature: float = None,
                             iec_60287_1_1_ver: str = None,
                             state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate circulating loss for metal sheath/screen solidly bonded 3 phase systems in flat un-transposed formation

    Calculates the metal sheath/screen loss (lambda_1') due to circulating currents for 3 phase flat un-transposed cable
    systems.

    IEC 60287-1-1 clause 5.3.4

    :param cable_set: cable_set
    :param cable_num: index number of the cable in the cable set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.4'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.3'
    else:
        raise IEC60287Exception(f'trying to calculate the 3 phase flat formation un-transposed solidly bonded'
                                f' sheath loss (IEC 60287-1-1 ED3 Section 5.3.4)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is not None:
        cable_state = state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    xm = calc_xm_5_3_4(cable_set, iec_60287_1_1_ver=iec_60287_1_1_ver, state=state, log=log).get_value2(unit='Ω/m')
    r_s = iec60287support.calc_sheath_screen_resistance(cable, sheath_temperature,
                                                        ignore_csw_tape=False,
                                                        iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                        state=cable_state, log=log).get_value2(unit='Ω/m')
    r_c = calc_r_ac(cable_set, cable_num, conductor_temperature,
                    iec_60287_1_1_ver=iec_60287_1_1_ver,
                    state=state, log=log).get_value2(unit='Ω/m')
    c_p = calc_cp_5_3_4(cable_set, cable_num, iec_60287_1_1_ver=iec_60287_1_1_ver,
                        state=state, log=log).get_value2(unit='')
    c_q = calc_cq_5_3_4(cable_set, cable_num, state=state, log=log).get_value2(unit='')
    phase = iec60287support.calc_cable_phase_wrt_centre(cable_set, cable_num, state=state, log=log)

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

    return QFloat(lambda_1_dash, '', f'{source}',
                  description='circulating sheath loss', symbol=symbol)


@LogSection("C_P")
def calc_cp_5_3_4(cable_set: CableSet, cable_no: int,
                  iec_60287_1_1_ver: str = None,
                  state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the value of C_P for flat formation, not transposed

    IEC 60287-1-1 clause 5.3.4: C_P (Ω/m)

    :param cable_set: cable_set
    :param cable_no: index number of the cable in the cable set
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: C_P (Ω/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.4'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.3'
    else:
        raise IEC60287Exception(f'trying to calculate the 3 phase flat formation un-transposed solidly bonded'
                                f' C_P (IEC 60287-1-1 ED3 Section 5.3.4)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    x = calc_x_5_3_4(cable_set, cable_no, iec_60287_1_1_ver=iec_60287_1_1_ver,
                     state=state, log=log).get_value2(unit='Ω/m')
    xm = calc_xm_5_3_4(cable_set, iec_60287_1_1_ver=iec_60287_1_1_ver, state=state, log=log).get_value2(unit='Ω/m')
    p = x + xm

    return QFloat(p, 'Ω/m', f'{source}, C_P',
                  description='C_P', symbol='C_P')


@LogSection("C_Q")
def calc_cq_5_3_4(cable_set: CableSet, cable_no: int,
                  iec_60287_1_1_ver: str = None,
                  state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the value of C_Q for flat formation, not transposed

    IEC 60287-1-1 clause 5.3.4: C_Q (Ω/m)

    :param cable_set: cable_set
    :param cable_no: index number of the cable in the cable set
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to use
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: C_Q (Ω/m)
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.4'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.3'
    else:
        raise IEC60287Exception(f'trying to calculate the 3 phase flat formation un-transposed solidly bonded'
                                f' C_Q (IEC 60287-1-1 ED3 Section 5.3.4)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    x = calc_x_5_3_4(cable_set, cable_no, iec_60287_1_1_ver=iec_60287_1_1_ver,
                     state=state, log=log).get_value2(unit='Ω/m')
    xm = calc_xm_5_3_4(cable_set, iec_60287_1_1_ver=iec_60287_1_1_ver,
                       state=state, log=log).get_value2(unit='Ω/m')
    c_q = x - xm / 3

    return QFloat(c_q, 'Ω/m', f'{source}, C_Q',
                  description='C_Q', symbol='C_Q')


@UseState("X", level=cabsys.data_classes.state_cct.CABLE)
@LogSection("X")
def calc_x_5_3_4(cable_set: CableSet, cable_num: int,
                 iec_60287_1_1_ver: str = None,
                 state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the reactance for metal sheath/screen between adjacent cables, flat cables not transposed

    Calculates the metal sheath/screen reactance(X) between adjacent cables.

    IEC 60287-1-1 clause 5.3.4: reactance per unit length of sheath or screen per unit length of cable (Ω/m)

    :param cable_set: cable_set
    :param cable_num: index number of the cable in the cable set
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: reactance per unit length of sheath or screen per unit length of cable (Ω/m)
    """

    # state needed for decorator UseState, the following line fools PyCharm into thinking state is used
    if state:
        pass

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.4'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.3'
    else:
        raise IEC60287Exception(f'trying to calculate the 3 phase flat formation un-transposed solidly bonded'
                                f' X (IEC 60287-1-1 ED3 Section 5.3.4)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    f = cable_set.f.get_value2('Hz', log=log)
    s = iec60287support.calc_cable_spacing(cable_set, log=log)
    number_cores = cable.number_cores.get_value(unit='', log=log)

    if number_cores == iec.SINGLE_CORE:
        # check that the cable set 3 cables in flat formation not transposed
        number_cables = cable_set.find_no_cables(log=log)
        formation = iec60287support.calc_cable_formation(cable_set, log=log)
        transposed = cable_set.transposed.get_value('', log=log)
        if number_cables == 3 and formation == iec.FLAT:
            d = iec60287support.calc_sheath_screen_mean_diameter(cable, ignore_csw_tape=False,
                                                                 log=log).get_value2(unit='mm')
        else:
            raise IEC60287Exception(f'calculating X for 3 S/C flat transposed but {number_cables} cables '
                                    f'in {formation} formation and transposed: {transposed}')
    elif number_cores == iec.THREE_CORE or number_cores == iec.TWO_CORE:
        raise IEC60287Exception(f'calculating X for single core cable but cable has "{number_cores}" number of cores')
    else:
        raise IEC60287Exception(f'calculating X but do not recognise "{number_cores}" number of cores')

    x = 2 * 2 * math.pi * f * 10 ** -7 * math.log(2 * s / d)

    return QFloat(x, 'Ω/m', f'{source}, sheath/screen reactance',
                  description='sheath/screen reactance', symbol='X')


@LogSection("Xm")
def calc_xm_5_3_4(cable_set: CableSet,
                  iec_60287_1_1_ver: str = None,
                  state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the reactance for metal sheath/screen of outer cable, for flat cables not transposed

    Calculates the metal sheath/screen reactance (Xm) of outer cable

    IEC 60287-1-1 clause 5.3.4: reactance per unit length of sheath or screen per unit length of cable (Ω/m)

    :param cable_set: cable_set
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: cable set state, used to get and set other calculations
    :param log: logger used to store results
    :return: reactance per unit length of sheath or screen per unit length of cable (Ω/m)
    """

    # state needed for decorator UseState, the following line fools PyCharm into thinking state is used
    if state:
        pass

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.4'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.3'
    else:
        raise IEC60287Exception(f'trying to calculate the 3 phase flat formation un-transposed solidly bonded'
                                f' Xm (IEC 60287-1-1 ED3 Section 5.3.4)'
                                f' but IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config not recognised')

    f = cable_set.f.get_value2('Hz', log=log)
    xm = 2 * 2 * math.pi * f * 10 ** -7 * math.log(2)

    return QFloat(xm, 'Ω/m', f'{source}, sheath/screen reactance',
                  description='sheath/screen reactance', symbol='Xm')


# TODO: implement Section 2.3.4 Variation of spacing


@UseState('C_F', cabsys.data_classes.state_cct.CABLE)
@LogSection('C_F')
def calc_f_c_s5_3_6(install: Install, cable_set: CableSet, cable_num: int,
                    sheath_screen_temperature: float = None,
                    sheath_screen_resistance: float = None,
                    state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate C_F, proportion of eddy current loss in solid bond Millikan cables

    Calculate C_F, see IEC 60287-1-1 Section 5.3.6.

    Either the metal sheath/screen temperature or resistance needs to be given. Note if there is more than one metal
    sheath/screen, each with an individually calculated temperature then the sheath/screen resistance should be given.

    :param install: installation object
    :param cable_set: cable_set object containing the cable
    :param cable_num: cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param sheath_screen_resistance: metal sheath / screen electrical resistance (ohm)
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: C_F
    """

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is not None:
        cable_state = state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    iec_60287_1_1_ver = install.config.iec_60287_1_1_ver.value
    calc_c_f_iec_value = install.config.calc_c_f_iec.value

    if sheath_screen_resistance is None and sheath_screen_temperature is None:
        raise IEC60287Exception('trying to calculate C_F but neither metal sheath/screen temperature or resistance '
                                'has been given')

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.6'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.5'
    elif iec_60287_1_1_ver in [iec.CIGRE_TB880_2022]:
        source = 'CIGRE TB 880 2022 Guidance Point 6 & 31'
    else:
        raise IEC60287Exception(f'trying to calculate C_F (IEC 60287-1-1 ED3 Section 5.3.6) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    kp = iec60287support.get_q_parameter(cable.conductor.kp, log=log)
    if kp is None:
        kp = find_kp(cable, log=log).get_value2(unit='')

    if kp > 0.5 and calc_c_f_iec_value:
        c_f = 0.0
    else:
        if sheath_screen_resistance is None:
            rs = iec60287support.calc_sheath_screen_resistance(cable, sheath_screen_temperature,
                                                               ignore_csw_tape=True,
                                                               iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                               state=cable_state, log=log).get_value2(unit='Ω/m')
        else:
            rs = sheath_screen_resistance

        if rs == math.inf:
            c_f = 0.0
            if log is not None:
                log.add_line('metal sheath/screen has zero eddy current losses', 0.0,
                             unit='', source="missing from IEC")
        else:
            number_cores = cable.number_cores.get_value('', log=log)
            if number_cores == iec.SINGLE_CORE:
                number_cables = cable_set.find_no_cables(log=log)
                if number_cables == 1:
                    raise IEC60287Exception('trying to calculate C_F for one single core cable')
                elif number_cables == 2:
                    c_m1 = calc_cm1_s5_3_6a(cable_set, cable_num,
                                            sheath_screen_temperature=sheath_screen_temperature,
                                            sheath_screen_resistance=sheath_screen_resistance,
                                            iec_60287_1_1_ver=iec_60287_1_1_ver,
                                            state=state, log=log)
                    c_n = calc_cn_s5_3_6a(cable_set, cable_num,
                                          sheath_screen_temperature=sheath_screen_temperature,
                                          sheath_screen_resistance=sheath_screen_resistance,
                                          iec_60287_1_1_ver=iec_60287_1_1_ver,
                                          state=state, log=log).get_value2(unit='Ω/m')
                elif number_cables == 3:
                    formation = iec60287support.calc_cable_formation(cable_set, log=log)
                    if formation == iec.TREFOIL:
                        c_m1 = calc_cm1_s5_3_6a(cable_set, cable_num,
                                                sheath_screen_temperature=sheath_screen_temperature,
                                                sheath_screen_resistance=sheath_screen_resistance,
                                                iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                state=state, log=log)
                        c_n = calc_cn_s5_3_6a(cable_set, cable_num,
                                              sheath_screen_temperature=sheath_screen_temperature,
                                              sheath_screen_resistance=sheath_screen_resistance,
                                              iec_60287_1_1_ver=iec_60287_1_1_ver,
                                              state=state, log=log).get_value2(unit='Ω/m')
                    elif formation == iec.FLAT:
                        c_m1 = calc_cm1_s5_3_6b(cable_set, cable_num,
                                                sheath_screen_temperature=sheath_screen_temperature,
                                                sheath_screen_resistance=sheath_screen_resistance,
                                                iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                state=state, log=log)
                        c_n = calc_cn_s5_3_6b(cable_set, cable_num,
                                              sheath_screen_temperature=sheath_screen_temperature,
                                              sheath_screen_resistance=sheath_screen_resistance,
                                              iec_60287_1_1_ver=iec_60287_1_1_ver,
                                              state=state, log=log).get_value2(unit='Ω/m')
                    else:
                        raise IEC60287Exception(f'trying to calculate C_F but cable formation is {formation}')
                else:
                    raise IEC60287Exception(f'trying to calculate C_F for single core cables but number of '
                                            f'cables {number_cables}')
            elif number_cores == iec.THREE_CORE:
                raise IEC60287Exception(f'trying to calculate C_F for three core cable')
            else:
                raise IEC60287Exception(f'trying to calculate C_F for cable with {number_cores}')
            c_f = ((4 * c_m1.value ** 2 * c_n ** 2 + (c_m1.value + c_n) ** 2) /
                   (4 * (c_m1.value ** 2 + 1) * (c_n ** 2 + 1)))

    return QFloat(c_f, '', f'{source}, C_F',
                  description='proportion of eddy current losses C_F', symbol='C_F')


@LogSection('C_M1 (trefoil)')
def calc_cm1_s5_3_6a(cable_set: CableSet, cable_num: int,
                     sheath_screen_temperature: float = None,
                     sheath_screen_resistance: float = None,
                     iec_60287_1_1_ver: str = None,
                     state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate C_M1 for trefoil cables

    IEC 60287-1-1 only includes 3 single core cables in trefoil but this is extended to 2 single core cables or a
    three core cable with separate sheaths.

    Calculate C_M1, see IEC 60287-1-1 Section 5.3.6.

    :param cable_set: cable set containing the cable
    :param cable_num: cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param sheath_screen_resistance: metal sheath / screen resistance (ohm)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: C_M1
    """

    if sheath_screen_resistance is None and sheath_screen_temperature is None:
        raise IEC60287Exception('trying to calculate C_F but neither metal sheath/screen temperature or resistance '
                                'has been given')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is not None:
        cable_state = state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.6'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.5'
    else:
        raise IEC60287Exception(f'trying to calculate C_M1 trefoil (IEC 60287-1-1 ED3 Section 5.3.6) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    x = calc_x_5_3_2(cable_set, cable_num, state=state, log=log).get_value2(unit='Ω/m')

    if sheath_screen_resistance is None:
        rs = iec60287support.calc_sheath_screen_resistance(cable, sheath_screen_temperature,
                                                           ignore_csw_tape=True,
                                                           iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                           state=cable_state, log=log).value
    else:
        rs = sheath_screen_resistance

    c_m1 = rs / x
    return QFloat(c_m1, '', f'{source}, C_M1 trefoil',
                  description='C_M1 for trefoil cables', symbol='C_M1')


@LogSection('C_N (trefoil)')
def calc_cn_s5_3_6a(cable_set: CableSet, cable_num: int,
                    sheath_screen_temperature: float = None,
                    sheath_screen_resistance: float = None,
                    iec_60287_1_1_ver: str = None,
                    state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate C_N for trefoil cables

    IEC 60287-1-1 only includes 3 single core cables in trefoil but this is extended to 2 single core cables or a
    three core cable with separate sheaths.

    Calculate C_N, see IEC 60287-1-1 Section 5.3.6.

    :param cable_set: cable set containing the cable
    :param cable_num: cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param sheath_screen_resistance: metal sheath / screen resistance (ohm)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: C_N
    """

    if sheath_screen_resistance is None and sheath_screen_temperature is None:
        raise IEC60287Exception('trying to calculate C_F but neither metal sheath/screen temperature or resistance '
                                'has been given')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is not None:
        cable_state = state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.6'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.5'
    else:
        raise IEC60287Exception(f'trying to calculate C_N trefoil (IEC 60287-1-1 ED3 Section 5.3.6) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    x = calc_x_5_3_2(cable_set, cable_num, state=state, log=log).get_value2(unit='Ω/m')

    if sheath_screen_resistance is None:
        rs = iec60287support.calc_sheath_screen_resistance(cable, sheath_screen_temperature,
                                                           ignore_csw_tape=True,
                                                           iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                           state=cable_state, log=log).value
    else:
        rs = sheath_screen_resistance

    c_n = rs / x
    return QFloat(c_n, '', f'{source}, C_N trefoil',
                  description='C_N for trefoil cables', symbol='C_N')


@LogSection('C_M1 (flat)')
def calc_cm1_s5_3_6b(cable_set: CableSet, cable_num: int,
                     sheath_screen_temperature: float = None,
                     sheath_screen_resistance: float = None,
                     iec_60287_1_1_ver: str = None,
                     state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate C_M1 for flat cables

    Calculate C_M1, see IEC 60287-1-1 Section 3.3.6.

    :param cable_set: cable set containing the cable
    :param cable_num: cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param sheath_screen_resistance: metal sheath / screen resistance (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: C_M1
    """

    if sheath_screen_resistance is None and sheath_screen_resistance is None:
        raise IEC60287Exception('trying to calculate C_F but neither metal sheath/screen temperature or resistance '
                                'has been given')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is not None:
        cable_state = state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.6'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.5'
    else:
        raise IEC60287Exception(f'trying to calculate C_M1 flat (IEC 60287-1-1 ED3 Section 5.3.6) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    x = calc_x_5_3_4(cable_set, cable_num, iec_60287_1_1_ver=iec_60287_1_1_ver, state=state, log=log)
    xm = calc_xm_5_3_4(cable_set, iec_60287_1_1_ver=iec_60287_1_1_ver, state=state, log=log).get_value2(unit='Ω/m')

    if sheath_screen_resistance is None:
        rs = iec60287support.calc_sheath_screen_resistance(cable, sheath_screen_temperature,
                                                           ignore_csw_tape=True,
                                                           iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                           state=cable_state, log=log)
    else:
        rs = sheath_screen_resistance

    c_m1 = rs.value / (x.value + xm)
    return QFloat(c_m1, '', f'{source}, C_M1 flat',
                  description='C_M1 for flat cables', symbol='C_M1')


@LogSection('C_N (flat)')
def calc_cn_s5_3_6b(cable_set: CableSet, cable_num: int,
                    sheath_screen_temperature: float = None,
                    sheath_screen_resistance: float = None,
                    iec_60287_1_1_ver: str = None,
                    state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate C_N for flat cables

    Calculate C_N, see IEC 60287-1-1 Section 5.3.6.

    :param cable_set: cable set containing the cable
    :param cable_num: cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param sheath_screen_resistance: metal sheath / screen temperature (ohm)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: C_N
    """

    if sheath_screen_resistance is None and sheath_screen_resistance is None:
        raise IEC60287Exception('trying to calculate C_F but neither metal sheath/screen temperature or resistance '
                                'has been given')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is not None:
        cable_state = state.placed_cable_states[cable_num].cable_state
    else:
        cable_state = None

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.6'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.5'
    else:
        raise IEC60287Exception(f'trying to calculate C_N flat (IEC 60287-1-1 ED3 Section 5.3.6) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    x = calc_x_5_3_4(cable_set, cable_num, iec_60287_1_1_ver=iec_60287_1_1_ver, state=state, log=log)
    xm = calc_xm_5_3_4(cable_set, iec_60287_1_1_ver=iec_60287_1_1_ver, state=state, log=log)

    if sheath_screen_resistance is None:
        rs = iec60287support.calc_sheath_screen_resistance(cable, sheath_screen_temperature,
                                                           ignore_csw_tape=True,
                                                           iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                           state=cable_state, log=log)
    else:
        rs = sheath_screen_resistance

    c_n = rs.value / (x.value - xm.value / 3)
    return QFloat(c_n, '', f'{source}, C_N trefoil',
                  description='C_N for trefoil cables', symbol='C_N')


@UseState("lambda_1_dash_dash", level=cabsys.data_classes.state_cct.CABLE)
@LogSection("λ_1''")
def calc_lambda1_dash_dash_5_3_7_1(install: Install, circuit_num: int, cable_set_num: int, cable_num: int,
                                   conductor_temperature: float,
                                   sheath_screen_temperature: float,
                                   state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate sheath loss factor due to eddy currents

    see IEC 60287-1-1 Section 5.3.7.1.

    :param install: installation containing cable being considered
    :param circuit_num: circuit number being considered
    :param cable_set_num: cable_set number containing the cable
    :param cable_num: cable number in the cable_set
    :param conductor_temperature: temperature of the conductor
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: sheath loss factor due to eddy currents
    """

    cable_set = install.install_circuits[circuit_num].cable_sets[cable_set_num]
    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if state is not None:
        install_circuit_state = state.install_circuit_states[circuit_num]
        cable_set_state = install_circuit_state.cable_set_states[cable_set_num]
        cable_state = cable_set_state.placed_cable_states[cable_num].cable_state
    else:
        cable_set_state = None
        cable_state = None

    iec_60287_1_1_ver = install.config.iec_60287_1_1_ver.get_value(unit='', log=log)
    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.7.1'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.6.1'
    else:
        raise IEC60287Exception(f'trying to calculate lambda1'' (IEC 60287-1-1 ED3 Section 5.3.7.1) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    foil_eddy_loss_rt = install.config.foil_eddy_loss_rt.get_value(unit='mm', log=log)
    if (cable.sheath.material.get_value(unit='', log=log) != iec.NONE and
            cable.sheath.thickness.get_value(unit='mm', log=log) >= foil_eddy_loss_rt):
        r_s = iec60287support.calc_sheath_screen_resistance(cable, sheath_screen_temperature,
                                                            ignore_csw_tape=True,
                                                            iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                            state=cable_state, log=log)
        r_c = calc_r_ac(cable_set, cable_num, conductor_temperature,
                        iec_60287_1_1_ver=iec_60287_1_1_ver,
                        state=cable_set_state, log=log)
        always_calc_c_gs = install.config.always_calc_c_gs.get_value(unit='', log=log)
        c_gs = calc_cgs_5_3_7_1(cable_set, cable_num, sheath_screen_temperature,
                                always_calc_c_gs=always_calc_c_gs, state=cable_set_state, log=log)
        lambda0 = calc_lambda0_5_3_7_1(cable_set, cable_num, sheath_screen_temperature,
                                       iec_60287_1_1_ver=iec_60287_1_1_ver,
                                       state=cable_set_state, log=log)
        always_calc_delta = install.config.always_calc_delta.get_value(unit='', log=log)
        delta1 = calc_delta1_5_3_7_1(cable_set, cable_num, sheath_screen_temperature,
                                     always_calc_delta=always_calc_delta,
                                     iec_60287_1_1_ver=iec_60287_1_1_ver,
                                     state=cable_set_state, log=log)
        delta2 = calc_delta2_5_3_7_1(cable_set, cable_num, sheath_screen_temperature,
                                     always_calc_delta=always_calc_delta,
                                     iec_60287_1_1_ver=iec_60287_1_1_ver,
                                     state=cable_set_state, log=log)

        beta1 = None
        if not always_calc_c_gs:
            sheath_material = cable.sheath.material.get_value(unit='', log=log)
            if sheath_material == iec.LEAD:
                beta1 = 0.0
                if log is not None:
                    log.add_line('beta1', 0.0, '', 'IEC 60287-1-1, Section 5.3.7.1 lead sheath')
        if beta1 is None:
            beta1 = calc_beta1_5_3_7_1(cable_set, cable_num, sheath_screen_temperature,
                                       iec_60287_1_1_ver=iec_60287_1_1_ver,
                                       state=cable_set_state, log=log).value

        ts = cable.sheath.thickness.get_value('mm', log=log)

        lambda1_dash_dash = (r_s.value / r_c.value * (c_gs.value * lambda0.value * (1 + delta1.value + delta2.value) +
                             (beta1 * ts) ** 4 / (12 * 10 ** 12)))
    else:
        # copper wire screen or tape does not have any eddy current losses
        log.add_line("λ_1''", 0.0, '', 'IEC 60287-1-1, Section 5.3.7.1 wire screen, tape, foil -> λ_1'' negligible')
        lambda1_dash_dash = 0.0

    return QFloat(lambda1_dash_dash, '', f"{source} lambda1''",
                  description='eddy current sheath loss', symbol="λ_1''")


@LogSection('C_gs')
def calc_cgs_5_3_7_1(cable_set: CableSet, cable_num: int,
                     sheath_screen_temperature: float = None,
                     always_calc_c_gs: bool = True,
                     iec_60287_1_1_ver: str = None,
                     state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate C_gs (factor used for specially bonded sheath loss factor)

    see IEC 60287-1-1 Section 5.3.7.1.

    :param cable_set: the cable set containing the cable
    :param cable_num: the cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param always_calc_c_gs: if set True, C_gs is always calculated even if IEC allows it to be 1.0
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: C_gs
    """

    # does nothing but put in to stop Pycharm from complaining (note may be right in this case)
    if state:
        pass

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.7.1'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.6.1'
    else:
        raise IEC60287Exception(f'trying to calculate C_gs (IEC 60287-1-1 ED3 Section 5.3.7.1) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    if not always_calc_c_gs:
        sheath_material = cable.sheath.material.get_value(unit='', log=log)
        if sheath_material == iec.LEAD:
            c_gs = 1.0
            if log is not None:
                log.add_line('C_gs', 1.0, '', 'IEC 60287-1-1, Section 5.3.7.1 lead sheath')
        elif sheath_material == iec.ALUMINIUM:
            if (cable.sheath.dia.get_value(unit='mm', log=log) < 70.0 and
                    cable.sheath.thickness.get_value(unit='mm', log=log) < 2.0):
                c_gs = 1.0
                if log is not None:
                    log.add_line('C_gs', 1.0, '', 'IEC 60287-1-1, Section 5.3.7.1 small Al sheath')
            else:
                c_gs = None
        else:
            c_gs = None
    else:
        c_gs = None

    if c_gs is None:
        ts = iec60287support.calc_sheath_screen_thickness(cable, ignore_csw_tape=True,
                                                          log=log).get_value2(unit='mm')
        d_s = iec60287support.calc_sheath_diameter(cable, log=log).get_value2(unit='mm')
        beta1 = calc_beta1_5_3_7_1(cable_set, cable_num, sheath_screen_temperature,
                                   iec_60287_1_1_ver=iec_60287_1_1_ver,
                                   log=log).value
        c_gs = 1 + (ts / d_s) ** 1.74 * (beta1 * d_s * 10 ** -3 - 1.6)

    return QFloat(c_gs, '', f'{source} C_gs',
                  description='C_gs factor to calculate eddy current sheath loss', symbol='C_gs')


@LogSection('β1')
def calc_beta1_5_3_7_1(cable_set: CableSet, cable_num: int,
                       sheath_screen_temperature: float = None,
                       iec_60287_1_1_ver: str = None,
                       state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate beta1 (factor used for specially bonded sheath loss factor)

    see IEC 60287-1-1 Section 5.3.7.1.

    :param cable_set: the cable set containing the cable
    :param cable_num: the cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: beta1
    """

    # does nothing but stops Pycharm complaining (maybe right in this case)
    if state:
        pass

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.7.1'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.6.1'
    else:
        raise IEC60287Exception(f'trying to calculate beta1 (IEC 60287-1-1 ED3 Section 5.3.7.1) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    f = cable_set.f.get_value('Hz', log=log)
    rho_s = iec60287support.calc_sheath_screen_resistivity(cable, sheath_screen_temperature,
                                                           log=log)

    beta1 = math.sqrt(4 * math.pi * 2 * math.pi * f / (10 ** 7 * rho_s.value))

    return QFloat(beta1, '', f'{source}, beta1',
                  description='factor to calculated specially bonded sheath loss', symbol='β1')


@LogSection('m')
def calc_m_5_3_7_1(cable_set: CableSet, cable_num: int,
                   sheath_screen_temperature: float = None,
                   iec_60287_1_1_ver: str = None,
                   state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate m (factor used for specially bonded sheath loss factor)

    see IEC 60287-1-1 Section 5.3.7.1.

    :param cable_set: the cable set containing the cable
    :param cable_num: the cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: m
    """

    # does nothing but stops Pycharm linter complaining (Pycharm maybe right in this case though)
    if state:
        pass

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.7.1'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.6.1'
    else:
        raise IEC60287Exception(f'trying to calculate m (IEC 60287-1-1 ED3 Section 5.3.7.1) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    f = cable_set.f.get_value('Hz', log=log)
    # note that for rho_s the state argument is not passed on purpose
    rho_s = iec60287support.calc_sheath_screen_resistance(cable, sheath_screen_temperature,
                                                          ignore_csw_tape=True,
                                                          iec_60287_1_1_ver=iec_60287_1_1_ver,
                                                          log=log)

    m = 2 * math.pi * f / rho_s.value * 10 ** -7

    return QFloat(m, '', f'{source}, m',
                  description='factor to calculated specially bonded sheath loss', symbol='m')


@LogSection('λ_0')
def calc_lambda0_5_3_7_1(cable_set: CableSet, cable_num: int,
                         sheath_screen_temperature: float = None,
                         iec_60287_1_1_ver: str = None,
                         state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate lambda0 (factor used for specially bonded sheath loss factor)

    see IEC 60287-1-1 Section 5.3.7.1

    :param cable_set: cable set containing the cable
    :param cable_num: cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: lambda0
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.7.1'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.6.1'
    else:
        raise IEC60287Exception(f'trying to calculate lambda0 (IEC 60287-1-1 ED3 Section 5.3.7.1) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    cable = cable_set.placed_cables[cable_num].cable
    if cable is None:
        raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

    m = calc_m_5_3_7_1(cable_set, cable_num, sheath_screen_temperature,
                       iec_60287_1_1_ver=iec_60287_1_1_ver,
                       state=state, log=log)
    d = iec60287support.calc_sheath_screen_mean_diameter(cable, ignore_csw_tape=True, log=log)
    s = iec60287support.calc_cable_spacing(cable_set, log=log)

    number_cores = cable.number_cores.get_value('', log=log)
    if number_cores == iec.SINGLE_CORE:
        number_cables = cable_set.find_no_cables(log=log)
        formation = iec60287support.calc_cable_formation(cable_set, log=log)
        if number_cables == 3:
            if formation == iec.TREFOIL:
                source = source + '-1'
                lambda0 = 3 * (m.value ** 2 / (1 + m.value ** 2)) * (d.value / (2 * s)) ** 2
            elif formation == iec.FLAT:
                phase = iec60287support.calc_cable_phase_wrt_centre(cable_set, cable_num, state=state, log=log)
                if phase.value == iec.YELLOW:
                    source = source + '-2a'
                    lambda0 = 6 * (m.value ** 2 / (1 + m.value ** 2)) * (d.value / (2 * s)) ** 2
                elif phase.value == iec.RED:
                    source = source + '-2b'
                    lambda0 = 1.5 * (m.value ** 2 / (1 + m.value ** 2)) * (d.value / (2 * s)) ** 2
                elif phase.value == iec.BLUE:
                    source = source + '-2c'
                    lambda0 = 1.5 * (m.value ** 2 / (1 + m.value ** 2)) * (d.value / (2 * s)) ** 2
                else:
                    raise IEC60287Exception(f'calculating lambda0 but phase "{phase}" not recognised')
            else:
                raise IEC60287Exception(f'calculating lambda0 but formation "{formation}" not implemented')
        else:
            raise IEC60287Exception(f'calculating lambda0 but found {number_cables} cables and'
                                    f'only 3 cables can be calculated')
    else:
        raise IEC60287Exception(f'calculating lambda0 but cable is "{number_cores}" type '
                                f'and not single core cables')

    return QFloat(lambda0, '', f'{source}',
                  description='factor to calculated specially bonded sheath loss', symbol='λ_0')


@LogSection('Δ_1')
def calc_delta1_5_3_7_1(cable_set: CableSet, cable_num: int,
                        sheath_screen_temperature: float = None,
                        always_calc_delta: bool = True,
                        iec_60287_1_1_ver: str = None,
                        state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate delta1 (factor used for specially bonded sheath loss factor)

    IEC allows delta_1 to be neglected if m < 0.1. The default is to always calculate delta_1 but setting the argument
    always_calc_delta allows delta_1 to be set to 0 if m < 0.1.

    see IEC 60287-1-1 Section 5.3.7.1

    :param cable_set: the cable set containing the cable
    :param cable_num: the cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param always_calc_delta: always calc delta even if IEC allows it to be neglected
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: delta1
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.7.1'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.6.1'
    else:
        raise IEC60287Exception(f'trying to calculate delta1 (IEC 60287-1-1 ED3 Section 5.3.7.1) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    m = calc_m_5_3_7_1(cable_set, cable_num, sheath_screen_temperature,
                       iec_60287_1_1_ver=iec_60287_1_1_ver,
                       state=state, log=log)
    if not always_calc_delta and m.value <= 0.1:
        delta1 = 0.0
        if log is not None:
            log.add_line('Δ_1', 0.0, '', f'{source}, m < 0.1')
    else:
        cable = cable_set.placed_cables[cable_num].cable
        if cable is None:
            raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

        d = iec60287support.calc_sheath_screen_mean_diameter(cable, ignore_csw_tape=True, log=log)
        s = iec60287support.calc_cable_spacing(cable_set, log=log)

        number_cores = cable.number_cores.get_value('', log=log)
        if number_cores == iec.SINGLE_CORE:
            number_cables = cable_set.find_no_cables(log=log)
            formation = iec60287support.calc_cable_formation(cable_set, log=log)
            if number_cables == 3:
                if formation == iec.TREFOIL:
                    source = source + '-1'
                    delta1 = (1.14 * m.value ** 2.45 + 0.33) * (d.value / (2 * s)) ** (0.92 * m.value + 1.66)
                elif formation == iec.FLAT:
                    phase = iec60287support.calc_cable_phase_wrt_centre(cable_set, cable_num, state=state, log=log)
                    if phase.value == iec.YELLOW:
                        source = source + '-2a'
                        delta1 = 0.86 * m.value ** 3.08 * (d.value / (2 * s)) ** (1.4 * m.value + 0.7)
                    elif phase.value == iec.RED:
                        source = source + '-2b'
                        delta1 = 4.7 * m.value ** 0.7 * (d.value / (2 * s)) ** (0.16 * m.value + 2.0)
                    elif phase.value == iec.BLUE:
                        source = source + '-2c'
                        delta1 = (-(0.74 * (m.value + 2.0) * m.value ** 0.5) / (2 + (m.value - 0.3) ** 2.0) *
                                  (d.value / (2 * s)) ** (m.value + 1.0))
                    else:
                        raise IEC60287Exception(f'calculating delta1 but phase "{phase}" not recognised')
                else:
                    raise IEC60287Exception(f'calculating delta1 but formation "{formation}" not implemented')
            else:
                raise IEC60287Exception(f'calculating delta1 but found {number_cables} cables and'
                                        f'only 3 cables can be calculated')
        else:
            raise IEC60287Exception(f'calculating delta1 but cable is "{number_cores}" type '
                                    f'and not single core cables')

    return QFloat(delta1, '', f'{source}',
                  description='factor to calculated specially bonded sheath loss', symbol='Δ_1')


@LogSection('Δ_2')
def calc_delta2_5_3_7_1(cable_set: CableSet, cable_num: int,
                        sheath_screen_temperature: float = None,
                        always_calc_delta: bool = True,
                        iec_60287_1_1_ver: str = None,
                        state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate delta1 (factor used for specially bonded sheath loss factor trefoil formation)

    IEC allows delta_1 to be neglected if m < 0.1. The default is to always calculate delta_1 but setting the argument
    always_calc_delta allows delta_1 to be set to 0 if m < 0.1.

    see IEC 60287-1-1 Section 5.3.7.1

    :param cable_set: the cable set containing the cable
    :param cable_num:  the cable number in the cable_set
    :param sheath_screen_temperature: metal sheath / screen temperature (°C)
    :param always_calc_delta: always calc delta even if IEC allows it to be neglected
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: delta1
    """

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.7.1'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.6.1'
    else:
        raise IEC60287Exception(f'trying to calculate delta2 (IEC 60287-1-1 ED3 Section 5.3.7.1) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    m = calc_m_5_3_7_1(cable_set, cable_num, sheath_screen_temperature,
                       iec_60287_1_1_ver=iec_60287_1_1_ver,
                       state=state, log=log)
    if not always_calc_delta and m.value <= 0.1:
        delta2 = 0.0
        if log is not None:
            log.add_line('Δ_2', 0.0, '', f'{source}, m < 0.1')
    else:
        cable = cable_set.placed_cables[cable_num].cable
        if cable is None:
            raise IEC60287Exception(f'cable in cable set {cable_num} is set to None')

        d = iec60287support.calc_sheath_screen_mean_diameter(cable, ignore_csw_tape=True, log=log)
        s = iec60287support.calc_cable_spacing(cable_set, log=log)

        number_cores = cable.number_cores.get_value('', log=log)
        if number_cores == iec.SINGLE_CORE:
            number_cables = cable_set.find_no_cables(log=log)
            formation = iec60287support.calc_cable_formation(cable_set, log=log)
            if number_cables == 3:
                if formation == iec.TREFOIL:
                    source = source + '-1'
                    delta2 = 0.0
                elif formation == iec.FLAT:
                    phase = iec60287support.calc_cable_phase_wrt_centre(cable_set, cable_num, state=state, log=log)
                    if phase.value == iec.YELLOW:
                        source = source + '-2a'
                        delta2 = 0.0
                    elif phase.value == iec.RED:
                        source = source + '-2b'
                        delta2 = 21 * m.value ** 3.3 * (d.value / (2 * s)) ** (1.47 * m.value + 5.06)
                    elif phase.value == iec.BLUE:
                        source = source + '-2c'
                        delta2 = 0.92 * m.value ** 3.7 * (d.value / (2 * s)) ** (m.value + 2.0)
                    else:
                        raise IEC60287Exception(f'calculating delta2 but phase "{phase}" not recognised')
                else:
                    raise IEC60287Exception(f'calculating delta2 but formation "{formation}" not implemented')
            else:
                raise IEC60287Exception(f'calculating delta2 but found {number_cables} cables and'
                                        f'only 3 cables can be calculated')
        else:
            raise IEC60287Exception(f'calculating delta2 but cable is "{number_cores}" type '
                                    f'and not single core cables')

    return QFloat(delta2, '', f'{source}',
                  description='factor to calculated specially bonded sheath loss', symbol='Δ_2')


@UseState('rcc', level=cabsys.data_classes.state_cct.CABLE_SET)
@LogSection('rcc')
def calc_rcc_5_3_7_2(cable_set: CableSet,
                     iec_60287_1_1_ver: str = None,
                     state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate residual circulating current (cross bonded unbalanced cables)

    see IEC 60287-1-1 Section 5.3.7.2.

    :param cable_set: the cable set containing the cable
    :param iec_60287_1_1_ver: version of IEC 60287-1-1 to be used
    :param state: object holding results relating to cables
    :param log: logger used to store results
    :return: residual circulating current
    """

    # not needed but stops PyCharms complaining that state is not used (it is but in the UseState decorator)
    if state:
        pass

    if iec_60287_1_1_ver in [None, iec.IEC60287_1_1_ED3, iec.IEC60287_1_1_ED3_STRICT]:
        source = 'IEC 60287-1-1 ED3 Section 5.3.7.2'
    elif iec_60287_1_1_ver in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-1-1 ED2 Section 2.3.6.2'
    else:
        raise IEC60287Exception(f'trying to calculate rcc (IEC 60287-1-1 ED3 Section 5.3.7.2) but'
                                f' IEC 60287-1-1 version "{iec_60287_1_1_ver}" in install config'
                                f' not recognised')

    length1 = cable_set.length1.get_value2('m', log=log)
    length2 = cable_set.length2.get_value2('m', log=log)
    length3 = cable_set.length3.get_value2('m', log=log)

    shortest_length = min(length1, length2, length3)

    len1 = length1 / shortest_length
    len2 = length2 / shortest_length
    len3 = length3 / shortest_length

    if len1 == 1.0:
        if log is not None:
            log.add_line('C_p', len2, '', '')
            log.add_line('C_q', len3, '', '')
        rcc = calc_rcc_2_5_3_7_2(len2, len3)
    elif len2 == 1.0:
        if log is not None:
            log.add_line('C_p', len1, '', '')
            log.add_line('C_q', len3, '', '')
        rcc = calc_rcc_2_5_3_7_2(len1, len3)
    elif len3 == 1.0:
        if log is not None:
            log.add_line('C_p', len1, '', '')
            log.add_line('C_q', len2, '', '')
        rcc = calc_rcc_2_5_3_7_2(len1, len2)
    else:
        raise IEC60287Exception('calculating rcc but did not find shortest length')

    return QFloat(rcc, '', f'{source}, residual circulating current',
                  description='residual circulating current for cross bonded systems', symbol='rcc')


def calc_rcc_2_5_3_7_2(c_p: float, c_q: float) -> float:
    """ Calculate residual circulating current for unbalanced cross bonded cables

    IEC 60287-1-1 clause 5.3.7.2
    p length of one cable as a ratio of the shortest cable
    q length of other cable as a ratio of the shortest cable
    """
    rcc = (c_p ** 2 + c_q ** 2 + 1 - c_p - c_p * c_q - c_q) / (c_p + c_q + 1) ** 2
    return rcc


@UseState('lambda_2', level=cabsys.data_classes.state_cct.CABLE)
@LogSection('λ_2')
def calc_lambda_2(install: Install, circuit_num, cable_set_no: int, cable_no: int,
                  state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the metal sheath/screen loss

    Calculates the metal sheath/screen loss (lambda_1).

    IEC 60287-1-1 clause 5.4: This is undermined by IEC 60287-2-1 clause 4.2.4.2.1 TODO: update clause

    :param install: object containing cable_set
    :param circuit_num: circuit number
    :param cable_set_no: index number of cable set in the install
    :param cable_no: index number of the cable in the cable set
    :param state: install set state, used to get and set other calculations
    :param log: logger used to store results
    :return: metal sheath/screen loss (W/m)
    """

    if state is not None:
        install_circuit_state = state.install_circuit_states[circuit_num]
        cable_set_state = install_circuit_state.cable_set_states[cable_set_no]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        cable_state = cable_set_state.placed_cable_states[cable_no].cable_state
    else:
        cable_state = None

    if cable_state is None:
        pass

    if log is None:
        pass

    # if sheath_temperature is None:
    #     sheath_temperature = cable_state.get_quantity('theta_sc', log=log)
    # else:
    #     cable_state.set_quantity('theta_sc', sheath_temperature,)
    # if sheath_temperature is None:
    #     raise IEC60287Exception('calculating sheath/screen loss but sheath temperature not specified')

    cable_set = install.install_circuits[circuit_num].cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    if cable is None:
        pass

    lambda2 = 0.0

    return QFloat(lambda2, '', 'IEC 60287-1-1 Section 5.4 sheath/screen loss factor',
                  description='sheath/screen loss factor', symbol='λ_2')


# TODO: rest of spec

# IEC 60287-1-1 Table 1 Resistivity
cond_resistivity = {iec.COPPER: (1.7241e-8, 3.93e-3),
                    iec.ALUMINIUM: (2.8264e-8, 4.03e-3)}

sheath_resistivity = {iec.COPPER: (1.7241e-8, 3.93e-3),  # <- this is added as copper may be used
                      iec.LEAD: (21.4e-8, 4.0e-3),
                      iec.STEEL: (13.8e-8, 4.5e-3),
                      iec.BRONZE: (3.5e-8, 3.0e-3),
                      iec.STAINLESS_STEEL: (70e-8, 0.0),
                      iec.ALUMINIUM: (2.84e-8, 4.03e-3)}


@LogSection('ρ')
def find_rho(conductor: CableConductor, log: Log = None) -> QFloat:
    """Find dc resistivity at 20°C from IEC 60287-1-1 Table 1 for a cable conductor

    :param conductor: conductor of the cable
    :param log: calculation log
    :return: dc resistance of cable conductor at 20 °C (Ω/m)
    """

    cond_mat = conductor.material.get_value(unit='', log=log)
    rho = cond_resistivity[cond_mat][0]
    if log is not None:
        log.add_line('ρ', rho, 'Ω/m', 'IEC 60287-1-1 Table 1')
    return QFloat(rho, 'Ω/m', 'IEC 60287-1-1 Table 1',
                  description='dc resistivity at 20°C', symbol='ρ')


# repeated in test_iec60287support.py otherwise imports would not work
@LogSection('ρ_sheath')
def find_rho_sheath(material: str, log: Log = None) -> QFloat:
    """Find dc resistivity at 20°C from IEC 60287-1-1 Table 1 for a cable sheath

    :param material: material
    :param log: calculation log
    :return: dc resistance of cable conductor at 20 °C (Ω/m)
    """

    rho = sheath_resistivity[material][0]
    if log is not None:
        log.add_line('ρ_sheath', rho, 'Ω/m', 'IEC 60287-1-1 Table 1')
    return QFloat(rho, 'Ω/m', 'IEC 60287-1-1 Table 1',
                  description='dc resistivity at 20°C', symbol='ρ_sheath')


@LogSection('α₂₀')
def find_alpha20(cable: Cable, log: Log = None) -> QFloat:
    """Find dc coefficient of resistance at 20°C from IEC 60287-1-1 Table 1 for a cable conductor

    :param cable: cable with conductor
    :param log: calculation log
    :return: coefficient of resistance of cable conductor at 20 °C (1/K)
    """

    cond_mat = cable.conductor.material.get_value(unit='', log=log)
    alpha20 = cond_resistivity[cond_mat][1]
    alpha20ref = 'IEC 60287-1-1 Table 1'
    if log is not None:
        log.add_line('α₂₀', alpha20, '1/°C', alpha20ref)
    return QFloat(alpha20, '1/°C', alpha20ref,
                  description='dc coefficient of resistance at 20°C', symbol='α₂₀')


# repeated in test_iec60287support.py otherwise imports would not work
@LogSection('α₂₀_sheath')
def find_alpha20_sheath(material: str, log: Log = None) -> QFloat:
    """Find dc coefficient of resistance at 20°C from IEC 60287-1-1 Table 1 for a cable sheath

    :param material: sheath material
    :param log: calculation log
    :return: coefficient of resistance of cable sheath at 20 °C (Ω/m)
    """

    alpha20 = sheath_resistivity[material][1]
    alpha20ref = 'IEC 60287-1-1 Table 1'
    if log is not None:
        log.add_line('α₂₀_sheath', alpha20, '1/°C', alpha20ref)
    return QFloat(alpha20, '1/°C', alpha20ref,
                  description='dc coefficient of resistance at 20°C', symbol='α₂₀_sheath')


# IEC 60287-1-1 Table 2 Skin and Proximity co-efficients
ks_kp_factor = {iec.COPPER: {iec.ROUND_SOLID: (1.0, 1.0, iec.CIRCULAR),
                             iec.ROUND_STRANDED_IMPREGNATED: (1.0, 0.8, iec.CIRCULAR),
                             iec.ROUND_STRANDED_EXTRUDED: (1.0, 1.0, iec.CIRCULAR),
                             iec.ROUND_MILLIKEN_IMPREGNATED: (0.435, 0.37, iec.CIRCULAR),
                             iec.ROUND_MILLIKEN_INSULATED_EXTRUDED: (0.35, 0.20, iec.CIRCULAR),
                             iec.ROUND_MILLIKEN_BARE_UNI_EXTRUDED: (0.62, 0.37, iec.CIRCULAR),
                             iec.ROUND_MILLIKEN_BARE_BI_EXTRUDED: (0.80, 0.37, iec.CIRCULAR),
                             iec.HOLLOW_STRANDED_IMPREGNATED: ('a', 0.8, iec.CIRCULAR),
                             iec.HOLLOW_KEYSTONE_IMPREGNATED: ('a', 0.8, iec.CIRCULAR),
                             iec.SECTOR_SHAPED_IMPREGNATED: (1.0, 0.8, iec.SHAPED),
                             iec.SECTOR_SHAPED_EXTRUDED: (1.0, 1.0, iec.SHAPED)},
                iec.ALUMINIUM: {iec.ROUND_SOLID: (1.0, 1.0, iec.CIRCULAR),
                                iec.ROUND_STRANDED_EXTRUDED: (1.0, 0.8, iec.CIRCULAR),
                                iec.ROUND_STRANDED_IMPREGNATED: (1.0, 0.8, iec.CIRCULAR),
                                iec.ROUND_MILLIKEN_IMPREGNATED: (0.25, 0.15, iec.CIRCULAR),
                                iec.ROUND_MILLIKEN_INSULATED_EXTRUDED: (0.25, 0.15, iec.CIRCULAR),
                                iec.ROUND_MILLIKEN_BARE_UNI_EXTRUDED: (0.25, 0.15, iec.CIRCULAR),
                                iec.ROUND_MILLIKEN_BARE_BI_EXTRUDED: (0.25, 0.15, iec.CIRCULAR),
                                iec.HOLLOW_STRANDED_IMPREGNATED: ('a', 0.8, iec.CIRCULAR),
                                iec.HOLLOW_KEYSTONE_IMPREGNATED: ('a', 0.8, iec.CIRCULAR)}}


def ks_ducted(dc_dash, di):
    """Calculate the skin effect factor (ks) for hollow, helical stranded conductors.

    Note: also applicable to keystone conductors

    IEC 60287-1-1 Table 2 note a

    dc_dash   outside diameter of the equivalent solid conductor having the same central duct (mm)
    di        inside diameter of the conductor, central duct (mm)
    """

    ks_part = (dc_dash + 2.0 * di) / (dc_dash + di)
    return (dc_dash - di) / (dc_dash + di) * ks_part**2


@LogSection('k_s')
def find_ks(cable: Cable, log: Log = None) -> QFloat:
    """Get ks from IEC 60287-1-1 Table 2

    :param cable: the cable
    :param log: logging object used to track results
    :return: ks
    """
    cond_mat = cable.conductor.material.get_value(unit='', log=log)
    cond_makeup = cable.conductor.makeup.get_value(unit='', log=log)
    if cond_makeup == iec.OVAL_STRANDED_IMPREGNATED:
        ks = 1.0
        if log is not None:
            log.add_warning('ks oval conductor not included in Table 2 of IEC 60287-1-1')
    else:
        ks = ks_kp_factor[cond_mat][cond_makeup][0]
    if ks == 'a':
        ks = calc_ks_ducted(cable, log=log).value

    return QFloat(ks, '-', 'IEC 60287-1-1 Table 2, skin effect factor',
                  description='skin effect factor', symbol='k_s')


@LogSection('k_s ducted')
def calc_ks_ducted(cable: Cable, log: Log = None) -> QFloat:
    """Calculate the skin effect factor (ks) for hollow, helical stranded conductors

    Also applicable to keystone conductors.

    IEC 60287-1-1 Table 2 note a

    :param cable: cable with helical stranded conductor
    :param log: logger
    :return: ks
    """

    dc_dash = iec60287support.get_q_parameter(cable.conductor.dc_dash_dia, log=log)
    if dc_dash is None:
        dc_dash = calc_dc_dash(cable, log=log).value

    di = cable.conductor.duct_dia.get_value2('mm', log=log)

    ks = ks_ducted(dc_dash, di)
    return QFloat(ks, '-', 'IEC 60287-1-1 Table 2 note a, skin effect for hollow helical stranded conductor',
                  description='skin effect factor', symbol='k_s')


@LogSection("d'_c")
def calc_dc_dash(cable: Cable, log: Log = None) -> QFloat:
    """Calculate the equivalent conductor diameter

    Calculate the equivalent conductor diameter of a solid conductor with the same cross section and duct

    :param cable: cable with helical stranded conductor
    :param log: logger
    :return: equivalent conductor diameter
    """

    compaction = iec60287support.get_q_parameter(cable.conductor.compaction, log=log)
    if compaction is None:
        compaction = calc_compaction(cable, log=log).value

    duct_dia = cable.conductor.duct_dia.get_value(unit='mm', log=log)
    cond_dia = cable.conductor.dia.get_value(unit='mm', log=log)
    conductor_area = math.pi / 4 * (cond_dia ** 2 - duct_dia ** 2)
    equivalent_area = conductor_area * compaction / 100
    dc_dash = math.sqrt(equivalent_area / math.pi * 4 + duct_dia ** 2)

    return QFloat(dc_dash, 'mm', 'no reference',
                  description='equivalent conductor diameter', symbol="d'_c")


@LogSection('compaction')
def calc_compaction(cable: Cable, log: Log = None) -> QFloat:
    """Calculate the compaction of a conductor

    :param cable: cable with helical stranded conductor
    :param log: logger
    :return: compaction
    """
    cond_makeup = cable.conductor.makeup.get_value(unit='', log=log)
    oil_ratio = iec60287support.VOID_CONTENT[cond_makeup]
    compaction = (1 - oil_ratio) * 100

    return QFloat(compaction, '%', 'No reference',
                  description='compaction of cable conductor', symbol='compaction')


@LogSection('k_p')
def find_kp(cable: Cable, log: Log = None) -> QFloat:
    """Get kp from IEC 60287-1-1 Table 2

    :param cable: the cable
    :param log: logging object used to track results
    :return: kp
    """
    cond_mat = cable.conductor.material.get_value(unit='', log=log)
    cond_makeup = cable.conductor.makeup.get_value(unit='', log=log)
    if cond_makeup is None:
        raise IEC60287Exception(f'trying to find kp for cable {cable.name} but cond_makeup is None')
    if cond_makeup == iec.OVAL_STRANDED_IMPREGNATED:
        kp = 0.8
        if log is not None:
            log.add_warning('kp oval conductor not included in Table 2 of IEC 60287-1-1')
    else:
        if cond_mat is None:
            raise IEC60287Exception(f'trying to find kp for cable {cable.name} but cond_mat is None')
        kp = ks_kp_factor[cond_mat][cond_makeup][1]
    return QFloat(kp, '-', 'IEC 60287-1-1 Table 2, proximity effect factor',
                  description='proximity effect factor', symbol='k_p')


# IEC 60287-1-1 Table 3 ***********
#             insulation type: up to voltage, (relative permittivity, tan d)
INSULATION_LOSS_CONST = {iec.INS_PAPER_SOLID: [(9999.1, 4.0, 0.01)],
                         iec.INS_PAPER_SCOF: [(0036.1, 3.6, 0.0035),
                                              (0087.1, 3.6, 0.0033),
                                              (0160.1, 3.5, 0.0030),
                                              (0220.1, 3.5, 0.0028)],
                         iec.INS_PAPER_OF_PIPE: [(9999.1, 3.7, 0.0045)],
                         iec.INS_PAPER_GAS_EXT: [(9999.1, 3.6, 0.0040)],
                         iec.INS_PAPER_GAS_INT_PRE: [(9999.0, 3.6, 0.0040)],
                         iec.INS_BUTYL: [(9999.1, 4.0, 0.0500)],
                         iec.INS_EPR: [(0018.1, 3.0, 0.0200),
                                       (9999.1, 3.0, 0.0050)],
                         iec.INS_PVC: [(9999.1, 8.0, 0.1000)],
                         iec.INS_PE: [(9999.1, 2.3, 0.0010)],
                         iec.INS_XLPE_UNFILLED: [(0018.1, 2.5, 0.0040),
                                                 (9999.1, 2.5, 0.0010)],
                         iec.INS_XLPE_FILLED: [(0018.1, 2.5, 0.0040),
                                               (9999.1, 3.0, 0.0050)],
                         iec.INS_PPL: [(0062.9, None, None),
                                       (9999.1, 2.7, 0.0010)]}


#             insulation type: up to voltage to take account of losses
INSULATION_LOSS_IGNORE = {iec.INS_PAPER_SOLID: 38.0,
                          iec.INS_PAPER_SCOF:  63.5,
                          iec.INS_PAPER_OF_PIPE: 63.5,
                          iec.INS_PAPER_GAS_EXT: 63.5,
                          iec.INS_PAPER_GAS_INT_PRE: 63.5,
                          iec.INS_BUTYL: 18.0,
                          iec.INS_EPR: 63.5,
                          iec.INS_PVC: 6.0,
                          iec.INS_PE: 127.0,
                          iec.INS_XLPE_UNFILLED: 127.0,
                          iec.INS_XLPE_FILLED: 63.5,
                          iec.INS_PPL: 0.0}


@LogSection("ε")
def find_insulation_permittivity(cable: Cable, log: Log = None) -> QFloat:
    """Get the insulation relative permittivity from IEC 60287-1-1 Table 3

    :param cable: the cable with the insulation
    :param log: logger used to store results
    :return: relative permittivity
    """

    ins_mat = cable.core.insulation_material.get_value(unit='', log=log)
    volts = cable.design_volts.get_value(unit='kV', log=log)
    rows = INSULATION_LOSS_CONST[ins_mat]
    e = None
    for row in rows:
        if volts < row[0]:
            e = row[1]
            break
    if e is None:
        raise IEC60287Exception(f'permittivity not found for {ins_mat} with design voltage {volts} V.')

    return QFloat(e, '-', 'IEC 60287-1-1 Table 3',
                  description='insulation relative permittivity', symbol="ε")


@LogSection("tan δ")
def find_insulation_tan_d(cable: Cable, log: Log = None) -> QFloat:
    """Get the insulation tan delta from IEC 60287-1-1 Table 3

    :param cable: the cable with the insulation
    :param log: logger used to store results
    :return: tan delta
    """

    ins_mat = cable.core.insulation_material.get_value(unit='', log=log)
    volts = cable.design_volts.get_value(unit='kV', log=log)
    rows = INSULATION_LOSS_CONST[ins_mat]
    tan_d = None
    for row in rows:
        if volts < row[0]:
            tan_d = row[2]
            break
    if tan_d is None:
        raise IEC60287Exception(f'tan_d not found for {ins_mat} with design voltage {volts} V.')

    return QFloat(tan_d, '-', 'IEC 60287-1-1 Table 3',
                  description='insulation relative permittivity', symbol="tan δ")
