import math
from typing import Optional

from cabsys.quantity.log import Log, LogSection
from cabsys.data_classes.install import Install
from cabsys.data_classes.state import InstallState
from cabsys.quantity.quantity_store import QFloat, QuantityBase
import cabsys.iec.iec_constants as iec
import cabsys.iec.iec60949 as iec60949


def get_quantity(obj: object, attr_name: str, log: Log) -> Optional[QuantityBase]:
    if hasattr(obj, attr_name):
        quantity = getattr(obj, attr_name)
        log.add_line(attr_name, quantity.value, quantity.unit, quantity.source)
        return quantity
    else:
        raise Exception(f'Attribute {attr_name} not found in {obj}')


def results(install: Install, state: InstallState, log: Log = None) -> None:
    """Calculate details

    The results are just put in a logger.

    :param install: the installation
    :param state: the results in an InstallState object
    :param log: logger used to store results
    :return: none
    """

    log.start_section('iec_results', '')

    for cable_set_num, cable_set_state in enumerate(state.cable_set_states):
        log.start_section(f'cable set {cable_set_num} current', '')
        amps = get_quantity(cable_set_state, 'I', log)
        for cable_num, place_cable_state in enumerate(cable_set_state.placed_cable_states):
            log.start_section('cable', '')
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
            if install.cable_sets[cable_set_num].duct_layout.value != iec.NO_DUCTS:
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
        log.end_section(f'cable set {cable_set_num} current', amps.value, amps.unit, amps.source)

    log.end_section('iec_results', '', '', '')
    return