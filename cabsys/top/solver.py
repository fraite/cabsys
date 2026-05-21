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
     - The inner diameter of the covering is assumed to be the external diameter of the armour, but it this does not
       exist then the external diameter of the sheath/screen is used.
     - T3 is not given for many cases, for example SL or SA cables
* Section 4.2.4.3.3 T4 trefoil touching buried part metal
     - voltages for T1 multiplication do not specify U0, Um, or probably working. Best use U0 to match other places?
     - voltages for T1 multiplication stop at 150 kV, but seem to get worse?
* Section 4.2.4.3.4 T4 trefoil touching buried no sheath: no T1 or T3 multiplication factors.

"""

from typing import Optional, List, Tuple
from datetime import date
import cabsys.top.cabsys_constants as cabsys_consts
# from cabsys.data_classes.data_store import QStr
from cabsys.quantity.log import Log, no_log
from cabsys.data_classes.auto_install import AutoInstall  # , CableSet, CableSetState
from cabsys import InstallState
import cabsys.iec.iec_constants as iec
import cabsys.cigre.electra087wrapper as elt087
import cabsys.iec.iec_solver as iec_solver
import cabsys.iec.iec_solver_cct as iec_solver_cct
from cabsys.top.Exception import InvalidInput


def solve(install: AutoInstall, selected_scenario_name: str = None, state: InstallState = None,
          log: Log = no_log) -> [str, Optional[List[List[float]]], Optional[List[float]],
                               Optional[List[List[List[Tuple[float, List]]]]]]:
    """Calculate the current rating of an installation

    :param install: the installation
    :param selected_scenario_name: the scenario (for example winter)
    :param state: the state object used to hold the results
    :param log: the log used to record the intermediate calculations
    :return: (current_str: status string,
              install_cond_thetas: cable temperatures °C,
              install_amps: current of each cable set A,
              transient_result: transient results)
    """

    if log is not None:
        log.add_line(f'Cabsys version', cabsys_consts.CODE_VERSION, unit='')
        log.add_line('Date of calculation', str(date.today()), unit='')

    rating_type = install.get_rating_type(selected_scenario_name, log=log)

    if state is not None:
        state.set_memorise(install.config.memorise.get_value(unit='', log=log))

    if rating_type == iec.RATING_CONTINUOUS:
        solver = install.config.solver_continuous.get_value(unit='', log=log)
        if solver == iec.CALC_TEMPERATURE:
            current_str, cond_thetas, cond_amps = iec_solver.solve_calc_temperature(install,
                                                                                    selected_scenario_name,
                                                                                    state=state, log=log)
            transient_result = None
        elif solver == iec.CALC_CURRENT:
            current_str, cond_thetas, cond_amps = iec_solver.solve_calc_current(install,
                                                                                selected_scenario_name,
                                                                                state=state, log=log)
            transient_result = None
        elif solver == iec.CALC_TEMPERATURE_NEW:
            current_str, cond_thetas, cond_amps = iec_solver.solve_calc_temperature_new(install,
                                                                                        selected_scenario_name,
                                                                                        state=state, log=log)
            transient_result = None
        elif solver == iec.CALC_TEMPERATURE_CCT_CIRCUIT or solver == iec.CALC_TEMPERATURE_CCT_INSTALL:
            current_str, cond_thetas, cond_amps = iec_solver_cct.solve_calc_temperature_new(install,
                                                                                            selected_scenario_name,
                                                                                            state=state, log=log)
            transient_result = None
        else:
            raise InvalidInput(f'continuous rating solver "{solver}" not recognised', 'solver-62')

    elif rating_type in [iec.RATING_EMERGENCY, iec.RATING_CYCLIC, iec.RATING_TRANSIENT]:
        # TODO: update for scenarios
        current_str, max_cond_temp, transient_result = elt087.solve_calc_temperature(install, state=state, log=log)
        cond_thetas = max_cond_temp
        cond_amps = None
    else:
        raise InvalidInput(f'rating type "{rating_type}" not recognised', 'solver-66')

    if state is not None:
        state.cancel = False

    return current_str, cond_thetas, cond_amps, transient_result
