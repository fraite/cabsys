"""Electra 87 equations wrapper.

This module contains wrapper methods for the methods in the electra87  module that implement the equations in Electra 87
"Computer method for the calculation of the response of single-core cables to a step function thermal transient".

The following comments/changes were made with Electra 87:

general:

"""

from typing import Optional, cast, List, Tuple
import math
import time

import numpy as np
import scipy.sparse as sps

import cabsys.data_classes.auto_cable
import cabsys.data_classes.state
import cabsys.quantity.quantity_constants as dc
import cabsys.cigre.cigre_constants as cigre_consts
import cabsys.iec.iec60287_2_1 as iec60287_2_1wrapper
import cabsys.iec.iec60287_1_1 as iec60287_1_1wrapper
import cabsys.iec.iec60287support as iec60287support
import cabsys.iec.iec60853_2
import cabsys.iec.iec60853_2 as iec60853_2
# import cabsys.data_classes.transient_constants as tc
from cabsys.data_classes.install import Install
from cabsys.data_classes.cable import Cable
from cabsys.data_classes.auto_install import AutoInstall
import cabsys.iec.iec_constants as iec
# from cabsys.data_classes.data_store import DataStore
# from cabsys import CableState, CableSetState, InstallState
from cabsys.data_classes.state import InstallState, Elt087State, LayerState, AdjacentCable, UseState
from cabsys.data_classes.state import State
from cabsys.quantity.log import Log, LogSection
from cabsys.quantity.quantity_store import QFloat, QInt, QStr
import cabsys.iec.iec_extra as iec_extra
# import cabsys.data_classes.ds_constants as dc
import cabsys.iec.iec_solver as iec_solver


# Some house-keeping functions for the logger


def log_start_section(log: Log, text: str, source: str, section_log_level: Optional[int] = None):
    if log is not None:
        log.start_section(text, source, section_log_level)


def log_end_section(log: Log, text: str, value: any, unit: str, source: str = ''):
    if log is not None:
        log.end_section(text, value, unit, source)


def log_add_line(log: Log, text: str, value: any, unit: str, source: str = ''):
    if log is not None:
        log.add_line(text, value, unit, source)


def log_add_warning(log: Log, text: str):
    if log is not None:
        log.add_warning(text)


def get_ambient_temperature(install: Install, cable_set_no: int, cable_no: int, log: Log) -> float:
    if install.kind.value == iec.TUNNEL:
        raise Exception('Trying to get ambient temperature for Electra 87 calculation but installation kind is tunnel')
    else:
        theta_a = install.get_ambient_temperature(install.selected_scenario.value, cable_set_no, cable_no,
                                                  unit='°C', log=log)
    return theta_a


# **********************  elt087 runner ******************************

def solve_calc_temperature(install: AutoInstall, selected_scenario_name: str = None, state: InstallState = None,
                           log: Log = None) -> Tuple[str,
                                                     Optional[List[List[float]]],
                                                     Optional[List[List[List[Tuple[float, List]]]]]]:
    """Calculate conductor temperatures for a given installation and set of transient currents

    The transient temperatures are calculated for a given installation. For any cable sets that do not have a fixed
    desired current, the currents will be changed to obtain the maximum possible current for those cable sets.

    :param install: installation
    :param selected_scenario_name: scenario for rating to be calculated
    :param state:
    :param log:
    :return: (current_str: status string,
              install_cond_thetas: cable temperatures °C,
              transient_result: transient results)
    """

    allow_conductor_current_change = False
    for cable_set in install.cable_sets:
        if cable_set.desired_I_change.value:
            allow_conductor_current_change = True

    old_ratio = -1.0
    current_ratio = 1.0
    iteration_number = 0
    start_time = time.perf_counter()
    time_taken = 0.0
    transient_result = None

    while (abs(old_ratio - current_ratio) > 0.0001 and allow_conductor_current_change and
            (time_taken < 1.0 or not install.config.auto_calc.value)):
        # print(old_ratio, current_ratio)
        iteration_number = iteration_number + 1
        if state is not None:
            state.progress = f'Try ratio={round(current_ratio, 3)} (try {iteration_number}). '
        log.start_section('current ratio', source=f'{iteration_number}', section_log_level=70)
        old_ratio = current_ratio
        new_current_ratio, install_cond_temp, transient_result = calc_temperature_iteration(install, old_ratio,
                                                                                            selected_scenario_name,
                                                                                            state=state, log=log)
        if new_current_ratio is None:
            return 'cancelled', None, None
        current_ratio = new_current_ratio if allow_conductor_current_change else 1.0

        log.end_section('current ratio', current_ratio, '', source=f'iteration number = {iteration_number}')
        time_taken = time.perf_counter() - start_time

        if state is not None and state.cancel:
            return 'cancelled', None, None

    if iteration_number > 0:
        log.add_line('number of iterations', iteration_number, '', '')
        log.add_line('time taken', time_taken, 's', '')

    if ((time_taken < 1.0 or not install.config.auto_calc.value) and
            current_ratio > 0.01):
        # repeat last calculation so that it is logged
        start_time = time.perf_counter()
        if state is not None:
            state.progress = f'Ratio={round(current_ratio, 3)}. '
        log.start_section('current ratio', source=f'iteration number = {iteration_number}')
        new_current_ratio, install_cond_temp, transient_result = calc_temperature_iteration(install, old_ratio,
                                                                                            selected_scenario_name,
                                                                                            state=state, log=log)
        if new_current_ratio is None:
            return 'cancelled', None, None
        time_taken = time.perf_counter() - start_time
        log.add_line('time taken', time_taken, 's', '')
        current_ratio = new_current_ratio if allow_conductor_current_change else 1.0
        log.end_section('current ratio', current_ratio, '', source=f'iteration number = {iteration_number}')
        temperature_str = ''
        for cable_set_no, cable_set in enumerate(install.cable_sets):
            theta_max_cct = max(theta for theta in install_cond_temp[cable_set_no])
            if state is not None:
                state.cable_set_states[cable_set_no].set_quantity('theta_max', theta_max_cct, '°C',
                                                                  'maximum conductor temperature of cable set',
                                                                  'calculate temperature solver', symbol='theta_max')
            # log.add_line(f'theta_max cable_set={cable_set_no}', theta_max_cct, '°C', 'calculate temperature solver')
            temperature_str = f'{temperature_str}cable set {cable_set_no}: theta_c max={round(theta_max_cct, 1)} °C '
            if cable_set.current_curve is None:
                current_curve_max = cable_set.desired_I.value
            elif cable_set.current_curve.normalise_curve.value:
                current_curve_max = (cable_set.current_curve.calc_max(calc_transient_end_time(install, log=log)).value *
                                     cable_set.desired_I.value)
            else:
                current_curve_max = cable_set.current_curve.calc_max(calc_transient_end_time(install, log=log)).value
            if cable_set.desired_I_change.value:
                temperature_str = f'{temperature_str} I_peak={round(current_ratio * current_curve_max, 1)} A, '
            else:
                temperature_str = f'{temperature_str} I_peak={round(current_curve_max, 1)} A, '
    elif current_ratio <= 0.1:
        temperature_str = f'Error: ratio too low ({current_ratio}), user set desired rating too high'
        install_cond_temp = None
    else:
        temperature_str = f'Error: iterations took too long, press rate button'
        install_cond_temp = None
        install.config.auto_calc.set_value(False, source=dc.ATTR_COMPUTER_SET)

    if state is not None:
        state.progress = ''

    return temperature_str, install_cond_temp, transient_result


def calc_temperature_iteration(install: AutoInstall, old_ratio: float,
                               selected_scenario_name: str = None,
                               state: InstallState = None,
                               log: Log = None) -> Tuple[Optional[float],
                                                         Optional[List[List[float]]],
                                                         Optional[List[List[List[Tuple[float, List]]]]]]:
    """Calculated the conductor temperature after a transient, and estimates ratio to get maximum conductor temperature

    The next iteration of conductor temperatures is calculated for a given list of conductor currents and a list of old
    conductor temperatures. Additionally the permissible increase in conductor current to give the maximum conductor
    temperature is calculated.

    The conductor currents is given as a list of currents, one value for each cable set in the install object, in the
    same order as the cable sets are found in the install object. The values in the list are multiplied by the old_ratio
    value.

    If no conductor currents are given (by setting install_current to None), the conductor currents are taken from
    the Install.CableSet.desired_I attribute. This value is modified my the old_ratio value so long as the
    Install.CableSet.desired_I_change attribute is set to True. This allows some conductor currents to be fixed, while
    other conductor currents are optimised.

    The old conductor temperatures are given as a nested list. The innermost list is a list of conductor temperatures
    for each cable in a cable_set. The outer list is a list of cable_set conductor temperatures.

    The function returns the newly calculated conductor temperatures following a single iteration, in the same format
    as the old_install_cond_temp.

    The function also returns a new current_ratio, which when multiplied by the conductor currents gives an estimate
    of the maximum conductor currents that can be applied without exceeding maximum conductor temperatures.

    Note: if memorisation is being used, the existing values such as conductor resistance are no longer valid so the
    state object if given is cleared before the calculation starts.

    :param install: installation object
    :param old_ratio: old conductor current ratio
    :param selected_scenario_name: scenario used to calculate the current rating
    :param state: holds results from calculation (warning: any state object passed into function may be cleared)
    :param log: results logger
    :return: current_ratio and list of conductor temperatures
    """

    rating_type = install.get_rating_type(selected_scenario_name)
    if rating_type == iec.RATING_CYCLIC:
        install_cond_temp, transient_result = calc_cyclic_temperature(install, old_ratio, state=state, log=log)
    elif rating_type == iec.RATING_TRANSIENT or rating_type == iec.RATING_EMERGENCY:
        install_cond_temp, transient_result = calc_transient_temperature(install,
                                                                         selected_scenario_name=selected_scenario_name,
                                                                         current_ratio=old_ratio, state=state, log=log)
    else:
        raise Exception(f'calculating transient but "{rating_type}" not recognised')

    if install_cond_temp is None:
        return None, None, None

    new_ratio = math.inf
    for cable_set_no, cable_set in enumerate(install.cable_sets):
        for cable_no, placed_cable in enumerate(cable_set.placed_cables):
            if rating_type == iec.RATING_EMERGENCY and (cable_set.current_curve is None or
                                                        cable_set.current_curve.emergency.value):
                max_cond_temp = iec60287support.get_emergency_cond_temp(placed_cable.cable).get_value(unit='°C')
            else:
                max_cond_temp = iec60287support.get_cond_temp(placed_cable.cable).get_value(unit='°C')
            calc_cond_temp = install_cond_temp[cable_set_no][cable_no]

            # ambient_temp = placed_cable.ambient_theta.get_value(unit='°C')
            ambient_temp = get_ambient_temperature(install, cable_set_no, cable_no, log)
            if calc_cond_temp == ambient_temp:
                new_cable_ratio = math.inf
            else:
                new_cable_ratio = old_ratio * math.sqrt((max_cond_temp - ambient_temp) /
                                                        (calc_cond_temp - ambient_temp))
            new_ratio = min(new_cable_ratio, new_ratio)
    current_ratio = new_ratio

    return current_ratio, install_cond_temp, transient_result


def calc_transient_temperature(install: AutoInstall,
                               selected_scenario_name: str = None,
                               current_ratio: float = 1.0,
                               state: InstallState = None,
                               log: Log = None) -> Tuple[Optional[list], Optional[list]]:

    #    -> Tuple[Optional[List[List[float]]],
    #                                                            Optional[List[List[List[Tuple[float, List]]]]]]:
    """Calculate the cable temperatures for a transient load

    Calculates the initial cable temperatures prior to the transient and then the cable temperatures for the transient
    period defined by Install.end_time

    :param install: cable installation
    :param selected_scenario_name:
    :param current_ratio: multiplier for cable currents allowed to change
    :param state: InstallState
    :param log: logger used to store results
    :return: maximum conductor temperatures reached, or None if calculation canceled
    """

    build_ladders_result = build_ladders(install, state=state, log=log)
    if build_ladders_result is None:
        return None, None

    calc_initial_temperatures(install,
                              selected_scenario_name=selected_scenario_name, current_ratio=current_ratio,
                              state=state, log=log)

    end_time = calc_transient_end_time(install, log=log)
    if end_time is None:
        raise Exception(f'calculating transient but end time of transient in {install.name} is "None"')

    install_cond_temp, transient_result = calc_transient_section_temperature(install, current_ratio,
                                                                             state=state, log=log)
    return install_cond_temp, transient_result


def calc_cyclic_temperature(install: AutoInstall,

                            current_ratio: float = 1.0,
                            state: InstallState = None,
                            log: Log = None) -> Tuple[Optional[list], Optional[list]]:

    #    -> Tuple[Optional[List[List[float]]],
    #                                                            Optional[List[List[List[Tuple[float, List]]]]]]:
    """Calculate the cable temperatures for a cyclic load

    Calculates the cable temperatures for a cyclic load, the cyclic time defined by Install.cyclic_time

    :param install: cable installation
    :param current_ratio: multiplier for cable currents allowed to change
    :param state: InstallState
    :param log: logger used to store results
    :return: maximum conductor temperatures reached, or None if calculation canceled
    """

    progress_prefix = '' if state is None else state.progress

    cycle_time = install.get_cycle_time(install.selected_scenario.value, unit='s')
    if cycle_time <= 0.0:
        raise Exception(f'calculating cyclic rating but install.cycle_time is {cycle_time} s')

    for cable_set in install.cable_sets:
        if cable_set.current_curve is not None and not cable_set.current_curve.cyclic.value:
            raise Exception(f'calculating cyclic rating but transient load curve set')

    for cable_set in install.cable_sets:
        if cable_set.current_curve is not None and cable_set.current_curve.cyclic.value:
            if cycle_time % cable_set.current_curve.cycle_time.value != 0.0:
                raise Exception(f"cyclic times in curves do not match cycle time in install {cycle_time}")

    build_ladders_result = build_ladders(install, state=state, log=log)
    if build_ladders_result is None:
        return None, None

    calc_initial_temperatures(install, current_ratio=current_ratio, state=state, log=log)

    end_time = calc_transient_end_time(install, log=log)
    if end_time is None:
        raise Exception(f'calculating cyclic rating but cycle time in {install.name} is "None"')

    install_cond_temp, transient_result = calc_transient_section_temperature(install, current_ratio,
                                                                             state=state, log=log)
    cyclic_found = False
    cyclic_accuracy = install.config.elt87_config.cyclic_accuracy.get_value(unit='°C', log=log)
    i = 0
    while not cyclic_found:
        i = i + 1
        state.progress = f'{progress_prefix} cycle {i}'
        new_install_cond_temp, transient_result = calc_transient_section_temperature(install, current_ratio,
                                                                                     state=state, log=log)
        cyclic_found = True
        for i_cable_set, old_cond_temp in enumerate(install_cond_temp):
            if abs(new_install_cond_temp[i_cable_set][0] - old_cond_temp[0]) > cyclic_accuracy:
                cyclic_found = False
        install_cond_temp = new_install_cond_temp
        # print(install_cond_temp)

    return install_cond_temp, transient_result


def calc_transient_end_time(install: AutoInstall, selected_scenario_name: str = None, log: Log = None):
    rating_type = install.get_rating_type(selected_scenario_name)
    if rating_type == iec.RATING_CYCLIC:
        end_time = install.get_cycle_time(install.selected_scenario.value, unit='s', log=log)
    elif rating_type == iec.RATING_TRANSIENT or rating_type == iec.RATING_EMERGENCY:
        end_time = install.get_end_time(install.selected_scenario.value, unit='s', log=log)
    else:
        raise Exception(f'calculating transient end time but rating type "{rating_type}" not recognised')
    return end_time


def calc_transient_section_temperature(install: AutoInstall, current_ratio: float = 1.0,
                                       state: InstallState = None,
                                       log: Log = None) -> Tuple[Optional[list], Optional[list]]:

    #    -> Tuple[Optional[List[List[float]]],
    #                                                            Optional[List[List[List[Tuple[float, List]]]]]]:
    """Calculate the conductor temperature rise after transient section

    Calculates the temperature change after the application of a current_curve.

    :param install: cable installation
    :param current_ratio: multiplier for cable currents allowed to change
    :param state: InstallState
    :param log: logger used to store results
    :return: maximum conductor temperatures reached, or None if calculation canceled
    """

    progress_prefix = '' if state is None else state.progress

    max_cond_temp = [[-math.inf for _cn in cs.placed_cables] for cs in install.cable_sets]

    transient_time = 0.0
    end_time = calc_transient_end_time(install, log=log)

    theta_cable_sets = []
    for csn, cable_set_state in enumerate(state.cable_set_states):
        theta_cables = []
        for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            # placed_cable = install.cable_sets[csn].placed_cables[cn]
            theta_a = get_ambient_temperature(install, csn, cn, log)
            theta_c = calc_conductor_temperature(state, csn, cn, theta_a, log=log)
            theta_cables.append(theta_c)
        theta_cable_sets.append(theta_cables)

    # transient_result = []
    currents = []
    for cable_set in install.cable_sets:
        if cable_set.preload_type.value == iec.PRELOAD_CONST_CURRENT:
            currents.append(cable_set.preload_current.value)
        elif cable_set.preload_type.value == iec.PRELOAD_OFF or cable_set.preload_type.value is None:
            currents.append(0.0)
        elif cable_set.preload_type.value == iec.PRELOAD_AVE_LOSS:
            if cable_set.current_curve.normalise_curve:
                current = cable_set.current_curve.calc_ave(end_time).value * cable_set.desired_I.value
            else:
                current = cable_set.current_curve.calc_ave(end_time).value
            currents.append(current)
        else:
            raise Exception(f'current preload "{cable_set.preload_type.value}" not recognised')
    transient_result = [(0.0, theta_cable_sets, currents)]

    last_c_curve_time_point = 0.0
    # transient_result = []
    end_curve_step = False
    while transient_time < end_time and not state.cancel:
        next_time_point_curve = end_time
        for cable_set in install.cable_sets:
            c_curve = cable_set.current_curve

            if c_curve is None:
                next_time_point_cs = None
            else:
                if transient_time == 0.0:
                    if c_curve.points[0].time.value != 0.0:
                        raise Exception(f'current curve {c_curve.name} does not have time zero set')

                if c_curve.cyclic.value:
                    next_time_point_cs = (transient_time - transient_time % c_curve.cycle_time.value
                                          + c_curve.calc_next_time(transient_time, log=log).value)
                else:
                    next_time_point_cs = c_curve.calc_next_time(transient_time, log=log).value
            if next_time_point_cs is not None and next_time_point_cs < next_time_point_curve:
                next_time_point_curve = next_time_point_cs

        # currents = [cable_set.current_curve.calc_current_time(time=time, log=log).value
        #             for cable_set in install.cable_sets]
        currents = []
        for cable_set in install.cable_sets:
            if cable_set.current_curve is None:
                current = cable_set.desired_I.value
            elif cable_set.current_curve.normalise_curve.value:
                current = (cable_set.current_curve.calc_current_time(transient_time, log=log).value *
                           cable_set.desired_I.value / cable_set.current_curve.calc_max(end_time).value)
            else:
                current = cable_set.current_curve.calc_current_time(transient_time, log=log).value
            if cable_set.desired_I_change.value:
                current = current * current_ratio
            currents.append(current)
            log.add_line('current', current, 'A', 'elt087 program')

        log_start_section(log, 'next time point in curve', 'elt087 program')
        if install.config.elt87_config.vary_time_step.value == cigre_consts.TIME_STEP_USER_VARY:
            while transient_time < end_time and not state.cancel:
                log_start_section(log, 'next iteration time point', 'elt087 program')
                max_time_step = install.config.elt87_config.elt87_time_step.value
                time_step1 = install.config.elt87_config.time_step1.value
                time_period1 = install.config.elt87_config.time_period1.value
                time_step2 = install.config.elt87_config.time_step2.value
                time_period2 = install.config.elt87_config.time_period2.value
                if transient_time - last_c_curve_time_point < time_period1:
                    if state is not None:
                        state.progress = f'{progress_prefix} Time period 1 (time step = {time_step1} s).'
                    delta_time = time_step1
                    if next_time_point_curve > transient_time + time_period1:
                        next_iteration_time_point = transient_time + time_period1
                    else:
                        next_iteration_time_point = next_time_point_curve
                elif transient_time - last_c_curve_time_point < time_period2:
                    if state is not None:
                        state.progress = f'{progress_prefix} Time period 2 (time step = {time_step2} s).'
                    delta_time = time_step2
                    if next_time_point_curve > transient_time + time_period2 - time_period1:
                        next_iteration_time_point = transient_time + time_period2 - time_period1
                    else:
                        next_iteration_time_point = next_time_point_curve
                else:
                    if state is not None:
                        state.progress = f'{progress_prefix} Default period (time step = {max_time_step} s).'
                    delta_time = max_time_step
                    next_iteration_time_point = next_time_point_curve

                no_iterations = int((next_iteration_time_point - transient_time) / delta_time)
                if no_iterations == 0:
                    no_iterations = 1
                    delta_time = next_iteration_time_point - transient_time
                log_add_line(log, 'delta time', delta_time, 's', f'elt087 ({delta_time/60} mins)')
                log_add_line(log, 'number of iterations', no_iterations, '', 'elt087')

                resolution = install.config.elt87_config.time_resolution.value

                log_end_section(log, 'next iteration time point', next_iteration_time_point, 's',
                                f'elt087 program ({next_iteration_time_point/60} mins)')

                max_cond_temp, transient_part = calc_fd_transient(install, currents, no_iterations, delta_time,
                                                                  resolution=resolution,
                                                                  old_max_cond_temp=max_cond_temp,
                                                                  start_time=transient_time,
                                                                  state=state, log=log)
                if max_cond_temp is not None:
                    transient_result.extend(transient_part)
                    transient_time = transient_time + no_iterations * delta_time
                else:
                    return None, None
        elif install.config.elt87_config.vary_time_step.value == cigre_consts.TIME_STEP_CONSTANT:
            delta_time = install.config.elt87_config.elt87_time_step.value
            resolution = install.config.elt87_config.time_resolution.value
            no_iterations = int((next_time_point_curve - transient_time) / delta_time)
            if no_iterations == 0:
                no_iterations = 1
                delta_time = next_time_point_curve - transient_time
            max_cond_temp, transient_part = calc_fd_transient(install, currents, no_iterations, delta_time,
                                                              resolution=resolution,
                                                              old_max_cond_temp=max_cond_temp,
                                                              start_time=transient_time,
                                                              state=state, log=log)
            if max_cond_temp is not None:
                transient_result.extend(transient_part)
                transient_time = transient_time + no_iterations * delta_time
            else:
                return None, None
        elif install.config.elt87_config.vary_time_step.value == cigre_consts.TIME_STEP_ELT_87:
            if not end_curve_step:
                log_start_section(log, 'time_step', 'smallest value of all cables / 10')
                delta_time = math.inf
                for cable_set_i, cable_set in enumerate(install.cable_sets):
                    for cable_i in range(len(cable_set.placed_cables)):
                        delta_time = min(delta_time, int(calc_time_step(state, cable_set_i, cable_i,
                                                                        next_time_point_curve - transient_time,
                                                                        log=log).value / 10))
                resolution = delta_time * 5
                log_end_section(log, 'time_step', delta_time, 's', 'smallest value of all cables / 10')
                log_add_line(log, 'resolution', resolution, 's', 'time_step * 5')
                no_iterations = int((next_time_point_curve - transient_time) / delta_time)
                end_curve_step = (no_iterations * delta_time < next_time_point_curve)
            else:
                no_iterations = 1
                delta_time = next_time_point_curve - transient_time
                resolution = delta_time * 5
                log_add_line(log, 'time_step', delta_time, 's', 'finish off curve step')
                end_curve_step = False
            max_cond_temp, transient_part = calc_fd_transient(install, currents, no_iterations, delta_time,
                                                              resolution=resolution,
                                                              old_max_cond_temp=max_cond_temp,
                                                              start_time=transient_time,
                                                              state=state, log=log)
            if max_cond_temp is not None:
                transient_result.extend(transient_part)
                transient_time = transient_time + no_iterations * delta_time
            else:
                return None, None
        else:
            raise Exception(f'vary time step {install.config.elt87_config.vary_time_step.value} not recognised')

        log_end_section(log, 'next time point in curve', next_time_point_curve, 's',
                        f'elt087 program ({next_time_point_curve / 60 / 60} hours)')
        last_c_curve_time_point = next_time_point_curve

        if state is not None:
            state.progress = progress_prefix

    return max_cond_temp, transient_result


# **********************  Electra 87  **************************

# **********************  Section 3.1: Amount of Soil to be Considered for Buried Cables

@UseState('elt087_W_I', level=cabsys.data_classes.state.PLACED_CABLE)
@LogSection('elt087_W_I')
def calc_w_i(install: AutoInstall, cable_set_no: int, cable_no: int,
             state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate the difference between maximum and minimum heat loss of a cable (W/m).

    Electra 87 Section 3.1

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no: cable number in cable_set
    :param state: cable set state
    :param log: logger used to store results
    :return: W_I difference in heat loss (W/m)
    """

    cable_set = install.cable_sets[cable_set_no]
    # cable = cable_set.placed_cables[cable_no].cable

    # if state is not None:
    #     cable_set_state = state.cable_set_states[cable_set_no]
    # else:
    #     cable_set_state = None
    # if cable_set_state is not None:
    #     cable_state = cable_set_state.placed_cable_states[cable_no].cable_state
    # else:
    #     cable_state = None

    # current_low = cigre_support.calc_curve_min(cable_set, state=cable_set_state, log=log).value
    # current_high = cigre_support.calc_curve_max(cable_set, state=cable_set_state, log=log).value

    curve = cable_set.current_curve
    if curve is None:
        current_low = 0.0
        current_high = cable_set.desired_I.value
    else:
        current_curve_normalise = curve.normalise_curve.value
        if current_curve_normalise:
            current_low = curve.calc_min().value / curve.calc_max().value * cable_set.desired_I.value
            current_high = cable_set.desired_I.value
        else:
            current_low = cable_set.current_curve.calc_min().value
            current_high = cable_set.current_curve.calc_max().value
        if cable_set.preload_type.value == iec.PRELOAD_CONST_CURRENT:
            if current_low > cable_set.preload_current.get_value(unit='A'):
                current_low = cable_set.preload_current.get_value(unit='A')
            if current_high < cable_set.preload_current.get_value(unit='A'):
                current_high = cable_set.preload_current.get_value(unit='A')

    log_start_section(log, 'W_I', 'step change in load')
    # not using state as don't want to remember values
    w_cable_high = iec_extra.calc_w_cable(install, cable_set_no, cable_no, current_high, log=log).value
    if cable_set.preload_type.value == iec.PRELOAD_OFF or cable_set.preload_type.value is None:
        w_cable_low = 0.0
        log_add_line(log, 'W_I low', 0.0, 'W/m', 'W_I low as preload is no load')
    else:
        w_cable_low = iec_extra.calc_w_cable(install, cable_set_no, cable_no, current_low, log=log).value

    w_i = w_cable_high - w_cable_low
    log_end_section(log, 'W_I', w_i, 'W/m', 'step change in load')

    return QFloat(w_i, 'W/m', 'Electra 87, Section 3.1', description='change in heat loss between high and low current',
                  symbol='elt087_W_I')


@LogSection('θ_r_t')
def calc_theta_r_t(install: AutoInstall, cable_set_no: int, cable_no: int, r: float,
                   state: InstallState = None, log: Log = None) -> QFloat:
    """Estimate the temperature rise at an external radius of soil considered for the transient (°C).

    Electra 87 Section 3.1

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no: cable number in cable_set
    :param r: radius of the ground
    :param state: cable set state
    :param log: logger used to store results
    :return: theta(r,t) temperature rise (°C)
    """

    if log is not None:
        log.add_line('r', r, 'm', 'set by program')

    w_i = calc_w_i(install, cable_set_no, cable_no, state=state, log=log).value
    rho_t = install.get_ground_tr(install.selected_scenario.value, unit='K.m/W')
    diffusivity = cabsys.iec.iec60853_2.calc_soil_diffusivity(install, log=log).value
    time_elapsed = calc_transient_end_time(install, log=log)
    if time_elapsed <= 0.0:
        raise Exception(f'calculating θ_r_t but end time is {time_elapsed} and must be greater than zero')
    exp_int = calc_exponential_integral(r**2 / (4 * diffusivity * time_elapsed), log=log).value
    theta_r_t = w_i * rho_t / (4 * math.pi) * exp_int

    return QFloat(theta_r_t, '°C', 'Electra 87, Section 3.1', description='temperature rise at radius r after time t',
                  symbol='θ_r_t')


@UseState('elt087_r_t', level=cabsys.data_classes.state.PLACED_CABLE)
@LogSection('r_t')
def calc_d_t(install: AutoInstall, cable_set_no: int, cable_no: int,
             state: InstallState = None, log: Log = None) -> QFloat:
    """Estimate the external radius of soil considered for the transient (°C).

    Estimate the external radius of the soil, such that the external radius (or boundary) does not change temperature
    by more than that set by install.config.elt87_accuracy.

    Electra 87 Section 3.1

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no: cable number in cable_set
    :param state: cable set state
    :param log: logger used to store results
    :return: W_I difference in heat loss (W/m)
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    required_accuracy = install.config.elt87_config.elt87_boundary_accuracy.value

    # check to make sure r is not outside the furthest cable in the installation (including images)
    log_start_section(log, 'r_i', 'Electra 87, Section 2.4: distance to furthest image +10%')
    cable_x = cable_set.placed_cables[cable_no].x.get_value(unit='mm', log=log)
    cable_y = cable_set.placed_cables[cable_no].y.get_value(unit='mm', log=log)
    ri = 0.0
    for cable_set_i_no, cable_set_i in enumerate(install.cable_sets):
        for placed_cable_i_no, placed_cable_i in enumerate(cable_set_i.placed_cables):
            log_start_section(log, f'd_pk cable_set:{cable_set_i_no} cable:{placed_cable_i_no}',
                              'Electra 87, Section 2.4: find distance between cable and images')
            cable_i_x = placed_cable_i.x.get_value(unit='mm', log=log)
            cable_i_y = placed_cable_i.y.get_value(unit='mm', log=log)
            dpk = math.sqrt((cable_i_y + cable_y) ** 2 + (cable_i_x - cable_x) ** 2) / 1000
            log_end_section(log, f'd_pk cable_set:{cable_set_i_no} cable:{placed_cable_i_no}', dpk, 'm',
                            'Electra 87, Section 2.4: find distance between cable and images')
            ri = max(ri, dpk)
        ri = ri * 1.1
    log_end_section(log, 'r_i', ri, 'm', 'Electra 87, Section 2.4: distance to furthest image +10%')

    if (install.cable_sets[cable_set_no].preload_type.value == iec.PRELOAD_OFF or
            install.cable_sets[cable_set_no].preload_type.value is None):
        # start by estimating r as lowest value just outside cable radius
        log_start_section(log, 'r_t_min', 'Electra 87, Section 3.1: find minimum r_t')
        low_r_t = cable.calc_outer_diameter(log=log) / 2.0 / 1000.0 * 1.1
        theta = calc_theta_r_t(install, cable_set_no, cable_no, low_r_t, state=state, log=log).value
        log_end_section(log, 'r_t_min', low_r_t, 'm', 'Electra 87, Section 3.1: find minimum r_t')

        # if minimum r not far enough out for required accuracy need to find r
        r = low_r_t
        if theta > required_accuracy:
            # first find outer radius that has accuracy lower than required accuracy
            log_start_section(log, 'r_t_max', 'Electra 87, Section 3.1: find maximum r_t')
            high_r_t = low_r_t
            while theta > required_accuracy:
                high_r_t = 2 * high_r_t
                theta = calc_theta_r_t(install, cable_set_no, cable_no, high_r_t, state=state, log=log).value
            log_end_section(log, 'r_t_max', high_r_t, 'm', 'Electra 87, Section 3.1: find maximum r_t')
            # do a binary search to find r that has required accuracy
            log_start_section(log, 'r_t', 'Electra 87, Section 3.1: binary search for r_t')
            required_accuracy2 = install.config.elt87_config.elt87_boundary_accuracy2.get_value(unit='', log=log)
            r = high_r_t
            while round(high_r_t, required_accuracy2) != round(low_r_t, required_accuracy2):
                r = (high_r_t + low_r_t) / 2.0
                log_start_section(log, f'try r_t = {r}', 'binary search')
                theta = calc_theta_r_t(install, cable_set_no, cable_no, r, state=state, log=log).value
                if theta > required_accuracy:
                    low_r_t = r
                    result = 'becomes low limit'
                else:
                    high_r_t = r
                    result = 'becomes high limit'
                log_end_section(log, f'try r_t = {r}', result, '', 'binary search')
            log_end_section(log, 'r_t', r, 'm', 'Electra 87, Section 3.1: binary search for r_t')
            r = math.ceil(r * 10 ** required_accuracy2) / 10 ** required_accuracy2
            log_add_line(log, 'r_t', r, 'm', f'r_t rounded up (number of d.p. {required_accuracy2})')

        r = min(r, ri)
    else:
        r = ri

    return QFloat(r, 'm', 'Electra 87, Section 3.1', description='radius of external soil boundary',
                  symbol='r_t')


@UseState('elt087_ni')
@LogSection('elt087_ni')
def calc_ni(cable: Cable, state: State = None, log: Log = None) -> QInt:
    """Calculate the number of elementary layers in the insulation.

    Electra 87 Section 3.2
    :param cable: cable to calculate number of layers
    :param state: cable state
    :param log: logger used to store results
    :return: ni, number of insulation layers
    """

    number_cores = cable.number_cores.get_value(unit='', log=log)

    if number_cores == iec.SINGLE_CORE or number_cores == iec.CONCENTRIC:
        t1_thickness = iec60287support.get_q_parameter(cable.core.t1, log=log)
        if t1_thickness is None:
            t1_thickness = iec60287_2_1wrapper.calc_t1_thermal_thickness(cable, log=log).value
    else:
        raise Exception(f'calculating number of insulation layers for {number_cores} cable,'
                        f' only single core cables implemented')

    if t1_thickness < 5.0:
        ni = 4
    else:
        ni = 10

    return QInt(ni, '', 'Electra 87, Section 3.2', description='number of layers in the insulation',
                symbol='elt087_ni')


@UseState('elt087_ns', level=cabsys.data_classes.state.PLACED_CABLE)
@LogSection('elt087_ns')
def calc_ns(install: AutoInstall, cable_set_no: int, cable_no: int,
            state: InstallState = None, log: Log = None) -> QInt:
    """Calculate the number of elementary layers in the soil (excluding impact of nearby heat sources)

    Electra 87 Section 3.2, equation 2

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no: cable number in cable_set
    :param state: cable set state
    :param log: logger used to store results
    :return: ns, number of soil layers not taking account of nearby heat sources
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    de = cable.calc_outer_diameter(log=log)
    dt = calc_d_t(install, cable_set_no, cable_no, state=state, log=log).value * 1000 * 2

    ns = int((dt - de) / (2 * 0.16 * de)) + 1

    return QInt(ns, '', 'Electra 87, Section 3.2, equation 2', description='number of layers in the soil',
                symbol='elt087_ns')


@LogSection('Tj')
def calc_t_j(rho_t: float, inner_radius: float, outer_radius: float, log: Log = None) -> QFloat:
    """Calculate the thermal resistance of a layer

    Electra 87 Section 3.3, equation 3

    :param rho_t: thermal resistivity (K.m/W)
    :param inner_radius: inner radius of layer
    :param outer_radius: outer radius of layer
    :param log: logger used to store results
    :return: Tj, thermal resistance of layer (K.m/W)
    """

    log_add_line(log, 'rho_t', rho_t, 'K.m/W', 'thermal resistivity')
    log_add_line(log, 'r_j-1', inner_radius, 'm', 'inner radius of layer')
    log_add_line(log, 'rj', outer_radius, 'm', 'outer radius of layer')
    t_j = rho_t / (2 * math.pi) * math.log(outer_radius / inner_radius)

    return QFloat(t_j, 'K.m/W', 'Electra 87, Section 3.3, equation 3', description='thermal resistance of layer',
                  symbol='Tj')


@LogSection('Qj_Eq_4')
def calc_q_j(alpha: float, radius: float, inner_radius: float, outer_radius: float,
             log: Log = None, symbol: str = None) -> QFloat:
    """Calculate the thermal capacitance of a node

    Electra 87 Section 3.3, equation 4

    :param alpha: volumetric specific heat capacity of layer (J/K/m³)
    :param radius: radius of node (m)
    :param inner_radius: radius of inner node (m)
    :param outer_radius: radius of outer node (m)
    :param log: logger used to store results
    :param symbol: symbol used by logger
    :return: Tj, thermal capacitance of node (J/m.K)
    """

    log_add_line(log, 'alpha', alpha, 'K.m/W', 'thermal resistivity')
    log_add_line(log, 'r_j', radius, 'm', 'radius of layer')
    log_add_line(log, 'r_j-1', inner_radius, 'm', 'inner radius of layer')
    log_add_line(log, 'r_j+1', outer_radius, 'm', 'outer radius of layer')
    q_j = math.pi * alpha * (((radius + outer_radius)/2)**2 - ((radius + inner_radius)/2)**2)

    if symbol is None:
        symbol = 'Qj'
    return QFloat(q_j, 'J/m.K', 'Electra 87, Section 3.3, equation 4', description='thermal capacitance of layer',
                  symbol=symbol)


@LogSection('built_ladders')
def build_ladders(install: AutoInstall, state: InstallState = None, log: Log = None) -> Optional[QStr]:
    """Build the 1 dimensional finite element ladders for all cables.

    Builds the 1 dimensional finite element ladders for each cable

    Electra87 Section 3.3

    :param install: cable installation
    :param state: cable set state
    :param log: logger used to store results
    :return: ns, number of soil layers not taking account of nearby heat sources
    """

    progress_prefix = state.progress
    no_ladders = 0

    for cable_set_no, cable_set in enumerate(install.cable_sets):
        log_start_section(log, 'built ladders: cable set no', 'cable set number built', section_log_level=30)
        for cable_no, placed_cable in enumerate(cable_set.placed_cables):
            log_start_section(log, 'cable', 'build cable ladder')
            build_ladder(install, cable_set_no, cable_no, state=state, log=log)
            log_end_section(log, 'cable', cable_no, '', 'build cable ladder')

            if state.cancel:
                return None
            state.progress = f'{progress_prefix} Build ladder for cable set {cable_set_no}, cable {cable_no}'

        log_end_section(log, 'built ladders: cable set no', cable_set_no, '', 'cable set number built')

    no_sources = 0
    log_start_section(log, 'build sources: number of sources:', 'build adjacent cable list', section_log_level=70)
    for cable_set_no, cable_set in enumerate(install.cable_sets):
        log_start_section(log, 'build sources: cable set no:', 'build adjacent cable list', section_log_level=70)
        for cable_no, placed_cable in enumerate(cable_set.placed_cables):
            log_start_section(log, 'cable', 'build adjacent cable list')
            no_ladders = no_ladders + 1
            no_sources += build_adjacent_heat_source_list(install, cable_set_no, cable_no, state=state, log=log)
            log_end_section(log, 'cable', cable_no, '', 'build adjacent cable list')
        log_end_section(log, 'build sources: cable set no:', cable_set_no, '', 'find adjacent cable sources')
    log_end_section(log, 'build sources: number of sources:', no_sources, '', 'find adjacent cable sources')

    state.progress = progress_prefix

    return QStr('', '', 'Electra 87, Section 3.3', description='number of ladders built',
                symbol='no_ladders_built')


def build_ladder(install: AutoInstall, cable_set_no: int, cable_no: int,
                 state: InstallState = None, log: Log = None) -> QStr:
    """Build the 1 dimensional finite element ladder for a cable.

    Builds the 1 dimensional finite element ladders for a cable

    Electra87 Section 3.3

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no: cable number in cable_set
    :param state: install state
    :param log: logger used to store results
    :return: ns, number of soil layers not taking account of nearby heat sources
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    if state is not None:
        cable_set_state = state.cable_set_states[cable_set_no]
    else:
        cable_set_state = None
    if cable_set_state is not None:
        placed_cable_state = cable_set_state.placed_cable_states[cable_no]

    else:
        raise Exception(f'attempting to build Electra 87 ladder but no stata specified to store result')

    cable_id = f'cable {cable_set_no}, {cable_no}'

    old_elt87_state = getattr(placed_cable_state, 'elt87_state', None)
    if old_elt87_state is not None:
        delattr(placed_cable_state, 'elt87_state')

    elt87_state = Elt087State()
    placed_cable_state.add_quantity_store('elt87_state', elt87_state)
    # elt87_state = placed_cable_state.elt97_state

    total_capacitance = 0.0
    total_resistance = 0.0

    # thickness of insulation layers, layer_thickness
    log_start_section(log, 'ins_layer_rt', 'Electra 87')
    if not install.config.single_t1_rho.value:
        raise Exception('building ladder for transient but multiple insulation layers not implemented')
    if install.config.elt87_config.screen_layers.get_value(unit='', log=log):
        cond_screen_dia = cable.core.cond_screen_dia.get_value(unit='mm', log=log)
        no_cores = cable.number_cores.get_value(unit='', log=log)
        ins_dia = cable.core.insu_dia.get_value(unit='mm', log=log)
        if no_cores == iec.SINGLE_CORE or no_cores == iec.CONCENTRIC:
            ins_rt = (ins_dia - cond_screen_dia) / 2
        else:
            raise Exception('insulation thickness: only single core or concentric cable implemented')
    else:
        ins_rt = iec60287_2_1wrapper.calc_t1_thermal_thickness(cable, log=log).value

    if install.config.elt87_config.n_i.value is None:
        ni = calc_ni(cable, state=placed_cable_state, log=log)
    else:
        ni = install.config.elt87_config.n_i
        log_add_line(log, 'n_i', ni.value, '', 'set in elt87_config')
    ins_layer_rt = ins_rt / ni.value / 1000
    log_end_section(log, 'ins_layer_rt', ins_layer_rt, 'm', 'thickness of each layer of insulation')

    log_start_section(log, 'soil_layer_rt', 'Electra 87')
    ns = calc_ns(install, cable_set_no, cable_no, state=state, log=log).value
    r = calc_d_t(install, cable_set_no, cable_no, state=state, log=log).value
    cable_outer_radius = cable.calc_outer_diameter(log=log) / 2000
    soil_layer_rt = (r - cable_outer_radius) / ns
    log_end_section(log, 'soil_layer_rt', soil_layer_rt, 'm', 'thickness of each layer of soil')

    insu_rho_t = iec60853_2.find_insulation_rho_t(cable, log=log).value
    # cond_v_s_heat = iec60853_2.find_cond_v_s_heat(cable, log=log).value
    insu_v_s_heat = iec60853_2.find_insulation_v_s_heat(cable, log=log).value

    # add layer list to elt87_state
    # ladder_list = elt87_state.add_data_store_list('layer', [])
    ladder_list = elt87_state.layers

    # build conductor layer
    log_start_section(log, 'conductor layer', 'elt087')
    ds = LayerState()
    ladder_list.append(ds)
    layer_radius = cable.conductor.dia.get_value(unit='mm', log=log) / 2.0 / 1000
    ds.delta_theta_j.set_value(0.0, unit='°C', description='conductor temperature', source='elt087 program')
    ds.layer_radius.set_value(layer_radius, unit='m', description='radius of conductor layer',
                              source='elt087 program', log=log)
    ds.Wj.set_value(0.0, unit='W/m', description='conductor loss', source='elt087 program')
    if install.config.elt87_config.screen_layers.value:
        layer_next_radius = cable.core.cond_screen_dia.get_value(unit='mm', log=log) / 1000 / 2
    else:
        layer_next_radius = layer_radius + ins_layer_rt
    layer_no = 0
    elt87_state.conductor_layer.set_value(0, source='elt087 program')
    log_start_section(log, 'Qj', 'layer heat capacity')
    q_ins = calc_q_j(insu_v_s_heat, layer_radius, layer_radius, layer_next_radius, log=log, symbol='Qj_ins')
    q_c = iec60853_2.calc_q_c(cable, state=placed_cable_state, log=log)
    layer_q = q_ins.value + q_c.value
    ds.Qj.set_value(layer_q, unit='J/m.K', description='conductor heat capacity', source='elt087 program')
    log_end_section(log, 'Qj', layer_q, 'J/m.K', 'layer heat capacity')
    log_end_section(log, 'conductor layer', 0, '', 'elt087, number of layers')
    total_capacitance += layer_q

    # build conductor screen layer
    if install.config.elt87_config.screen_layers.value:
        log_start_section(log, 'build conductor screen', 'build conductor screen layer')
        layer_no = layer_no + 1
        layer_previous_radius = layer_radius
        layer_radius = layer_next_radius
        layer_next_radius = layer_radius + ins_layer_rt
        ds = LayerState()
        ds.delta_theta_j.set_value(0.0, unit='°C', description='conductor screen layer temperature',
                                   source='elt087 program')
        ds.layer_radius.set_value(layer_radius, unit='m', description='radius of conductor screen layer',
                                  source='elt087 program')
        ds.Wj.set_value(0.0, unit='W/m', description='conductor screen loss', source='elt087 program')
        tj = calc_t_j(insu_rho_t, layer_previous_radius, layer_radius, log).value
        ds.Tj.set_value(tj, unit='K.m/W', description='thermal resistance of conductor screen layer',
                        source='Electra 87 Equation 3')
        qj = calc_q_j(insu_v_s_heat, layer_radius, layer_previous_radius, layer_next_radius, log=log).value
        ds.Qj.set_value(qj, unit='J/m.K', description='thermal capacitance of conductor screen layer',
                        source='Electra 87 Equation 4')
        ladder_list.append(ds)
        log_end_section(log, 'build conductor screen', layer_no, '', 'build conductor screen layer')
        total_resistance += tj
        total_capacitance += qj

    # build insulation layers
    number_insulation_layers = ni.value - 1
    for count in range(number_insulation_layers):
        log_start_section(log, 'build insulation', 'build insulation layer')
        layer_no = layer_no + 1
        layer_previous_radius = layer_radius
        layer_radius = layer_next_radius
        layer_next_radius = layer_radius + ins_layer_rt
        ds = LayerState()
        ds.delta_theta_j.set_value(0.0, unit='°C', description='insulation layer temperature', source='elt087 program')
        ds.layer_radius.set_value(layer_radius, unit='m', description='radius of insulation layer',
                                  source='elt087 program')
        ds.Wj.set_value(0.0, unit='W/m', description='insulation loss', source='elt087 program')
        tj = calc_t_j(insu_rho_t, layer_previous_radius, layer_radius, log).value
        ds.Tj.set_value(tj, unit='K.m/W', description='thermal resistance of insulation layer',
                        source='Electra 87 Equation 3')
        qj = calc_q_j(insu_v_s_heat, layer_radius, layer_previous_radius, layer_next_radius, log=log).value
        ds.Qj.set_value(qj, unit='J/m.K', description='thermal capacitance of insulation layer',
                        source='Electra 87 Equation 4')
        ladder_list.append(ds)
        log_end_section(log, 'build insulation', layer_no, '', 'build insulation layer')
        total_resistance += tj
        total_capacitance += qj

    # build insulation screen layer
    if install.config.elt87_config.screen_layers.value:
        log_start_section(log, 'build last insulation', 'build last insulation layer')
        layer_no = layer_no + 1
        layer_previous_radius = layer_radius
        layer_radius = layer_next_radius
        layer_next_radius = iec60287support.calc_clearance_dia(cable, log=log).value / 1000 / 2
        ds = LayerState()
        ds.delta_theta_j.set_value(0.0, unit='°C', description='last insulation layer temperature',
                                   source='elt087 program')
        ds.layer_radius.set_value(layer_radius, unit='m', description='radius of last insulation layer',
                                  source='elt087 program')
        ds.Wj.set_value(0.0, unit='W/m', description='last insulation layer loss', source='elt087 program')
        tj = calc_t_j(insu_rho_t, layer_previous_radius, layer_radius, log).value
        ds.Tj.set_value(tj, unit='K.m/W', description='thermal resistance of last insulation layer',
                        source='Electra 87 Equation 3')
        qj = calc_q_j(insu_v_s_heat, layer_radius, layer_previous_radius, layer_next_radius, log=log).value
        ds.Qj.set_value(qj, unit='J/m.K', description='thermal capacitance of last insulation layer',
                        source='Electra 87 Equation 4')
        ladder_list.append(ds)
        log_end_section(log, 'build last insulation', layer_no, '', 'build last insulation layer')
        total_resistance += tj
        total_capacitance += qj

    # build outer insulation / sheath / serving layer
    if install.config.elt87_config.screen_layers.value:
        inner_layer_desc = 'insulation screen'
    else:
        inner_layer_desc = ' insulation'
    log_start_section(log, f'build {inner_layer_desc}/sheath', f'build {inner_layer_desc}/sheath layer')
    layer_no = layer_no + 1
    elt87_state.sheath_layer.set_value(layer_no, source='elt087 program')
    layer_previous_radius = layer_radius
    layer_radius = layer_next_radius
    ds = LayerState()
    ds.delta_theta_j.set_value(0.0, description='sheath layer temperature', source='elt087 program')
    ds.layer_radius.set_value(layer_radius, unit='m', description='radius of sheath layer (inner)',
                              source='elt087 program')
    ds.Wj.set_value(0.0, unit='W/m', description='sheath loss', source='elt087 program')
    tj = calc_t_j(insu_rho_t, layer_previous_radius, layer_radius, log).value
    ds.Tj.set_value(tj, unit='K.m/W', description=f'{inner_layer_desc} layer next to sheath',
                    source='Electra 87 Equation 3')
    log_start_section(log, 'Qj', 'sheath layer thermal capacitance')
    q_j_ins = calc_q_j(insu_v_s_heat, layer_radius, layer_previous_radius, layer_radius, log=log).value
    q_s = iec60853_2.calc_q_s(cable, state=placed_cable_state, log=log).value
    log_start_section(log, 'Qj_serv_sheath', 'serving layer next to sheath thermal capacitance')
    serving_mat = cable.serving.material.get_value(unit='', log=log)
    if serving_mat == iec.NONE:
        q_j_serv = 0.0
    else:
        da_dash = iec60287support.calc_sheath_screen_diameter(cable, log=log).value
        d_outer = cable.calc_outer_diameter(log=log)
        serv_v_s_heat = iec60853_2.find_serving_v_s_heat(cable, log=log).value
        q_j_serv = calc_q_j(serv_v_s_heat, da_dash/2000, da_dash/2000, d_outer/2000, log=log).value
    log_end_section(log, 'Qj_serv_sheath', q_j_serv, 'J/m.K', 'serving layer next to sheath thermal capacitance')
    q_j = q_j_ins + q_s + q_j_serv
    ds.Qj.set_value(q_j, unit='J/m.K', description=f'thermal capacitance of sheath/{inner_layer_desc} layer',
                    source='Electra 87 Equation 4')
    log_end_section(log, 'Qj', q_j, 'J/m.K', 'sheath layer thermal capacitance')
    ladder_list.append(ds)
    log_end_section(log, f'build {inner_layer_desc}/sheath', layer_no, '', f'build {inner_layer_desc}/sheath layer')
    total_resistance += tj
    total_capacitance += q_j

    # build serving node
    log_start_section(log, 'build serving', 'build serving node')
    layer_no = layer_no + 1
    layer_previous_radius = iec60287support.calc_sheath_screen_diameter(cable, log=log).value / 2000.0
    layer_radius = cable.calc_outer_diameter(log=log) / 2000.0
    ds = LayerState()
    ds.delta_theta_j.set_value(0.0, unit='°C', description='serving layer temperature', source='elt087 program')
    ds.layer_radius.set_value(layer_radius, unit='m', description='radius of serving layer (outer)',
                              source='elt087 program', log=log)
    ds.Wj.set_value(0.0, unit='W/m', description='serving loss', source='elt087 program')
    log_start_section(log, 'r_j+1', 'layer next radius (in soil)')
    layer_next_radius_ignoring_source = layer_radius + soil_layer_rt
    r_source = adjacent_heat_source_distance(install, cable_set_no, cable_no, layer_radius,
                                             layer_next_radius_ignoring_source, log=log)
    if r_source is None:
        layer_next_radius = layer_next_radius_ignoring_source
        layer_next_radius_ignoring_source = None
    else:
        layer_next_radius = r_source
    log_end_section(log, 'r_j+1', layer_next_radius, 'm', 'layer next radius (in soil)')
    # calculate Tj
    if serving_mat == iec.NONE:
        tj = 0.0
        log_add_line(log, 'Tj', tj, 'K.m/W', 'no serving so thermal resistance zero')
    else:
        serv_rho_t = iec60853_2.find_serving_rho_t(cable, log=log).value
        tj = calc_t_j(serv_rho_t, layer_previous_radius, layer_radius, log).value
    ds.Tj.set_value(tj, unit='K.m/W', description='thermal resistance of serving', source='Electra 87 Equation 3')
    # calculate Qj
    log_start_section(log, 'Qj', 'thermal capacitance of serving node')
    log_start_section(log, 'Qj_serv_serv', 'serving layer next to soil thermal capacitance')
    serving_mat = cable.serving.material.get_value(unit='', log=log)
    if serving_mat == iec.NONE:
        q_j_serv = 0.0
    else:
        da_dash = iec60287support.calc_sheath_screen_diameter(cable, log=log).value
        d_outer = cable.calc_outer_diameter(log=log)
        serv_v_s_heat = iec60853_2.find_serving_v_s_heat(cable, log=log).value
        q_j_serv = calc_q_j(serv_v_s_heat, d_outer/2000, da_dash/2000, d_outer/2000, log=log).value
    log_end_section(log, 'Qj_serv_serv', q_j_serv, 'J/m.K', 'serving layer next to soil thermal capacitance')
    log_start_section(log, 'Qj_serv_soil', 'soil layer next to serving thermal capacitance')
    r_soil_serv = (layer_radius + layer_next_radius) / 2
    soil_v_s_heat = install.get_ground_v_s_heat(install.selected_scenario.value, unit='J/K/m³', log=log)
    q_soil_serv = math.pi * soil_v_s_heat * (r_soil_serv**2 - layer_radius**2)
    log_end_section(log, 'Qj_serv_soil', q_soil_serv, 'J/m.K', 'soil layer next to serving thermal capacitance')
    q_j = q_j_serv + q_soil_serv
    ds.Qj.set_value(q_j, unit='J/m.K', description='thermal capacitance of serving node',
                    source='Electra 87 Equation 4')
    log_end_section(log, 'Qj', q_j, 'J/m.K', 'thermal capacitance of serving node')

    ladder_list.append(ds)
    log_end_section(log, 'build serving', layer_no, '', 'build serving node')
    total_resistance += tj
    total_capacitance += q_j_serv
    elt87_state.total_resistance.set_value(total_resistance, unit='K.m/W', source='elt087 program', log=log)
    elt87_state.total_capacitance.set_value(total_capacitance, unit='J/m.K', source='elt087 program', log=log)

    if install.cable_sets[cable_set_no].duct_layout.value != iec.NO_DUCTS:
        raise Exception(f'trying to calculate ladder for cable set {cable_set_no} but cables are inducts')

    # build soil layers
    soil_rho_t = install.get_ground_tr(install.selected_scenario.value, unit='K.m/W')
    soil_layer_no = 0
    while layer_radius < r:
        layer_no = layer_no + 1
        log_start_section(log, f'soil layer {layer_no} radius', 'build soil layer')
        soil_layer_no += 1
        layer_previous_radius = layer_radius
        layer_radius = layer_next_radius
        ds = LayerState()
        ds.delta_theta_j.set_value(0.0, description='soil layer temperature', source='elt087 program')
        ds.layer_radius.set_value(layer_radius, unit='m', description='radius of soil layer',
                                  source='elt087 program')
        ds.Wj.set_value(0.0, unit='W/m', description='adjacent cable loss', source='elt087 program')
        # calculate next layer radius taking account that it may be a heat top
        log_start_section(log, 'r_j+1', 'next layer radius (in soil)')
        if layer_next_radius_ignoring_source is None:
            layer_next_radius_ignoring_source = layer_radius + soil_layer_rt
        r_source = adjacent_heat_source_distance(install, cable_set_no, cable_no, layer_radius,
                                                 layer_next_radius_ignoring_source, log=log)
        if r_source is None:
            layer_next_radius = layer_next_radius_ignoring_source
            layer_next_radius_ignoring_source = None
        else:
            layer_next_radius = r_source
        log_end_section(log, 'r_j+1', layer_next_radius, 'm', 'next layer radius (in soil)')
        # Calculate Tj and Qj
        tj = calc_t_j(soil_rho_t, layer_previous_radius, layer_radius, log).value
        ds.Tj.set_value(tj, unit='K.m/W', description='thermal resistance of soil layer',
                        source='Electra 87 Equation 3')
        qj = calc_q_j(soil_v_s_heat, layer_radius, layer_previous_radius, layer_next_radius, log=log).value
        ds.Qj.set_value(qj, unit='J/m.K', description='thermal capacitance of soil layer',
                        source='Electra 87 Equation 4')
        ladder_list.append(ds)
        log_end_section(log, f'soil layer {layer_no} radius', layer_radius, '', f'build soil layer')

    return QStr(cable_id, '', 'Electra 87, Section 3.3', description='number of layers',
                symbol='build_ladder')


def adjacent_heat_source_distance(install: AutoInstall, cable_set_no: int, cable_no: int,
                                  inner_r: float, outer_r: float, log: Log = None) -> Optional[float]:
    """Find the distance of the nearest heat top in a layer.

    When the thermal field being considered includes adjacent or image top(s) the elementary layer takes account
    of the heat top.

    Electra87 Section 3.3

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no: cable number in cable_set
    :param inner_r: inner radius of layer (m)
    :param outer_r: outer radius of layer (m)
    :param log: logger used to store results
    :return: ns, number of soil layers not taking account of nearby heat sources
    """

    log_start_section(log, 'source_distance', 'adjacent heat top distance')

    cable_set = install.cable_sets[cable_set_no]
    placed_cable = cable_set.placed_cables[cable_no]

    cable_x = placed_cable.x.get_value(unit='mm', log=log)
    cable_y = placed_cable.y.get_value(unit='mm', log=log)

    result_distance = None

    for source_cable_set_no, source_cable_set in enumerate(install.cable_sets):
        for source_cable_no, source_placed_cable in enumerate(source_cable_set.placed_cables):
            # check for cables adjacent
            log_start_section(log, f'source_distance {source_cable_set_no}, {source_cable_no}',
                              'adjacent heat top distance')
            source_cable_x = source_placed_cable.x.get_value(unit='mm', log=log)
            source_cable_y = source_placed_cable.y.get_value(unit='mm', log=log)
            distance = math.sqrt((source_cable_x - cable_x)**2 + (source_cable_y - cable_y)**2) / 1000
            log_end_section(log, f'source_distance {source_cable_set_no}, {source_cable_no}', distance,
                            'm', 'adjacent heat top distance')
            if (inner_r + 0.001) < distance < (outer_r - 0.001):
                if result_distance is None or distance < result_distance:
                    result_distance = distance
            # check for image cables adjacent
            log_start_section(log, f'image_source_distance {source_cable_set_no}, {source_cable_no}',
                              'adjacent image heat top distance')
            source_cable_x = source_placed_cable.x.get_value(unit='mm', log=log)
            source_cable_y = -source_placed_cable.y.get_value(unit='mm', log=log)
            distance = math.sqrt((source_cable_x - cable_x)**2 + (source_cable_y - cable_y)**2) / 1000
            log_end_section(log, f'image_source_distance {source_cable_set_no}, {source_cable_no}', distance,
                            'm', 'adjacent image heat top distance')
            if (inner_r + 0.001) < distance < (outer_r - 0.001):
                if result_distance is None or distance < result_distance:
                    result_distance = distance
    log_end_section(log, 'source_distance', result_distance, 'm', 'adjacent heat top distance')

    return result_distance


def heat_source_distance(install: AutoInstall, cable_set_no1: int, cable_no1: int,
                         cable_set_no2: int, cable_no2: int, image: bool = None, log: Log = None) -> Optional[float]:
    """Find the distance between two cable sources.

    If image is True, then the distance will be between the image cables

    Electra87 Section 3.3

    :param install: cable installation
    :param cable_set_no1: cable set number in install
    :param cable_no1: cable number in cable_set
    :param cable_set_no2: cable set number in install
    :param cable_no2: cable number in cable_set
    :param image: find distance between image cables
    :param log: logger used to store results
    :return: ns, number of soil layers not taking account of nearby heat sources
    """

    log_start_section(log, f'source_distance {"image" if image else ""}', 'heat top distance')
    cable_set1 = install.cable_sets[cable_set_no1]
    placed_cable1 = cable_set1.placed_cables[cable_no1]
    cable1_x = placed_cable1.x.get_value(unit='mm', log=log)
    cable1_y = placed_cable1.y.get_value(unit='mm', log=log)
    cable_set2 = install.cable_sets[cable_set_no2]
    placed_cable2 = cable_set2.placed_cables[cable_no2]
    cable2_x = placed_cable2.x.get_value(unit='mm', log=log)
    cable2_y = placed_cable2.y.get_value(unit='mm', log=log)
    if image:
        distance = math.sqrt((cable2_x - cable1_x) ** 2 + (cable2_y + cable1_y) ** 2) / 1000
    else:
        distance = math.sqrt((cable2_x - cable1_x) ** 2 + (cable2_y - cable1_y) ** 2) / 1000
    log_end_section(log, f'source_distance {"image" if image else ""}', distance, 'm', 'heat top distance')
    return distance


def build_adjacent_heat_source_list(install: AutoInstall, cable_set_no: int, cable_no: int,
                                    state: InstallState = None, log: Log = None) -> int:
    """Build list adjacent heat sources.

    Adds a list of adjacent cable heat top that are in the cable's ladder. The list is added to the
    Elt087State.AdjacentCable list.

    Electra87 Section 3.3

    :param install: cable installation
    :param cable_set_no: cable set number of cable heat source
    :param cable_no: cable number of heat source
    :param state: InstallState
    :param log: logger used to store results
    :return: number of sources added
    """

    log_start_section(log, 'number sources', 'number of adjacent heat sources added')
    no_sources = 0

    placed_cable_state = state.cable_set_states[cable_set_no].placed_cable_states[cable_no]
    elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))

    for adj_cable_set_no, adj_cable_set in enumerate(install.cable_sets):

        for adj_placed_cable_no, adj_placed_cable in enumerate(adj_cable_set.placed_cables):
            no_sources_cable = 0
            adj_placed_cable_state = state.cable_set_states[adj_cable_set_no].placed_cable_states[adj_placed_cable_no]
            adj_elt87_state = cast(Elt087State, adj_placed_cable_state.get_quantity_store('elt87_state'))

            log_start_section(log, f'adjacent cable', f'cable {adj_cable_set_no}, {adj_placed_cable_no}')
            if not (adj_cable_set_no == cable_set_no and adj_placed_cable_no == cable_no):
                # place heat top loss if within ladder
                hsd = heat_source_distance(install, adj_cable_set_no, adj_placed_cable_no,
                                           cable_set_no, cable_no,
                                           log=log)
                layer_with_heat_source = None
                if adj_elt87_state.layers[-1].layer_radius.value < (hsd + 0.001):
                    layer_with_heat_source = None
                else:
                    for layer_no, layer in enumerate(reversed(adj_elt87_state.layers)):
                        if layer.layer_radius.value > (hsd - 0.001):
                            layer_with_heat_source = len(adj_elt87_state.layers) - layer_no - 1
                        else:
                            break
                if layer_with_heat_source is not None:
                    adjacent_cable = AdjacentCable()
                    adjacent_cable.cable_no = adj_placed_cable_no
                    adjacent_cable.cable_set_no = adj_cable_set_no
                    adjacent_cable.layer_no = layer_with_heat_source
                    adjacent_cable.image = False
                    elt87_state.adjacent_cables.append(adjacent_cable)
                    no_sources += 1
                    no_sources_cable += 1
            # place image heat sources if within ladder
            hsd = heat_source_distance(install, adj_cable_set_no, adj_placed_cable_no,
                                       cable_set_no, cable_no, image=True,
                                       log=log)
            layer_with_heat_source = None
            if adj_elt87_state.layers[-1].layer_radius.value < (hsd + 0.001):
                layer_with_heat_source = None
            else:
                for layer_no, layer in enumerate(reversed(adj_elt87_state.layers)):
                    if layer.layer_radius.value > (hsd - 0.001):
                        layer_with_heat_source = len(adj_elt87_state.layers) - layer_no - 1
                    else:
                        break
            if layer_with_heat_source is not None:
                adjacent_cable = AdjacentCable()
                adjacent_cable.cable_no = adj_placed_cable_no
                adjacent_cable.cable_set_no = adj_cable_set_no
                adjacent_cable.layer_no = layer_with_heat_source
                adjacent_cable.image = True
                elt87_state.adjacent_cables.append(adjacent_cable)
                no_sources += 1
                no_sources_cable += 1
            log_end_section(log, f'adjacent cable', no_sources_cable, '',
                            f'cable {adj_cable_set_no}, {adj_placed_cable_no}')

    log_end_section(log, 'number sources', no_sources, 'm', 'number of adjacent heat sources added')
    return no_sources


def build_heat_sources(install: AutoInstall, currents: List[float], state: InstallState = None, log: Log = None):
    """Build heat sources.

    Adds all the heat sources from internal heat sources and adjacent heat sources to the ladder networks held in
    InstallState.CableSetStates[].PlacedCableStates[].Elt087State objects.

    The heat sources are calculated using the currents defined at the time specified in each current curve.

    Electra87 Section 3.3

    :param install: cable installation
    :param currents: list of currents in each cable set
    :param state: InstallState
    :param log: logger used to store results
    :return: something
    """

    log_start_section(log, 'heat sources', 'build heat sources', section_log_level=70)
    no_heat_sources = 0

    for cable_set_no, cable_set in enumerate(install.cable_sets):
        log_start_section(log, 'cable set', 'build heat sources for cable set')
        current = currents[cable_set_no]
        log_add_line(log, 'I', current, 'A', 'current in cable set')
        for placed_cable_no, placed_cable in enumerate(cable_set.placed_cables):
            no_heat_sources += 1
            log_start_section(log, f'cable heat loss', f'cable {cable_set_no}, {placed_cable_no}')
            placed_cable_state = state.cable_set_states[cable_set_no].placed_cable_states[placed_cable_no]
            elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
            layer = elt87_state.layers

            # theta_a = placed_cable.ambient_theta.get_value(unit='°C', log=log)
            theta_a = get_ambient_temperature(install, cable_set_no, placed_cable_no, log)
            theta_c, theta_sc, theta_cs = calc_conductor_temperature(state, cable_set_no, placed_cable_no, theta_a,
                                                                     log=log)
            if theta_c < -30.0 or theta_sc < -30.0:
                raise Exception('conductor or sheath temperature less than -30°C, probably iteration unstable. '
                                'Suggest reduce time slice')

            r_ac = iec60287_1_1wrapper.calc_r_ac(cable_set, placed_cable_no, theta_c,
                                                 iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                                 log=log)
            # theta_sc = layer[elt87_state.sheath_layer.value].delta_theta_j
            lambda1 = iec60287_1_1wrapper.calc_lambda_1(install, cable_set_no, placed_cable_no, theta_c,
                                                        theta_sc, log=log)
            wd = iec60287_1_1wrapper.calc_wd(install, cable_set_no, placed_cable_no, log=log)
            w_cond = current**2 * r_ac.value + wd.value / 2
            layer[elt87_state.conductor_layer.value].Wj.set_value(w_cond, unit='W/m', source='elt087 program')
            log_add_line(log, 'W_0', w_cond, 'W/m', 'conductor heat loss')
            w_sc = current**2 * r_ac.value * lambda1.value + wd.value / 2
            layer[elt87_state.sheath_layer.value].Wj.set_value(w_sc, unit='W/m', source='elt087 program')
            log_add_line(log, 'W_' + str(elt87_state.sheath_layer.value), w_sc, 'W/m', 'sheath/screen heat loss')
            w_tot = current**2 * r_ac.value * (1 + lambda1.value) + wd.value

            log_end_section(log, f'cable heat loss', w_tot, 'W/m', f'cable {cable_set_no}, {placed_cable_no}')
        log_end_section(log, 'cable set', cable_set_no, '', 'build heat sources for cable set')
    log_end_section(log, 'heat sources', no_heat_sources, 'm', 'build heat sources')


def calc_conductor_temperature(state: InstallState, cable_set_no: int, placed_cable_no: int, theta_a: float,
                               log: Log = None) -> [float, float, float]:
    """Calculate the conductor temperature of a cable (°C)

    Calculates the actual conductor temperature, taking account of the ambient temperature and temperature rise due
    to other cables nearby.

    returns conductor temperature, sheath temperature and cable surface temperature

    :param state: InstallState object that holds layer temperatures
    :param cable_set_no: the cable set containing the cable
    :param placed_cable_no: the cable number
    :param theta_a: ambient temperature (°C)
    :param log: logger used to store results
    :return: conductor temperature and sheath temperature
    """

    placed_cable_state = state.cable_set_states[cable_set_no].placed_cable_states[placed_cable_no]
    elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
    layer = elt87_state.layers

    log_start_section(log, f'theta_c ({cable_set_no}, {placed_cable_no})',
                      'conductor temperature Electra 87 Section 4.1')
    theta_c = theta_a   # conductor temperature
    theta_sc = theta_a  # sheath/screen temperature
    theta_cs = theta_a  # cable surface temperature
    cond_j = elt87_state.conductor_layer.value
    theta_c = theta_c + layer[cond_j].delta_theta_j.get_value(unit='°C', log=log, log_symbol=f'theta_{cond_j}')
    sheath_j = elt87_state.sheath_layer.value
    theta_sc = theta_sc + layer[sheath_j].delta_theta_j.get_value(unit='°C', log=log, log_symbol=f'theta_{sheath_j}')
    theta_cs = theta_cs + layer[sheath_j+1].delta_theta_j.get_value(unit='°C',
                                                                    log=log, log_symbol=f'theta_{sheath_j+1}')
    for adj_cable in elt87_state.adjacent_cables:
        adj_cable_set_no = adj_cable.cable_set_no.value
        adj_cable_no = adj_cable.cable_no.value
        adj_cable_image = 'image' if adj_cable.image.value else ''
        log_start_section(log, f'adjacent cable {adj_cable_image}', 'cable set number, cable number')
        adj_cable_layer_no = adj_cable.layer_no.value
        log_add_line(log, 'layer number', adj_cable_layer_no, '', 'layer number of adjacent cable')
        adj_cable_state = state.cable_set_states[adj_cable_set_no].placed_cable_states[adj_cable_no]
        adj_elt87_state = cast(Elt087State, adj_cable_state.get_quantity_store('elt87_state'))
        if adj_cable_image == 'image':
            adj_delta_theta = -adj_elt87_state.layers[adj_cable_layer_no].delta_theta_j.get_value(unit='°C')
        else:
            adj_delta_theta = adj_elt87_state.layers[adj_cable_layer_no].delta_theta_j.get_value(unit='°C')
        log_add_line(log, 'delta_theta', adj_delta_theta, '°C', 'elt087')
        theta_c = theta_c + adj_delta_theta
        theta_sc = theta_sc + adj_delta_theta
        theta_cs = theta_cs + adj_delta_theta
        log_end_section(log, f'adjacent cable {adj_cable_image}', f'{adj_cable_set_no}, {adj_cable_no}', '',
                        'cable set number, cable number')
    log_end_section(log, f'theta_c ({cable_set_no}, {placed_cable_no})', theta_c, '°C',
                    'conductor temperature Electra 87 Section 4.1')
    return theta_c, theta_sc, theta_cs


def calc_conductor_temperature_matrix(state: InstallState, cable_set_no: int, placed_cable_no: int, theta_a: float,
                                      theta_matrices: List[List[np.array]], log: Log = None) -> [float, float, float]:
    """Calculate the conductor temperature of a cable (°C) with matrix input

    Calculates the actual conductor temperature, taking account of the ambient temperature and temperature rise due
    to other cables nearby.

    returns conductor temperature, sheath temperature and cable surface temperature

    :param state: InstallState object that holds layer temperatures
    :param cable_set_no: the cable set containing the cable
    :param placed_cable_no: the cable number
    :param theta_a: ambient temperature (°C)
    :param theta_matrices: node temperature matrices (list of (list of cable matrices in cable_set) in install)
    :param log: logger used to store results
    :return: conductor temperature and sheath temperature
    """

    placed_cable_state = state.cable_set_states[cable_set_no].placed_cable_states[placed_cable_no]
    elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))

    log_start_section(log, f'theta_c ({cable_set_no}, {placed_cable_no})',
                      'conductor temperature Electra 87 Section 4.1')
    theta_c = theta_a   # conductor temperature
    theta_sc = theta_a  # sheath/screen temperature
    theta_cs = theta_a  # cable surface temperature
    cond_j = elt87_state.conductor_layer.value
    theta_c = float(theta_c + theta_matrices[cable_set_no][placed_cable_no][cond_j].item())
    log_add_line(log, f'theta_{cond_j}', theta_c, '°C')
    sheath_j = elt87_state.sheath_layer.value
    theta_sc = float(theta_sc + theta_matrices[cable_set_no][placed_cable_no][sheath_j].item())
    log_add_line(log, f'theta_{sheath_j}', theta_sc, '°C')
    theta_cs = float(theta_cs + theta_matrices[cable_set_no][placed_cable_no][sheath_j+1].item())
    log_add_line(log, f'theta_{sheath_j+1}', theta_cs, '°C')

    for adj_cable in elt87_state.adjacent_cables:
        adj_cable_set_no = adj_cable.cable_set_no.value
        adj_cable_no = adj_cable.cable_no.value
        adj_cable_image = 'image' if adj_cable.image.value else ''
        log_start_section(log, f'adjacent cable {adj_cable_image}', 'cable set number, cable number')
        adj_cable_layer_no = adj_cable.layer_no.value
        log_add_line(log, 'layer number', adj_cable_layer_no, '', 'layer number of adjacent cable')
        adj_cable_state = state.cable_set_states[adj_cable_set_no].placed_cable_states[adj_cable_no]
        adj_elt87_state = cast(Elt087State, adj_cable_state.get_quantity_store('elt87_state'))
        if adj_cable_image == 'image':
            adj_delta_theta = -adj_elt87_state.layers[adj_cable_layer_no].delta_theta_j.get_value(unit='°C')
        else:
            adj_delta_theta = adj_elt87_state.layers[adj_cable_layer_no].delta_theta_j.get_value(unit='°C')
        log_add_line(log, 'delta_theta', adj_delta_theta, '°C', 'elt087')
        theta_c = theta_c + adj_delta_theta
        theta_sc = theta_sc + adj_delta_theta
        theta_cs = theta_cs + adj_delta_theta
        log_end_section(log, f'adjacent cable {adj_cable_image}', f'{adj_cable_set_no}, {adj_cable_no}', '',
                        'cable set number, cable number')
    log_end_section(log, f'theta_c ({cable_set_no}, {placed_cable_no})', theta_c, '°C',
                    'conductor temperature Electra 87 Section 4.1')
    return theta_c, theta_sc, theta_cs


def calc_initial_temperatures(install: AutoInstall,
                              selected_scenario_name: str = None,
                              current_ratio: float = 1, state: InstallState = None, log: Log = None):
    """Calculate initial temperatures at time zero

    Calculates the temperatures in the resistance ladder at the start of the transient. The cables pre-loading type
    is defined in the Cable_set object. The pre-load is a steady state current and solved using IEC 60287. If the
    pre-load type is an average loss type, the average loss will be scaled by the current_ratio.

    Electra87 Section 3.3

    :param install: cable installation
    :param selected_scenario_name:
    :param current_ratio: the ratio of desired_rating needed to achieve maximum operating temperature
    :param state: InstallState
    :param log: logger used to store results
    :return: True if calculation successful
    """

    log_start_section(log, 'Set initial temperatures', 'elt087')
    log_start_section(log, 'calc conductor temperature rises', 'elt087')
    log_start_section(log, 'calc continuous rating', 'elt087')
    currents = []
    u_pe_list = []
    for cable_set in install.cable_sets:
        if cable_set.current_curve is not None and cable_set.current_curve.cyclic.value:
            if cable_set.preload_type.value != iec.PRELOAD_AVE_LOSS:
                raise Exception(f'cable set is has cyclic load but preload is {cable_set.preload_type.value}')
        if cable_set.preload_type.value == iec.PRELOAD_OFF or cable_set.preload_type.value is None:
            currents.append(0.0)
            u_pe_list.append([0.0] * len(cable_set.placed_cables))
        elif cable_set.preload_type.value == iec.PRELOAD_CONST_CURRENT:
            currents.append(cable_set.preload_current.get_value(unit='A'))
            u_pe_cable_set = []
            for placed_cable in cable_set.placed_cables:
                u_pe_cable_set.append(placed_cable.u_pe.value)
            u_pe_list.append(u_pe_cable_set)
        elif cable_set.preload_type.value == iec.PRELOAD_AVE_LOSS:
            end_time = calc_transient_end_time(install, log=log)
            if cable_set.current_curve.normalise_curve:
                current = cable_set.current_curve.calc_ave(end_time).value * cable_set.desired_I.value * current_ratio
            else:
                current = cable_set.current_curve.calc_ave(end_time).value * current_ratio
            currents.append(current)
            u_pe_cable_set = []
            for placed_cable in cable_set.placed_cables:
                u_pe_cable_set.append(placed_cable.u_pe.value)
            u_pe_list.append(u_pe_cable_set)
        else:
            raise Exception(f'calculating preload temperatures but type {cable_set.preload_type} not recognised')

    # TODO: should this use the new solve_calc_temperature version? This does not use max conductor temperatures
    current_str, install_cond_temp, _ = iec_solver.solve_calc_temperature(install,
                                                                          selected_scenario_name= selected_scenario_name,
                                                                          cable_set_currents=currents,
                                                                          u_pe_list=u_pe_list,
                                                                          log=log)
    log_end_section(log, 'calc continuous rating', '', '', 'elt087')
    # cond_temp_rise = iec_solver.calc_install_cond_temp(install, currents, install_cond_temp,
    #                                                    u_pe_list=u_pe_list, calc_temperature_rise=True,
    #                                                    log=log)
    log_end_section(log, 'calc conductor temperature rises', '', '', 'elt087')

    log_start_section(log, 'calc initial temperature rises', 'elt087')
    for cable_set_no, cable_set_state in enumerate(state.cable_set_states):
        log_start_section(log, 'cable_set_no', 'elt087')
        for cable_no, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            log_start_section(log, 'cable_no', 'elt087')
            elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
            r_ac = iec60287_1_1wrapper.calc_r_ac(install.cable_sets[cable_set_no], cable_no,
                                                 install_cond_temp[cable_set_no][cable_no],
                                                 iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value).value
            sheath_temp = iec60287_1_1wrapper.calc_theta_sc(install, cable_set_no, cable_no,
                                                            currents[cable_set_no],
                                                            install_cond_temp[cable_set_no][cable_no]).value
            lambda1 = iec60287_1_1wrapper.calc_lambda_1(install, cable_set_no, cable_no,
                                                        conductor_temperature=install_cond_temp[cable_set_no][cable_no],
                                                        sheath_temperature=sheath_temp).value
            w_d = iec60287_1_1wrapper.calc_wd(install, cable_set_no, cable_no,
                                              u_pe=u_pe_list[cable_set_no][cable_no]).value
            w_c = currents[cable_set_no]**2 * r_ac + w_d / 2.0
            w_tot = currents[cable_set_no]**2 * r_ac * (1 + lambda1) + w_d
            # theta = cond_temp_rise[cable_set_no][cable_no]
            theta = 0.0
            log_add_line(log, 'W_c', w_c, 'W/m', 'elt087')
            log_add_line(log, 'W_tot', w_tot, 'W/m', 'elt087')
            elt87_state.layers[-1].delta_theta_j.value = theta
            for layer_no in range(len(elt87_state.layers) - 2, -1, -1):
                # layer = elt87_state.layers[len(elt87_state.layers) - layer_no - 2]
                layer = elt87_state.layers[layer_no]
                layer_tr = elt87_state.layers[layer_no + 1]
                if 0 <= layer_no < elt87_state.sheath_layer.value:
                    theta = theta + w_c * layer_tr.Tj.value
                elif layer_no >= elt87_state.sheath_layer.value:
                    theta = theta + w_tot * layer_tr.Tj.value
                layer.delta_theta_j.value = theta
                log_add_line(log, f'theta {layer_no}', theta, '°C', 'elt087')
                # print(layer_no, theta)
            log_end_section(log, 'cable_no', cable_no, '', 'elt087')
        log_end_section(log, 'cable_set_no', cable_set_no, '', 'elt087')
    log_end_section(log, 'calc initial temperature rises', '', '', 'elt087')
    log_end_section(log, 'Set initial temperatures', '', '', 'elt087')


@LogSection('time_step')
def calc_time_step(state: InstallState, cable_set_no: int, cable_no: int, transient_time: float, log: Log = None):
    """Calculate the time step of an iteration at a time

    The time step for the next iteration is calculated at a given time into the transient response for a given cable.

    Electra87 Section 3.4

    :param state: InstallState
    :param cable_set_no: cable set number
    :param cable_no: cable number
    :param transient_time: time in transient response
    :param log: logger used to store results
    :return: something
    """

    placed_cable_state = state.cable_set_states[cable_set_no].placed_cable_states[cable_no]
    elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
    total_resistance = elt87_state.total_resistance.get_value(unit='K.m/W', log=log)
    total_capacitance = elt87_state.total_capacitance.get_value(unit='J/m.K', log=log)
    time_constant = total_resistance * total_capacitance
    if transient_time < time_constant / 3:
        time_step = 10**(1/3 * math.log(transient_time / time_constant, 10) - 1.58) * time_constant
    else:
        time_step = 10**(math.log(transient_time / time_constant, 10) - 1.25) * time_constant

    return QFloat(time_step, 's', 'Electra 87, Section 3.4', description='time step of iteration',
                  symbol='time_step')


def calc_fd_transient(install: AutoInstall, currents: List[float], no_iterations: int, delta_time: float,
                      resolution=None,
                      old_max_cond_temp: List[List[float]] = None,
                      start_time: float = 0.0,
                      state: InstallState = None,
                      log: Log = None) -> Tuple[Optional[List[List[float]]],
                                                Optional[List[Tuple[float,
                                                                    List[List[Tuple[float, float, float]]],
                                                                    List[float]]]]]:
    """Calculate a temperature rise after a number of iterations

    Calculates the temperature rise after the application of a current for each cable set in an installation for a given
    number of iterations with a given time step. The start temperature rise is in the Elt087State.Layer[0].delta_theta_j
    object of the given InstallState object. The end temperature is in the same object at the start temperature.

    The function recalculates the conductor and sheath losses if the conductor temperature on any cable changes by
    more than install.config.elt87_max_delta_theta.value.

    The function will check the state.cancel flag and if this is set the calculation is aborted and None is returned.
    Otherwise the function returns a nested list of maximum conductor temperatures reached

    If period_label is given, this string is used to tell the user which set of iterations is being solved if the size
    of the time steps is being varied. This has no effect on the actual calculations.

    Electra87 Section 3.5

    :param install: cable installation
    :param state: InstallState
    :param currents: list of currents in cable sets (A)
    :param no_iterations: number of iterations
    :param delta_time: size of iteration time step (s)
    :param resolution: size of iteration time step used to calculate losses and store results (s)
    :param old_max_cond_temp: maximum conductor temperatures reached previously (°C)
    :param start_time: start time of transient (s)
    :param log: logger used to store results
    :return: maximum conductor temperatures (°C), or None if calculation canceled
    """

    transient_solver = install.config.solver_transient.get_value(unit='', log=log)
    if transient_solver == iec.CALC_TRANSIENT_ELT_87_EXPLICIT_MATRIX:
        return calc_transient_explicit_matrix(install, currents, no_iterations, delta_time,
                                              resolution=resolution,
                                              old_max_cond_temp=old_max_cond_temp,
                                              start_time=start_time,
                                              state=state, log=log)
    elif transient_solver == iec.CALC_TRANSIENT_ELT_87_IMPLICIT_MATRIX:
        return calc_transient_implicit_matrix(install, currents, no_iterations, delta_time,
                                              resolution=resolution,
                                              old_max_cond_temp=old_max_cond_temp,
                                              start_time=start_time,
                                              state=state, log=log)
    elif transient_solver == iec.CALC_TRANSIENT_ELT_87:
        return calc_transient_elt087(install, currents, no_iterations, delta_time,
                                     resolution=resolution,
                                     old_max_cond_temp=old_max_cond_temp,
                                     start_time=start_time,
                                     state=state, log=log)
    else:
        raise Exception(f'trying to calculate transient but {transient_solver} not recognised')


def calc_transient_elt087(install: AutoInstall, currents: List[float], no_iterations: int, delta_time: float,
                          resolution=None,
                          old_max_cond_temp: List[List[float]] = None,
                          start_time: float = 0.0,
                          state: InstallState = None,
                          log: Log = None) -> Tuple[Optional[List[List[float]]],
                                                    Optional[List[Tuple[float,
                                                                        List[List[Tuple[float, float, float]]],
                                                                        List[float]]]]]:
    """Calculate a temperature rise after a number of iterations

    Calculates the temperature rise after the application of a current for each cable set in an installation for a given
    number of iterations with a given time step. The start temperature rise is in the Elt087State.Layer[0].delta_theta_j
    object of the given InstallState object. The end temperature is in the same object at the start temperature.

    The function recalculates the conductor and sheath losses if the conductor temperature on any cable changes by
    more than install.config.elt87_max_delta_theta.value.

    The function will check the state.cancel flag and if this is set the calculation is aborted and None is returned.
    Otherwise, the function returns a nested list of maximum conductor temperatures reached

    If period_label is given, this string is used to tell the user which set of iterations is being solved if the size
    of the time steps is being varied. This has no effect on the actual calculations.

    Electra87 Section 3.5

    :param install: cable installation
    :param state: InstallState
    :param currents: list of currents in cable sets (A)
    :param no_iterations: number of iterations
    :param delta_time: size of iteration time step (s)
    :param resolution: size of iteration time step used to calculate losses and store results (s)
    :param old_max_cond_temp: maximum conductor temperatures reached previously (°C)
    :param start_time: start time of transient (s)
    :param log: logger used to store results
    :return: maximum conductor temperatures (°C), or None if calculation canceled
    """

    if install.config.solver_transient.value == iec.CALC_TRANSIENT_ELT_87_EXPLICIT_MATRIX:
        return calc_transient_explicit_matrix(install, currents, no_iterations, delta_time,
                                              resolution=resolution,
                                              old_max_cond_temp=old_max_cond_temp,
                                              start_time=start_time,
                                              state=state, log=log)
    elif install.config.solver_transient.value == iec.CALC_TRANSIENT_ELT_87_IMPLICIT_MATRIX:
        return calc_transient_implicit_matrix(install, currents, no_iterations, delta_time,
                                              resolution=resolution,
                                              old_max_cond_temp=old_max_cond_temp,
                                              start_time=start_time,
                                              state=state, log=log)

    log_start_section(log, 'Electra 87 steps', 'Electra 87 finite difference step')
    progress_prefix = state.progress
    transient_result = []

    build_heat_sources(install, currents=currents, state=state, log=log)

    # build Aj,i equation 7 in Electra 87
    install_max_theta_c = []
    install_delta_theta_list = []
    install_losses_start_theta_list = []
    install_a_list = []
    for csn, cable_set_state in enumerate(state.cable_set_states):
        cs_max_theta_c = []
        cs_delta_theta_list = []
        cs_start_theta_list = []
        cs_a_list = []
        for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            log_start_section(log, f'A (number of elements)', 'Electra 87 Equation 7', section_log_level=70)
            elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
            a_list = []
            layers = elt87_state.layers
            for j in range(len(layers) - 1):
                log_start_section(log, f'A_{j}_i', 'Electra 87 Equation 7')
                q_j = layers[j].Qj.get_value(unit='J/m.K', log=log)
                if len(a_list) > 0:    # j > 0
                    t_j = layers[j].Tj.get_value(unit='K.m/W', log=log)
                t_jp1 = layers[j + 1].Tj.get_value(unit='K.m/W')
                log_add_line(log, 'Tj+1', t_jp1, 'K.m/W', 'Electra 87 Equation 7')
                if len(a_list) == 0:    # j == 0
                    a = 1 / (q_j * t_jp1 / delta_time + 1)
                else:
                    t_j = layers[j].Tj.get_value(unit='K.m/W', log=log)
                    a = 1 / ((1 - a_list[-1]) * t_jp1 / t_j + q_j * t_jp1 / delta_time + 1)
                a_list.append(a)
                log_end_section(log, f'A_{j}_i', a, '', 'Electra 87 Equation 7')
            cs_a_list.append(a_list)
            log_end_section(log, f'A (number of elements)', len(a_list), '', 'Electra 87 Equation 7')

            # build delta_theta_list (initial temperatures)
            elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
            delta_theta_list = []
            layers = elt87_state.layers
            for j in range(len(layers)):
                delta_theta_list.append(layers[j].delta_theta_j.value)
            cs_delta_theta_list.append(delta_theta_list)
            cs_start_theta_list.append(delta_theta_list[:])
            if old_max_cond_temp is None:
                cs_max_theta_c.append(-math.inf)
            else:
                cs_max_theta_c.append(old_max_cond_temp[csn][cn])
        install_a_list.append(cs_a_list)
        install_delta_theta_list.append(cs_delta_theta_list)
        install_losses_start_theta_list.append(cs_start_theta_list)
        install_max_theta_c.append(cs_max_theta_c)

    # start loop
    elt087_time = 0.0
    iterations = 0
    need_recalculate_losses = False
    # TODO: replace with for iterations in range(no_iterations)
    while iterations < no_iterations:
        elt087_time += delta_time
        iterations += 1

        if no_iterations == iterations:
            log_level = 30
        else:
            log_level = 50
        # log_start_section(log, f'matrix_time', '', section_log_level=log_level)
        log_start_section(log, f'elt087_time', '', section_log_level=log_level)

        if no_iterations == iterations:
            log_level = 30
        else:
            log_level = 70
        log_start_section(log, f'calculate Δθ', '', section_log_level=log_level)
        for csn, cable_set_state in enumerate(state.cable_set_states):
            for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                log_start_section(log, f'conductor Δθ cable {csn}, {cn}', '')

                # build Bj,i equation 8 in Electra 87
                log_start_section(log, f'B (number of elements)', 'Electra 87 Equation 8', section_log_level=90)
                elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
                a_list = install_a_list[csn][cn]
                delta_theta_list = install_delta_theta_list[csn][cn]
                b_list = []
                layers = elt87_state.layers
                for j in range(len(layers) - 1):
                    log_start_section(log, f'B_{j}_i', 'Electra 87 Equation 8')
                    q_j = layers[j].Qj.get_value(unit='J/m.K', log=log)
                    if len(b_list) > 0:    # j > 0
                        t_j = layers[j].Tj.get_value(unit='K.m/W', log=log)
                    t_jp1 = layers[j+1].Tj.get_value(unit='K.m/W', log=log)
                    w_j = layers[j].Wj.get_value(unit='W/m', log=log)
                    if len(b_list) == 0:    # j == 0
                        b = a_list[j] * t_jp1 * (w_j + delta_theta_list[j] * q_j / delta_time)
                    else:
                        t_j = layers[j].Tj.get_value(unit='K.m/W', log=log)
                        b = a_list[j] * t_jp1 * (w_j + delta_theta_list[j] * q_j / delta_time + b_list[j-1] / t_j)
                        log_add_line(log, f'B_{j-1}', b_list[j-1], 'C', '')
                    b_list.append(b)
                    log_add_line(log, f'θ_{j}', delta_theta_list[j], 'C', '')
                    log_end_section(log, f'B_{j}_i', b, '', 'Electra 87 Equation 8')
                log_end_section(log, f'B (number of elements)', len(b_list), '', 'Electra 87 Equation 8')

                # build new theta
                log_start_section(log, f'new theta (conductor)', 'Electra 87 Equation 8', section_log_level=90)
                a_list = install_a_list[csn][cn]
                new_theta_list = install_delta_theta_list[csn][cn][:]
                for j in range(len(layers) - 1, -1, -1):
                    # print(f"theta: cable set {csn}, cable {cn} {j}")
                    # outer layer stays constant
                    log_start_section(log, f'theta_{j}_i', 'Electra 87 Equation 9 corrected')
                    if j == len(layers) - 1:
                        new_theta = 0.0
                    else:
                        new_theta = a_list[j] * new_theta_list[j+1] + b_list[j]
                    start_theta = install_losses_start_theta_list[csn][cn][j]
                    if abs(new_theta - start_theta) > install.config.elt87_config.elt87_max_delta_theta.value:
                        need_recalculate_losses = True
                    if j == len(layers) - 1:
                        log_add_line(log, 'theta_j+1', 0.0, '-', '')
                    else:
                        log_add_line(log, 'a_j', a_list[j], '-', '')
                        log_add_line(log, 'b_j', b_list[j], '-', '')
                        log_add_line(log, 'theta_j+1', new_theta_list[j+1], '-', '')
                    new_theta_list[j] = new_theta
                    log_end_section(log, f'theta_{j}_i', new_theta, '°C', 'Electra 87 Equation 9 corrected')
                install_delta_theta_list[csn][cn] = new_theta_list
                log_end_section(log, f'new theta (conductor)', new_theta_list[0], '°C',
                                'Electra 87 Equation 9 corrected')

                log_end_section(log, f'conductor Δθ cable {csn}, {cn}', new_theta_list[0], '°C', '')
        log_end_section(log, f'calculate Δθ', '', 'Electra 87 Section 3.5', '')

        time_resolution = resolution
        if time_resolution is None or elt087_time % time_resolution < delta_time or no_iterations == iterations:
            # update results
            # copy temperatures back into state
            for csn, cable_set_state in enumerate(state.cable_set_states):
                for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                    elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
                    delta_theta_list = install_delta_theta_list[csn][cn]
                    layers = elt87_state.layers
                    for j in range(len(layers) - 1):
                        layers[j].delta_theta_j.value = delta_theta_list[j]
            theta_install = []
            for csn, cable_set_state in enumerate(state.cable_set_states):
                theta_cable_set = []
                for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                    # placed_cable = install.cable_sets[csn].placed_cables[cn]
                    theta_a = get_ambient_temperature(install, csn, cn, log)
                    theta_c = calc_conductor_temperature(state, csn, cn, theta_a, log=log)
                    theta_cable_set.append(theta_c)
                    if theta_c[0] > install_max_theta_c[csn][cn]:
                        install_max_theta_c[csn][cn] = theta_c[0]
                theta_install.append(theta_cable_set)

            transient_result.append((start_time + delta_time * iterations, theta_install, currents))

            log_start_section(log, f'need recalculate losses', '', section_log_level=30)
            old_need_recalculate_losses = need_recalculate_losses
            if need_recalculate_losses:
                # copy temperatures back into state
                for csn, cable_set_state in enumerate(state.cable_set_states):
                    for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                        elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
                        delta_theta_list = install_delta_theta_list[csn][cn]
                        layers = elt87_state.layers
                        for j in range(len(layers) - 1):
                            layers[j].delta_theta_j.value = delta_theta_list[j]
                        install_losses_start_theta_list[csn][cn] = delta_theta_list[:]
                build_heat_sources(install, currents=currents, state=state, log=log)
                need_recalculate_losses = False
            log_end_section(log, f'need recalculate losses', old_need_recalculate_losses, '',
                            f'elt87_max_delta_theta = {install.config.elt87_config.elt87_max_delta_theta}')

        if state.cancel:
            return None, None
        state.progress = f'{progress_prefix} Step: {iterations} of {no_iterations}.'

        log_end_section(log, f'elt087_time', elt087_time, 's', '')

    # copy temperatures back into state
    for csn, cable_set_state in enumerate(state.cable_set_states):
        for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
            delta_theta_list = install_delta_theta_list[csn][cn]
            layers = elt87_state.layers
            for j in range(len(layers) - 1):
                layers[j].delta_theta_j.value = delta_theta_list[j]

    state.progress = progress_prefix
    log_end_section(log, 'Electra 87 steps', iterations, '', 'Electra 87 finite difference step')
    return install_max_theta_c, transient_result


def calc_transient_explicit_matrix(install: AutoInstall, currents: List[float], no_iterations: int, delta_time: float,
                                   resolution=None,
                                   old_max_cond_temp: List[List[float]] = None,
                                   start_time: float = 0.0,
                                   state: InstallState = None,
                                   log: Log = None) -> Tuple[Optional[List[List[float]]],
                                                             Optional[List[Tuple[float,
                                                                                 List[List[Tuple[float, float, float]]],
                                                                                 List[float]]]]]:
    """Calculate a temperature rise after a number of iterations

    Calculates the temperature rise after the application of a current for each cable set in an installation for a given
    number of iterations with a given time step. The start temperature rise is in the Elt087State.Layer[0].delta_theta_j
    object of the given InstallState object. The end temperature is in the same object at the start temperature.

    The function recalculates the conductor and sheath losses if the conductor temperature on any cable changes by
    more than install.config.elt87_max_delta_theta.value.

    The function will check the state.cancel flag and if this is set the calculation is aborted and None is returned.
    Otherwise the function returns a nested list of maximum conductor temperatures reached

    If period_label is given, this string is used to tell the user which set of iterations is being solved if the size
    of the time steps is being varied. This has no effect on the actual calculations.

    Explicit Matrix method replaces Electra87 Section 3.5

    :param install: cable installation
    :param state: InstallState
    :param currents: list of currents in cable sets (A)
    :param no_iterations: number of iterations
    :param delta_time: size of iteration time step (s)
    :param resolution: size of time step between storing temperatures and calculating losses (s)
    :param old_max_cond_temp: maximum conductor temperatures reached previously (°C)
    :param start_time: start time of transient (s)
    :param log: logger used to store results
    :return: maximum conductor temperatures (°C), or None if calculation canceled
    """

    log_start_section(log, 'Matrix steps', 'Electra 87 explicit finite difference step replacement')
    progress_prefix = state.progress
    transient_result = []

    build_heat_sources(install, currents=currents, state=state, log=log)

    # build explicit Finite Difference (FD) matrices and heat loss vectors
    fd_matrices = []
    fd_heat_loss_matrices = []
    limit_matrices = []
    limit_heat_matrices = []
    theta_matrices = []
    start_theta_matrices = []
    for csn, cable_set_state in enumerate(state.cable_set_states):
        cable_set_fd_matrices = []
        cable_set_heat_loss_matrices = []
        cable_set_limit_matrices = []
        cable_set_limit_heat_matrices = []
        cable_set_theta_matrices = []
        cable_set_start_theta_matrices = []
        for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
            n = len(elt87_state.layers)

            # build explicit FD matrix: construct the thermal matrix
            row_list = []
            col_list = []
            data_list = []
            # if stabilising FD, then the FD calculates the temperature difference between iterations
            ident = 0.0 if install.config.elt87_config.stabilise_fd.value else 1.0
            for row in range(n):
                # element left of diagonal of matrix
                if 0 < row < n - 1:
                    row_list.append(row)
                    col_list.append(row - 1)
                    data_list.append(delta_time / elt87_state.layers[row].Qj.value / elt87_state.layers[row].Tj.value)
                # element on diagonal of matrix
                if row == 0:
                    row_list.append(row)
                    col_list.append(row)
                    data_list.append(ident - delta_time / elt87_state.layers[row].Qj.value *
                                     (1 / elt87_state.layers[row+1].Tj.value))
                elif row == n - 1:
                    row_list.append(row)
                    col_list.append(row)
                    data_list.append(ident)
                else:
                    row_list.append(row)
                    col_list.append(row)
                    data_list.append(ident - delta_time / elt87_state.layers[row].Qj.value *
                                     (1 / elt87_state.layers[row].Tj.value + 1 / elt87_state.layers[row+1].Tj.value))
                # element right of diagonal of matrix
                if row < n - 1:
                    row_list.append(row)
                    col_list.append(row+1)
                    data_list.append(delta_time / elt87_state.layers[row].Qj.value *
                                     (1 / elt87_state.layers[row+1].Tj.value))

            row = np.array(row_list)
            col = np.array(col_list)
            data = np.array(data_list)
            cable_set_fd_matrices.append(sps.csr_matrix((data, (row, col)), shape=(n, n), dtype=np.float32))
            # print(row_list)
            # print(col_list)
            # print(data_list)
            # fd_matrix = sps.csr_matrix((data, (row, col)), shape=(n, n))
            # print(fd_matrix.todense())

            # build explicit FD heat loss matrix
            heat_matrix = np.zeros((n, 1), dtype=np.float32)
            for row in range(n):
                heat_matrix[row, 0] = delta_time * elt87_state.layers[row].Wj.value / elt87_state.layers[row].Qj.value
            cable_set_heat_loss_matrices.append(heat_matrix)
            # print(heat_matrix)

            # construct matrices for limiting version
            row_list = []
            col_list = []
            data_list = []
            for row in range(n):
                # element left of diagonal of matrix
                if 0 < row < n - 1:
                    row_list.append(row)
                    col_list.append(row - 1)
                    data_list.append(1 / elt87_state.layers[row].Tj.value /
                                     (1 / elt87_state.layers[row].Tj.value + 1 / elt87_state.layers[row+1].Tj.value))
                # element on diagonal of matrix
                if row == n - 1:
                    row_list.append(row)
                    col_list.append(row)
                    data_list.append(1)
                # element right of diagonal of matrix
                if row == 0:
                    row_list.append(row)
                    col_list.append(row)
                    data_list.append(1)
                elif row < n - 1:
                    row_list.append(row)
                    col_list.append(row+1)
                    data_list.append(1 / elt87_state.layers[row+1].Tj.value /
                                     (1 / elt87_state.layers[row].Tj.value + 1 / elt87_state.layers[row+1].Tj.value))

            row = np.array(row_list)
            col = np.array(col_list)
            data = np.array(data_list)
            cable_set_limit_matrices.append(sps.csr_matrix((data, (row, col)), shape=(n, n), dtype=np.float32))

            # l_matrix = sps.csr_matrix((data, (row, col)), shape=(n, n))
            # print(l_matrix.todense())

            # build explicit limit heat loss matrix
            limit_heat_matrix = np.zeros((n, 1), dtype=np.float32)
            for row in range(n):
                if row == 0:
                    limit_heat_matrix[row, 0] = elt87_state.layers[row].Wj.value * elt87_state.layers[row+1].Tj.value
                elif row < n - 1:
                    limit_heat_matrix[row, 0] = (elt87_state.layers[row].Wj.value /
                                                 (1 / elt87_state.layers[row].Tj.value +
                                                  1 / elt87_state.layers[row+1].Tj.value))
            cable_set_limit_heat_matrices.append(limit_heat_matrix)
            # print(limit_heat_matrix)

            # build temperature matrix
            theta_matrix = np.zeros((n, 1), dtype=np.float32)
            for row in range(n):
                theta_matrix[row, 0] = elt87_state.layers[row].delta_theta_j.value
            cable_set_theta_matrices.append(theta_matrix)
            cable_set_start_theta_matrices.append(theta_matrix.copy())
            # print(theta_matrix)

        fd_matrices.append(cable_set_fd_matrices)
        fd_heat_loss_matrices.append(cable_set_heat_loss_matrices)
        limit_matrices.append(cable_set_limit_matrices)
        limit_heat_matrices.append(cable_set_limit_heat_matrices)
        theta_matrices.append(cable_set_theta_matrices)
        start_theta_matrices.append(cable_set_start_theta_matrices)

    # build max_theta_c
    install_max_theta_c = []
    for csn, cable_set_state in enumerate(state.cable_set_states):
        cs_max_theta_c = []
        for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            if old_max_cond_temp is None:
                cs_max_theta_c.append(-math.inf)
            else:
                cs_max_theta_c.append(old_max_cond_temp[csn][cn])
        install_max_theta_c.append(cs_max_theta_c)

    # start loop
    elt087_time = 0.0
    # need_recalculate_losses = False
    for iterations in range(no_iterations):
        elt087_time += delta_time

        if no_iterations - 1 == iterations:
            log_level = 30
        else:
            log_level = 50
        log_start_section(log, f'matrix_time', '', section_log_level=log_level)

        if no_iterations - 1 == iterations:
            log_level = 30
        else:
            log_level = 70
        log_start_section(log, f'calculate Δθ', '', section_log_level=log_level)
        # log_start_section(log, f'calculate Δθ', '')

        for csn, cable_set_state in enumerate(state.cable_set_states):
            for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                log_start_section(log, f'conductor Δθ cable {csn}, {cn}', '')

                # work out next iteration of temperature
                fd_theta_matrix = fd_matrices[csn][cn].dot(theta_matrices[csn][cn]) + fd_heat_loss_matrices[csn][cn]
                if install.config.elt87_config.stabilise_fd.value:
                    limit_theta_matrix = (limit_matrices[csn][cn].dot(theta_matrices[csn][cn]) +
                                          limit_heat_matrices[csn][cn] - theta_matrices[csn][cn])
                    bool_theta_matrix = (np.abs(fd_theta_matrix) <= np.abs(limit_theta_matrix))
                    delta_theta_matrix = np.where(bool_theta_matrix, fd_theta_matrix, limit_theta_matrix)
                    fd_theta_matrix = theta_matrices[csn][cn] + delta_theta_matrix

                # print(theta_matrices[csn][cn][0], fd_theta_matrix[0])
                theta_matrices[csn][cn] = fd_theta_matrix
                log_end_section(log, f'conductor Δθ cable {csn}, {cn}', float(fd_theta_matrix[0][0]), '°C', 'FD Matrix')

        time_resolution = resolution
        if time_resolution is None or elt087_time % time_resolution < delta_time or no_iterations - 1 == iterations:
            # update results
            # calculate cable conductor temperature
            theta_install = []
            for csn, cable_set_state in enumerate(state.cable_set_states):
                theta_cable_set = []
                for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                    theta_a = get_ambient_temperature(install, csn, cn, log)
                    theta_c = calc_conductor_temperature_matrix(state, csn, cn, theta_a, theta_matrices, log=log)
                    theta_cable_set.append(theta_c)
                    if theta_c[0] > install_max_theta_c[csn][cn]:
                        install_max_theta_c[csn][cn] = theta_c[0]
                theta_install.append(theta_cable_set)

            transient_result.append((start_time + delta_time * iterations, theta_install, currents))

            # recalculate heat losses if required
            matrix_need_recalculate_losses = False
            for csn, cable_set_state in enumerate(state.cable_set_states):
                for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                    if ((np.abs(theta_matrices[csn][cn] - start_theta_matrices[csn][cn]) >
                         install.config.elt87_config.elt87_max_delta_theta.value).any()):
                        matrix_need_recalculate_losses = True
                        break
            if matrix_need_recalculate_losses:
                for csn, cable_set_state in enumerate(state.cable_set_states):
                    for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                        start_theta_matrices[csn][cn] = theta_matrices[csn][cn].copy()

            log_start_section(log, f'need recalculate losses', '', section_log_level=30)
            old_need_recalculate_losses = matrix_need_recalculate_losses
            if matrix_need_recalculate_losses:
                # copy temperatures back into state
                for csn, cable_set_state in enumerate(state.cable_set_states):
                    for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                        elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
                        layers = elt87_state.layers
                        for j in range(len(layers) - 1):
                            layers[j].delta_theta_j.value = float(theta_matrices[csn][cn][j][0])
                build_heat_sources(install, currents=currents, state=state, log=log)
                # copy heat loss back into heat_loss_matrix
                for csn, cable_set_state in enumerate(state.cable_set_states):
                    for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                        elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
                        for row in range(len(fd_heat_loss_matrices[csn][cn])):
                            fd_heat_loss_matrices[csn][cn][row, 0] = (delta_time * elt87_state.layers[row].Wj.value /
                                                                      elt87_state.layers[row].Qj.value)
            log_end_section(log, f'need recalculate losses', old_need_recalculate_losses, '',
                            f'elt87_max_delta_theta = {install.config.elt87_config.elt87_max_delta_theta}')

        if state.cancel:
            return None, None
        state.progress = f'{progress_prefix} Step: {iterations} of {no_iterations}.'

        log_end_section(log, 'calculate Δθ', ' ', '', '***')

        log_end_section(log, f'matrix_time', elt087_time, 's', '')

    # copy temperatures back into state
    for csn, cable_set_state in enumerate(state.cable_set_states):
        for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
            layers = elt87_state.layers
            for j in range(len(layers) - 1):
                layers[j].delta_theta_j.value = float(theta_matrices[csn][cn][j][0])

    state.progress = progress_prefix
    log_end_section(log, 'Matrix steps', no_iterations, '', 'Electra 87 finite difference step')
    return install_max_theta_c, transient_result


def calc_transient_implicit_matrix(install: AutoInstall, currents: List[float], no_iterations: int, delta_time: float,
                                   resolution=None,
                                   old_max_cond_temp: List[List[float]] = None,
                                   start_time: float = 0.0,
                                   state: InstallState = None,
                                   log: Log = None) -> Tuple[Optional[List[List[float]]],
                                                             Optional[List[Tuple[float,
                                                                                 List[List[Tuple[float, float, float]]],
                                                                                 List[float]]]]]:
    """Calculate a temperature rise after a number of iterations

    Calculates the temperature rise after the application of a current for each cable set in an installation for a given
    number of iterations with a given time step. The start temperature rise is in the Elt087State.Layer[0].delta_theta_j
    object of the given InstallState object. The end temperature is in the same object at the start temperature.

    The function recalculates the conductor and sheath losses if the conductor temperature on any cable changes by
    more than install.config.elt87_max_delta_theta.value.

    The function will check the state.cancel flag and if this is set the calculation is aborted and None is returned.
    Otherwise the function returns a nested list of maximum conductor temperatures reached

    If period_label is given, this string is used to tell the user which set of iterations is being solved if the size
    of the time steps is being varied. This has no effect on the actual calculations.

    Implicit matrix method replaces Electra87 Section 3.5

    :param install: cable installation
    :param state: InstallState
    :param currents: list of currents in cable sets (A)
    :param no_iterations: number of iterations
    :param delta_time: size of iteration time step (s)
    :param resolution: size of time step between storing temperatures and calculating losses (s)
    :param old_max_cond_temp: maximum conductor temperatures reached previously (°C)
    :param start_time: start time of transient (s)
    :param log: logger used to store results
    :return: maximum conductor temperatures (°C), or None if calculation canceled
    """

    log_start_section(log, 'Matrix steps', 'Electra 87 implicit finite difference step replacement')
    progress_prefix = state.progress
    transient_result = []

    build_heat_sources(install, currents=currents, state=state, log=log)

    # build implicit Finite Difference (FD) matrices and heat loss vectors
    fd_matrices = []
    fd_heat_loss_matrices = []
    theta_matrices = []
    start_theta_matrices = []
    for csn, cable_set_state in enumerate(state.cable_set_states):
        cable_set_fd_matrices = []
        cable_set_heat_loss_matrices = []
        cable_set_theta_matrices = []
        cable_set_start_theta_matrices = []
        for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
            n = len(elt87_state.layers)

            # build inverted implicit FD matrix: construct the thermal matrix
            row_list = []
            col_list = []
            data_list = []
            for row in range(n):
                # element left of diagonal of matrix
                if 0 < row < n - 1:
                    row_list.append(row)
                    col_list.append(row - 1)
                    data_list.append(-delta_time / elt87_state.layers[row].Qj.value /
                                     elt87_state.layers[row].Tj.value)
                # element on diagonal of matrix
                if row == 0:
                    row_list.append(row)
                    col_list.append(row)
                    data_list.append(1 + delta_time / elt87_state.layers[row].Qj.value *
                                     (1 / elt87_state.layers[row+1].Tj.value))
                elif row == n - 1:
                    row_list.append(row)
                    col_list.append(row)
                    data_list.append(1)
                else:
                    row_list.append(row)
                    col_list.append(row)
                    data_list.append(1 + delta_time / elt87_state.layers[row].Qj.value *
                                     (1 / elt87_state.layers[row].Tj.value + 1 / elt87_state.layers[row+1].Tj.value))
                # element right of diagonal of matrix
                if row < n - 1:
                    row_list.append(row)
                    col_list.append(row+1)
                    data_list.append(-delta_time / elt87_state.layers[row].Qj.value *
                                     (1 / elt87_state.layers[row+1].Tj.value))

            row = np.array(row_list)
            col = np.array(col_list)
            data = np.array(data_list)
            fd_matrix = sps.csr_matrix((data, (row, col)), shape=(n, n)).todense()
            inv_fd_matrix = np.linalg.inv(fd_matrix)
            cable_set_fd_matrices.append(inv_fd_matrix)
            # cable_set_fd_matrices.append(sps.csr_matrix((data, (row, col)), shape=(n, n), dtype=np.float32))
            # print(row_list)
            # print(col_list)
            # print(data_list)
            # fd_matrix = sps.csr_matrix((data, (row, col)), shape=(n, n))
            # print(fd_matrix.todense())

            # build explicit FD heat loss matrix
            heat_matrix = np.zeros((n, 1), dtype=np.float32)
            for row in range(n):
                heat_matrix[row, 0] = delta_time * elt87_state.layers[row].Wj.value / elt87_state.layers[row].Qj.value
            cable_set_heat_loss_matrices.append(heat_matrix)
            # print(heat_matrix)

            # build temperature matrix
            theta_matrix = np.zeros((n, 1), dtype=np.float32)
            for row in range(n):
                theta_matrix[row, 0] = elt87_state.layers[row].delta_theta_j.value
            cable_set_theta_matrices.append(theta_matrix)
            cable_set_start_theta_matrices.append(theta_matrix.copy())
            # print(theta_matrix)

        fd_matrices.append(cable_set_fd_matrices)
        fd_heat_loss_matrices.append(cable_set_heat_loss_matrices)
        theta_matrices.append(cable_set_theta_matrices)
        start_theta_matrices.append(cable_set_start_theta_matrices)

    # build max_theta_c
    install_max_theta_c = []
    for csn, cable_set_state in enumerate(state.cable_set_states):
        cs_max_theta_c = []
        for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            if old_max_cond_temp is None:
                cs_max_theta_c.append(-math.inf)
            else:
                cs_max_theta_c.append(old_max_cond_temp[csn][cn])
        install_max_theta_c.append(cs_max_theta_c)

    # start loop
    elt087_time = 0.0
    # need_recalculate_losses = False
    for iterations in range(no_iterations):
        elt087_time = elt087_time + delta_time

        if no_iterations - 1 == iterations:
            log_level = 30
        else:
            log_level = 50
        log_start_section(log, f'matrix_time', '', section_log_level=log_level)

        if no_iterations - 1 == iterations:
            log_level = 30
        else:
            log_level = 70
        log_start_section(log, f'calculate Δθ', '', section_log_level=log_level)
        # log_start_section(log, f'calculate Δθ', '')

        for csn, cable_set_state in enumerate(state.cable_set_states):
            for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                log_start_section(log, f'conductor Δθ cable {csn}, {cn}', '')

                # work out next iteration of temperature
                fd_theta_matrix = fd_matrices[csn][cn].dot(theta_matrices[csn][cn] + fd_heat_loss_matrices[csn][cn])

                # print(theta_matrices[csn][cn][0], fd_theta_matrix[0])
                theta_matrices[csn][cn] = fd_theta_matrix
                log_end_section(log, f'conductor Δθ cable {csn}, {cn}', float(fd_theta_matrix[0][0].item()), '°C', 'FD Matrix')

        time_resolution = resolution
        if time_resolution is None or elt087_time % time_resolution < delta_time or no_iterations - 1 == iterations:
            # update results
            # calculate cable conductor temperature
            theta_install = []
            for csn, cable_set_state in enumerate(state.cable_set_states):
                theta_cable_set = []
                for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                    # placed_cable = install.cable_sets[csn].placed_cables[cn]
                    theta_a = get_ambient_temperature(install, csn, cn, log)
                    theta_c = calc_conductor_temperature_matrix(state, csn, cn, theta_a, theta_matrices, log=log)
                    theta_cable_set.append(theta_c)
                    if theta_c[0] > install_max_theta_c[csn][cn]:
                        install_max_theta_c[csn][cn] = theta_c[0]
                theta_install.append(theta_cable_set)

            transient_result.append((start_time + delta_time * iterations, theta_install, currents))

            # recalculate heat losses if required
            matrix_need_recalculate_losses = False
            for csn, cable_set_state in enumerate(state.cable_set_states):
                for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                    if ((np.abs(theta_matrices[csn][cn] - start_theta_matrices[csn][cn]) >
                         install.config.elt87_config.elt87_max_delta_theta.value).any()):
                        matrix_need_recalculate_losses = True
                        break
            if matrix_need_recalculate_losses:
                for csn, cable_set_state in enumerate(state.cable_set_states):
                    for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                        start_theta_matrices[csn][cn] = theta_matrices[csn][cn].copy()

            log_start_section(log, f'need recalculate losses', '', section_log_level=30)
            old_need_recalculate_losses = matrix_need_recalculate_losses
            if matrix_need_recalculate_losses:
                # copy temperatures back into state
                for csn, cable_set_state in enumerate(state.cable_set_states):
                    for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                        elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
                        layers = elt87_state.layers
                        for j in range(len(layers) - 1):
                            layers[j].delta_theta_j.value = float(theta_matrices[csn][cn][j][0].item())
                build_heat_sources(install, currents=currents, state=state, log=log)
                # copy heat loss back into heat_loss_matrix
                for csn, cable_set_state in enumerate(state.cable_set_states):
                    for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
                        elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
                        for row in range(len(fd_heat_loss_matrices[csn][cn])):
                            fd_heat_loss_matrices[csn][cn][row, 0] = (delta_time * elt87_state.layers[row].Wj.value /
                                                                      elt87_state.layers[row].Qj.value)
            log_end_section(log, f'need recalculate losses', old_need_recalculate_losses, '',
                            f'elt87_max_delta_theta = {install.config.elt87_config.elt87_max_delta_theta}')

        if state.cancel:
            return None, None
        state.progress = f'{progress_prefix} Step: {iterations} of {no_iterations}.'

        log_end_section(log, 'calculate Δθ', ' ', '', '***')

        log_end_section(log, f'matrix_time', elt087_time, 's', '')

    # copy temperatures back into state
    for csn, cable_set_state in enumerate(state.cable_set_states):
        for cn, placed_cable_state in enumerate(cable_set_state.placed_cable_states):
            elt87_state = cast(Elt087State, placed_cable_state.get_quantity_store('elt87_state'))
            layers = elt87_state.layers
            for j in range(len(layers) - 1):
                layers[j].delta_theta_j.value = float(theta_matrices[csn][cn][j][0].item())

    state.progress = progress_prefix
    log_end_section(log, 'Matrix steps', no_iterations, '', 'Electra 87 finite difference step')
    return install_max_theta_c, transient_result


# Appendix: Evaluation of the exponential integral function -Ei(-x)

@LogSection('-Ei(-x)')
def calc_exponential_integral(x: float, log: Log = None) -> QFloat:
    """Calculate the exponential integral function

    Calculates -Ei(-x)

    :param x: value greater than 0
    :param log: logger used to store results
    :return: -Ei(-x)
    """

    if log is not None:
        log.add_line('x', x, '', 'set by program')

    if 0.0 < x <= 1.0:
        a0 = -0.57721566
        a1 = +0.99999193
        a2 = -0.24991055
        a3 = +0.05519968
        a4 = -0.00976004
        a5 = +0.00107857
        exp_int = -math.log(x) + a0 + a1*x + a2*x**2 + a3*x**3 + a4*x**4 + a5*x**5
    elif x > 1.0:
        a1 = 2.334733
        b1 = 3.330657
        a2 = 0.250621
        b2 = 1.681534
        exp_int = 1/x * math.exp(-x)*((x**2 + a1*x + a2) / (x**2 + b1*x + b2))
    else:
        raise Exception(f'calculating exponential integral but input value is {x} outside allowed range')

    return QFloat(exp_int, '', 'Electra 87, Appendix', description='exponential integral',
                  symbol='-Ei(-x)')
