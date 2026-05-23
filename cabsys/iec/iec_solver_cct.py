"""Solver

* Section 4.1.2.1 T1
     - is undermined by Section 4.2.4.3.3 trefoil touching part metal covered cables buried cables, and
       probably also by Section 4.2.4.3.4 for non-metal sheathed cables as T1 is multiplied by 1.07/1.16
     - used t1 defined as thickness between conductor and sheath/screen but conflicts with T1 in
       IEC 60287-1-1
* Section 4.1.4.1 T3
     - is undermined by Section 4.2.4.3.2 trefoil touching metal sheath cables, Section 4.2.4.3.3 trefoil touching part
       metal covered cables buried cables, and probably also by Section 4.2.4.3.4 for non-metal sheathed cables as T3 is
       multiplied by 1.6
     - The inner diameter of the covering is assumed to be the external diameter of the armour, but this does not
       exist then the external diameter of the sheath/screen is used.
     - T3 is not given for many cases, for example SL or SA cables
* Section 4.2.4.3.3 T4 trefoil touching buried part metal
     - voltages for T1 multiplication do not specify U0, Um, or probably working. Best use U0 to match other places?
     - voltages for T1 multiplication stop at 150 kV, but seem to get worse?
* Section 4.2.4.3.4 T4 trefoil touching buried no sheath: no T1 or T3 multiplication factors.

"""

import math
import time
import copy
from typing import List, Tuple, Optional

import cabsys.data_classes.state
from cabsys.data_classes.state_cct import UseState
# import cabsys.quantity.quantity_constants as dc
from cabsys.quantity.quantity_store import QFloat
from cabsys.quantity.log import Log, LogSection, no_log
# from cabsys.data_classes.cable import Cable
from cabsys.data_classes.auto_install import AutoInstall  # , CableSet, CableSetState
from cabsys.data_classes.state_cct import InstallState
from cabsys import IEC60287Exception
# from cabsys.data_classes.project import Project
# from cabsys import CableState
# from cabsys.data_classes.install import CableSet
import cabsys.iec.iec60287support as iec60287support
import cabsys.iec.iec60287_1_1_cct as iec60287_1_1
import cabsys.iec.iec60287_2_1_cct as iec60287_2_1
import cabsys.iec.iec_constants as iec
import cabsys.cigre.tb283_cim as tb283_cim
# import cabsys.cigre.electra087wrapper as elt087
# import cabsys.iec.iec60853_2 as iec60853_2
# from cabsys.top.Exception import InvalidInput, SolverException

CableParamsList = List[List[List[float]]]
"""List of cable parameters in an installation

List of parameters associated with each cable in an installation, for example conductor temperature:

  [[cct1_set1_θ, cct1_set2_θ, cct1_set2_θ, ...],
  [cct2_set1_θ, cct2_set2_θ, ...], ...]
where
  cct*_set*_θ = [θ_c, θ_1, θ_2] for a three phase circuit"""


def create_result_string(install: AutoInstall, install_cond_thetas: CableParamsList,
                         install_cable_amps: Optional[CableParamsList]=None,
                         install_circuit_amps: Optional[List[float]]=None) -> str:
    """Create a string that summarises the given conductor temperature and circuit currents

    If the cable amps is given the circuit amps is calculated. Otherwise, the circuit amps given will be used.

    :param install: the installation
    :param install_cond_thetas: a nested list that contains the conductor temperatures of the installation (°C)
    :param install_cable_amps: nested list of cable currents (A)
    :param install_circuit_amps: list of circuit currents (A)
    :return: string summarising conductor temperatures and circuit currents
    """

    current_str = 'θ, I ='
    for circuit_num, install_circuit in enumerate(install.install_circuits):
        max_cond_theta = -math.inf
        if install_cable_amps is not None:
            circuit_amp = 0.0
        elif install_circuit_amps is not None:
            circuit_amp = install_circuit_amps[circuit_num]
        else:
            raise IEC60287Exception('trying to create a result string but no amps have been given')
        for cable_set_num, cable_set in enumerate(install_circuit.cable_sets):
            set_cond_thetas = install_cond_thetas[circuit_num][cable_set_num]
            set_max_cond_theta = max(set_cond_thetas)
            max_cond_theta = max(set_max_cond_theta, max_cond_theta)
            if install_cable_amps is not None:
                circuit_amp = circuit_amp + install_cable_amps[circuit_num][cable_set_num][0]
        current_str = current_str + (f' cct {circuit_num}: {round(max_cond_theta, 1)}, '
                                     f'{round(circuit_amp, 1)}')
    return current_str


def solve_calc_temperature_new(install: AutoInstall,
                               selected_scenario_name: Optional[str] = None,
                               u_pe_list: Optional[List[List[List[float]]]] = None,
                               state: Optional[InstallState] = None,
                               log: Optional[Log] = None) -> Tuple[str, CableParamsList, CableParamsList]:
    """Calculate conductor temperatures for a given installation and set of currents

    Calculates the conductor temperature for a list of given cable_set conductor currents, listed in order of cable
    sets.

    The calculations calculate the a.c. resistance of the conductors at the actual temperatures the conductors are at
    rather than at the maximum operating temperature and hence the results do not comply with IEC 60287 but are closer
    to reality.

    If no cable_set currents are given, the currents defined in the given install are used. The install has the option
    to change the currents so that the maximum conductor temperature is reached, set by the desired_I_change flag in
    the cable_set object. This will change all the cable_set currents that are allowed to change by the same ratio until
    at least one cable in one cable_set reaches the maximum conductor operating temperature.

    :param install: installation
    :param selected_scenario_name: the scenario (for example winter)
    :param u_pe_list: list of phase to earth voltages applied to cables (V)
    :param state:
    :param log:
    :return: (current_str: status string,
              install_cable_cond_thetas: cable temperatures °C,
              circuit_amps: current of each cable set A)
    """

    if log is None:
        log = no_log

    log.start_section('current, temperature', source=f'solve_calc_temperature')
    log.add_line('max_cond_resistance', install.config.max_cond_theta.value, unit='',
                 source=f'IEC 60287-1-1 Section 5.1.1')
    log.add_line('amp_accuracy', install.config.amp_accuracy.value, unit='A',
                 source='config: iteration accuracy current rating')
    log.add_line('cond_theta_accuracy', install.config.cond_theta_accuracy.value, unit='°C',
                 source='config: iteration accuracy conductor temperature')

    start_time = time.perf_counter()
    time_taken = 0.0

    # set initial values of conductor temperature and current for each placed cable / cable set
    log.start_section('initial θ and circuit I', source=f'solve_calc_temperature')
    install_cable_cond_thetas = []
    install_circuit_amps = []
    install_cable_amps = []
    ambient_theta = install.ambient_theta.get_value(unit='°C', log=log)
    if ambient_theta is None:
        raise IEC60287Exception('trying to calculate rating but ambient_theta is None for this installation')
    for install_circuit_num, install_circuit in enumerate(install.install_circuits):
        log.start_section(f'I circuit={install_circuit_num}', source=f'solve_calc_temperature')
        install_circuit_cond_thetas = []
        circuit_cable_amps = []
        circuit_amp_estimate = 0.0
        if install_circuit.desired_I_change.value and install.config.solver_continuous.value == iec.CALC_TEMPERATURE_CCT_CIRCUIT:
            for cable_set_num, cable_set in enumerate(install_circuit.cable_sets):
                log.start_section(f'I cable_set={cable_set_num}', source=f'solve_calc_temperature')
                cable_set_thetas = []
                cable_set_r0 = []
                cable_set_w_d = []
                log.start_section(f'Wd, Rd', source=f'solve_calc_temperature')
                for p_cable_num, p_cable in enumerate(cable_set.placed_cables):
                    log.start_section(f'Wd, Rd cable_num={p_cable_num}', source=f'solve_calc_temperature')
                    cable_theta = iec60287support.get_cond_temp(p_cable.cable).get_value(unit='°C', log=log)
                    cable_set_thetas.append(cable_theta)
                    cable_set_r0.append(iec60287_1_1.calc_r_dash(p_cable.cable, cable_theta, log=log).value)
                    if u_pe_list is None:
                        u_pe = None
                    else:
                        u_pe = u_pe_list[install_circuit_num][cable_set_num][p_cable_num]
                    cable_w_d = iec60287_1_1.calc_wd(install, install_circuit_num, cable_set_num, p_cable_num,
                                                     u_pe=u_pe,
                                                     state=state, log=log).value
                    if cable_w_d is None:
                        raise Exception(f'trying to calculate cable_w_d but the result is None')
                    cable_set_w_d.append(cable_w_d)
                    log.end_section(f'Wd, Rd cable_num={p_cable_num}', f'{round(cable_w_d, 4)}, {cable_set_r0[-1]}', 'W/m',
                                    source=f'solve_calc_temperature')
                install_circuit_cond_thetas.append(cable_set_thetas)
                conductor_theta = min(cable_set_thetas)
                w_d = max(cable_set_w_d)
                r0 = max(cable_set_r0)
                log.end_section(f'Wd, Rd', f'{round(w_d, 4)},  {r0}', 'W/m, ohm/m',
                                source=f'solve_calc_temperature')
                if install.kind.get_value(unit='', log=log) == iec.BURIED:
                    ground_tr = install.ground_tr.get_value(unit='K.m/W', log=log)
                    amp_estimate = math.sqrt((conductor_theta - ambient_theta - w_d * 1.5 * ground_tr)
                                             / (r0 * 1.5 * ground_tr))
                else:
                    amp_estimate = math.sqrt((conductor_theta - ambient_theta - w_d * 0.25)
                                             / (r0 * 0.25))
                set_cable_amps = [amp_estimate] * len(cable_set.placed_cables)
                circuit_cable_amps.append(set_cable_amps)
                circuit_amp_estimate = circuit_amp_estimate + amp_estimate
                log.end_section(f'I cable_set={cable_set_num}', amp_estimate, unit="A",
                                source='iec_solver.calculate_temperature')
            install_cable_amps.append(circuit_cable_amps)
        else:
            # user has set the current rating of the circuit
            circuit_amp_estimate = install_circuit.desired_I.get_value(unit='A')
            for cable_set_num, cable_set in enumerate(install_circuit.cable_sets):
                log.start_section(f'cable_set={cable_set_num}', source=f'solve_calc_temperature')
                cable_set_thetas = []
                for p_cable_num, p_cable in enumerate(cable_set.placed_cables):
                    log.start_section(f'cable_num={p_cable_num}', source=f'solve_calc_temperature')
                    cable_theta = iec60287support.get_cond_temp(p_cable.cable).get_value(unit='°C', log=log)
                    cable_set_thetas.append(cable_theta)
                    log.end_section(f'cable_num={p_cable_num}', '-', '-',
                                    source=f'solve_calc_temperature')
                install_circuit_cond_thetas.append(cable_set_thetas)
                log.end_section(f'cable_set={cable_set_num}', '-', unit="-",
                                source='iec_solver.calculate_temperature')

        install_cable_cond_thetas.append(install_circuit_cond_thetas)
        install_circuit_amps.append(circuit_amp_estimate)
        log.end_section(f'I circuit={install_circuit_num}', circuit_amp_estimate, unit="A",
                        source='iec_solver.calculate_temperature')
    # create current_str
    current_str = create_result_string(install, install_cable_cond_thetas, install_circuit_amps=install_circuit_amps)
    log.end_section('initial θ and circuit I', current_str, '°C, A',  source=f'solve_calc_temperature')

    install_cable_amps = tb283_cim.cim(install, install_circuit_amps, state=state, log=log)

    iteration = 0
    accuracy_achieved = False
    max_num_iterations = install.config.max_rate_iteration.get_value(log=log)

    if install.config.log_iterate.value:
        log_iterate = log
    else:
        log_iterate = no_log

    old_install_cable_amps = old_install_cable_cond_thetas = None  # <-- needed to stop linter complaining
    while (iteration < max_num_iterations and not accuracy_achieved and
           (time_taken < 1.0 or not install.config.auto_calc.value)):
        iteration = iteration + 1

        old_install_cable_cond_thetas = copy.deepcopy(install_cable_cond_thetas)
        old_install_cable_amps = copy.deepcopy(install_cable_amps)

        accuracy_achieved, install_cable_amps, install_cable_cond_thetas = calc_temperatures(install,
                                                                                             install_cable_amps,
                                                                                             install_cable_cond_thetas,
                                                                                             iteration,
                                                                                             selected_scenario_name,
                                                                                             u_pe_list,
                                                                                             state, log_iterate)
        time_taken = time.perf_counter() - start_time

    # repeat last calculation if only logging last iteration
    if (not install.config.log_iterate.value and (time_taken < 1.0 or not install.config.auto_calc.value) and
        old_install_cable_amps is not None and old_install_cable_cond_thetas is not None ):
        accuracy_achieved, install_cable_amps, install_cable_cond_thetas = calc_temperatures(install,
                                                                                 old_install_cable_amps,
                                                                                 old_install_cable_cond_thetas,
                                                                                 iteration, selected_scenario_name,
                                                                                 u_pe_list,
                                                                                 state, log)

    # create current_str
    current_str = create_result_string(install, install_cable_cond_thetas, install_cable_amps)
    log.end_section('current, temperature', current_str, '', source=f'solve_calc_temperature')

    if log is not None:
        log.add_line('number of iterations', iteration, '', '')
        log.add_line('time taken', time_taken, 's', '')

    return current_str, install_cable_cond_thetas, install_circuit_amps


def calc_temperatures(install: AutoInstall,
                      old_install_cable_amps: CableParamsList,
                      old_install_cable_cond_thetas: CableParamsList,
                      iteration: int,
                      selected_scenario_name: Optional[str] = None,
                      u_pe_list: Optional[List[List[List[float]]]] = None,
                      state: Optional[InstallState] = None,
                      log: Log = no_log) -> Tuple[bool, CableParamsList, CableParamsList]:
    """Calculate estimate conductor temperatures and new estimated current ratings

    For a given set of conductor currents and estimated conductor temperatures, calculate new estimated conductor
    temperatures and current ratings. This is a single iteration, which needs to be repeated to get an accurate
    estimate. The function calculates if the required accuracy is achieved.

    :param install:
    :param old_install_cable_amps:
    :param old_install_cable_cond_thetas:
    :param iteration:
    :param selected_scenario_name:
    :param u_pe_list:
    :param state:
    :param log:
    :return: accuracy_achieved, install_amps, install_cond_thetas
    """

    # Can not use results from past iteration so need to clear state object if memorisation is being used
    if state is not None and state.get_memorise():
        state.clear_quantities()

    # start iteration
    log.start_section(f'iteration={iteration}', source=f'solve_calc_temperature')
    install_cable_cond_thetas = []
    install_cable_amps = []
    install_circuit_amp_ratios = []
    install_circuit_theta_ratios = []
    install_amp_ratio = math.inf
    install_theta_ratio = math.inf
    for i_circuit, install_circuit in enumerate(install.install_circuits):
        log.start_section(f'I, θ ratio (circuit {i_circuit})', 'calculate temperature solver')
        circuit_cable_cond_thetas: List[List[float]] = []
        circuit_amp_ratio = math.inf
        circuit_theta_ratio = math.inf
        for i_cable_set, cable_set in enumerate(install_circuit.cable_sets):
            log.start_section(f'max θ_est (cable set {i_cable_set})', 'calculate temperature solver')
            cable_set_cond_thetas = []
            for i_placed_cable, placed_cable in enumerate(cable_set.placed_cables):
                if old_install_cable_amps[i_circuit][i_cable_set][i_placed_cable] is None:
                    raise IEC60287Exception(f'calculating conductor temperature but current is None for cable set {i_cable_set}')
                log.start_section(f'θ_est cable={i_placed_cable}', source='calculate temperature solver')
                log.add_line('assumed I', old_install_cable_amps[i_circuit][i_cable_set][i_placed_cable],
                             'A', 'calculate temperature solver')
                cable_cond_theta = calc_cable_cond_temp(install, i_circuit, i_cable_set, i_placed_cable,
                                                        old_install_cable_amps, old_install_cable_cond_thetas,
                                                        selected_scenario_name,
                                                        u_pe_list=u_pe_list,
                                                        state=state, log=log).get_value2(unit='°C')
                cable_set_cond_thetas.append(cable_cond_theta)
                log.start_section(f'I, θ ratio', 'calculate temperature solver')
                log.start_section(f'desired_I_change', 'user want conductor current be calculated?')
                if install_circuit.desired_I_change.value:


                    old_cable_cond_theta = old_install_cable_cond_thetas[i_circuit][i_cable_set][i_placed_cable]
                    old_circuit_amps = old_install_cable_amps[i_circuit][i_cable_set][i_placed_cable]
                    if u_pe_list is None:
                        u_pe = None
                    else:
                        u_pe = u_pe_list[i_circuit][i_cable_set][i_placed_cable]
                    delta_theta_d = iec60287_1_1.calc_delta_theta_d(install,
                                                                    i_circuit, i_cable_set, i_placed_cable,
                                                                    current=old_circuit_amps,
                                                                    cond_temp=old_cable_cond_theta,
                                                                    u_pe=u_pe,
                                                                    state=state, log=log).get_value2(unit='°C')
                    max_cond_theta = iec60287support.get_cond_temp(placed_cable.cable).get_value2(unit='°C', log=log)
                    ambient_theta = install.ambient_theta.get_value(unit='°C', log=log)



                    amp_ratio = math.sqrt((max_cond_theta - delta_theta_d - ambient_theta)
                                          / (cable_cond_theta - delta_theta_d - ambient_theta))
                    theta_ratio = max_cond_theta / cable_cond_theta
                else:
                    amp_ratio = 1.0
                    theta_ratio = 1.0
                log.end_section(f'desired_I_change', install_circuit.desired_I_change.value, '',
                                'user want conductor current be calculated?')

                # cable_amp_ratios.append(amp_ratio)
                circuit_amp_ratio = min(amp_ratio, circuit_amp_ratio)
                install_amp_ratio = min(amp_ratio, install_amp_ratio)
                # cable_theta_ratios.append(theta_ratio)
                circuit_theta_ratio = min(theta_ratio, circuit_theta_ratio)
                install_theta_ratio = min(theta_ratio, install_theta_ratio)
                log.end_section(f'I, θ ratio', f'{amp_ratio: .7f}, {theta_ratio: .7f}',
                                unit='', source='calculate temperature solver')
                log.end_section(f'θ_est cable={i_placed_cable}',
                                f'{cable_cond_theta: .7f}',
                                unit='°C', source='estimated conductor temperature')
            # check to see if using IEC 60287-1-1 simplification - all cables in set use max conductor temperature
            log.start_section(f'use max_cond_theta', 'use IEC 60287-2-1 Section 4.2.3.2 approximation')
            if install.config.max_cond_theta.value:
                circuit_cable_cond_thetas.append([max(cable_set_cond_thetas)] * len(cable_set_cond_thetas))
                log.add_line('θ', max(cable_set_cond_thetas), '°C', 'set all conductor θ')
            else:
                circuit_cable_cond_thetas.append(cable_set_cond_thetas)
            log.end_section(f'use max_cond_theta', install.config.max_cond_theta.value, '',
                            'use IEC 60287-2-1 Section 4.2.3.2 approximation')

            log.end_section(f'max θ_est (cable set {i_cable_set})',
                            f'{max(circuit_cable_cond_thetas[-1]): .7f}',
                            '°C', 'calc_install_cond_temp solver')
        # circuit_amp_ratio = min(cable_amp_ratios)
        install_circuit_amp_ratios.append(circuit_amp_ratio)
        # circuit_theta_ratio = min(cable_theta_ratios)
        install_circuit_theta_ratios.append(circuit_theta_ratio)
        install_cable_cond_thetas.append(circuit_cable_cond_thetas)
        log.end_section(f'I, θ ratio (circuit {i_circuit})',
                        f'{circuit_amp_ratio: .7f}, {circuit_theta_ratio: .7f}',
                        '', 'calculate temperature solver')

    # update install_amps and conductor temperatures
    log.start_section('update I and θ', source='')
    if install.config.solver_continuous.value == iec.CALC_TEMPERATURE_CCT_CIRCUIT:
        fixed_install_ratio = False
    elif install.config.solver_continuous.value == iec.CALC_TEMPERATURE_CCT_INSTALL:
        fixed_install_ratio = True
    else:
        raise IEC60287Exception(f'trying to update amps/thetas but continuous solver is {install.config.solver_continuous.value}')
    log.add_line('fixed install ratio?', fixed_install_ratio, '', 'install.config.solver_continuous')
    for i_circuit, install_circuit in enumerate(install.install_circuits):
        log.start_section(f'install circuit', source='')
        circuit_cable_thetas = install_cable_cond_thetas[i_circuit]
        circuit_cable_amps = []
        for i_cable_set, cable_set in enumerate(install_circuit.cable_sets):
            log.start_section(f'cable set', source='')
            set_cable_amps = []
            set_cable_thetas = circuit_cable_thetas[i_cable_set]
            for i_cable, conductor_theta in enumerate(set_cable_thetas):
                if fixed_install_ratio:
                    log.start_section(f'new I_est, θ_est cable={i_cable}', source=f'calculate estimated I (fixed install ratio)')
                    log.add_line('old I', old_install_cable_amps[i_circuit][i_cable_set][i_cable], 'A', 'previous calculation')
                    log.add_line('install amp ratio', f'{install_amp_ratio}', 'pu', 'previous calculation')
                    set_cable_amps.append(install_amp_ratio * old_install_cable_amps[i_circuit][i_cable_set][i_cable])
                    log.add_line('old θ', set_cable_thetas[i_cable], '°C', 'previous calculation')
                    log.add_line('install θ ratio', f'{install_theta_ratio}', 'pu', 'previous calculation')
                    set_cable_thetas[i_cable] = install_theta_ratio * set_cable_thetas[i_cable]
                    log.end_section(f'new I_est, θ_est cable={i_cable}',
                                    f'{set_cable_amps[i_cable]: 0.2f}, {set_cable_thetas[i_cable]: 0.2f}', unit='A, °C',
                                 source=f'calculate estimated I (fixed install ratio)')
                else:
                    log.start_section(f'new I_est, θ_est cable={i_cable}', source=f'calculate estimated I')
                    log.add_line('old I', old_install_cable_amps[i_circuit][i_cable_set][i_cable], 'A', 'previous calculation')
                    log.add_line('circuit amp ratio', f'{install_circuit_amp_ratios[i_circuit]}', 'pu', 'previous calculation')
                    set_cable_amps.append(install_circuit_amp_ratios[i_circuit] * old_install_cable_amps[i_circuit][i_cable_set][i_cable])
                    log.add_line('old θ', set_cable_thetas[i_cable], '°C', 'previous calculation')
                    log.add_line('circuit θ ratio', f'{install_circuit_theta_ratios[i_circuit]}', 'pu', 'previous calculation')
                    set_cable_thetas[i_cable] = install_circuit_theta_ratios[i_circuit] * set_cable_thetas[i_cable]
                    log.end_section(f'new I_est, θ_est cable={i_cable}',
                                    f'{set_cable_amps[i_cable]: 0.2f}, {set_cable_thetas[i_cable]: 0.2f}', unit='A, °C',
                                 source=f'calculate estimated I')
                if state is not None:
                    cable_set_state = state.install_circuit_states[i_circuit].cable_set_states[i_cable_set]
                    cable_state = cable_set_state.placed_cable_states[i_cable].cable_state
                    if  cable_state is not None:
                        cable_state.set_quantity('I', set_cable_amps[i_cable],
                                                 'A', 'current rating of cable set',
                                                 'new calculate temperature solver', symbol='I')


            circuit_cable_amps.append(set_cable_amps)

            thetas = " ".join(str(round(theta, 1)) for theta in install_cable_cond_thetas[i_circuit][i_cable_set])
            log.end_section(f'cable set', i_cable_set, unit='', source='')
        install_cable_amps.append(circuit_cable_amps)
        log.end_section(f'install circuit', i_circuit, unit='', source='')
    log.end_section('update I and θ', '', '', source='')

    # calculate if another iteration is required
    # calculate temperature accuracy
    log.start_section('accuracy I, θ', source=f'difference between estimated and assumed values')
    log.start_section('accuracy θ', source=f'max difference between estimated and assumed θ')
    max_theta_accuracy = 0.0
    for circuit_num, set_cable_cond_thetas in enumerate(install_cable_cond_thetas):
        circuit_max_theta_accuracy = 0.0
        log.start_section(f'accuracy θ cct={circuit_num}', source='')
        for cable_set_num, cable_set_thetas in enumerate(set_cable_cond_thetas):
            for cable_num, cable_theta in enumerate(cable_set_thetas):
                theta_accuracy = abs(cable_theta - old_install_cable_cond_thetas[circuit_num][cable_set_num][cable_num])
                circuit_max_theta_accuracy = max(circuit_max_theta_accuracy, theta_accuracy)
                max_theta_accuracy = max(max_theta_accuracy, theta_accuracy)
                log.add_line(f'accuracy θ (set={cable_set_num}, cable={cable_num})', theta_accuracy, '°C',
                             'difference between estimated and assumed θ')
        log.end_section(f'accuracy θ cct={circuit_num}', max_theta_accuracy, '', source='')
    log.end_section('accuracy θ', max_theta_accuracy, "°C", source=f'max difference between estimated and assumed θ')
    # calculate current rating accuracy
    log.start_section('accuracy I', source=f'max difference between estimated and assumed I')
    max_amp_accuracy = 0.0
    for circuit_num, circuit_cable_amps in enumerate(install_cable_amps):
        circuit_max_amp_accuracy = 0.0
        log.start_section(f'accuracy I cct={circuit_num}', source='')
        for cable_set_num, cable_set_amps in enumerate(circuit_cable_amps):
            for cable_num, cable_amp in enumerate(cable_set_amps):
                amp_accuracy = abs(cable_amp - old_install_cable_amps[circuit_num][cable_set_num][cable_num])
                circuit_max_amp_accuracy = max(circuit_max_amp_accuracy, amp_accuracy)
                max_amp_accuracy = max(max_amp_accuracy, amp_accuracy)
                log.add_line(f'accuracy I (set={cable_set_num})', amp_accuracy, 'A',
                             'difference between estimated and assumed I')
        log.end_section(f'accuracy I cct={circuit_num}', circuit_max_amp_accuracy, '', source='')
    log.end_section('accuracy I', max_amp_accuracy, 'A', source=f'max difference between estimated and assumed I')
    log.end_section('accuracy I, θ', f'{max_amp_accuracy: .2e}, {max_theta_accuracy: .2e}',
                    unit="A, °C", source=f'difference between estimated and assumed values')
    # is another iteration required
    log.start_section('accuracy achieved', source=f'or is another iteration required?')
    accuracy_achieved = ((max_theta_accuracy < install.config.cond_theta_accuracy.value) and
                         (max_amp_accuracy < install.config.amp_accuracy.value))
    log.add_line('θ accuracy', max_theta_accuracy, '°C',
                 f"required accuracy {install.config.cond_theta_accuracy.value}")
    log.add_line('I accuracy', max_amp_accuracy, 'A',
                 f"required accuracy {install.config.amp_accuracy.value}")
    log.end_section('accuracy achieved', accuracy_achieved, '', source=f'or is another iteration required?')

    current_str = create_result_string(install, install_cable_cond_thetas, install_cable_amps)
    log.end_section(f'iteration={iteration}', current_str, '', source=f'solve_calc_temperature')
    return accuracy_achieved, install_cable_amps, install_cable_cond_thetas



@UseState('cond_temp', level=cabsys.data_classes.state.CABLE)
@LogSection('θ')
def calc_cable_cond_temp(install: AutoInstall, circuit_num: int, cable_set_no: int, cable_no,
                         install_current: CableParamsList, old_install_cond_temp: CableParamsList,
                         selected_scenario_name: Optional[str] = None,
                         u_pe_list: Optional[CableParamsList] = None,
                         state: Optional[InstallState] = None, log: Optional[Log] = None) -> QFloat:
    """Calculate the cable conductor temperature

    Calculates the next iteration for a cable conductor temperature for a given current, which needs to assume the
    conductor temperature.

    :param install: installation containing the cable
    :param circuit_num: circuit number in the installation
    :param cable_set_no: cable set number for the cable set containing the cable
    :param cable_no: cable number
    :param install_current: list of currents for each cable_set
    :param old_install_cond_temp: assumed conductor temperatures for each cable
    :param selected_scenario_name: the scenario (for example winter)
    :param u_pe_list: list of phase to earth voltages applied to cables (V)
    :param state: object holding results
    :param log: logger
    :return: conductor temperature or conductor temperature rise (°C)
    """

    if log is None:
        log = no_log

    u_pe = None if u_pe_list is None else u_pe_list[circuit_num][cable_set_no][cable_no]
    log.add_line('assumed θ', old_install_cond_temp[circuit_num][cable_set_no][cable_no],
                 '°C', 'calculated previously or set')
    dt = iec60287_1_1.calc_delta_theta(install, circuit_num=circuit_num, cable_set_num=cable_set_no, cable_num=cable_no,
                                       current=install_current[circuit_num][cable_set_no][cable_no],
                                       cond_temp=old_install_cond_temp[circuit_num][cable_set_no][cable_no],
                                       u_pe=u_pe,
                                       state=state, log=log).value

    kind = install.kind.get_value(unit='', log=log)
    if kind == iec.BURIED:
        delta_theta_p = iec60287_2_1.calc_delta_theta_p(install, circuit_num, cable_set_no, cable_no,
                                                        old_install_cond_temp,
                                                        install_current,
                                                        u_pe_list=u_pe_list,
                                                        state=state, log=log).value
    else:
        delta_theta_p = 0.0

    # theta_a = install.cable_sets[cable_set_no].placed_cables[cable_no].ambient_theta.get_value(unit='°C', log=log)
    # placed_cable = install.cable_sets[cable_set_no].placed_cables[cable_no]
    theta_a = install.get_ambient_temperature_cct(selected_scenario_name,
                                                  circuit_num, cable_set_no, cable_no, unit='°C', log=log)
    cond_temp = delta_theta_p + dt + theta_a
    description = 'conductor temperature'
    symbol = 'θ'

    return QFloat(cond_temp, '°C', 'IEC 60287-1-1 clause 2.1', description=description, symbol=symbol)

