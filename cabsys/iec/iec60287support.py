import math
from typing import Any, Union, Tuple

from cabsys import IEC60287Exception
import cabsys.data_classes.auto_install
from cabsys.quantity.quantity_store import QuantityStore, QStr, QFloat, QInt, QBool
import cabsys.quantity.quantity_constants as dc
import cabsys as cs
import cabsys.iec.iec_constants as iec
from cabsys.data_classes.state import CableState, CableSetState, CABLE
from cabsys.data_classes.state import UseState
from cabsys.data_classes.cable import Cable, Tape, Wire, Sheath
from cabsys.quantity.log import Log, LogSection

TAPE_LAY_SHORT = 'short lay length'
TAPE_LAY_54 = 'lay angle at approximately 54°'
TAPE_LAY_LONG = 'long lay length'
TAPE_LAY_MULTIPLE_LAYERS = 'multiple layers of tape'


def get_parameter(parameter_store: QuantityStore, attr_name: str, log: cs.Log = None) -> Any:
    """Get a parameter from a DataStore object's attribute

    Parameters such as conductor dc resistance at 20 °C can be found as attributes of a DataStore object. Parameters
    are normally defined as values in IEC but may be set by the user in the DataStore object. In such cases the object
    will hold the value as an attribute of the DataStore class and the top will indicate this has been set by the
    user. The value will be returned and the Log updated to warn that the user has set the value. Otherwise None is
    returned.

    :param attr_name:         attribute name of parameter
    :param parameter_store:   the object potentially holding the attribute
    :param log:               the calculation log
    :return:                  the parameter value if found, otherwise None
    """

    if (getattr(parameter_store, attr_name) is not None and
            parameter_store.get_source(attr_name) in dc.ATTR_FIXED_INPUTS):
        parameter_value = parameter_store.get_quantity(attr_name, log=log)
        if log is not None:
            log.add_warning(attr_name + ' set by user input')
    else:
        parameter_value = None
    return parameter_value


# TODO: get rid of get_q_parameter and use qantity.get_fixed_value instead
def get_q_parameter(quantity: Union[QFloat, QInt, QStr, QBool], log: cs.Log = None) -> Any:
    """Get a parameter

    Parameters such as conductor dc resistance at 20 °C can be found as a Quantity of a QuantityStore object. Parameters
    are normally defined as values in IEC but may be set by the user in the QuantityStore object. In such cases the
    object will hold the value as a Quantity in the QuantityStore class and the source will indicate this has been set
    by the user. The value will be returned and the Log updated to warn that the user has set the value. Otherwise, None
    is returned.

    :param quantity:           the Quantity potentially holding the parameter
    :param log:               the calculation log
    :return:                  the parameter value if found, otherwise None
    """

    if quantity.source in dc.ATTR_FIXED_INPUTS:
        parameter_value = quantity.get_value(log=log)
        if log is not None:
            log.add_warning(f'{quantity.symbol} set by user input')
    else:
        parameter_value = None
    return parameter_value


def get_cond_temp(cable: Cable, cond_temp: float = None,
                  state: cabsys.data_classes.state.CableState = None, log: cabsys.Log = None) -> QFloat:
    """Get the operating conductor temperature of a cable

    The operating conductor temperature of a cable is determined in the following order:

    * the value given in the argument (in which case cable_state is updated)
    * cable_state if defined if user input #TODO: this feature does not work anymore
    * max_cond_temp in the cable object if user input
    * IEC default maximum temperature (90°C)

    :param cable: the cable
    :param cond_temp: operating conductor temperature (°C)
    :param state: the result object
    :param log: calculation log
    :return: operating conductor temperature (°C)
    """

    if cond_temp is not None:
        symbol = 'θ'
        if state is not None:
            state.set_quantity('cond_temp', cond_temp, '°C', log=log,
                               source='set or calculated previously', symbol='θ')
    else:
        if state is not None and state.get_source('cond_temp') in dc.ATTR_FIXED_INPUTS:
            cond_temp = state.get_quantity('cond_temp', log=log).value
            if log is not None:
                log.add_warning('conductor temperature set by user input in cable state')
            symbol = 'θ'
        elif cable.max_cond_temp.value is not None and cable.max_cond_temp.source in dc.ATTR_FIXED_INPUTS:
            # cond_temp = cable.max_cond_temp
            cond_temp = cable.max_cond_temp.get_value(unit='°C', log=log)
            if log is not None:
                log.add_warning('maximum conductor temperature set by user input in cable parameters')
            cond_temp_unit = '°C'
            if state is not None:
                state.set_quantity('cond_temp', cond_temp, cond_temp_unit,
                                   source='cable parameters maximum conductor temperature',
                                   description='conductor temperature', symbol='θ max')
            symbol = 'θ max'
        else:
            cond_temp = 90.0
            if log is not None:
                log.add_line('θ', cond_temp, '°C', 'IEC 60840, IEC 62067 or IEC 60141')
            if state is not None:
                state.set_quantity('cond_temp', cond_temp, '°C',
                                   source='IEC 60840, IEC 62067 or IEC 60141',
                                   description='conductor temperature', symbol='θ max')
            symbol = 'θ max'

    return QFloat(cond_temp, '°C', 'IEC 60840, IEC 62067 or IEC 60141',
                  description='conductor temperature', symbol=symbol)


@LogSection('θ max')
def get_max_cond_temp(cable: Cable, log: cabsys.Log = None) -> QFloat:
    """Get the maximum conductor temperature of a cable

    The maximum conductor temperature of a cable is determined in the following order:

    * max_cond_temp in the cable object if user input
    * IEC default maximum temperature (90°C)

    :param cable: the cable
    :param log: calculation log
    :return: operating conductor temperature (°C)
    """

    if cable is None:
        raise IEC60287Exception('trying to get maximum conductor temperature but no cable defined (cable = None)')

    if cable.max_cond_temp.value is not None and cable.max_cond_temp.source in dc.ATTR_FIXED_INPUTS:
        cond_temp = cable.max_cond_temp.get_value(unit='°C', log=log)
        if log is not None:
            log.add_warning('maximum conductor temperature set by user input in cable parameters')
    else:
        # TODO: get rid of magic number
        cond_temp = 90.0

    return QFloat(cond_temp, '°C', 'IEC 60840, IEC 62067 or IEC 60141',
                  description='conductor temperature', symbol='θ max')


def get_emergency_cond_temp(cable: Cable, emergency_cond_temp: float = None,
                            state: cabsys.data_classes.state.CableState = None, log: cabsys.Log = None) -> QFloat:
    """Get the emergency conductor temperature of a cable

    The emergency operating conductor temperature of a cable is determined in the following order:

    * the value given in the argument (in which case cable_state is updated)
    * cable_state if defined if user input
    * max_emergency_cond_temp in the cable object if user input
    * maximum operating temperature

    :param cable: the cable
    :param emergency_cond_temp: operating conductor temperature (°C)
    :param state: the result object
    :param log: calculation log
    :return: operating conductor temperature (°C)
    """

    if emergency_cond_temp is not None:
        symbol = 'θ_e'
        if state is not None:
            state.set_quantity('emergency_cond_temp', emergency_cond_temp,
                               '°C', log=log, source='set or calculated previously', symbol='θ_e')
    else:
        if state is not None and state.get_source('emergency_cond_temp') in dc.ATTR_FIXED_INPUTS:
            emergency_cond_temp = state.get_quantity('emergency_cond_temp', log=log).value
            if log is not None:
                log.add_warning('emergency conductor temperature set by user input in cable state')
            symbol = 'θ_e'
        elif (cable.max_emergency_cond_temp.value is not None and
              cable.max_emergency_cond_temp.source in dc.ATTR_FIXED_INPUTS):
            # cond_temp = cable.max_cond_temp
            emergency_cond_temp = cable.max_emergency_cond_temp.get_value(unit='°C', log=log)
            if log is not None:
                log.add_warning('maximum emergency conductor temperature set by user input in cable parameters')
            cond_temp_unit = '°C'
            if state is not None:
                state.set_quantity('emergency_cond_temp', emergency_cond_temp, cond_temp_unit,
                                   source='cable parameters maximum emergency conductor temperature',
                                   description='emergency conductor temperature', symbol='θ_e max')
            symbol = 'θ_e max'
        else:
            emergency_cond_temp = get_cond_temp(cable, state=state, log=log).value
            symbol = 'θ_e max'

    return QFloat(emergency_cond_temp, '°C', 'IEC 60840, IEC 62067 or IEC 60141',
                  description='emergency conductor temperature', symbol=symbol)


@LogSection('Clearance')
def calc_clearance_dia(cable: Cable, log: cabsys.Log = None) -> QFloat:
    """Calculate the metal sheath / screen internal diameter

    Finds the clearance under the innermost metal sheath or screen.

    :param cable: cable
    :param log: logger
    :return: clearance of cable
    """

    if cable.tape.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating clearance: tape material not defined')
    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating clearance: sheath material not defined')
    if cable.wire_screen.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating clearance: wire screen material not defined')

    clearance = math.inf

    if cable.wire_screen.material.get_value(unit='') != iec.NONE:
        clearance = min(cable.wire_screen.dia_under_wire.get_value(unit='mm', log=log), clearance)

    if cable.sheath.material.get_value(unit='') != iec.NONE:
        dia_under_sheath = cable.sheath.dia_under_sheath.get_value(unit='mm', log=log)
        sheath_dia = cable.sheath.dia.get_value(unit='mm', log=log)
        sheath_rt = cable.sheath.thickness.get_value(unit='mm', log=log)
        sheath_clearance = (dia_under_sheath + sheath_dia) / 2 - sheath_rt
        clearance = min(sheath_clearance, clearance)
        if log is not None:
            log.add_line('metal sheath clearance', sheath_clearance, unit='mm', source='IEC 60287 support')

    if cable.tape.material.get_value(unit='') != iec.NONE:
        clearance = min(cable.tape.dia_under_tape.get_value(unit='mm', log=log), clearance)

    if clearance == math.inf:
        raise IEC60287Exception('Calculating clearance: cable does not have a metal sheath, screen or tape')

    return QFloat(clearance, 'mm', 'IEC 60287 support function',
                  description='internal diameter of sheath/screen', symbol='clearance')


@LogSection('Ds')
def calc_sheath_diameter(cable: Cable, log: cabsys.Log = None) -> QFloat:
    """Calculate the metal sheath external diameter

    Finds the diameter of the sheath.

    :param cable: cable
    :param log: logger
    :return: sheath/screen diameter
    """

    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating metal sheath diameter: sheath material not defined')

    if cable.sheath.material.get_value(unit='') != iec.NONE:
        dia_under_sheath = cable.sheath.dia_under_sheath.get_value(unit='mm', log=log)
        sheath_dia = cable.sheath.dia.get_value(unit='mm', log=log)
        sheath_rt = cable.sheath.thickness.get_value(unit='mm', log=log)
        if dia_under_sheath is None or sheath_dia is None or sheath_rt is None:
            raise IEC60287Exception(f'trying to calculate sheath diameter dia_under_sheath or'
                                    f' sheath_dia or sheath_rt is None')
        diameter = (dia_under_sheath + sheath_dia) / 2 + sheath_rt
    else:
        raise IEC60287Exception('Calculating sheath diameter: cable does not have a metal sheath')
    return QFloat(diameter, 'mm', 'IEC 60287 support function',
                  description='diameter of sheath', symbol='D_s')


@LogSection('Ds')
def calc_sheath_screen_diameter(cable: Cable, log: cabsys.Log = None) -> QFloat:
    """Calculate the metal sheath / screen external diameter

    Finds the diameter of the outermost metal sheath or screen. It is assumed that the order of the metal layers
    are: copper wire screen, metal sheath, metal tape.

    :param cable: cable
    :param log: logger
    :return: sheath/screen diameter
    """

    if cable.tape.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating screen diameter: tape material not defined')
    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating screen diameter: sheath material not defined')
    if cable.wire_screen.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating screen thickness: wire screen material not defined')
    if cable.tape.material.get_value(unit='') != iec.NONE:
        diameter = cable.tape.dia.get_value(unit='mm', log=log)
    elif cable.sheath.material.get_value(unit='') != iec.NONE:
        diameter = calc_sheath_diameter(cable, log).value
    elif cable.wire_screen.material.get_value(unit='') != iec.NONE:
        diameter = cable.wire_screen.dia.get_value(unit='mm', log=log)
    else:
        raise IEC60287Exception('Calculating sheath/screen diameter: cable does not have a metal sheath,'
                                ' screen or tape')
    return QFloat(diameter, 'mm', 'IEC 60287 support function',
                  description='diameter of sheath/screen', symbol='D_s')


@LogSection('sheath/screen rms diameter')
def calc_sheath_screen_mean_diameter(cable: Cable, ignore_csw_tape: bool = False,
                                     log: cabsys.Log = None) -> QFloat:
    """Calculate the metal sheath / screen mean diameter

    The mean sheath / screen diameter for each sheath or screen is calculated, and the r.m.s of all the mean sheath
    diameter is then calculated. If ignore_cws_tape is set to True then the wire screen and tape layer is ignored, as
    required for calculating eddy current losses.

    :param cable: cable with sheath or screen
    :param ignore_csw_tape: if True then result does not include the wire screen
    :param log: logger
    :return: sheath/screen rms diameter
    """

    dia_tot = 0.0
    n = 0.0
    if cable.tape.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating sheath/screen thickness: tape material not defined')
    if cable.tape.material.get_value(unit='') != iec.NONE and not ignore_csw_tape:
        diameter = cable.tape.dia.get_value(unit='mm', log=log)
        clearance = cable.tape.dia_under_tape.get_value(unit='mm', log=log)
        mean_tape_dia = (diameter + clearance) / 2
        dia_tot = dia_tot + mean_tape_dia ** 2
        if log is not None:
            log.add_line('mean tape dia', mean_tape_dia, unit='mm')
        n = n + 1

    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating sheath/screen thickness: sheath material not defined')
    if cable.sheath.material.get_value(unit='') != iec.NONE:
        dia_under_sheath = cable.sheath.dia_under_sheath.get_value(unit='mm', log=log)
        sheath_dia = cable.sheath.dia.get_value(unit='mm', log=log)
        mean_sheath_dia = ((dia_under_sheath + sheath_dia) / 2)
        dia_tot = dia_tot + mean_sheath_dia ** 2
        if log is not None:
            log.add_line('mean sheath dia', mean_sheath_dia, unit='mm')
        n = n + 1

    if cable.wire_screen.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating sheath/screen thickness: wire screen material not defined')
    if cable.wire_screen.material.get_value(unit='') != iec.NONE and not ignore_csw_tape:
        clearance = cable.wire_screen.dia_under_wire.get_value(unit='mm', log=log)
        diameter = cable.wire_screen.dia.get_value(unit='mm', log=log)
        mean_wire_dia = ((clearance + diameter) / 2)
        dia_tot = dia_tot + mean_wire_dia ** 2
        if log is not None:
            log.add_line('mean wire dia', mean_wire_dia, unit='mm')
        n = n + 1

    if n == 0:
        raise IEC60287Exception('Calculating sheath/screen mean diameter:'
                                ' cable does not have a metal sheath, screen or tape')
    else:
        rms_dia = math.sqrt(dia_tot / n)

    return QFloat(rms_dia, 'mm', 'IEC 60287 60287-1-1:2023 Section 5.4.2',
                  description='rms diameter of sheath/screen', symbol='d')


@LogSection('tape lay length')
def calc_tape_lay_length(tape: Tape, log: cabsys.Log = None) -> QStr:
    """Calculate the tape lay length

    IEC 60287-1-1 Section 2.4.1 states that the reinforcement resistance is dependent on the lay of the tapes. Four
    scenarios are specified, long lay, approximately 54°, short and multiple layers. No boundaries between each category
    is specified and the following has been implemented:

    * TAPE_LAY_LONG single layer with angle < 10°
    * TAPE_LAY_54 single layer with 40° < angle < 60°
    * TAPE_LAY_SHORT single layer with angle > 70°
    * TAPE_MULTIPLE_TAPE_LAYERS number layers > 1 and angle > 70°

    :param tape: tape layer within a cable
    :param log: logger
    :return: tape lay length
    """

    tape_angle = tape.angle.get_value(unit='°', log=log)
    number_layers = tape.number_layers.get_value(unit='', log=log)

    if number_layers == 1 and tape_angle < 10.0:
        tape_lay = TAPE_LAY_LONG
    elif number_layers == 1 and 40.0 < tape_angle < 60.0:
        tape_lay = TAPE_LAY_54
    elif number_layers == 1 and tape_angle > 70.0:
        tape_lay = TAPE_LAY_SHORT
    elif number_layers > 1 and tape_angle > 70.0:
        tape_lay = TAPE_LAY_MULTIPLE_LAYERS
    else:
        raise IEC60287Exception(f'Calculating tape lay type but {number_layers} tape layers with angel of {tape_angle}'
                                f' not in IEC 60287-1-1 Section 2.4.1')

    return QStr(tape_lay, 'n/a', 'IEC 60287-1-1 Section 4.4.1 (support function)',
                description='tape lay length', symbol='tape lay')


@LogSection('t_s')
def calc_sheath_screen_thickness(cable: Cable, ignore_csw_tape: bool = False, log: cabsys.Log = None) -> QFloat:
    """Calculate the metal sheath / screen thickness

    The sheath / screen thickness for each sheath or screen is calculated, and the total for all sheaths / screens is
    then calculated. If ignore_cws_tape is set to True then the wire screen and tape layers are ignored, as required for
    specially bonded cables.

    Raises IEC60287exception if ignore_cws_tape not set to True, as thickness is only required for specially bonded
    cables and calculation of tape thickness unclear (probably needs to follow tape resistance rules)

    :param cable: cable with sheath or screen
    :param ignore_csw_tape: if True then result does not include the wire screen
    :param log: logger
    :return: sheath/screen thickness (mm)
    """

    if not ignore_csw_tape:
        raise IEC60287Exception('Calculating metal sheath/screen thickness but only ignore_cws_tape implemented')

    sheath_thickness = None

    if cable.tape.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating screen thickness: tape material not defined')
    if cable.tape.material.get_value(unit='') != iec.NONE and not ignore_csw_tape:
        # tape_thickness = cable.tape.get_attr('tape_thickness', log=log)
        raise IEC60287Exception('tape layer not implemented')

    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating screen thickness: sheath material not defined')
    if cable.sheath.material.get_value(unit='') != iec.NONE:
        sheath_thickness = cable.sheath.thickness.get_value(unit='mm', log=log)
        if sheath_thickness is None:
            raise IEC60287Exception('trying to calculate screen thickness: it sheath_thickness is None')

    if cable.wire_screen.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating screen thickness: wire screen material not defined')
    if cable.wire_screen.material.get_value(unit='') != iec.NONE and not ignore_csw_tape:
        raise IEC60287Exception('copper wire screen not implemented')

    return QFloat(sheath_thickness, 'mm', 'IEC 60287 support function',
                  description='sheath thickness', symbol='t_s')


@LogSection('R_tape')
def calc_tape_resistance(tape: Tape, tape_temperature: float, log: cabsys.Log = None) -> QFloat:
    """Calculate the resistance of tape layer

    Calculates the resistance of a given tape layer, either screen, reinforcement or armour. The method used is based
    on the IEC 60287-1-1 method for tape reinforcement.

    :param tape: tape layer within a cable
    :param tape_temperature: temperature of tape (°C)
    :param log: logger
    :return: tape resistance (ohm/m)
    """

    res20 = get_q_parameter(tape.dc_resistance20, log=log)
    if res20 is None:
        res20 = calc_tape_resistance20(tape, log=log).value

    alpha20 = get_q_parameter(tape.alpha20, log=log)
    if alpha20 is None:
        material = tape.material.get_value(unit='', log=log)
        alpha20 = find_alpha20_sheath(material, log=log).value

    res = res20 * (1 + (tape_temperature - 20) * alpha20)

    return QFloat(res, 'Ω/m', 'IEC 60287 support function',
                  description='tape resistance', symbol='tape resistance')


@LogSection('R_tape20')
def calc_tape_resistance20(tape: Tape, log: cabsys.Log = None) -> QFloat:
    """Calculate the resistance of tape layer at 20 °C

    Calculates the resistance of a given tape layer at 20 °C, either screen, reinforcement or armour. The method used is
    based on the IEC 60287-1-1 method for tape reinforcement.

    :param tape: tape layer within a cable
    :param log: logger
    :return: tape resistance (ohm/m)
    """

    tape_lay_length = calc_tape_lay_length(tape, log=log)
    number_tapes = tape.number_tapes.get_value(unit='', log=log)
    tape_thickness = tape.tape_thickness.get_value(unit='mm', log=log)
    tape_width = tape.tape_width.get_value(unit='mm', log=log)
    lay_angle = tape.angle.get_value(unit='°', log=log)

    rho = get_q_parameter(tape.resistivity, log=log)
    if rho is None:
        material = tape.material.get_value(unit='', log=log)
        rho = find_rho_sheath(material, log=log).value

    area = number_tapes * tape_thickness * tape_width / math.cos(lay_angle * math.pi / 180.0)
    res20_long_lay = rho / area * 1e6

    res = None
    if tape_lay_length.value == TAPE_LAY_LONG:
        res = res20_long_lay
    if tape_lay_length.value == TAPE_LAY_54:
        res = 2 * res20_long_lay
    if tape_lay_length.value == TAPE_LAY_SHORT:
        res = math.inf
    if tape_lay_length.value == TAPE_LAY_MULTIPLE_LAYERS:
        res = 2 * res20_long_lay

    return QFloat(res, 'Ω/m', 'IEC 60287 support function',
                  description='tape resistance at 20 °C', symbol='R_tape20')


@LogSection('R_wire')
def calc_wire_resistance(wire: Wire, wire_temperature: float, log: cabsys.Log = None) -> QFloat:
    """Calculate the resistance of wire screen (or armour) layer

    Calculates the resistance of a given wire screen layer.

    :param wire: wire screen layer within a cable
    :param wire_temperature: temperature of wire screen (°C)
    :param log: logger
    :return: wire screen resistance (ohm/m)
    """

    res20 = get_q_parameter(wire.dc_resistance20, log=log)
    if res20 is None:
        res20 = calc_wire_resistance20(wire, log=log).value

    alpha20 = get_q_parameter(wire.alpha20, log=log)
    if alpha20 is None:
        material = wire.material.get_value(unit='', log=log)
        alpha20 = find_alpha20_sheath(material, log=log).value

    res = res20 * (1 + (wire_temperature - 20) * alpha20)

    return QFloat(res, 'Ω/m', 'IEC 60287 support function',
                  description='wire resistance', symbol='wire resistance')


@LogSection('R_wire20')
def calc_wire_resistance20(wire: Wire, log: cabsys.Log = None) -> QFloat:
    """Calculate the resistance of wire screen (or armour) layer at 20°C

    Calculates the resistance of a given wire screen layer at 20°C.

    :param wire: wire screen layer within a cable
    :param log: logger
    :return: wire screen resistance (ohm/m)
    """

    number_wires = wire.number_wires.get_value(unit='', log=log)
    wire_size = wire.wire_size.get_value(unit='mm', log=log)

    rho = get_q_parameter(wire.resistivity, log=log)
    if rho is None:
        material = wire.material.get_value(unit='', log=log)
        rho = find_rho_sheath(material, log=log).value

    area = number_wires * math.pi * wire_size ** 2 / 4
    res20 = rho / area * 1e6

    return QFloat(res20, 'Ω/m', 'IEC 60287 support function',
                  description='wire resistance at 20 °C', symbol='R_wire20')


@LogSection('R_sheath')
def calc_sheath_resistance(sheath: Sheath, sheath_temperature: float = None, log: cabsys.Log = None) -> QFloat:
    """Calculate the resistance of metal sheath

    Calculates the resistance of a given sheath layer.

    :param sheath: sheath layer within a cable
    :param sheath_temperature: temperature of sheath (°C)
    :param log: logger
    :return: wire screen resistance (ohm/m)
    """

    res20 = calc_sheath_resistance20(sheath, log=log).value
    alpha20 = get_q_parameter(sheath.alpha20, log=log)
    if alpha20 is None:
        material = sheath.material.get_value(unit='', log=log)
        alpha20 = find_alpha20_sheath(material, log=log).value
    res = res20 * (1 + (sheath_temperature - 20) * alpha20)

    return QFloat(res, 'Ω/m', 'IEC 60287 support function',
                  description='sheath resistance', symbol='sheath resistance')


@LogSection('R_sheath20')
def calc_sheath_resistance20(sheath: Sheath, log: cabsys.Log = None) -> QFloat:
    """Calculate the resistance of metal sheath at 20°C

    Calculates the resistance of a given sheath layer.

    :param sheath: sheath layer within a cable
    :param log: logger
    :return: wire screen resistance (ohm/m)
    """

    res20 = get_q_parameter(sheath.dc_resistance20, log=log)
    if res20 is None:
        sheath_dia = sheath.dia.get_value(unit='mm', log=log)
        dia_under_sheath = sheath.dia_under_sheath.get_value('mm', log=log)
        sheath_thickness = sheath.thickness.get_value(unit='mm', log=log)
        rho = get_q_parameter(sheath.resistivity, log=log)
        if rho is None:
            material = sheath.material.get_value(unit='', log=log)
            rho = find_rho_sheath(material, log=log).value
        area = (sheath_dia + dia_under_sheath) / 2 * sheath_thickness * math.pi
        res20 = rho / area * 1e6

    return QFloat(res20, 'Ω/m', 'IEC 60287 support function',
                  description='sheath resistance at 20°C', symbol='R_sheath20')


# TODO: make into single input and output only, following IEC?
# @UseState('R_s_multi')
# @LogSection('R_s_multi')
def calc_sheath_screen_resistance(cable: Cable,
                                  theta_sc: Union[Tuple[float, float, float], float] = None,
                                  ignore_csw_tape: bool = False,
                                  iec_60287_1_1_ver: str = None,
                                  state: CableState = None,
                                  log: cabsys.Log = None) -> Union[Tuple[float, float, float, float], QFloat]:
    """Calculate the metal sheath / screen resistance ohm/m)

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

    if state is not None and isinstance(theta_sc, QFloat):
        if state.get_source('R_s') in dc.ATTR_FIXED_INPUTS or (state.get_memorise() and
                                                               state.get_quantity('R_s') is not None):
            return state.get_q_float('R_s', log=log)

    if state is not None and isinstance(theta_sc, tuple):
        if state.get_source('R_s_c') in dc.ATTR_FIXED_INPUTS or (state.get_memorise() and
                                                                 state.get_quantity('R_s_c') is not None):
            resistance = state.get_quantity('R_s_c', log=log).value
            wire_resistance = state.get_quantity('R_s_w', log=log).value
            sheath_resistance = state.get_quantity('R_s_s', log=log).value
            tape_resistance = state.get_quantity('R_s_t', log=log).value
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
            wire_resistance = calc_wire_resistance(cable.wire_screen, theta_sc_w, log=log).value
            inv_sheath_screen_resistance = inv_sheath_screen_resistance + 1 / wire_resistance
    else:
        wire_resistance = math.inf

    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating sheath/screen resistance: metal sheath material has not been defined')
    if cable.sheath.material.get_value(unit='') != iec.NONE:
        sheath_resistance = calc_sheath_resistance(cable.sheath, theta_sc_s, log=log).value
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
            tape_resistance = calc_tape_resistance(cable.tape, theta_sc_t, log=log).value
            inv_sheath_screen_resistance = inv_sheath_screen_resistance + 1 / tape_resistance
    else:
        tape_resistance = math.inf

    if inv_sheath_screen_resistance == 0:
        resistance = math.inf
    else:
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

    if isinstance(theta_sc, tuple):
        if state is not None:
            state.set_quantity('R_s_c', resistance, 'Ω/m', source=source, symbol='R_s_c')
            state.set_quantity('R_s_w', wire_resistance, 'Ω/m', source=source, symbol='R_s_w')
            state.set_quantity('R_s_s', sheath_resistance, 'Ω/m', source=source, symbol='R_s_s')
            state.set_quantity('R_s_t', tape_resistance, 'Ω/m', source=source, symbol='R_s_t')
        return resistance, wire_resistance, sheath_resistance, tape_resistance
    else:
        if state is not None:
            state.set_quantity('R_s', resistance, 'Ω/m', source=source, symbol='R_s')
        return QFloat(resistance, 'Ω/m', source=source,
                      description='sheath/screen resistance', symbol='R_s')
        # return resistance


@LogSection('ρ_s')
def calc_sheath_screen_resistivity(cable: Cable,
                                   sheath_screen_temperature, sheath_temp_source: str = 'set or calculated previously',
                                   log: cabsys.Log = None) -> QFloat:
    """Calculate the metal sheath / screen resistivity

    The sheath / screen resistivity at working sheath/screen temperature for the cable is returned. If there is a
    combination of sheaths, wire screens and tape then the resistivity of only one layer is given in the following
    priority order:

    * sheath
    * wire screen
    * tape

    :param cable: cable with sheath or screen
    :param sheath_screen_temperature: temperature of sheath or screen (°C)
    :param sheath_temp_source: top of sheath/screen temperature
    :param log: logger
    :return: sheath/screen resistance (ohm/m)
    """

    # sheath_type = cable.sheath_type.get_value(unit='')

    if log is not None:
        log.add_line('θ_sc', sheath_screen_temperature, '°C', sheath_temp_source)

    if cable.sheath.material.get_value(unit='') != iec.NONE:
        if cable.sheath.material.get_value(unit='') is None:
            raise IEC60287Exception('calculating screen resistivity: metal sheath material is not defined')
        rho = get_q_parameter(cable.sheath.resistivity, log=log)
        if rho is None:
            material = cable.sheath.material.get_value(unit='', log=log)
            rho = find_rho_sheath(material, log=log).value
        alpha20 = get_q_parameter(cable.sheath.alpha20, log=log)
        if alpha20 is None:
            material = cable.sheath.material.get_value(unit='', log=log)
            alpha20 = find_alpha20_sheath(material, log=log).value
    elif cable.wire_screen.material.get_value(unit='') != iec.NONE:
        if cable.wire_screen.material.get_value(unit='') is None:
            raise IEC60287Exception('calculating screen resistivity: wire screen material is not defined')
        rho = get_q_parameter(cable.wire_screen.resistivity, log=log)
        if rho is None:
            material = cable.wire_screen.material.get_value(unit='', log=log)
            rho = find_rho_sheath(material, log=log).value
        alpha20 = get_q_parameter(cable.wire_screen.alpha20, log=log)
        if alpha20 is None:
            material = cable.wire_screen.material.get_value(unit='', log=log)
            alpha20 = find_alpha20_sheath(material, log=log).value
    elif cable.tape.material.get_value(unit='') != iec.NONE:
        if cable.tape.material.get_value(unit='') is None:
            raise IEC60287Exception('calculating screen resistivity: tape screen material is not defined')
        rho = get_q_parameter(cable.tape.resistivity, log=log)
        if rho is None:
            material = cable.tape.material.get_value(unit='', log=log)
            rho = find_rho_sheath(material, log=log).value
        alpha20 = get_q_parameter(cable.tape.alpha20, log=log)
        if alpha20 is None:
            material = cable.tape.material.get_value(unit='', log=log)
            alpha20 = find_alpha20_sheath(material, log=log).value
    else:
        raise IEC60287Exception('finding sheath / screen resistivity but no sheath or screen found')

    rho_s = rho * (1 + (sheath_screen_temperature - 20) * alpha20)

    return QFloat(rho_s, 'Ω/m', 'IEC 60287 support function',
                  description='sheath/screen resistivity', symbol='ρ_s')


sheath_resistivity = {iec.COPPER: (1.7241e-8, 3.93e-3),  # <- this is added as copper may be used
                      iec.LEAD: (21.4e-8, 4.0e-3),
                      iec.STEEL: (13.8e-8, 4.5e-3),
                      iec.BRONZE: (3.5e-8, 3.0e-3),
                      iec.STAINLESS_STEEL: (70e-8, 0.0),
                      iec.ALUMINIUM: (2.84e-8, 4.03e-3)}


@LogSection('ρ_sheath')
def find_rho_sheath(material: str, log: Log = None) -> QFloat:
    """Find dc resistivity at 20°C from IEC 60287-1-1 Table 1 for a cable sheath

    :param material: material
    :param log: calculation log
    :return: dc resistance of cable conductor at 20 °C (ohm/m)
    """

    try:
        rho = sheath_resistivity[material][0]
    except KeyError:
        raise IEC60287Exception(f'trying to find sheath or screen resistivity but material "{material}" not recognised')

    if log is not None:
        log.add_line('ρ_sheath', rho, 'Ω/m', 'IEC 60287-1-1 Table 1')
    return QFloat(rho, 'Ω/m', 'IEC 60287-1-1 Table 1',
                  description='dc resistivity at 20°C', symbol='ρ_sheath')


@LogSection('α₂₀_sheath')
def find_alpha20_sheath(material: str, log: Log = None) -> QFloat:
    """Find dc coefficient of resistance at 20°C from IEC 60287-1-1 Table 1 for a cable sheath

    :param material: sheath material
    :param log: calculation log
    :return: coefficient of resistance of cable sheath at 20 °C (ohm/m)
    """

    alpha20 = sheath_resistivity[material][1]
    alpha20ref = 'IEC 60287-1-1 Table 1'
    if log is not None:
        log.add_line('α₂₀_sheath', alpha20, '1/°C', alpha20ref)
    return QFloat(alpha20, '1/°C', alpha20ref,
                  description='dc coefficient of resistance at 20°C', symbol='α₂₀_sheath')


def calc_cable_formation(cable_set: cabsys.CableSet, log: cabsys.Log = None) -> str:
    """Calculate the formation of the CableSet

    Returns either:
        FLAT
        TREFOIL
        ARBITRARY

    :param cable_set: cable_set that contains the cable that the number of cores will be worked out
    :param log: calculation log
    :return: formation of cable set
    """
    if log is not None:
        log.start_section('cable formation', 'support function')
    result = cable_set.calc_formation_spacing(log)[0]
    if log is not None:
        log.end_section('cable formation', result, '', 'support function: formation of cables')
    return result


def calc_cable_spacing(cable_set: cabsys.CableSet, log: cabsys.Log = None) -> float:
    """Calculate the cable spacing of the CableSet

    Returned value is axial spacing between cables. For 3 cables in a cableset if the cables are in flat formation but
    not equally spaced then the return value is the rms of the 2 spacing values between outer and centre cable. For
    cables in an arbitrary formation the result is the rms of the 3 spacing values. For single cables in a cableset
    the returned value is iec60287definitions.NA

    :param cable_set: cable_set that contains the cable that the number of cores will be worked out
    :param log: calculation log
    :return: formation of cable set (mm)
    """
    if log is not None:
        log.start_section('cable spacing', 'support function')
    result = cable_set.calc_formation_spacing(log)[1]
    if log is not None:
        log.end_section('cable spacing', result, 'mm', 'support function: axial spacing between cables')
    return result


@LogSection('centre cable')
def calc_centre_cable(cable_set: cabsys.CableSet, log: cabsys.Log = None) -> QInt:
    """Calculate the centre cable in the CableSet

    Finds the centre cable in a cable set and returns the index number of the centre cable, or the cable nearest the
    centre. If there is more than one cable that is nearest the centre of the cable set then the number of cables (3)
    is returned.

    :param cable_set: cable_set that contains the cable that the number of cores will be worked out
    :param log: calculation log
    :return: index number of central cable
    """

    no_cables = cable_set.find_no_cables(log=log)

    if no_cables != 3:
        raise IEC60287Exception(f'trying to find central cable but cable set has {no_cables} cables')

    if log is not None:
        log.start_section('centre of cable_set (x,y)', 'IEC60287support')
    x_tot = y_tot = 0.0
    for placed_cable in cable_set.placed_cables:
        x_tot = x_tot + placed_cable.x.get_value('mm', log=log)
        y_tot = y_tot + placed_cable.y.get_value('mm', log=log)
    x_ave = x_tot / 3
    y_ave = y_tot / 3
    if log is not None:
        log.end_section('centre of cable_set (x,y)', f'({x_ave}, {y_ave}', 'mm', 'IEC60287 support function')

    minimum_distance_from_centre = math.inf
    found_index = 3
    tie = False
    for index, placed_cable in enumerate(cable_set.placed_cables):
        x_distance = placed_cable.x.get_value('mm', log=log) - x_ave
        y_distance = placed_cable.y.get_value('mm', log=log) - y_ave
        distance_from_centre = math.sqrt(x_distance ** 2 + y_distance ** 2)
        if distance_from_centre == minimum_distance_from_centre:
            tie = True
        if distance_from_centre < minimum_distance_from_centre:
            minimum_distance_from_centre = distance_from_centre
            tie = False
            found_index = index

    if tie:
        found_index = 3

    return QInt(found_index, '', 'IEC60287 support function', description='centre cable index', symbol='centre cable')


# @UseState('phase', level=CABLE)
@LogSection('cable phase wrt centre')
def calc_cable_phase_wrt_centre(cable_set: cabsys.CableSet, cable_no: int, state: CableSetState = None,
                                log: cabsys.Log = None) -> QStr:
    """Calculate the cable phase with respect to the centre cable

    Calculates the cable phase, with respect to the central cable in the cable set.

    :param cable_set: cable_set that contains the cable
    :param cable_no: index of the cable in the cable_set
    :param state: the state of the cable_set
    :param log: calculation log
    :return: cable phase
    """

    # state is needed for decorator
    if state is None:
        pass

    cable_phase = cable_set.placed_cables[cable_no].phase.get_value('', log=log)
    if cable_phase != iec.RED and cable_phase != iec.YELLOW and cable_phase != iec.BLUE:
        raise IEC60287Exception(f'calculating phase of cable {cable_no} with respect to centre'
                                f' but phase set to {cable_phase}')
    centre_cable_no = calc_centre_cable(cable_set, log)
    if centre_cable_no.value == 3:
        raise IEC60287Exception('trying to calculate cable phase but no distinct centre cable in cable set')
    centre_cable_phase = cable_set.placed_cables[centre_cable_no.value].phase.get_value('', log=log)
    if cable_phase == centre_cable_phase:
        cable_phase_wrt_centre = iec.YELLOW
    elif ((centre_cable_phase == iec.YELLOW and cable_phase == iec.RED) or
          (centre_cable_phase == iec.RED and cable_phase == iec.BLUE) or
          (calc_centre_cable == iec.BLUE and cable_phase == iec.YELLOW)):
        cable_phase_wrt_centre = iec.RED
    elif ((centre_cable_phase == iec.YELLOW and cable_phase == iec.BLUE) or
          (centre_cable_phase == iec.RED and cable_phase == iec.YELLOW) or
          (calc_centre_cable == iec.BLUE and cable_phase == iec.RED)):
        cable_phase_wrt_centre = iec.BLUE
    else:
        raise IEC60287Exception('calculating phase of cable with respect to centre cable but phases not correct')
    return QStr(cable_phase_wrt_centre, '', 'IEC60287 support function', description='cable phase wrt centre cable',
                symbol='cable phase')


@LogSection('% screen')
def calc_metal_coverage(cable: Cable, log: cabsys.Log = None) -> QFloat:
    """Calculate the metal sheath / screen coverage

    Finds the metal coverage provided by the metal sheath or screen of the cable.

    If the cable has a:
       * metal sheath, even if it is thin such as a foil, the coverage is 100%.
       * wire screen the coverage is calculated.
       * tape screen, the coverage is 0 %. TODO: change this to calculated?

    :param cable: cable
    :param log: logger
    :return: % metal coverage of sheath
    """

    if cable.sheath.material.value is None:
        raise IEC60287Exception(f'trying to calculate sheath/screen coverage but'
                                f' metal sheath is {cable.sheath.material.value}')
    if cable.wire_screen.material.value is None:
        raise IEC60287Exception(f'trying to calculate sheath/screen coverage but wire screen'
                                f' is {cable.wire_screen.material.value}')
    if cable.tape.material.value is None:
        raise IEC60287Exception(f'trying to calculate sheath/screen coverage but tape screen'
                                f' is {cable.tape.material.value}')

    if cable.sheath.material.get_value(unit='', log=log) != iec.NONE:
        coverage = 100.0
    elif cable.wire_screen.material.get_value(unit='', log=log) != iec.NONE:
        clearance = cable.wire_screen.dia_under_wire.get_value(unit='mm', log=log)
        dia = cable.wire_screen.dia.get_value(unit='mm', log=log)
        wire_size = cable.wire_screen.wire_size.get_value(unit='mm', log=log)
        number_wires = cable.wire_screen.number_wires.get_value(unit='', log=log)
        coverage = wire_size * number_wires / (((clearance + dia) / 2) * math.pi) * 100.0
    elif cable.tape.material.get_value(unit='', log=log) != iec.NONE:
        coverage = 0.0
    else:
        raise IEC60287Exception('Calculating clearance: cable does not have a metal sheath, screen or tape')
    return QFloat(coverage, '%', 'IEC 60287 support function',
                  description='coverage of sheath/screen', symbol='% screen')


#  Void/oil content ratio of cable components
VOID_CONTENT = {iec.DUCT: 1.0,
                iec.DUCT_SPIRAL: 0.25,
                iec.ROUND_SOLID: 0.0,
                iec.ROUND_STRANDED_IMPREGNATED: 0.16,
                iec.ROUND_STRANDED_EXTRUDED: 0.16,
                iec.OVAL_STRANDED_IMPREGNATED: 0.16,
                iec.ROUND_MILLIKEN_IMPREGNATED: 0.16,
                iec.ROUND_MILLIKEN_INSULATED_EXTRUDED: 0.16,
                iec.ROUND_MILLIKEN_BARE_UNI_EXTRUDED: 0.16,
                iec.ROUND_MILLIKEN_BARE_BI_EXTRUDED: 0.16,
                iec.HOLLOW_STRANDED_IMPREGNATED: 0.16,
                iec.SECTOR_SHAPED_IMPREGNATED: 0.16,
                iec.SECTOR_SHAPED_EXTRUDED: 0.16,
                iec.HOLLOW_KEYSTONE_IMPREGNATED: 0.03,
                iec.INSULATION: 0.5,
                iec.CLEARANCE: 1.0,
                iec.UNDER_CS: 0.5}
