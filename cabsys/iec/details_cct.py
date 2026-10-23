# import math
from typing import Optional

from cabsys.quantity.log import Log
from cabsys.data_classes.install import Install
from cabsys.data_classes.state_cct import InstallState
from cabsys.quantity.quantity_store import QuantityBase
import cabsys.iec.iec_constants as iec
# import cabsys.iec.iec60949 as iec60949


def get_quantity(obj: object, attr_name: str, log: Log) -> Optional[QuantityBase]:
    if hasattr(obj, attr_name):
        quantity = getattr(obj, attr_name)
        log.add_line(attr_name, quantity.value, quantity.unit, quantity.source)
        return quantity
    else:
        raise Exception(f'Attribute {attr_name} not found in {obj}')


def results(install: Install, state: InstallState, log: Optional[Log] = None) -> None:
    """Calculate details

    The results are just put in a logger. This is generally put at the end of the logger, in case the logger is set
    to log very little information, in which case the logger at least contains some summary information.

    :param install: the installation
    :param state: the results in an InstallState object
    :param log: logger used to store results
    :return: none
    """

    if log is None:
        return

    log.start_section('iec_results', '', section_log_level=5)

    for circuit_num, install_circuit_state in enumerate(state.install_circuit_states):
        log.start_section(f'circuit number {circuit_num} current', '')
        cable_set_states = install_circuit_state.cable_set_states
        circuit_amps = 0.0
        circuit_amps_unit = ''
        circuit_amps_source = ''
        for cable_set_num, cable_set_state in enumerate(cable_set_states):
            log.start_section(f'cable set {cable_set_num}', '')
            for cable_num, place_cable_state in enumerate(cable_set_state.placed_cable_states):
                log.start_section('cable', '')
                amps = get_quantity(place_cable_state.cable_state, 'I', log)
                cond_resistance = get_quantity(place_cable_state.cable_state, 'R_C', log)
                lambda_1 = get_quantity(place_cable_state.cable_state, 'lambda_1', log)

                log.start_section('total losses', 'calculated in results section')
                cond_loss = amps.value**2 * cond_resistance.value
                log.add_line('cond_loss', cond_loss, 'W/m', 'calculated in results section')
                wd = get_quantity(place_cable_state.cable_state, 'wd', log)
                sheath_loss = cond_loss * lambda_1.value
                log.add_line('sheath loss', sheath_loss, 'W/m', 'calculated in results section')
                total_loss = cond_loss + wd.value + sheath_loss
                log.end_section('total losses', total_loss, 'W/m', 'calculated in results section')

                log.start_section('thermal resistances', '')
                insulation_res = get_quantity(place_cable_state.cable_state, 'T_1', log)
                serving_res = get_quantity(place_cable_state.cable_state, 'T_3', log)
                if install.install_circuits[circuit_num].cable_sets[cable_set_num].duct_layout.value != iec.NO_DUCTS:
                    ground_t_4d = get_quantity(place_cable_state.cable_state, 'T_4d', log)
                    ground_t_4dd = get_quantity(place_cable_state.cable_state, 'T_4dd', log)
                else:
                    ground_t_4d = None
                    ground_t_4dd = None
                ground_t_4ddd = get_quantity(place_cable_state.cable_state, 'T_4ddd', log)
                ground_res = get_quantity(place_cable_state.cable_state, 'T_4', log)
                log.end_section('thermal resistances', '', '', source='calculated in results section')

                cond_temp = get_quantity(place_cable_state.cable_state, 'cond_temp', log)
                sheath_temp = get_quantity(place_cable_state.cable_state, 'sheath_temp', log)
                cable_surface_temp = sheath_temp.value - total_loss * serving_res.value
                log.add_line('θ cable surface', cable_surface_temp, '°C', 'calculated in results section')
                if hasattr(place_cable_state.cable_state, 'duct_air_temp'):
                    duct_air_temp = get_quantity(place_cable_state.cable_state, 'duct_air_temp', log)
                if ground_t_4d is not None:
                    duct_surface_temp = cable_surface_temp - total_loss * (ground_t_4d.value + ground_t_4dd.value)
                    log.add_line('θ duct surface', duct_surface_temp, '°C', 'calculated in results section')
                log.end_section('cable', cable_num, '', '')
                if cable_num == 0:
                    circuit_amps = circuit_amps + amps.value
                    circuit_amps_unit = amps.unit
                    circuit_amps_source = amps.source
            log.end_section(f'cable set {cable_set_num}', '', '', '')
        log.end_section(f'circuit number {circuit_num} current', circuit_amps, circuit_amps_unit, circuit_amps_source)

    log.end_section('iec_results', '', '', '')
    return