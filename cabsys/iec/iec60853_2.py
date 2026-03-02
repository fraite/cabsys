from typing import Optional
import math

from cabsys import IEC60853Exception
from cabsys import AutoInstall, PlacedCableState
from cabsys.quantity.log import Log, LogSection
from cabsys.data_classes.cable import Cable
from cabsys.data_classes.auto_cable import AutoCable
from cabsys.data_classes.state import UseState
from cabsys.quantity.quantity_store import QFloat
import cabsys.iec.iec_constants as iec
import cabsys.iec.iec60287support as iec60287support
import cabsys.iec.iec60287_1_1 as iec60287_1_1w

# Some housekeeping functions for the logger


def log_start_section(log: Log, text: str, source: str, section_log_level: Optional[int] = None):
    if log is not None:
        log.start_section(text, source, section_log_level)


def log_end_section(log: Log, text: str, value: any, unit: str, source: str = ''):
    if log is not None:
        log.end_section(text, value, unit, source)


def log_add_line(log: Log, text: str, value: any, unit: str, source: str = ''):
    if log is not None:
        log.add_line(text, value, unit, source)


# *****************************  IEC 60853-2  *****************************************


@UseState('Q_c')
@LogSection('Q_c')
def calc_q_c(cable: Cable, state: PlacedCableState = None, log: Log = None) -> QFloat:
    """Calculate Qc, the heat capacity of the conductor, including oil if present (J/K.m).

    Calculates the heat capacity of the conductor. The volume of the metal in the conductor is based on the diameter
    dc', the equivalent cross-section of the conductor assuming it is solid apart from the duct. If the cable is
    impregnated, then the gaps are assumed to be filled by oil.

    :param cable: cable with conductor
    :param state: placed cable state
    :param log: logger object
    :return: Qc (J/k.m)
    """

    log_start_section(log, 'Q_cond', 'specific heat capacity of conductor')
    duct_dia = cable.conductor.duct_dia.get_value('mm', log=log)

    if cable.conductor.conductor_volume.value is None:
        log_start_section(log, 'cond_area', 'cross sectional area of metal in conductor')
        dc_dash_dia = iec60287support.get_q_parameter(cable.conductor.dc_dash_dia, log=log)
        if dc_dash_dia is None:
            dc_dash_dia = iec60287_1_1w.calc_dc_dash(cable, log=log).value
        cond_area = math.pi / 4 * (dc_dash_dia**2 - duct_dia**2)
        log_end_section(log, 'cond_area', cond_area, 'mm²', 'cross sectional area of metal in conductor')
    else:
        cond_area = cable.conductor.conductor_volume.get_value(unit='mm³/mm', log=log)

    cond_q0 = find_cond_v_s_heat(cable, log=log).value

    q_cond = cond_area / 1e6 * cond_q0
    log_end_section(log, 'Q_cond', q_cond, 'J/K.m', 'specific heat capacity of conductor')

    log_start_section(log, 'Q_oil', 'specific heat capacity of oil in duct and conductor')
    cond_makeup = cable.conductor.makeup.get_value(unit='', log=log)
    if cond_makeup in iec.conductor_makeup_list_impregnated:
        oil_q0 = iec60287support.get_q_parameter(cable.conductor.duct_v_s_heat)
        if oil_q0 is None:
            rows = list(INSULATION_V_S_HEAT[iec.INS_OIL])
            oil_q0 = rows[0][2]
        log_start_section(log, 'oil area', 'cross section are of oil in the conductor')
        cond_dia = cable.conductor.dia.get_value(unit='mm', log=log)
        total_cond_area = math.pi / 4 * cond_dia**2
        log_add_line(log, 'total_cond_area', total_cond_area, 'mm²', 'total conductor area of conductor')
        log_add_line(log, 'cond_area', cond_area, 'mm²', 'cross sectional area of metal')
        oil_area = total_cond_area - cond_area
        log_end_section(log, 'oil area', oil_area, 'mm²', 'cross section are of oil in the conductor')
        q_oil = oil_area / 1e6 * oil_q0
    else:
        if duct_dia > 0.0:
            raise IEC60853Exception(f'calculating specific heat of conductor for solid cable but duct dia {duct_dia}'
                                    'suggest set duct dia to 0.0 mm')
        else:
            q_oil = 0.0

    log_end_section(log, 'Q_oil', q_oil, 'J/K.m', 'specific heat capacity of oil in duct and conductor')

    q_c = q_cond + q_oil

    return QFloat(q_c, 'J/K.m', 'iec60853_2 specific heat capacity of conductor',
                  description='specific heat capacity of conductor', symbol='q_c')


@UseState('Q_i')
@LogSection('Q_i')
def calc_q_i(cable: AutoCable, state: PlacedCableState = None, log: Log = None) -> QFloat:
    """Calculate Qi, the heat capacity of the insulation (J/K.m).

    Calculates the heat capacity of the insulation.

    :param cable: cable with insulation
    :param state: placed cable state
    :param log: logger object
    :return: Qc (J/k.m)
    """

    number_cores = cable.number_cores.get_value(unit='', log=log)

    if number_cores == iec.SINGLE_CORE or number_cores == iec.CONCENTRIC:
        dc = cable.conductor.dia.get_value(unit='mm', log=log)
        outer_dia = cable.core.bedding_dia.get_value(unit='mm', log=log)
        if outer_dia is None:
            outer_dia = cable.core.insu_screen_dia.get_value(unit='mm', log=log)
        if outer_dia is None:
            outer_dia = cable.core.insu_dia.get_value(unit='mm', log=log)
        if outer_dia is None:
            raise IEC60853Exception(f'calculating insulation heat capacity but no outer diameter for insulation')
        ins_v_s_heat = find_insulation_v_s_heat(cable, log=log).value
        q_i = ins_v_s_heat * math.pi / 4 * (outer_dia**2 - dc**2) / 1e6
    else:
        raise IEC60853Exception(f'calculating insulation heat capacity but only single core cable implemented')

    return QFloat(q_i, 'J/K.m', 'iec60853_2 specific heat capacity of insulation',
                  description='specific heat capacity of insulation', symbol='q_i')


@UseState('Q_s')
@LogSection('Q_s')
def calc_q_s(cable: Cable, state: PlacedCableState = None, log: Log = None) -> QFloat:
    """Calculate Qs, the heat capacity of the metal sheath / screen, including reinforcement if present.

    Calculates the heat capacity of all the metal sheath and screen layers. If none are present then the function
    returns 0.0 J/K.m.

    :param cable: cable with metal sheath / screen
    :param state: placed cable state
    :param log: logger object
    :return: Qs (J/k.m)
    """

    if not(cable.number_cores.value == iec.SINGLE_CORE or cable.number_cores.value == iec.CONCENTRIC):
        raise IEC60853Exception(f'calculating sheath specific heat capacity but {cable.number_cores} not implemented')

    sheath_type = cable.sheath_type.get_value(unit='')
    if cable.tape.material.get_value(unit='', log=log) != iec.NONE:
        log_start_section(log, 'Q_tape', 'specific heat capacity of tape screen')
        tape_q0 = iec60287support.get_q_parameter(cable.tape.v_s_heat, log=log)
        if tape_q0 is None:
            material = cable.tape.material.get_value(unit='', log=log)
            tape_q0 = find_sheath_v_s_heat(material, log=log).value
        number_tapes = cable.tape.number_tapes.get_value(unit='', log=log)
        tape_thickness = cable.tape.tape_thickness.get_value(unit='mm', log=log)
        tape_width = cable.tape.tape_width.get_value(unit='mm', log=log)
        tape_angle = cable.tape.angle.get_value(unit='°', log=log)
        area = number_tapes * tape_thickness * tape_width / math.cos(tape_angle * math.pi / 180.0) / 1e6
        q_tape = tape_q0 * area
        log_end_section(log, 'Q_tape', q_tape, 'J/K.m', 'specific heat capacity of tape screen')
    else:
        q_tape = 0.0

    if cable.sheath.material.get_value(unit='', log=log) != iec.NONE:
        log_start_section(log, 'Q_sheath', 'specific heat capacity of sheath')
        sheath_q0 = iec60287support.get_q_parameter(cable.sheath.v_s_heat, log=log)
        if sheath_q0 is None:
            material = cable.sheath.material.get_value(unit='', log=log)
            sheath_q0 = find_sheath_v_s_heat(material, log=log).value
        dia_under = cable.sheath.dia_under_sheath.get_value(unit='mm', log=log)
        dia = cable.sheath.dia.get_value(unit='mm', log=log)
        rt = cable.sheath.thickness.get_value(unit='mm', log=log)
        q_sheath = math.pi * (dia_under + dia) / 2000 * rt / 1000 * sheath_q0
        log_end_section(log, 'Q_sheath', q_sheath, 'J/K.m', 'specific heat capacity of sheath')
    else:
        q_sheath = 0.0

    if cable.wire_screen.material.get_value(unit='', log=log) != iec.NONE:
        log_start_section(log, 'Q_wire', 'specific heat capacity of wire screen')
        wire_q0 = iec60287support.get_q_parameter(cable.wire_screen.v_s_heat, log=log)
        if wire_q0 is None:
            material = cable.wire_screen.material.get_value(unit='', log=log)
            wire_q0 = find_sheath_v_s_heat(material, log=log).value
        number_wires = cable.wire_screen.number_wires.get_value(unit='', log=log)
        wire_size = cable.wire_screen.wire_size.get_value(unit='mm', log=log)
        q_wire = number_wires * math.pi / 4 * wire_size**2 / 1e6 * wire_q0
        log_end_section(log, 'Q_wire', q_wire, 'J/K.m', 'specific heat capacity of wire screen')
    else:
        q_wire = 0.0

    q_s = q_tape + q_sheath + q_wire

    return QFloat(q_s, 'J/K.m', 'iec60853_2 specific heat capacity of sheath/screen',
                  description='specific heat capacity of metal sheath/screen', symbol='q_s')


# **************************** Appendix D ***********************************************

# Table D1: Values of diffusivity for soil
#          oil TR K.m/W: soil diffusivity m²/s
SOIL_DIFFUSIVITY = {0.5: 0.8e-6,
                    0.6: 0.7e-6,
                    0.7: 0.6e-6,
                    0.8: 0.6e-6,
                    0.9: 0.5e-6,
                    1.0: 0.5e-6,
                    1.2: 0.4e-6,
                    1.5: 0.4e-6,
                    2.0: 0.3e-6,
                    2.5: 0.2e-6,
                    3.0: 0.2e-6}


@LogSection('δ')
def calc_soil_diffusivity_given_tr(tr: float, log: Log = None) -> QFloat:
    if 0.4 < tr <= 0.5:
        sd = 0.5
    elif 0.5 < tr <= 1.0:
        sd = SOIL_DIFFUSIVITY[round(tr, 1)]
    elif 1 < tr <= 1.1:
        sd = SOIL_DIFFUSIVITY[1.0]
    elif 1.1 < tr <= 1.75:
        sd = SOIL_DIFFUSIVITY[1.2]
    elif 1.75 < tr <= 2.25:
        sd = SOIL_DIFFUSIVITY[2.0]
    elif 2.25 < tr <= 4.0:
        sd = SOIL_DIFFUSIVITY[3.0]
    else:
        raise IEC60853Exception(f'calculating soil diffusivity to IEC 60853-2 Table D1 but TR {tr} K.m/W out of range')

    return QFloat(sd, 'm²/s', 'IEC 60853-2 Table D1, soil diffusivity',
                  description='soil diffusivity', symbol='δ')


@LogSection('δ')
def calc_soil_diffusivity(install: AutoInstall, log: Log = None) -> QFloat:
    q_ground_thermal_diffusivity = install.get_q_ground_thermal_diffusivity(install.selected_scenario.value)
    if q_ground_thermal_diffusivity.get_value(unit='m²/s', default=None, log=log) is not None:
        delta = q_ground_thermal_diffusivity
    elif install.get_ground_tr(install.selected_scenario.value, unit='K.m/W') is not None:
        if install.kind.value == iec.TUNNEL:
            raise Exception(
                'Trying to get ground TR (to determine ground diffusivity) for IEC 60853 part 2 (or Electra 87)'
                ' calculation but the installation kind is tunnel')
        else:
            ground_tr = install.get_ground_tr(install.selected_scenario.value, unit='K.m/W', log=log)
        delta = calc_soil_diffusivity_given_tr(ground_tr)
    else:
        raise IEC60853Exception(f'calculating soil diffusivity but no value found')

    return delta


# **************************** Appendix E ***********************************************

@LogSection("ρ_T insulation")
def find_insulation_rho_t(cable: Cable, log: Log = None) -> QFloat:
    """Get the insulation thermal resistivity

    Gets the insulation thermal resistivity. If this is set in the cable.core.rho_t quantity, this value is returned,
    and a warning is generated in the log. Otherwise, the value from IEC 60853-2 Table E1 is returned.

    :param cable: the cable with the insulation
    :param log: logger used to store results
    :return: insulation thermal resistivity (K.m/W)
    """

    if cable.core.rho_1.value is None:
        ins_mat = cable.core.insulation_material.get_value(unit='', log=log)
        volts = cable.design_volts.get_value(unit='kV', log=log)
        rows = INSULATION_V_S_HEAT[ins_mat]
        rho_t = None
        for row in rows:
            if volts < row[0]:
                rho_t = row[1]
                break
        if rho_t is None:
            raise IEC60853Exception(f'rho_t not found for {ins_mat} with design voltage {volts} V.')
        source = 'IEC 60853-2 Table E1'
    else:
        rho_t = cable.core.rho_1.get_value(unit='K.m/W', log=log)
        source = cable.core.rho_1.source
        if log is not None:
            log.add_warning(f'{cable.core.rho_1.symbol} set by user input')

    return QFloat(rho_t, 'K.m/W', source, description='insulation thermal resistivity', symbol="rho_t insulation")


@LogSection("v_s_heat insulation")
def find_insulation_v_s_heat(cable: Cable, log: Log = None) -> QFloat:
    """Get the insulation volumetric specific heat

    Gets the insulation volumetric specific heat. If this is set in the cable.core.v_s_heat quantity, this value is
    returned, and a warning is generated in the log. Otherwise, the value from IEC 60853-2 Table E1 is returned.

    :param cable: the cable with the insulation
    :param log: logger used to store results
    :return: insulation volumetric specific heat (J/m³.K)
    """

    if cable.core.v_s_heat.value is None:
        ins_mat = cable.core.insulation_material.get_value(unit='', log=log)
        volts = cable.design_volts.get_value(unit='kV', log=log)
        rows = INSULATION_V_S_HEAT[ins_mat]
        v_s_heat = None
        for row in rows:
            if volts < row[0]:
                v_s_heat = row[2]
                break
        if v_s_heat is None:
            raise IEC60853Exception(f'rho_t not found for {ins_mat} with design voltage {volts} V.')
        source = 'IEC 60853-2 Table E1'
    else:
        v_s_heat = cable.core.v_s_heat.get_value(unit='J/m³.K', log=log)
        source = cable.core.v_s_heat.source
        if log is not None:
            log.add_warning(f'{cable.core.v_s_heat.symbol} set by user input')

    return QFloat(v_s_heat, 'J/m³.K', source, description='insulation volumetric specific heat',
                  symbol="v_s_heat insulation")


# IEC 60853-2 Table E1 Volumetric Specific Heat (J/m3.K), note that thermal resistivity is in IEC 60287-2-1
#                         material                up to U0, TR, v_s_heat
INSULATION_V_S_HEAT = {iec.INS_PAPER_SOLID:        {(9999.1, 6.0, 2.0e6)},
                       iec.INS_PAPER_SCOF:         {(9999.1, 5.0, 2.0e6)},
                       iec.INS_PAPER_OF_PIPE:      {(9999.1, 5.0, 2.0e6)},
                       iec.INS_PAPER_GAS_EXT:      {(9999.1, 5.5, 2.0e6)},
                       iec.INS_PAPER_GAS_INT_PRE:  {(9999.1, 5.5, 2.0e6)},
                       iec.INS_PAPER_GAS_INT_MASS: {(9999.1, 6.0, 2.0e6)},
                       iec.INS_OIL:                {(9999.1, 7.0, 1.7e6)},
                       iec.INS_NITROGEN:           {(9999.1, '**', 0.017e6)},
                       iec.INS_PE:                 {(9999.1, 3.5, 2.4e6)},
                       iec.INS_XLPE_UNFILLED:      {(9999.1, 3.5, 2.4e6)},
                       iec.INS_XLPE_FILLED:        {(9999.1, 3.5, 2.4e6)},
                       iec.INS_PPL:                {(9999.1, 5.5, 2.0e6)},   # v_s_heat not in IEC 60853-2
                       iec.INS_PVC:                {(3.1, 5.0, 1.7e6),
                                                    (9999.1, 6.0, 1.7e6)},
                       iec.INS_EPR:                {(3.1, 3.5, 2.0e6),
                                                    (9999.1, 5.0, 2.0e6)},
                       iec.INS_BUTYL:              {(9999.1, 5.0, 2.0e6)},
                       iec.INS_RUBBER:             {(9999.1, 5.0, 2.0e6)}}


@LogSection("ρ_T serving")
def find_serving_rho_t(cable: Cable, log: Log = None) -> QFloat:
    """Get the serving thermal resistivity

    Gets the serving thermal resistivity. If this is set in the cable.serving.rho_t quantity, this value is returned,
    and a warning is generated in the log. Otherwise, the value from IEC 60853-2 Table E1 is returned.

    :param cable: the cable with the insulation
    :param log: logger used to store results
    :return: serving thermal resistivity (K.m/W)
    """

    if cable.serving.rho_t.value is None:
        serving_mat = cable.serving.material.get_value(unit='', log=log)
        volts = cable.design_volts.get_value(unit='kV', log=log)
        rows = SERVING_V_S_HEAT[serving_mat]
        rho_t = None
        for row in rows:
            if volts < row[0]:
                rho_t = row[1]
                break
        if rho_t is None:
            raise IEC60853Exception(f'rho_t not found for {serving_mat} with design voltage {volts} V.')
        source = 'IEC 60853-2 Table E1'
    else:
        rho_t = cable.serving.rho_t.get_value(unit='K.m/W', log=log)
        source = cable.serving.rho_t.source
        if log is not None:
            log.add_warning(f'{cable.serving.rho_t.symbol} set by user input')

    return QFloat(rho_t, 'K.m/W', source, description='serving thermal resistivity', symbol="rho_t serving")


@LogSection("v_s_heat serving")
def find_serving_v_s_heat(cable: Cable, log: Log = None) -> QFloat:
    """Get the serving volumetric specific heat from IEC 60853-2 Table E1

    Gets the serving volumetric specific heat. If this is set in the cable.serving.v_s_heat quantity, this value is
    returned, and a warning is generated in the log. Otherwise the value from IEC 60853-2 Table E1 is returned.

    :param cable: the cable with the serving
    :param log: logger used to store results
    :return: serving volumetric specific heat (J/m³.K)
    """

    if cable.serving.v_s_heat.value is None:
        serv_mat = cable.serving.material.get_value(unit='', log=log)
        volts = cable.design_volts.get_value(unit='kV', log=log)
        rows = SERVING_V_S_HEAT[serv_mat]
        v_s_heat = None
        for row in rows:
            if volts < row[0]:
                v_s_heat = row[2]
                break
        if v_s_heat is None:
            raise IEC60853Exception(f'rho_t not found for {serv_mat} with design voltage {volts} V.')
        source = 'IEC 60853-2 Table E1'
    else:
        v_s_heat = cable.serving.v_s_heat.get_value(unit='J/m³.K', log=log)
        source = cable.serving.v_s_heat.source
        if log is not None:
            log.add_warning(f'serving {cable.serving.v_s_heat.symbol} set by user input')

    return QFloat(v_s_heat, 'J/m³.K', source,
                  description='serving volumetric specific heat', symbol="v_s_heat insulation")


# IEC 60853-2 Table E1 Volumetric Specific Heat (J/m3.K), note that thermal resistivity is in IEC 60287-2-1
#                         material                up to U0, TR, v_s_heat
SERVING_V_S_HEAT = {iec.SERVING_JUTE:          {(9999.1, 6.0, 2.0e6)},
                    iec.SERVING_RUBBER_TAPE:   {(9999.1, 6.0, 2.0e6)},
                    iec.SERVING_POLYCHLOPRENE: {(9999.1, 5.5, 2.0e6)},
                    iec.SERVING_PVC:           {(35.1, 5.0, 1.7e6),
                                                (9999.1, 6.0, 1.7e6)},
                    iec.SERVING_PVC_CAS:       {(9999.1, 6.0, 1.7e6)},
                    iec.SERVING_PE:            {(9999.1, 3.5, 2.4e6)}}


# IEC 60853-2 Table E1 Volumetric Specific Heat (J/m3.K), note that thermal resistivity is in IEC 60287-2-1
#                         material        TR, v_s_heat
DUCT_V_S_HEAT = {iec.DUCT_CONCRETE:       (1.0, 1.9e6),
                 iec.DUCT_FIBRE:          (4.8, 2.0e6),
                 iec.DUCT_ASBESTOS:       (2.0, 2.0e6),
                 iec.DUCT_EARTHENWARE:    (1.2, 1.7e6),
                 iec.DUCT_PVC:            (6.0, 1.7e6),
                 iec.DUCT_PE11:             (3.5, 2.4e6)}


@LogSection('β₀')
def find_cond_beta0(cable: AutoCable, log: Log = None) -> QFloat:
    """Find reciprocal of dc coefficient of resistance at 0°C from IEC 60583-2 Table E2 for a cable conductor

    Gets the conductor beta0. If this is set in the cable.conductor.beta0, this value is
    returned, and a warning is generated in the log. Otherwise the value from IEC 60853-2 Table E2 is returned.

    :param cable: cable with conductor
    :param log: calculation log
    :return: reciprocal of coefficient of resistance of cable conductor at 0 °C (K)
    """

    if cable.conductor.beta0.value is None:
        cond_mat = cable.conductor.material.get_value(unit='', log=log)
        beta0 = CONDUCTOR_V_S_HEAT[cond_mat][0]
        beta0ref = 'IEC 60853-2 Table E2'
        if log is not None:
            log.add_line('β₀', beta0, 'K', beta0ref)
    else:
        beta0 = cable.conductor.beta0.get_value(unit='K', log=log)
        beta0ref = cable.conductor.beta0.source
        if log is not None:
            log.add_warning(f'conductor {cable.conductor.beta0.symbol} set by user input')

    return QFloat(beta0, 'K', beta0ref,
                  description='1 / coefficient of resistance at 0°C', symbol='β₀')


@LogSection('v_s_heat conductor')
def find_cond_v_s_heat(cable: Cable, log: Log = None) -> QFloat:
    """Find volumetric specific heat from IEC 60583-2 Table E2 for a cable conductor

    Gets the conductor volumetric specific heat. If this is set in the cable.conductor.conductor_v_s_heat, this value is
    returned, and a warning is generated in the log. Otherwise the value from IEC 60853-2 Table E2 is returned.

    :param cable: cable with conductor
    :param log: calculation log
    :return: volumetric specific heat of cable conductor (J/m³.K)
    """

    if cable.conductor.conductor_v_s_heat.value is None:
        cond_mat = cable.conductor.material.get_value(unit='', log=log)
        v_s_heat = CONDUCTOR_V_S_HEAT[cond_mat][1]
        v_s_heatref = 'IEC 60853-2 Table E2'
        if log is not None:
            log.add_line('v_s_heat', v_s_heat, 'J/m³.K', v_s_heatref)
    else:
        v_s_heat = cable.conductor.conductor_v_s_heat.get_value(unit='J/m³.K', log=log)
        v_s_heatref = cable.conductor.conductor_v_s_heat.source
        if log is not None:
            log.add_warning(f'conductor {cable.conductor.conductor_v_s_heat.symbol} set by user input')

    return QFloat(v_s_heat, 'J/m³.K', v_s_heatref,
                  description='volumetric specific heat', symbol='v_s_heat conductor')


@LogSection('ρ₂₀')
def find_cond_resistivity(cable: AutoCable, log: Log = None) -> QFloat:
    """Find electrical resistivity at 20°C from IEC 60583-2 Table E2 for a cable conductor

    Gets the conductor rho20. If this is set in the cable.conductor.rho20, this value is
    returned, and a warning is generated in the log. Otherwise the value from IEC 60853-2 Table E2 is returned.

    :param cable: cable with conductor
    :param log: calculation log
    :return: resistivity of cable conductor at 20 °C (Ω.m)
    """

    if cable.conductor.dc_resistivity20 is None:
        cond_mat = cable.conductor.material.get_value(unit='', log=log)
        rho20 = CONDUCTOR_V_S_HEAT[cond_mat][2]
        rho20ref = 'IEC 60853-2 Table E2'
        if log is not None:
            log.add_line('ρ₂₀', rho20, 'Ω.m', rho20ref)
    else:
        rho20 = cable.conductor.dc_resistivity20.get_value(unit='Ω.m')
        rho20ref = cable.conductor.dc_resistivity20.source
        if log is not None:
            log.add_warning(f'conductor {cable.conductor.dc_resistivity20.symbol} set by user input')

    return QFloat(rho20, 'Ω.m', rho20ref,
                  description='dc coefficient of resistance at 20°C', symbol='ρ₂₀')


# IEC 60853-2 Table E2 Volumetric Specific Heat (J/m3.K), note that electrical resistivity is in IEC 60287-2-1
#                         material        TR, v_s_heat
CONDUCTOR_V_S_HEAT = {iec.COPPER: (234.5, 3.45e6, 1.7241e-8),
                      iec.ALUMINIUM: (228, 2.5e6, 2.8264e-8)}


@LogSection('β₀ sheath/screen')
def find_sheath_beta0(material: str, log: Log = None) -> QFloat:
    """Find reciprocal of dc coefficient of resistance at 0°C from IEC 60583-2 Table E2 for a cable sheath/screen

    :param material: sheath material
    :param log: calculation log
    :return: reciprocal of coefficient of resistance of cable sheath/screen at 0 °C (K)
    """

    beta0 = SHEATH_V_S_HEAT[material][0]
    beta0ref = 'IEC 60853-2 Table E2'
    if log is not None:
        log.add_line('β₀', beta0, 'K', beta0ref)
    return QFloat(beta0, 'K', beta0ref,
                  description='dc coefficient of resistance at 20°C', symbol='β₀')


@LogSection('v_s_heat sheath/screen')
def find_sheath_v_s_heat(material: str, log: Log = None) -> QFloat:
    """Find volumetric specific heat from IEC 60583-2 Table E2 for a cable sheath/screen

    :param material: sheath material
    :param log: calculation log
    :return: volumetric specific heat of cable conductor (J/m³.K)
    """

    beta0 = SHEATH_V_S_HEAT[material][1]
    beta0ref = 'IEC 60853-2 Table E2'
    if log is not None:
        log.add_line('v_s_heat', beta0, 'J/m³.K', beta0ref)
    return QFloat(beta0, 'J/m³.K', beta0ref,
                  description='volumetric specific heat', symbol='v_s_heat sheath/screen')


@LogSection('ρ₂₀ sheath/screen')
def find_sheath_resistivity(material: str, log: Log = None) -> QFloat:
    """Find electrical resistivity at 20°C from IEC 60583-2 Table E2 for a cable sheath/screen

    :param material: sheath material
    :param log: calculation log
    :return: resistivity of cable conductor at 20 °C (Ω.m)
    """

    rho20 = SHEATH_V_S_HEAT[material][2]
    rho20ref = 'IEC 60853-2 Table E2'
    if log is not None:
        log.add_line('ρ₂₀', rho20, 'Ω.m', rho20ref)
    return QFloat(rho20, 'Ω.m', rho20ref,
                  description='dc coefficient of resistance at 20°C', symbol='ρ₂₀')


# IEC 60853-2 Table E2 Volumetric Specific Heat (J/m3.K), note that electrical resistivity is in IEC 60287-2-1
#                         material        TR, v_s_heat
SHEATH_V_S_HEAT = {iec.COPPER: (234.5, 3.45e6, 1.7241e-8),  # <- this is added as copper may be used
                   iec.LEAD: (230, 1.45e6, 21.4e-8),
                   iec.STEEL: (202, 3.8e6, 13.8e-8),
                   iec.BRONZE: (313, 3.4e6, 3.5e-8),
                   iec.STAINLESS_STEEL: ('*', 3.8e6, 70e-8),
                   iec.ALUMINIUM: (228, 2.5e6, 2.84e-8)}
