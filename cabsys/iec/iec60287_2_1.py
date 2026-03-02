"""Wrapper

* Section 4.1.2.1 T1
     - is undermined by Section 4.2.4.3.3 trefoil touching part metal covered cables buried cables, and
       probably also by Section 4.2.4.3.4 for non-metal sheathed cables as T1 is multiplied by 1.07/1.16
     - used t1 defined as thickness between conductor and sheath/screen but conflicts with T1 in
       IEC 60287-1-1
* Section 4.1.4.1 T3
     - is undermined by Section 4.2.4.3.2 trefoild touching metal sheath cables, Section 4.2.4.3.3 trefoil touching part
       metal covered cables buried cables, and probably also by Section 4.2.4.3.4 for non-metal sheathed cables as T3 is
       multiplied by 1.6
     - The inner diameter of the covering is assumed to be the external diameter of the armour, but it this does not
       exist then the external diameter of the sheath/screen is used.
     - T3 is not given for many cases, for example SL or SA cables
* Section 4.2.2 u
     - equation assumes that the cable is not in duct. De should be duct diameter if cables are in ducts.
* Section 4.2.4.3.3 T4 trefoil touching buried part metal
     - voltages for T1 multiplication do not specify U0, Um, or probably working. Best use U0 to match other places?
     - voltages for T1 multiplication stop at 150 kV, but seem to get worse?
* Section 4.2.4.3.4 T4 trefoil touching buried no sheath: no T1 or T3 multiplication factors.
* Table 1 has TR for duct material concrete, but Table 4 does not have U,V and Y constants for concrete
* Table 4 has some duct materials in air or concrete, but for others does not. Water filled ducts could be any duct
 material.

"""

import math
from typing import List, Union, Tuple

from cabsys import IEC60287Exception
import cabsys.data_classes.auto_cable
import cabsys.data_classes.state
from cabsys.quantity.quantity_store import QFloat, QStr
from cabsys.quantity.log import Log, LogSection
from cabsys.data_classes.cable import Cable
from cabsys.data_classes.install import PlacedCable
from cabsys.data_classes.install import Install
from cabsys.data_classes.auto_install import AutoInstall, AutoCableSet
# from cabsys.data_classes.project import Project
from cabsys import CableState, CableSetState, InstallState
# from cabsys.data_classes.install import CableSet
import cabsys.iec.iec60287support as iec60287support
from cabsys.data_classes.state import UseState
import cabsys.iec.iec60287_1_1 as iec60287_1_1w
import cabsys.iec.iec_constants as iec


@UseState('T_1', level=cabsys.data_classes.state.CABLE)
@LogSection('T_1')
def calc_t1(install: AutoInstall, cable_set_no: int, cable_no: int,
            state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate T_1, thermal resistance of a cable insulation

    IEC 60287-2-1 clause 4.1.2

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param state: cable state  (WARNING this is a CableState and not InstallState object)
    :param log: logger used to store results
    :return: thermal resistance of the cable insulation (k.m/W)
    """

    # not needed but stops PyCharms warning about unused arguments
    if state:
        pass

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.1.2'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.1.2'
    else:
        raise IEC60287Exception(f'trying to calculate T1 (IEC 60287-2-1 ED3 Section 4.1.2) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable
    number_cores = cable.number_cores.get_value(unit='', log=log)

    if number_cores == iec.SINGLE_CORE or number_cores == iec.CONCENTRIC:
        t_1 = calc_t1_4_1_2_1(install, cable_set_no, cable_no, log=log)
    elif number_cores == iec.THREE_CORE:
        separate_sheath = cable.separate_sheath.get_value(unit='', log=log)
        if separate_sheath:
            t_1 = calc_t1_4_1_2_1(install, cable_set_no, cable_no, log=log)
        else:
            raise IEC60287Exception('T1: three core common sheath not yet implemented')
    else:
        raise IEC60287Exception(f'T1: {number_cores} not yet implemented')

    return QFloat(t_1.value, 'K.m/W', f'{source}, thermal resistance of insulation',
                  description='thermal resistance of insulation', symbol='T_1')


@LogSection('T_1 single core')
def calc_t1_4_1_2_1(install: AutoInstall, cable_set_no: int, cable_no: int,
                    log: Log = None) -> QFloat:
    """Calculate T_1, thermal resistance of single core cable insulation

    IEC 60287-2-1 Section 4.1.2.1

    Includes over-ride in Section 4.2.4.3.3 and 4.2.4.3.4 for buried trefoil cables touching, which multiplies T1 by
    1.07 or 1.6 depending on voltage.

    If install.config.non_metal_screen_isotherm is set to True then only cables buried touching trefoil with
    20 % <= coverage <= 50 % will have T1 modified and cables buried touching trefoil with coverages < 20 % will not
    have T1 modified as this is missing from IEC 60287-2-1.

    For cables buried touching trefoil with a voltage greater than 150 kV the modification factor is missing and is
    assumed to 1.6. A waring is generated in the log in this case.

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param log: logger used to store results
    :return: thermal resistance of the cable insulation (k.m/W)
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    if install.config.single_t1_rho.value:
        if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
            source = 'IEC 60287-2-1 ED3 Section 4.1.2.1'
        elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
            source = 'IEC 60287-2-1 ED2 Section 4.1.2.1'
        else:
            raise IEC60287Exception(f'trying to calculate T1 (IEC 60287-2-1 ED3 Section 4.1.2.1) but '
                                    f'IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in '
                                    f'install config not recognised')
        if install.config.iec_60287_2_1_ver.value in [iec.CIGRE_TB880_2022] and log is not None:
            log.add_warning('single t1 resistivity specified in config but CIGRE TB 880 specified')
        t1_thickness = iec60287support.get_q_parameter(cable.core.t1, log=log)
        if t1_thickness is None:
            t1_thickness = calc_t1_thermal_thickness(cable, log=log).value
        rho_1 = iec60287support.get_q_parameter(cable.core.rho_1, log=log)
        if rho_1 is None:
            rho_1 = find_insulation_rho_1(cable.core.insulation_material, cable.design_volts, log=log).value

        if cable.core.binder_dia.value > cable.conductor.dia.value:
            ignore_conductor_binder = install.config.ignore_conductor_binder.get_value(unit='', log=log)
        else:
            ignore_conductor_binder = False

        if ignore_conductor_binder:
            raise Exception('ignore conductor binder in install.config not implemented for single T1 method')
        else:
            d_c = cable.conductor.dia.get_value('mm', log=log)
            t_1 = rho_1 / (2 * math.pi) * math.log(1.0 + 2 * t1_thickness / d_c)

    else:

        t_1_q = calc_t1_4_1_2_1alt(install, cable_set_no, cable_no, log=log)
        t_1 = t_1_q.get_value(unit='K.m/W')
        source = t_1_q.source

    coverage = iec60287support.calc_metal_coverage(cable, log=log).value
    strict_iec = install.config.non_metal_screen_isotherm.get_value(unit='', log=log)
    if (20.0 <= coverage <= 50.0) or (coverage < 50.0 and not strict_iec):
        if install.kind.value == iec.BURIED:
            formation = cable_set.calc_formation_spacing(log=log)
            if formation[0] == iec.TREFOIL and formation[3] == iec.TOUCHING:
                volts = cable.design_volts.get_value(unit='kV', log=log)
                if volts <= 18.0:
                    if log is not None:
                        log.add_line('trefoil multiplication factor', 1.07, 'n/a', 'IEC 60287-2-1 4.2.4.3')
                    t_1 = t_1 * 1.07
                elif volts <= 76.0:
                    if log is not None:
                        log.add_line('trefoil multiplication factor', 1.16, 'n/a', 'IEC 60287-2-1 4.2.4.3')
                    t_1 = t_1 * 1.16
                else:
                    if log is not None:
                        log.add_line('trefoil multiplication factor', 1.16, 'n/a', 'IEC 60287-2-1 4.2.4.3 (missing)')
                        log.add_warning('cable voltage U0 > 76 kV but IEC gives no correction factor for T1')
                    t_1 = t_1 * 1.16
            else:
                if log is not None:
                    log.add_line('trefoil multiplication factor', 1.0, 'n/a', 'IEC 60287-2-1 4.2.4.3')
    else:
        if log is not None:
            log.add_line('trefoil multiplication factor', 1.0, 'n/a', 'IEC 60287-2-1 4.2.4.3')

    return QFloat(t_1, 'K.m/W', f'{source}, S/C cable TR of insulation',
                  description='single core cable thermal resistance of insulation', symbol='T_1')


@LogSection('T_1 single core non-uniform rho1')
def calc_t1_4_1_2_1alt(install: AutoInstall, cable_set_no: int, cable_no: int,
                       log: Log = None) -> QFloat:
    """Calculate T_1, thermal resistance of single core cable insulation alternative method

    IEC 60287-2-1 Section 4.1.2.1 alternative method with multiple thermal resistivity

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param log: logger used to store results
    :return: thermal resistance of the cable insulation (k.m/W)
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    no_cores = cable.number_cores.get_value(unit='', log=log)
    if no_cores == iec.SINGLE_CORE or no_cores == iec.CONCENTRIC:
        pass
    else:
        raise IEC60287Exception('t1: only single core or concentric cable implemented')

    source = 'IEC 60287-2-1 ED3 Section 4.1.2.1 multiple T1 resistivity'
    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT,
                                                  iec.CIGRE_TB880_2022]:
        pass
    elif install.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2]:
        if log is not None:
            log.add_warning('multiple T1 resistivity specified in config but IEC 60287-2-1 Ed2 specified')
    else:
        raise IEC60287Exception(f'trying to calculate T1 (IEC 60287-2-1 ED3 Section 4.1.2.1) but '
                                f'IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in '
                                f'install config not recognised')

    if (cable.conductor.makeup.get_value(unit='', log=log) in
            [iec.SECTOR_SHAPED_IMPREGNATED, iec.SECTOR_SHAPED_IMPREGNATED, iec.OVAL, iec.OVAL_STRANDED_IMPREGNATED]):
        raise IEC60287Exception(f'calculating T_1 but {cable.conductor.makeup.value} not implemented yet')

    t_1 = 0.0
    design_volts = cable.design_volts

    vary_carbon_paper_tr = install.config.vary_carbon_paper_tr.value

    if cable.core.binder_dia.value > cable.conductor.dia.value:
        ignore_conductor_binder = install.config.ignore_conductor_binder.get_value(unit='', log=log)
    else:
        ignore_conductor_binder = True

    # conductor binder
    if not ignore_conductor_binder:
        t_1 = t_1 + calc_t1_layer_4_1_3(cable.core.binder_dia, cable.conductor.dia, cable.core.binder_rho_1,
                                        cable.core.binder_material, design_volts, 'binder',
                                        vary_carbon_paper_tr=vary_carbon_paper_tr,
                                        insulation_material=cable.core.insulation_material,
                                        log=log).value

    # conductor screen
    t_1 = t_1 + calc_t1_layer_4_1_3(cable.core.cond_screen_dia, cable.core.binder_dia, cable.core.cond_screen_rho_1,
                                    cable.core.cond_screen_material, design_volts, 'conductor screen',
                                    vary_carbon_paper_tr=vary_carbon_paper_tr,
                                    insulation_material=cable.core.insulation_material,
                                    log=log).value

    # electrical insulation
    t_1 = t_1 + calc_t1_layer_4_1_3(cable.core.insu_dia, cable.core.cond_screen_dia, cable.core.rho_1,
                                    cable.core.insulation_material, design_volts, 'insulation',
                                    vary_carbon_paper_tr=vary_carbon_paper_tr,
                                    insulation_material=cable.core.insulation_material,
                                    log=log).value

    # insulation screen
    t_1 = t_1 + calc_t1_layer_4_1_3(cable.core.insu_screen_dia, cable.core.insu_dia, cable.core.insu_screen_rho_1,
                                    cable.core.insu_screen_material, design_volts, 'insulation screen',
                                    vary_carbon_paper_tr=vary_carbon_paper_tr,
                                    insulation_material=cable.core.insulation_material,
                                    log=log).value

    # bedding
    t_1 = t_1 + calc_t1_layer_4_1_3(cable.core.bedding_dia, cable.core.insu_screen_dia, cable.core.bedding_rho_1,
                                    cable.core.bedding_material, design_volts, 'bedding',
                                    vary_carbon_paper_tr=vary_carbon_paper_tr,
                                    insulation_material=cable.core.insulation_material,
                                    log=log).value

    # TODO: change to use calc_t1_layer_4_1_3
    t_1 = t_1 + calc_t1_clearance(cable, source=source, log=log).value

    return QFloat(t_1, 'K.m/W', f'{source}',
                  description='single core cable thermal resistance of insulation', symbol='T_1')


@LogSection('t_1 thickness')
def calc_t1_thermal_thickness(cable: Cable, log: Log = None) -> QFloat:
    """Calculate t_1, thickness of thermal resistance of insulation (between conductor and sheath)

    :param cable: cable
    :param log: logger used to store results
    :return: thickness cable thermal insulation (mm)
    """

    if (cable.conductor.makeup.get_value(unit='', log=log) in
            [iec.SECTOR_SHAPED_IMPREGNATED, iec.SECTOR_SHAPED_IMPREGNATED, iec.OVAL, iec.OVAL_STRANDED_IMPREGNATED]):
        raise IEC60287Exception(f'calculating T_1 thickness but {cable.conductor.makeup.value} not implemented yet')

    dc = cable.conductor.dia.get_value(unit='mm', log=log)
    no_cores = cable.number_cores.get_value(unit='', log=log)
    clearance = iec60287support.calc_clearance_dia(cable, log=log).value

    if no_cores == iec.SINGLE_CORE or no_cores == iec.CONCENTRIC:
        t1 = (clearance - dc) / 2
    else:
        raise IEC60287Exception('t1: only single core or concentric cable implemented')

    return QFloat(t1, 'mm', 'IEC 60287-2-1 clause 4.1.2, thickness of thermal insulation',
                  description='thickness of thermal insulation', symbol='t_1')


@LogSection('T1 clearance')
def calc_t1_clearance(cable: Cable, source: str = None, log: cabsys.Log = None) -> QFloat:
    """Calculate the metal sheath / screen clearance thermal resistance

    Finds the thermal resistance of the clearance under the innermost metal sheath or screen.

    :param cable: cable
    :param source: source of calculation (e.g. IEC 60287-2-1)
    :param log: logger
    :return: clearance of cable
    """

    if cable.tape.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating T1 clearance: tape material not defined')
    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating T1 clearance: sheath material not defined')
    if cable.wire_screen.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating T1 clearance: wire screen material not defined')

    tape_dia = math.inf if cable.tape.material.value == iec.NONE else cable.tape.dia.get_value(unit='mm')
    sheath_dia = math.inf if cable.sheath.material.value == iec.NONE else cable.sheath.dia.get_value(unit='mm')
    wire_dia = math.inf if cable.wire_screen.material.value == iec.NONE else cable.wire_screen.dia.get_value(unit='mm')

    if wire_dia == min(wire_dia, sheath_dia, tape_dia):
        clearance = cable.wire_screen.dia_under_wire.get_value(unit='mm', log=log)
        bedding_dia = cable.core.bedding_dia.get_value(unit='mm', log=log)
        if clearance != bedding_dia:
            raise IEC60287Exception(f'calculating T1 clearance but under wire diameter does not equal core bedding')
        t_1 = 0.0

    elif sheath_dia == min(wire_dia, sheath_dia, tape_dia):
        dia_under_sheath = cable.sheath.dia_under_sheath.get_value(unit='mm', log=log)
        sheath_dia = cable.sheath.dia.get_value(unit='mm', log=log)
        sheath_rt = cable.sheath.thickness.get_value(unit='mm', log=log)
        clearance = round((dia_under_sheath + sheath_dia) / 2 - sheath_rt, 2)
        if log is not None:
            log.add_line('metal sheath clearance', clearance, unit='mm', source='IEC 60287 support')
        core_bedding_dia = cable.core.bedding_dia.get_value(unit='mm', log=log)
        if round(clearance, 2) == round(core_bedding_dia, 2):
            t_1 = 0.0
        elif round(clearance, 2) < round(core_bedding_dia, 2):
            raise IEC60287Exception(f'trying to calculate T1 but sheath clearance {clearance} mm is less than'
                                    f' core_bedding {core_bedding_dia} mm')
        else:
            rho_1 = iec60287support.get_q_parameter(cable.sheath.under_sheath_rho_1, log=log)
            if rho_1 is None:
                if cable.sheath.under_sheath_material.value == iec.NONE:
                    raise IEC60287Exception(f'trying to calculate T1 but under sheath material not specified')
                rho_1 = find_insulation_rho_1(cable.sheath.under_sheath_material, cable.design_volts, log=log).value

            t1 = (clearance - core_bedding_dia) / 2
            t_1 = rho_1 / (2 * math.pi) * math.log(1.0 + 2 * t1 / core_bedding_dia)

    elif tape_dia == min(wire_dia, sheath_dia, tape_dia):
        clearance = cable.tape.dia_under_tape.get_value(unit='mm', log=log)
        if clearance != cable.core.binder_dia:
            raise IEC60287Exception(f'calculating T1 clearance but under wire diameter greater than core binder')
        t_1 = 0.0

    else:
        raise IEC60287Exception('Calculating T1 clearance: cable does not have a metal sheath, screen or tape')

    return QFloat(t_1, 'K.m/W', source=source, description='thermal resistance of clearance', symbol='T1_clearance')


@LogSection('T_1 layer')
def calc_t1_layer_4_1_3(outer: QFloat, inner: QFloat, layer_rho_1: QFloat, layer_material: QStr,
                        design_volts: QFloat,
                        layer_name: str, vary_carbon_paper_tr: bool = None, insulation_material: QStr = None,
                        log: Log = None) -> QFloat:
    """Calculate T_1 layer, thermal resistance of layer of insulation

    Used as part of calculating T_1, the thermal resistance of the cable insulation, when multiple layers of material
    exist between the conductor and sheath.

    If the thermal resistivity of the layer (layer_rho_1) is not given then the layer material and design voltage of
    the cable will be used to determine the thermal resistivity of the layer.

    If TB880 ED1 is being used then carbon black and metalized paper has the same thermal resistivity as the insulation,
    which is generally 5.0 K.m/W for paper, and 6.0 K.m/W for PPL. Otherwise, carbon black and metalized paper has a
    thermal resistivity the same as paper, which is generally 5.0 K.m/W .

    :param outer: outer layer diameter (mm)
    :param inner: inner layer diameter (mm)
    :param layer_rho_1: thermal resistivity of insulation layer (K.m/W)
    :param layer_material: material of insulation layer
    :param design_volts: design voltage of the cable (not working voltage)
    :param layer_name: name of layer (used for log output)
    :param vary_carbon_paper_tr: does carbon/metalized paper have a single TR value or vary as per TB 880 Ed1
    :param insulation_material: cable insulation material (needed for TB 880 Ed1)
    :param log: logger used to store results
    :return: thermal resistance of layer (K.m/W)
    """

    if layer_material.get_value(unit='', log=log) == iec.NONE:
        t_1_layer = 0.0
    else:
        inner_dia = inner.get_value(unit='mm', log=log)
        outer_dia = outer.get_value(unit='mm', log=log)
        rho_1 = iec60287support.get_q_parameter(layer_rho_1, log=log)
        if rho_1 is None:
            if vary_carbon_paper_tr and layer_material.value in [iec.INS_CARBON_PAPER_TAPE_MI,
                                                                 iec.INS_METAL_PAPER_TAPE_MI,
                                                                 iec.INS_CARBON_PAPER_TAPE_OF,
                                                                 iec.INS_METAL_PAPER_TAPE_OF]:
                layer_material = insulation_material
                if log is not None:
                    log.add_line('ins mat', layer_material.value, unit='', source='TB 880 Ed 2 GP 16')
                    log.add_warning('setting screen material to have the same TR as insulation not safe')
            rho_1 = find_insulation_rho_1(layer_material, design_volts, log=log).value

        t1 = (outer_dia - inner_dia) / 2
        t_1_layer = rho_1 / (2 * math.pi) * math.log(1.0 + 2 * t1 / inner_dia)

    return QFloat(t_1_layer, 'K.m/W',
                  f'IEC 60287-2-1 Ed3 Section 4.1.3, thermal resistance of {layer_name} layer',
                  description=f'thermal resistance of {layer_name} layer', symbol='t_1_layer')


@UseState('T_2', level=cabsys.data_classes.state.CABLE)
@LogSection('T_2')
def calc_t2(cable: Cable, state: CableState = None, log: Log = None) -> QFloat:
    """Calculate T_1, thermal resistance of a cable

    IEC 60287-2-1 clause 4.1.3

    :param cable: the cable
    :param state: cable set state
    :param log: logger used to store results
    :return: thermal resistance of the cable insulation (k.m/W)
    """

    if state is None:
        pass
    if log is None:
        pass
    if cable is None:
        pass

    # number_cores = cable.number_cores.get_value(unit='', log=log)

    return QFloat(0.0, 'K.m/W', 'IEC 60287-2-1 Ed3 Section 4.1.4, thermal resistance of armour bedding',
                  description='thermal resistance of armour bedding', symbol='T_2')


@LogSection('t_3')
def calc_t3_thermal_thickness(install: AutoInstall, cable_set_no: int, cable_no: int,
                              log: Log = None) -> QFloat:
    """Calculate t_3, thickness of thermal resistance of insulation (between conductor and sheath)

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param log: logger used to store results
    :return: thickness cable thermal insulation (mm)
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.1.5.1'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.1.4.1'
    else:
        raise IEC60287Exception(f'trying to calculate t3(IEC 60287-2-1 ED3 Section 4.1.4.2) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    no_cores = cable.number_cores.get_value(unit='', log=log)
    ds = iec60287support.calc_sheath_screen_diameter(cable, log=log).value
    d_outer = cable.calc_outer_diameter(log=log)

    if (no_cores == iec.SINGLE_CORE or no_cores == iec.CONCENTRIC or
            (not cable.separate_sheath.get_value(unit='', log=log))):
        t3 = (d_outer - ds) / 2
    else:
        raise IEC60287Exception('t1: only single core or concentric cable implemented or common sheath cables')

    return QFloat(t3, 'mm', f'{source}, thickness of serving',
                  description='thickness of serving', symbol='t_3')


@UseState('T_3', level=cabsys.data_classes.state.CABLE)
@LogSection('T_3')
def calc_t3(install: AutoInstall, cable_set_no: int, cable_no: int,
            state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate T_3, thermal resistance of a cable outer covering

    IEC 60287-2-1 Ed3 clause 4.1.5

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param state: installation set state
    :param log: logger used to store results
    :return: thermal resistance of the cable insulation (k.m/W)
    """

    # this block stops the linter complaining about state not being used (it is via the decorator)
    if state is None:
        pass

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable
    number_cores = cable.number_cores.get_value(unit='', log=log)

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.1.5'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.1.4'
    else:
        raise IEC60287Exception(f'trying to calculate T3 (IEC 60287-2-1 ED3 Section 4.1.5) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    if cable.serving.material.get_value(unit='', log=log) == iec.NONE:
        t_3 = 0.0
    elif number_cores == iec.SINGLE_CORE or number_cores == iec.CONCENTRIC:
        t_3 = calc_t3_4_1_5_1(install, cable_set_no, cable_no, log=log).value
    elif number_cores == iec.THREE_CORE:
        separate_sheath = cable.separate_sheath.get_value(unit='', log=log)
        if not separate_sheath:
            t_3 = calc_t3_4_1_5_1(install, cable_set_no, cable_no, log=log).value
        else:
            raise IEC60287Exception('T3: three core separate sheath not yet implemented')
    else:
        raise IEC60287Exception(f'T3: {number_cores} not yet implemented')

    return QFloat(t_3, 'K.m/W', f'{source}, thermal resistance of serving',
                  description='thermal resistance of serving', symbol='T_3')


@LogSection('T_3 single core')
def calc_t3_4_1_5_1(install: AutoInstall, cable_set_no: int, cable_no: int,
                    log: Log = None) -> QFloat:
    """Calculate T_3, thermal resistance of single core cable insulation

    IEC 60287-2-1 Ed3 Section 4.1.5.1

    Includes over-ride in Section 4.2.4.3.3 and 4.2.4.3.3 for buried trefoil cables touching, which multiplies T1 by
    1.6.

    If install.config.non_metal_screen_isotherm is set to True then only cables buried touching trefoil with
    20 < coverage <= 100 will have T3 modified. If install.config.non_metal_screen_isotherm is set to False then all
    cables with in touching trefoil will have T3 modified by a factor of 1.6.

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param log: logger used to store results
    :return: thermal resistance of the cable insulation (k.m/W)
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.1.5'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.1.4'
    else:
        raise IEC60287Exception(f'trying to calculate T3 (IEC 60287-2-1 ED3 Section 4.1.5) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    t3_thickness = iec60287support.get_q_parameter(cable.serving.t3, log=log)
    if t3_thickness is None:
        t3_thickness = calc_t3_thermal_thickness(install, cable_set_no, cable_no, log=log).value
    rho_t = iec60287support.get_q_parameter(cable.serving.rho_t, log=log)
    if rho_t is None:
        rho_t = find_serving_rho_t(cable, log=log).value

    ds = iec60287support.calc_sheath_screen_diameter(cable, log=log).value
    if cable.armour.get_value(unit='', log=log) == iec.NONE:
        d_a = ds
    else:
        raise IEC60287Exception(f'Calculate T3: armour not implemented yet. {cable.armour} specified')

    t_3 = rho_t / (2 * math.pi) * math.log(1.0 + 2 * t3_thickness / d_a)

    coverage = iec60287support.calc_metal_coverage(cable, log=log).value
    strict_iec = install.config.non_metal_screen_isotherm.get_value(unit='', log=log)
    if (coverage >= 20.0) or (not strict_iec):
        if install.kind.value == iec.BURIED:
            formation = cable_set.calc_formation_spacing(log=log)
            if formation[0] == iec.TREFOIL and formation[3] == iec.TOUCHING:
                t_3 = t_3 * 1.6
                if log is not None:
                    log.add_line('trefoil multiplication factor', 1.6, 'n/a',
                                 'IEC 60287-2-1 Ed3 4.2.4.2 and 4.2.4.3')
                    if coverage < 20.0:
                        log.add_warning('metal coverage < 20 % but multiplication factor added'
                                        ' assuming IEC 60287-2-1 Ed 3 4.2.4.4 incorrect')

    return QFloat(t_3, 'K.m/W', f'{source}, single core cable thermal resistance of serving',
                  description='single core cable thermal resistance of insulation', symbol='T_3')


@UseState('T_4', level=cabsys.data_classes.state.CABLE)
@LogSection('T_4')
def calc_t4(install: AutoInstall, cable_set_no: int, cable_no: int,
            conductor_temperature: float,
            sheath_temperature: Union[float, Tuple[float, float, float]],
            duct_air_temp: float = None,
            state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate T_4, external thermal resistance

    IEC 60287-2-1 clause 4.2

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param duct_air_temp: average duct air temperature (°C)
    :param state: install set state
    :param log: logger used to store results
    :return: delta_theta_s
    """

    cable_set = install.cable_sets[cable_set_no]

    if cable_set.duct_layout.get_value(unit='', log=log) == iec.NO_DUCTS:
        t4 = calc_t4ddd(install, cable_set_no, cable_no, conductor_temperature, sheath_temperature, duct_air_temp,
                        state, log).value
    else:
        if duct_air_temp is None:
            raise IEC60287Exception('trying to calculate T4 cable installed in ducts but no duct temperature specified')
        t4 = calc_t4_duct_4_2_6_2(install, cable_set_no, cable_no, conductor_temperature, sheath_temperature,
                                  duct_air_temp, state=state, log=log).value

    return QFloat(t4, 'K.m/W', 'IEC 60287-2-1 clause 4.2',
                  description='external thermal resistance', symbol='T_4')


@UseState('T_4ddd', level=cabsys.data_classes.state.CABLE)
@LogSection('T_4ddd')
def calc_t4ddd(install: AutoInstall, cable_set_no: int, cable_no: int,
               conductor_temperature: float,
               sheath_temperature: Union[float, Tuple[float, float, float]],
               duct_air_temp: float = None,
               state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate T_4, thermal resistance of installation medium (external thermal resistance of duct / cable)

    IEC 60287-2-1 clause 4.2

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param duct_air_temp: average duct air temperature (°C)
    :param state: install set state
    :param log: logger used to store results
    :return: delta_theta_s
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

    duct_layout = cable_set.duct_layout.get_value(unit='', log=log)
    if duct_layout != iec.NO_DUCTS and duct_air_temp is None:
        raise IEC60287Exception('cable installed in ducts but no duct temperature specified')

    kind = install.kind.get_value(unit='', log=log)

    if kind == iec.IN_AIR_PROTECTED:
        if len(install.cable_sets) > 1:
            raise IEC60287Exception(f'trying to calculate T4, only 1 cable_set implemented for air installations')
        t4 = calc_t4_4_2_1_1(install, cable_set_no, cable_no,
                             conductor_temperature, sheath_temperature=sheath_temperature,
                             state=state, log=log).value
    elif kind == iec.BURIED:
        formation_spacing = cable_set.calc_formation_spacing()
        if (formation_spacing[3] == iec.SPACED or duct_layout in [iec.COMMON_AIR_DUCT, iec.COMMON_WATER_DUCT,
                                                                  iec.COMMON_FILLED_DUCT]):
            t4 = calc_t4_isolated_4_2_2(install, cable_set_no, cable_no, log=log).value
        elif ((formation_spacing[3] == iec.TOUCHING or formation_spacing[3] == iec.SOME_TOUCHING) and
              not install.config.use_touching_t4.value):
            log.add_warning("calculating T4 using spaced formulae but some cables are touching")
            t4 = calc_t4_isolated_4_2_2(install, cable_set_no, cable_no, log=log).value
        elif formation_spacing[3] == iec.TOUCHING and install.config.use_touching_t4.value:
            t4 = calc_t4_touching_4_2_4(install, cable_set_no, state=state, log=log).value
        else:
            raise Exception(f'trying to calculate T4 but cables are {formation_spacing[3]} and '
                            f'install.config.use_touching_t4 is {install.config.use_touching_t4}')
    else:
        raise IEC60287Exception(f'trying to calculate T_4 but installation kind "{kind}" not yet implemented')

    return QFloat(t4, 'K.m/W', 'IEC 60287-2-1 clause 4.2',
                  description='external thermal resistance', symbol='T_4ddd')


@LogSection('T_4 free air')
def calc_t4_4_2_1_1(install: AutoInstall, cable_set_no: int, cable_no: int,
                    conductor_temperature: float,
                    sheath_temperature: Union[float, Tuple[float, float, float]],
                    state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate T_4, external thermal resistance for cables in free air protected from the sun

    IEC 60287-2-1 clause 4.2.1.1

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param state: install set state
    :param log: logger used to store results
    :return: delta_theta_s
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    if state is not None:
        cable_set_state = state.cable_set_states[cable_set_no]
    else:
        cable_set_state = None
    # if cable_set_state is not None:
    #     cable_state = cable_set_state.placed_cable_states[cable_no].cable_state
    # else:
    #     cable_state = None

    de = cable.calc_outer_diameter(log=log)
    de_star = de / 1000

    h = calc_h_4_2_1_1(cable_set, cable_no, state=cable_set_state, log=log)

    delta_theta_s = calc_delta_theta_s_4_2_1_1(install, cable_set_no, cable_no,
                                               conductor_temperature, sheath_temperature=sheath_temperature,
                                               state=state, log=log)

    t4 = 1 / (math.pi * de_star * h.value * delta_theta_s.value)

    return QFloat(t4, 'K.m/W', 'IEC 60287-2-1 clause 4.2.1.1, T_4 free air',
                  description='T_4 free air', symbol='T_4 free air')


@UseState('h', level=cabsys.data_classes.state.CABLE)
@LogSection('h')
def calc_h_4_2_1_1(cable_set: AutoCableSet, cable_no: int,
                   state: CableSetState = None, log: Log = None) -> QFloat:
    """Calculate the heat dissipation coefficient (W/m^2K^(5/4)).

    IEC 60287-2-1 clause 4.2.1.1

    Calculate the heat dissipation coefficient for cables installed in free air protected for the sun.

    :param cable_set: cable set
    :param cable_no:  cable number in cable_set
    :param state: installation set state
    :param log: logger used to store results
    :return: thermal resistance of the cable insulation (k.m/W)
    """

    cable = cable_set.placed_cables[cable_no].cable

    de = cable.calc_outer_diameter(log=log)
    de_star = de / 1000

    air_arrangement = calc_air_arrangement(cable_set, cable_no, state=state, log=log).value

    z = FREE_AIR_CONSTANTS[air_arrangement][0]
    e = FREE_AIR_CONSTANTS[air_arrangement][1]
    c_g = FREE_AIR_CONSTANTS[air_arrangement][2]

    if log is not None:
        log.add_line('Z', z, '', 'IEC 60287-2-1 Table 2')
        log.add_line('E', e, '', 'IEC 60287-2-1 Table 2')
        log.add_line('C_g', c_g, '', 'IEC 60287-2-1 Table 2')

    h = z / (de_star ** c_g) + e

    return QFloat(h, '', 'IEC 60287-2-1 clause 4.2.1.1, heat dissipation coefficient',
                  description='heat dissipation coefficient', symbol='h')


@LogSection('K_A')
def calc_k_a_4_2_1_1(install: AutoInstall, cable_set_no: int, cable_no: int,
                     conductor_temperature: float,
                     sheath_temperature: Union[float, Tuple[float, float, float]],
                     state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate K_A, constant used to estimate (delta theta S)^(1/4)

    IEC 60287-2-1 clause 4.2.1.1

    K_A is a constant used to estimate (delta theta S)^(1/4), the excess of the cable surface temperature above the
    ambient temperature for cables installed in free air protected from the sun.

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param state: install set state
    :param log: logger used to store results
    :return: K_A
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

    de = cable.calc_outer_diameter(log=log)
    de_star = de / 1000
    h = calc_h_4_2_1_1(cable_set, cable_no, state=cable_set_state, log=log)
    lambda1 = iec60287_1_1w.calc_lambda_1(install, cable_set_no, cable_no, conductor_temperature,
                                          sheath_temperature,
                                          state=state, log=log)
    lambda2 = iec60287_1_1w.calc_lambda_2(install, cable_set_no, cable_no,
                                          state=state, log=log)
    n = cable_set.find_no_cores(cable_no, as_int=True, log=log)
    t1 = calc_t1(install, cable_set_no, cable_no, state=state, log=log)
    t2 = calc_t2(cable, state=cable_state, log=log)
    t3 = calc_t3(install, cable_set_no, cable_no, state=state, log=log)

    k_a = (math.pi * de_star * h.value / (1 + lambda1.value + lambda2.value) *
           (t1.value / n + t2.value * (1 + lambda1.value) + t3.value * (1 + lambda1.value + lambda2.value)))

    return QFloat(k_a, '', 'IEC 60287-2-1 clause 4.2.1.1, K_A constant',
                  description='K_A constant', symbol='K_A')


@LogSection('Δθ_S^(1/4)')
def calc_delta_theta_s_4_2_1_1(install: AutoInstall, cable_set_no: int, cable_no: int,
                               conductor_temperature: float,
                               sheath_temperature: Union[float, Tuple[float, float, float]],
                               state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate (delta theta S)^(1/4)

    IEC 60287-2-1 clause 4.2.1.1

    Calculate the excess of the cable surface temperature above the ambient temperature for cables installed in free
    air protected from the sun.

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param state: install set state
    :param log: logger used to store results
    :return: delta_theta_s
    """

    # cable_set = install.cable_sets[cable_set_no]
    # cable = cable_set.placed_cables[cable_no].cable

    # if state is not None:
    #     cable_set_state = state.cable_set_states[cable_set_no]
    # else:
    #     cable_set_state = None
    # if cable_set_state is not None:
    #     cable_state = cable_set_state.placed_cable_states[cable_no].cable_state
    # else:
    #     cable_state = None

    placed_cable = install.cable_sets[cable_set_no].placed_cables[cable_no]
    # ambient_temperature = placed_cable.ambient_theta.get_value(unit='°C', log=log)
    # ambient_temperature = cable_set.placed_cables[cable_no].ambient_theta.get_value(unit='°C', log=log)
    ambient_temp = iec60287support.get_q_parameter(placed_cable.ambient_theta, log=log)
    if ambient_temp is None:
        # ambient_temperature = install.ambient_theta.get_value(unit='°C', log=log)
        from cabsys.data_classes.scenario import Scenario
        if install.selected_scenario.value == Scenario.NO_SCENARIO:
            selected_scenario_name = None
        else:
            selected_scenario_name = install.selected_scenario.value
        ambient_temp = install.get_ambient_temperature(selected_scenario_name, cable_set_no,
                                                       cable_no=0, unit='°C', log=log)

    delta_theta = conductor_temperature - ambient_temp

    delta_theta_d = calc_delta_theta_d_4_2_1_1(install, cable_set_no, cable_no,
                                               conductor_temperature,
                                               sheath_temperature,
                                               state=state, log=log)
    k_a = calc_k_a_4_2_1_1(install, cable_set_no, cable_no, conductor_temperature,
                           sheath_temperature,
                           state=state, log=log)

    d_t_s = 1.0
    d_t_s2 = 2.0

    i = 0
    while abs(d_t_s2 - d_t_s) > 0.001:
        i = i + 1
        d_t_s = d_t_s2
        d_t_s2 = ((delta_theta + delta_theta_d.value) / (1 + k_a.value * d_t_s)) ** 0.25
        if log is not None:
            log.add_line(f'Δθ_s({i})', d_t_s2, '°C^(1/4)')

    return QFloat(d_t_s2, '°C^(1/4)', 'IEC 60287-2-1 clause 4.2.1.1, (Δθ_S)^(1/4)',
                  description='(Δθ_S)^(1/4)', symbol='(Δθ_S)^(1/4)')


@LogSection('Δθ_d')
def calc_delta_theta_d_4_2_1_1(install: AutoInstall, cable_set_no: int, cable_no: int,
                               conductor_temperature: float,
                               sheath_temperature: Union[float, Tuple[float, float, float]],
                               u_pe: float = None,
                               state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate delta theta d, a factor, which accounts for the dielectric loss

    Calculate delta theta d, a factor, which accounts for the dielectric losses when calculating the external thermal
    resistance of a cable installed in free air protected from the sun.

    IEC 60287-2-1 clause 4.2.1.1

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param u_pe: phase to earth voltage applied to cable (V)
    :param state: install set state
    :param log: logger used to store results
    :return: K_A
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

    # always_calc_wd = install.config.always_calc_wd.get_value(unit='', log=log)
    wd = iec60287_1_1w.calc_wd(install, cable_set_no, cable_no, u_pe=u_pe, state=state, log=log)
    lambda1 = iec60287_1_1w.calc_lambda_1(install, cable_set_no, cable_no, conductor_temperature,
                                          sheath_temperature,
                                          state=state, log=log)
    lambda2 = iec60287_1_1w.calc_lambda_2(install, cable_set_no, cable_no,
                                          state=state, log=log)
    n = cable_set.find_no_cores(cable_no, as_int=True, log=log)
    t1 = calc_t1(install, cable_set_no, cable_no, state=state, log=log)
    t2 = calc_t2(cable, state=cable_state, log=log)

    d_t_d = wd.value * ((1 / (1 + lambda1.value + lambda2.value) - 0.5) * t1.value - n * lambda2.value * t2.value /
                        (1 + lambda1.value + lambda2.value))

    return QFloat(d_t_d, '°C', 'IEC 60287-2-1 clause 4.2.1.1, Δθ_d', description='Δθ_d', symbol='Δθ_d')


# TODO: calculate T4 for cables in air exposed to sun


@LogSection('T_4 buried isolated cable')
def calc_t4_isolated_4_2_2(install: AutoInstall, cable_set_no: int, cable_no: int,
                           log: Log = None) -> QFloat:
    """Calculate T_4, external thermal resistance for single isolated buried cable

    IEC 60287-2-1 clause 4.2.2

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param log: logger used to store results
    :return: delta_theta_s
    """

    cable_set = install.cable_sets[cable_set_no]

    # rho_t = install.scenarios[install.selected_scenario.value].buried.ground_tr
    rho = install.get_q_ground_tr(install.selected_scenario.value).get_value(unit='K.m/W', log=log)
    u_1 = calc_u_1_4_2_2(cable_set, cable_no, log=log)

    t4 = rho / (2 * math.pi) * (math.log(u_1.value + math.sqrt(u_1.value ** 2 - 1)))

    return QFloat(t4, 'K.m/W', 'IEC 60287-2-1 clause 4.2.2, T_4 buried isolated cable',
                  description='T_4 buried single isolated cable', symbol='T_4 buried')


@LogSection('u_1')
def calc_u_1_4_2_2(cable_set: AutoCableSet, cable_no: int, log: Log = None) -> QFloat:
    """Calculate u_1, a ratio of 2 * cable depth to external diameter

    IEC 60287-2-1 clause 4.2.2

    Calculate the ratio of two times the cable depth to the cable external diameter. Previous versions of
    IEC 60287-2-1 called this u.

    :param cable_set: cable set
    :param cable_no:  cable number in cable_set
    :param log: logger used to store results
    :return: u_1
    """

    placed_cable = cable_set.placed_cables[cable_no]
    cable = placed_cable.cable

    duct_layout = cable_set.duct_layout.get_value(unit='', log=log)
    if duct_layout == iec.COMMON_AIR_DUCT or duct_layout == iec.COMMON_WATER_DUCT:
        depth = 0 - cable_set.pipe_y.get_value('mm', log=log)
    else:
        depth = 0 - placed_cable.y.get_value('mm', log=log)
    if duct_layout == iec.NO_DUCTS:
        de = cable.calc_outer_diameter(log=log)
    else:
        de = cable_set.duct_od.get_value(unit='mm', log=log)

    u_1 = 2 * depth / de

    return QFloat(u_1, '', 'IEC 60287-2-1 clause 4.2.2, u_1',
                  description='u_1', symbol='u_1')


@LogSection('Δθ_p')
def calc_delta_theta_p(install: AutoInstall, cable_set_no: int, cable_no: int,
                       install_cond_temp: List[List[float]], install_current: List[float],
                       u_pe_list: List[List[float]] = None,
                       state: InstallState = None, log: Log = None):
    """Calculate delta theta p, temperature rise at cable p due to other cables

    IEC 60287-2-1 clause 4.2.3.2

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param install_cond_temp: conductor temperature of each cable in install (°C)
    :param install_current: current in each cable set in install (A)
    :param u_pe_list: list of phase to earth cable voltages (V)
    :param state: install set state
    :param log: logger used to store results
    :return: K_A
    """
    delta_theta_p = 0.0
    for cable_set_count, cable_set in enumerate(install.cable_sets):
        duct_layout = cable_set.duct_layout.get_value(unit='', log=log)
        is_common_duct = duct_layout in [iec.COMMON_AIR_DUCT, iec.COMMON_WATER_DUCT, iec.COMMON_FILLED_DUCT]
        if cable_set_count == cable_set_no:
            formation = cable_set.calc_formation_spacing(log=log)
            if is_common_duct or (formation[3] == iec.TOUCHING and install.config.use_touching_t4.get_value(log=log)):
                # looking at cables in same cable set and common duct or using T4 touching
                log.add_line(f'Δθ_pk (cct={cable_set_count})', 0, '°C',
                             'temperature rise due to touching cables (use_touching_t4 = True)')
                continue
        elif is_common_duct and install.config.touching_delta_theta.get_value(unit='', log=log):
            raise IEC60287Exception('nearby common ducts not yet implemented with config.touching_delta_theta')

        for placed_cable_count, placed_cable in enumerate(cable_set.placed_cables):
            if cable_set_count == cable_set_no and placed_cable_count == cable_no:
                # check p != k
                continue
            log.start_section(f'Δθ_pk (cct={cable_set_count}, cable={placed_cable_count})',
                              'temperature rise due to adjacent cable')
            cond_temp = install_cond_temp[cable_set_count][placed_cable_count]
            cable_current = install_current[cable_set_count]
            u_pe = None if u_pe_list is None else u_pe_list[cable_set_count][placed_cable_count]
            sheath_temp = iec60287_1_1w.calc_theta_sc(install, cable_set_count, placed_cable_count,
                                                      current=cable_current,
                                                      conductor_temp=cond_temp,
                                                      u_pe=u_pe,
                                                      state=state, log=log)
            if isinstance(sheath_temp, QFloat):
                sheath_temp = sheath_temp.value
            else:
                sheath_temp = (sheath_temp[0].value, sheath_temp[1].value, sheath_temp[2].value)
            delta_theta_kp = calc_delta_kp_4_2_3_2(install, cable_set_no, cable_no,
                                                   cable_set_count, placed_cable_count,
                                                   cond_temp=cond_temp,
                                                   sheath_temp=sheath_temp,
                                                   current=cable_current,
                                                   u_pe=u_pe,
                                                   state=state, log=log)
            log.end_section(f'Δθ_pk (cct={cable_set_count}, cable={placed_cable_count})',
                            delta_theta_kp.value, '°C',
                            'temperature rise due to adjacent cable')
            delta_theta_p = delta_theta_p + delta_theta_kp.value

    return QFloat(delta_theta_p, '°C', 'IEC 60287-2-1 clause 4.2.3.2',
                  description='temperature rise at cable p due to other cables', symbol='Δθ_p')


@LogSection('Δθ_kp')
def calc_delta_kp_4_2_3_2(install: AutoInstall, cable_set_p_no: int, cable_p_no: int,
                          cable_set_k_no: int, cable_k_no: int,
                          cond_temp: float, sheath_temp: float, current: float,
                          u_pe: float = None,
                          state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate delta kp, temperature rise at cable p due to cable k (°C)

    IEC 60287-2-1 clause 4.2.3.2

    Calculate the temperature rise at cable p due to cable k.

    :param install: cable installation
    :param cable_set_p_no: cable set number in install
    :param cable_p_no:  cable number in cable_set
    :param cable_set_k_no: cable set number in install
    :param cable_k_no:  cable number in cable_set
    :param cond_temp: conductor temperature of cable k (°C)
    :param sheath_temp: sheath temperature of cable k (°C)
    :param current: current in conductor of cable k (A)
    :param u_pe: phase to earth voltage of cable k (V)
    :param state: install set state
    :param log: logger used to store results
    :return: delta_theta_kp (°C)
    """

    # rho_t = install.scenarios[install.selected_scenario.value].buried.ground_tr.get_value(unit='K.m/W', log=log)
    rho_t = install.get_q_ground_tr(install.selected_scenario.value).get_value(unit='K.m/W', log=log)
    w_k = calc_wk(install, cable_set_k_no, cable_k_no,
                  cond_temp, sheath_temp, current,
                  u_pe=u_pe,
                  state=state, log=log)
    cable_p = install.cable_sets[cable_set_p_no].placed_cables[cable_p_no]
    cable_k = install.cable_sets[cable_set_k_no].placed_cables[cable_k_no]
    d_pk = calc_d_pk_4_2_3_2(cable_p, cable_k, log=log)
    d_pk_dash = calc_d_pk_dash_4_2_3_2(cable_p, cable_k, log=log)

    delta_theta_kp = rho_t / (2 * math.pi) * w_k.value * math.log(d_pk_dash.value / d_pk.value)

    return QFloat(delta_theta_kp, '°C', 'IEC 60287-2-1 clause 4.2.3.2',
                  description='temperature rise at cable p due to cable k', symbol='Δθ_kp')


# @LogSection('Δθ_k_point')
def calc_delta_k_point_4_2_3_2(install: Install,
                               x_coordinate: float, y_coordinate: float,
                               cable_set_k_no: int, cable_k_no: int,
                               w_k: float,
                               log: Log = None) -> QFloat:
    """Calculate delta kp, temperature rise at cable k due to cable p (°C)

    IEC 60287-2-1 clause 4.2.3.2

    Calculate the temperature rise at cable p due to cable k. If the temperature rise at (x, y) coordinate and cable k
    is required then pass None for cable p for cable_set_p_no and then the coordinates.

    :param install: cable installation
    :param x_coordinate: x_coordinate if cable p is not given (mm)
    :param y_coordinate: y_coordinate if cable p is not given (mm)
    :param cable_set_k_no: cable set number in install
    :param cable_k_no:  cable number in cable_set
    :param w_k: heat loss of cable k (W/m)

    :param log: logger used to store results
    :return: delta_theta_kp (°C)
    """

    # rho_t = install.scenarios[install.selected_scenario.value].buried.ground_tr.get_value(unit='K.m/W', log=log)
    rho_t = install.get_q_ground_tr(install.selected_scenario.value).get_value(unit='K.m/W', log=log)
    cable_k = install.cable_sets[cable_set_k_no].placed_cables[cable_k_no]
    d_pk = calc_d_point_k_4_2_3_2(x_coordinate, y_coordinate, cable_k, log=log)
    d_pk_dash = calc_d_point_k_dash_4_2_3_2(x_coordinate, y_coordinate, cable_k,  log=log)

    delta_theta_kp = rho_t / (2 * math.pi) * w_k * math.log(d_pk_dash.value / d_pk.value)

    return QFloat(delta_theta_kp, '°C', 'IEC 60287-2-1 clause 4.2.3.2',
                  description='temperature rise at cable p due to cable k', symbol='Δθ_kp')


@UseState('w_k', level=cabsys.data_classes.state.CABLE)
@LogSection('w_k')
def calc_wk(install: AutoInstall, cable_set_no: int, cable_no: int,
            cond_temp: float, sheath_temp: float, current: float,
            u_pe: float = None,
            state: InstallState = None, log: Log = None):
    """Calculate the heat loss for a cable (W/m)

    Normally the phase to earth voltage is defined in the CableSet.PlacedCable object but this can be overridden by
    supplying a value as an argument.

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no: cable number in cable_set
    :param cond_temp:
    :param sheath_temp:
    :param current: current in cable (A)
    :param u_pe: phase to earth voltage applied to cable (V)
    :param state: cable set state
    :param log: logger used to store results
    :return: heat loss of cable (W/m)
    """
    if state is not None:
        cable_set_state = state.cable_set_states[cable_set_no]
    else:
        cable_set_state = None

    cable_set = install.cable_sets[cable_set_no]
    r_ac = iec60287_1_1w.calc_r_ac(cable_set, cable_no,
                                   cond_temp=cond_temp,
                                   iec_60287_1_1_ver=install.config.iec_60287_1_1_ver.value,
                                   state=cable_set_state, log=log)
    lambda1 = iec60287_1_1w.calc_lambda_1(install, cable_set_no, cable_no,
                                          conductor_temperature=cond_temp,
                                          sheath_temperature=sheath_temp,
                                          state=state, log=log)
    lambda2 = iec60287_1_1w.calc_lambda_2(install, cable_set_no, cable_no,
                                          state=state, log=log)
    # always_calc_wd = install.config.always_calc_wd.get_value(unit='', log=log)
    wd = iec60287_1_1w.calc_wd(install, cable_set_no, cable_no, u_pe=u_pe, state=state, log=log)
    w_k = current ** 2 * r_ac.value * (1 + lambda1.value + lambda2.value) + wd.value
    return QFloat(w_k, 'W/m', 'heat loss of cable k, used in IEC 60287 60287-2-1 Section 4.2.3.2',
                  description='heat loss for cable k', symbol='w_k')


@LogSection('d_pk')
def calc_d_pk_4_2_3_2(placed_cable_p: PlacedCable, placed_cable_k: PlacedCable, log: Log = None) -> QFloat:
    """Calculate dpk, distance between cable p and cable k (mm)

    Cables the distance between cable p and cable k.

    IEC 60287-2-1 clause 4.2.3.2

    :param placed_cable_p: cable p
    :param placed_cable_k: cable k
    :param log: logger used to store results
    :return: d_pk
    """

    p_x, p_y = placed_cable_p.x.get_value('mm', log), placed_cable_p.y.get_value('mm', log)
    k_x, k_y = placed_cable_k.x.get_value('mm', log), placed_cable_k.y.get_value('mm', log)
    d_pk = math.sqrt((k_x - p_x)**2 + (k_y - p_y)**2)

    return QFloat(d_pk, 'mm', 'IEC 60287-2-1 clause 4.2.3.2, d_pk',
                  description='distance between cable p and k', symbol='d_pk')


# @LogSection('d_point_k')
def calc_d_point_k_4_2_3_2(x_coordinate: float, y_coordinate: float,
                           placed_cable_k: PlacedCable,
                           log: Log = None) -> QFloat:
    """Calculate dp_point_k, distance between point p and cable k (mm)

    Cables the distance between point p and cable k.

    IEC 60287-2-1 clause 4.2.3.2

    :param x_coordinate: x_coordinate if cable p is not given
    :param y_coordinate: y_coordinate if cable p is not given
    :param placed_cable_k: cable k
    :param log: logger used to store results
    :return: d_pk
    """

    p_x, p_y = x_coordinate, y_coordinate
    k_x, k_y = placed_cable_k.x.get_value('mm', log), placed_cable_k.y.get_value('mm', log)
    d_pk = math.sqrt((k_x - p_x)**2 + (k_y - p_y)**2)

    return QFloat(d_pk, 'mm', 'IEC 60287-2-1 clause 4.2.3.2, d_pk',
                  description='distance between point p and k', symbol='d_point_k')


@LogSection('d_pk_dash')
def calc_d_pk_dash_4_2_3_2(placed_cable_p: PlacedCable, placed_cable_k: PlacedCable,
                           log: Log = None) -> QFloat:
    """Calculate dpk', distance between cable p and the image of cable k (mm)

    Cables the distance between cable p and reflection of cable k.

    IEC 60287-2-1 clause 4.2.3.2

    :param placed_cable_p: cable p
    :param placed_cable_k: cable k
    :param log: logger used to store results
    :return: d_pk'
    """

    p_x, p_y = placed_cable_p.x.get_value('mm', log), placed_cable_p.y.get_value('mm', log)
    k_x, k_y = placed_cable_k.x.get_value('mm', log), placed_cable_k.y.get_value('mm', log)
    d_pk = math.sqrt((k_x - p_x)**2 + (k_y + p_y)**2)

    return QFloat(d_pk, 'mm', "IEC 60287-2-1 clause 4.2.3.2, d_pk'",
                  description='distance between cable p and the image of k', symbol="d_pk'")


# @LogSection('d_point_k_dash')
def calc_d_point_k_dash_4_2_3_2(x_coordinate: float, y_coordinate: float,
                                placed_cable_k: PlacedCable,
                                log: Log = None) -> QFloat:
    """Calculate d_point_k', distance between point p and the image of cable k (mm)

    Cables the distance between point p and reflection of cable k.

    IEC 60287-2-1 clause 4.2.3.2

    :param x_coordinate: x_coordinate if cable p is not given
    :param y_coordinate: y_coordinate if cable p is not given
    :param placed_cable_k: cable k
    :param log: logger used to store results
    :return: d_pk'
    """

    p_x, p_y = x_coordinate, y_coordinate
    k_x, k_y = placed_cable_k.x.get_value('mm', log), placed_cable_k.y.get_value('mm', log)
    d_pk = math.sqrt((k_x - p_x)**2 + (k_y + p_y)**2)

    return QFloat(d_pk, 'mm', "IEC 60287-2-1 clause 4.2.3.2, d_point_k'",
                  description='distance between cable p and the image of k', symbol="d_point_k'")

# TODO: Section 4.2.3.3 (buried spaced cables equally loaded) to be implemented


# TODO: Section 4.2.4 (buried touching cables equally loaded) to be implemented
@LogSection('T4_touching')
def calc_t4_touching_4_2_4(install: AutoInstall, cable_set_num: int,
                           state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate T_4, external thermal resistance of touching cables/ducts (ground)

    IEC 60287-2-1 Section 4.2.4

    The thermal resistance of the ground for touching cables is calculated in line with IEC 60287-2-1. The methods
    do not use superposition exactly and try to take account of the metal screen/sheath.

    :param install: cable installation
    :param cable_set_num: cable set number in install
    :param state: install set state
    :param log: logger used to store results
    :return: external thermal resistance of the cable (k.m/W)
    """

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.2.4'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.2.4'
    else:
        raise IEC60287Exception(f'trying to calculate t4 touching (IEC 60287-2-1 ED3 Section 4.2.2) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    cable_set = install.cable_sets[cable_set_num]
    num_cables = len(cable_set.placed_cables)
    if num_cables == 2:
        raise Exception("touching T4 for 2 cables according to IEC not implemented yet")
    elif num_cables == 3:
        formation = cable_set.calc_formation_spacing()
        if formation[0] == iec.FLAT and formation[4] == iec.HORIZONTAL:
            raise Exception("flat horizontal touching T4 for 3 cables according to IEC not implemented yet")
        elif formation[0] == iec.TREFOIL:
            t_4 = calc_t4_touching_trefoil_4_2_4_3_1(install, cable_set_num, state=state, log=log).value
        else:
            raise Exception(f"touching T4 for 3 cables in {formation[0]}, {formation[4]} formation not covered by"
                            f" IEC 60287."
                            f" Try setting install.config.use_touching_t4 to false.")
    else:
        raise Exception(f"touching T4 for {num_cables} cables not covered by IEC 60287."
                        f" Try setting install.config.use_touching_t4 to false")

    return QFloat(t_4, 'K.m/W', f'{source}, external cable/duct thermal resistance',
                  description='cable/duct external thermal resistance', symbol='T_4')


@LogSection('T4_touching_trefoil')
def calc_t4_touching_trefoil_4_2_4_3_1(install: AutoInstall, cable_set_num: int,
                                       state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate T_4, external thermal resistance of 3 touching trefoil cables/ducts (ground)

    IEC 60287-2-1 Section 4.2.4.3.1

    The thermal resistance of the ground for touching trefoil cables is calculated in line with IEC 60287-2-1. The
    methods do not use superposition exactly and try to take account of the metal screen/sheath.

    :param install: cable installation
    :param cable_set_num: cable set number in install
    :param state: install set state
    :param log: logger used to store results
    :return: external thermal resistance of the cable (k.m/W)
    """

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.2.4.3.1'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.2.4.3.1'
    else:
        raise IEC60287Exception(f'trying to calculate t4 touching (IEC 60287-2-1 ED3 Section 4.2.4.3.1) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    cable_set = install.cable_sets[cable_set_num]
    cable = cable_set.placed_cables[0].cable
    # check cables are the same in cable_set
    for i_placed_cable in cable_set.placed_cables:
        if i_placed_cable.cable != cable:
            raise Exception('trying to calculate T4 touching trefoil but all the cables in the cable set'
                            ' are not the same')

    # check if trefoil is inverted
    y0 = cable_set.placed_cables[0].y.value
    y1 = cable_set.placed_cables[1].y.value
    y2 = cable_set.placed_cables[2].y.value
    y_list = sorted([y0, y1, y2])
    if y_list[0] == y_list[1] and y_list[2] > y_list[0]:
        trefoil_top_cable = 2
    elif y_list[1] == y_list[2] and y_list[0] > y_list[1]:
        trefoil_top_cable = 0
    elif y_list[2] == y_list[0] and y_list[1] > y_list[2]:
        trefoil_top_cable = 1
    else:
        raise Exception('trying to calculate T4 touching trefoil but cables are not in trefoil')

    duct_layout = cable_set.duct_layout.get_value(unit='', log=log)
    if duct_layout in [iec.COMMON_AIR_DUCT, iec.COMMON_WATER_DUCT, iec.COMMON_FILLED_DUCT]:
        raise Exception('trying to calculate T4 for touching trefoil but duct layout is common ducts')
    elif duct_layout == iec.NO_DUCTS:
        de = cable.calc_outer_diameter(log=log)
    elif duct_layout in [iec.INDIVIDUAL_AIR_DUCTS, iec.INDIVIDUAL_WATER_DUCT, iec.INDIVIDUAL_FILLED_DUCT]:
        de = cable_set.duct_od.get_value(unit='mm', log=log)
    else:
        raise Exception(f'trying to calculate T4 for touching trefoil but duct layout is {duct_layout}')
    log.add_line('D_e', de, 'mm')

    depth_l = -y_list[trefoil_top_cable] + de / math.sqrt(3)
    log.add_line('L', depth_l, 'mm', source=f'inverted trefoil {trefoil_top_cable}')

    u_1 = 2 * depth_l / de
    log.add_line('U_1', u_1, '', source)

    # FIXME: this is only for metal sheath cables
    coverage = iec60287support.calc_metal_coverage(cable, log=log).value
    if coverage > 50 and duct_layout == iec.NO_DUCTS:
        t_4 = calc_t4_touching_trefoil_metal_4_2_4_3_2(install, u_1, log=log).value
    elif coverage >= 20 and duct_layout == iec.NO_DUCTS:
        t_4 = calc_t4_touching_trefoil_part_metal_4_2_4_3_3(install, u_1, log=log).value
    elif coverage < 20 or (duct_layout in [iec.INDIVIDUAL_WATER_DUCT, iec.INDIVIDUAL_FILLED_DUCT,
                                           iec.INDIVIDUAL_AIR_DUCTS]):
        t_4 = calc_t4_touching_trefoil_non_metal_4_2_4_3_4(install, u_1, log=log).value
    else:
        raise Exception('part and no metal covered cables not implemented yet')

    return QFloat(t_4, 'K.m/W', f'{source}, external cable/duct thermal resistance',
                  description='cable/duct external thermal resistance', symbol='T_4')


@LogSection('T4_touching_trefoil_metal')
def calc_t4_touching_trefoil_metal_4_2_4_3_2(install: AutoInstall, u_1: float,
                                             log: Log = None) -> QFloat:
    """Calculate T_4, external thermal resistance of 3 touching trefoil metal sheathed cables (ground)

    IEC 60287-2-1 Section 4.2.4.3.2

    The thermal resistance of the ground for touching trefoil metal sheathed/screened cables is calculated in line with
    IEC 60287-2-1. The method does not use superposition exactly and tries to take account of the metal screen/sheath.

    :param install: cable installation
    :param u_1: U_1
    :param log: logger used to store results
    :return: external thermal resistance of the cable (k.m/W)
    """

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.2.4.3.2'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.2.4.3.2'
    else:
        raise IEC60287Exception(f'trying to calculate t4 touching (IEC 60287-2-1 ED3 Section 4.2.4.3.2) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    rho = install.ground_tr.get_value(unit='K.m/W', log=log)

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        t_4 = 1.5 / math.pi * rho * (math.log(u_1 + math.sqrt(u_1**2 - 1)) - 0.630)
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        t_4 = 1.5 / math.pi * rho * (math.log(2 * u_1) - 0.630)
    else:
        raise IEC60287Exception(f'trying to calculate t4 touching (IEC 60287-2-1 ED3 Section 4.2.4.3.2) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    return QFloat(t_4, 'K.m/W', f'{source}, external cable/duct thermal resistance',
                  description='cable/duct external thermal resistance', symbol='T_4')


@LogSection('T4_touching_trefoil_part_metal')
def calc_t4_touching_trefoil_part_metal_4_2_4_3_3(install: AutoInstall, u_1: float,
                                                  log: Log = None) -> QFloat:
    """Calculate T_4, external thermal resistance of 3 touching trefoil part metal sheathed cables (ground)

    IEC 60287-2-1 Section 4.2.4.3.3

    The thermal resistance of the ground for touching trefoil metal sheathed/screened cables is calculated in line with
    IEC 60287-2-1. The method does not use superposition exactly and tries to take account of the metal screen/sheath.

    :param install: cable installation
    :param u_1: U_1
    :param log: logger used to store results
    :return: external thermal resistance of the cable (k.m/W)
    """

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.2.4.3.3'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.2.4.3.3'
    else:
        raise IEC60287Exception(f'trying to calculate t4 touching (IEC 60287-2-1 ED3 Section 4.2.4.3.3) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    rho = install.ground_tr.get_value(unit='K.m/W', log=log)
    t_4 = 1.5 / math.pi * rho * (math.log(u_1 + math.sqrt(u_1**2 - 1)) - 0.630)

    return QFloat(t_4, 'K.m/W', f'{source}, external cable/duct thermal resistance',
                  description='cable/duct external thermal resistance', symbol='T_4')


@LogSection('T4_touching_trefoil_non_metal')
def calc_t4_touching_trefoil_non_metal_4_2_4_3_4(install: AutoInstall, u_1: float,
                                                 log: Log = None) -> QFloat:
    """Calculate T_4, external thermal resistance of 3 touching trefoil non-metal sheathed cables (ground)

    IEC 60287-2-1 Section 4.2.4.3.4

    The thermal resistance of the ground for touching trefoil metal sheathed/screened cables is calculated in line with
    IEC 60287-2-1. The method does not use superposition exactly and tries to take account of the metal screen/sheath.

    :param install: cable installation
    :param u_1: U_1
    :param log: logger used to store results
    :return: external thermal resistance of the cable (k.m/W)
    """

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.2.4.3.4'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.2.4.3.4'
    else:
        raise IEC60287Exception(f'trying to calculate t4 touching (IEC 60287-2-1 ED3 Section 4.2.4.3.4) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    rho = install.ground_tr.get_value(unit='K.m/W', log=log)
    t_4 = 1 / (2 * math.pi) * rho * (math.log(u_1 + math.sqrt(u_1**2)) + 2 * math.log(u_1))

    return QFloat(t_4, 'K.m/W', f'{source}, external cable/duct thermal resistance',
                  description='cable/duct external thermal resistance', symbol='T_4')


# TODO: Section 4.2.5 (cables in buried troughs) to be implemented


@LogSection('t_4 duct')
def calc_t4_duct_4_2_6_2(install: AutoInstall, cable_set_no: int, cable_num: int,
                         conductor_temperature: float, sheath_temperature: float,
                         duct_air_temp: float,
                         state: InstallState = None, log: Log = None) -> QFloat:
    """Calculate T_4 duct, external thermal resistance of cables for ducted installations

    IEC 60287-2-1 Section 4.2.6.2 extended

    The basic IEC 60287-2-1 equation is used but extended to take account of multiple cables in a common duct

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_num: cable number in cable_set
    :param conductor_temperature: conductor temperature (°C)
    :param sheath_temperature: sheath/screen temperature (°C)
    :param duct_air_temp: average duct air temperature (°C)
    :param state: install set state
    :param log: logger used to store results
    :return: external thermal resistance of the cable (k.m/W)
    """

    # cable_set = install.cable_sets[cable_set_no]
    # cable = cable_set.placed_cables[cable_no].cable

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.2.6.2add'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.2.7.1add'
    else:
        raise IEC60287Exception(f'trying to calculate t4 duct (IEC 60287-2-1 ED3 Section 4.2.6.2) but'
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    t4dash = calc_t4dash_4_2_6_3(install, cable_set_no, cable_num, duct_air_temp, log=log).value
    t4dd = calc_t4dd_4_2_6_4(install, cable_set_no, cable_num, log=log).value
    t4ddd = calc_t4ddd(install, cable_set_no, cable_num, conductor_temperature, sheath_temperature, duct_air_temp,
                       state, log).value
    n_d = install.cable_sets[cable_set_no].calc_num_cables_in_ducts(log=log).value
    t_4 = n_d * (t4dash + t4dd + t4ddd)

    return QFloat(t_4, 'K.m/W', f'{source}, external cable thermal resistance (duct)',
                  description='cable external thermal resistance', symbol='T_4 duct')


@LogSection('T_4dash')
def calc_t4dash_4_2_6_3(install: AutoInstall, cable_set_no: int, cable_no: int,
                        duct_air_temperature: float,
                        log: Log = None) -> QFloat:
    """Calculate T_4', thermal resistance between cable and duct

    IEC 60287-2-1 clause 4.2.6.3

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param duct_air_temperature: average duct air temperature (°C)
    :param log: logger used to store results
    :return: delta_theta_s
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.2.6.3'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.2.7.2'
    else:
        raise IEC60287Exception(f"trying to calculate T4' (IEC 60287-2-1 ED3 Section 4.2.6.3) but"
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    duct_layout = cable_set.duct_layout.get_value(unit='', log=log)

    de_cable = cable.calc_outer_diameter(log=log)
    if duct_layout in [iec.INDIVIDUAL_WATER_DUCT, iec.INDIVIDUAL_AIR_DUCTS, iec.INDIVIDUAL_FILLED_DUCT]:
        de = de_cable
        if de > 100.0 or de < 25.0:
            if log is not None:
                log.add_warning(f"calculating T4' but cable diameter {de} mm is outside IEC limits")
    elif duct_layout in [iec.COMMON_WATER_DUCT, iec.COMMON_AIR_DUCT, iec.COMMON_FILLED_DUCT]:
        number_cables = cable_set.find_no_cables(log=log)
        if number_cables == 1:
            de = de_cable
        elif number_cables == 2:
            de = de_cable * 1.65
        elif number_cables == 3:
            de = de_cable * 2.15
        elif number_cables == 4:
            de = de_cable * 2.5
        else:
            raise IEC60287Exception(f"calculating T4' but {number_cables} in duct not recognised")
        if de > 100.0 or de < 25.0:
            if log is not None:
                log.add_warning(f"calculating T4' but effective cable diameter {de} mm is outside IEC limits")
    else:
        raise IEC60287Exception(f"calculating T4' but duct layout is {duct_layout}")
    if log is not None:
        log.add_line('De', de, 'mm', f'{source}')

    if duct_layout == iec.INDIVIDUAL_FILLED_DUCT or duct_layout == iec.COMMON_FILLED_DUCT:
        filling_rho_t = cable_set.duct_filling_rho_t.get_value(unit='K.m/W', log=log)
        if filling_rho_t is None:
            raise IEC60287Exception("trying to calculate duct filling thermal resistance T4' but"
                                    "duct filling thermal resistivity is set to None")
        d_d = cable_set.duct_id.get_value('mm', log=log)
        t4dash = filling_rho_t / (2 * math.pi) * math.log(d_d / de)
        source = 'Missing, used IEC 60287-2-1:2023 Section 4.2.6.4'
    else:
        if install.kind.get_value(unit='', log=log) == iec.BURIED:
            in_air = False
        else:
            in_air = True
        u = find_duct_u(cable_set, in_air, log=log).value
        v = find_duct_v(cable_set, in_air, log=log).value
        y = find_duct_y(cable_set, in_air, log=log).value

        if log is not None:
            log.add_line('θ_m', duct_air_temperature, '°C')
        t4dash = u / (1 + 0.1 * (v + y * duct_air_temperature) * de)

    return QFloat(t4dash, 'K.m/W', f"{source}, T_4'",
                  description="T_4'", symbol="T_4dash")


@LogSection('t_4dd')
def calc_t4dd_4_2_6_4(install: AutoInstall, cable_set_no: int, cable_no: int,
                      log: Log = None) -> QFloat:
    """Calculate T_4dd, thermal resistance of duct walls

    IEC 60287-2-1 Section 4.2.6.4

    :param install: cable installation
    :param cable_set_no: cable set number in install
    :param cable_no:  cable number in cable_set
    :param log: logger used to store results
    :return: thermal resistance of the cable insulation (k.m/W)
    """

    cable_set = install.cable_sets[cable_set_no]
    cable = cable_set.placed_cables[cable_no].cable
    # TODO: calculate duct thermal resistance for each duct

    if install.config.iec_60287_2_1_ver.value in [None, iec.IEC60287_2_1_ED3, iec.IEC60287_2_1_ED3_STRICT]:
        source = 'IEC 60287-2-1 ED3 Section 4.2.6.4'
    elif install.config.iec_60287_2_1_ver.value in [iec.IEC60287_2_1_ED2, iec.CIGRE_TB880_2022]:
        source = 'IEC 60287-2-1 ED2 Section 4.2.7.3'
    else:
        raise IEC60287Exception(f"trying to calculate T4'' (IEC 60287-2-1 ED3 Section 4.2.6.4) but"
                                f' IEC 60287-2-1 version "{install.config.iec_60287_2_1_ver.value}" in install config'
                                f' not recognised')

    rho_t = iec60287support.get_q_parameter(cable_set.duct_rho_t, log=log)
    if rho_t is None:
        rho_t = find_duct_rho_t(cable_set, log=log).value
    d_d = cable_set.duct_id.get_value('mm', log=log)
    d_o = cable_set.duct_od.get_value('mm', log=log)
    t_4dd = rho_t / (2 * math.pi) * math.log(d_o / d_d)

    return QFloat(t_4dd, 'K.m/W', f'{source}, cable duct thermal resistance',
                  description='cable duct thermal resistance', symbol='T_4dd')


# ********************** tables ***********************

# IEC 60287-1-1 Table 1 Thermal Resistivity
#                         material        up to U0, value
INSULATION_RESISTIVITY = {iec.INS_PAPER_SOLID:           [(9999.1, 6.0, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_PAPER_SCOF:            [(9999.1, 5.0, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_PAPER_OF_PIPE:         [(9999.1, 5.0, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_PAPER_GAS_EXT:         [(9999.1, 5.5, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_PAPER_GAS_INT_PRE:     [(9999.1, 5.5, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_PAPER_GAS_INT_MASS:    [(9999.1, 6.0, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_PE:                    [(9999.1, 3.5, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_XLPE_UNFILLED:         [(9999.1, 3.5, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_XLPE_FILLED:           [(9999.1, 3.5, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_PPL:                   [(9999.1, 5.5, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_PVC:                   [(3.1, 5.0, 'IEC 60287-2-1 ED3 Table 1'),
                                                          (9999.1, 6.0, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_EPR:                   [(3.1, 3.5, 'IEC 60287-2-1 ED3 Table 1'),
                                                          (9999.1, 5.0, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_BUTYL:                 [(9999.1, 5.0, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_RUBBER:                [(9999.1, 5.0, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_SEMI_CON_XLPE:         [(9999.1, 2.5, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_SEMI_CON_PE:           [(9999.1, 2.5, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_SEMI_CON_EPR:          [(9999.1, 3.5, 'IEC 60287-2-1 ED3 Table 1')],
                          iec.INS_SEMI_CON_TAPE:         [(9999.1, 6.0, 'CIGRE TB880')],
                          iec.INS_WATER_BLOCK_TAPE:      [(9999.1, 12.0, 'CIGRE TB880')],
                          iec.INS_CU_FABRIC_TAPE:        [(9999.1, 6.0, 'CIGRE TB880')],
                          iec.INS_OIL:                   [(9999.1, 10.0, 'Wikipedia')],
                          iec.INS_AIR:                   [(9999.1, 10.0, 'Wikipedia')],
                          iec.INS_CARBON_PAPER_TAPE_MI:  [(9999.1, 6.0, 'CIGRE TB880 amended')],
                          iec.INS_METAL_PAPER_TAPE_MI:   [(9999.1, 6.0, 'CIGRE TB880 amended')],
                          iec.INS_CARBON_PAPER_TAPE_OF:  [(9999.1, 5.0, 'CIGRE TB880 amended')],
                          iec.INS_METAL_PAPER_TAPE_OF:   [(9999.1, 5.0, 'CIGRE TB880 amended')],
                          iec.INS_METAL_PAPER_OF_PIPE:          [(9999.1, 5.0, 'CIGRE TB880 amended')],
                          iec.INS_CARBON_PAPER_OF_PIPE:         [(9999.1, 5.0, 'CIGRE TB880 amended')],
                          iec.INS_METAL_PAPER_GAS_EXT:          [(9999.1, 5.5, 'CIGRE TB880 amended')],
                          iec.INS_CARBON_PAPER_GAS_EXT:         [(9999.1, 5.5, 'CIGRE TB880 amended')],
                          iec.INS_METAL_PAPER_GAS_INT_PRE:      [(9999.1, 5.5, 'CIGRE TB880 amended')],
                          iec.INS_CARBON_PAPER_GAS_INT_PRE:     [(9999.1, 5.5, 'CIGRE TB880 amended')],
                          iec.INS_METAL_PAPER_GAS_INT_MASS:     [(9999.1, 6.0, 'CIGRE TB880 amended')],
                          iec.INS_CARBON_PAPER_GAS_INT_MASS:    [(9999.1, 6.0, 'CIGRE TB880 amended')],
                          iec.BED_BITUMEN_COTTON:               [(9999.1, 6.0, 'no source')]}


@LogSection("ρ_1 insulation")
def find_insulation_rho_1(insulation_material: QStr, design_volts: QFloat, log: Log = None) -> QFloat:
    """Get the insulation material thermal resistivity from IEC 60287-2-1 Table 1


    :param insulation_material: insulation material of the cable
    :param design_volts: design voltage of the cable
    :param log: logger used to store results
    :return: insulation thermal resistivity (K.m/W)
    """

    ins_mat = insulation_material.get_value(unit='', log=log)
    volts = design_volts.get_value(unit='kV', log=log)
    rows = INSULATION_RESISTIVITY[ins_mat]
    rho_t = None
    source = None
    for row in rows:
        if volts < row[0]:
            rho_t = row[1]
            source = row[2]
            break
    if rho_t is None:
        raise IEC60287Exception(f'rho_1 not found for {ins_mat} with design voltage {volts} V.')

    if source != 'IEC 60287-2-1 ED3 Table 1' and log is not None:
        log.add_warning(f'material {ins_mat} thermal resistivity is from {source} and not IEC')

    return QFloat(rho_t, 'K.m/W', source,
                  description='insulation thermal resistivity', symbol="rho_1 insulation")


# IEC 60287-1-1 Table 1 Thermal Resistivity
#                         material        up to U0, value
SERVING_RESISTIVITY = {iec.SERVING_JUTE:          [(9999.1, 6.0)],
                       iec.SERVING_RUBBER_TAPE:   [(9999.1, 6.0)],
                       iec.SERVING_POLYCHLOPRENE: [(9999.1, 5.5)],
                       iec.SERVING_PVC:           [(35.1, 5.0),
                                                   (9999.1, 6.0)],
                       iec.SERVING_PVC_CAS:       [(9999.1, 6.0)],
                       iec.SERVING_PE:            [(9999.1, 3.5)]}


@LogSection("ρ_T serving")
def find_serving_rho_t(cable: Cable, log: Log = None) -> QFloat:
    """Get the serving thermal resistivity from IEC 60287-2-1 Table 1

    :param cable: the cable with the insulation
    :param log: logger used to store results
    :return: serving thermal resistivity (K.m/W)
    """

    rho_t = None
    volts = 'N/A'
    serving_mat = cable.serving.material.get_value(unit='', log=log)
    if serving_mat == iec.SERVING_PVC:
        if cable.sheath_type.value == iec.CAS_SHEATH:
            rho_t = 6.0
    if rho_t is None:
        volts = cable.design_volts.get_value(unit='kV', log=log)
        rows = SERVING_RESISTIVITY[serving_mat]
        rho_t = None
        for row in rows:
            if volts < row[0]:
                rho_t = row[1]
                break
    if rho_t is None:
        raise IEC60287Exception(f'rho_t not found for {serving_mat} with design voltage {volts} V.')

    return QFloat(rho_t, 'K.m/W', 'IEC 60287-2-1 Table 1',
                  description='insulation thermal resistivity', symbol="rho_t serving")


# IEC 60287-1-1 Table 1 Thermal Resistivity
#                         material        up to U0, value
DUCT_RESISTIVITY = {iec.DUCT_CONCRETE:       1.0,
                    iec.DUCT_FIBRE:          4.8,
                    iec.DUCT_ASBESTOS:       2.0,
                    iec.DUCT_EARTHENWARE:    1.2,
                    iec.DUCT_PVC:            6.0,
                    iec.DUCT_PE11:             3.5}


@LogSection("ρ_T duct")
def find_duct_rho_t(cable_set: AutoCableSet, log: Log = None) -> QFloat:
    """Get the cable duct thermal resistivity from IEC 60287-2-1 Table 1

    :param cable_set: the cable_set with the duct
    :param log: logger used to store results
    :return: duct thermal resistivity (K.m/W)
    """

    duct_mat = cable_set.duct_material.get_value(unit='', log=log)
    rho_t = DUCT_RESISTIVITY[duct_mat]

    return QFloat(rho_t, 'K.m/W', 'IEC 60287-2-1 Table 1',
                  description='duct thermal resistivity', symbol="rho_t duct")


# Table 3 - Values for constants Z, E and Cg for black surfaces of cables in free air

#                      installation,                              Z,    E,    Cg
FREE_AIR_CONSTANTS = {iec.AIR_SINGLE_CABLE:                     (0.21, 3.94, 0.60),
                      iec.AIR_TWO_CABLES_TOUCHING_HORIZONTAL:   (0.29, 2.35, 0.50),
                      iec.AIR_THREE_CABLES_TOUCHING_TREFOIL:    (0.96, 1.25, 0.20),
                      iec.AIR_THREE_CABLES_TOUCHING_HORIZONTAL: (0.62, 1.95, 0.25),
                      iec.AIR_TWO_CABLES_TOUCHING_VERTICAL:     (1.42, 0.86, 0.25),
                      iec.AIR_TWO_CABLES_SPACED_DE_VERTICAL:    (0.75, 2.80, 0.30),
                      iec.AIR_THREE_CABLES_TOUCHING_VERTICAL:   (1.61, 0.42, 0.20),
                      iec.AIR_THREE_CABLES_SPACED_DE_VERTICAL:  (1.31, 2.00, 0.20)}


@UseState('air_arrangement', level=cabsys.data_classes.state.CABLE)
@LogSection("air arrangement")
# TODO: correct for clipped to wall
def calc_air_arrangement(cable_set: AutoCableSet, cable_no: int,
                         state: CableSetState = None, log: Log = None) -> QStr:
    """Calculate the arrangement of the cable set for air installations.

    Works out which arrangement in IEC 60287-2-1 Table 1 that the cable set is installed in. If strict_iec is set to
    True then the spacing has to be exact.

    IEC 60287-2-1 Table 2

    :param cable_set: cable_set
    :param cable_no:  cable number in cable_set
    :param state: cable set state
    :param log: logger used to store results
    :return: thermal resistance of the cable insulation (k.m/W)
    """

    cable = cable_set.placed_cables[cable_no].cable
    number_cables = cable_set.find_no_cables(log=log)

    return_val = None

    if number_cables == 1:
        return_val = iec.AIR_SINGLE_CABLE

    formation = cable_set.calc_formation_spacing(log=log)

    iec_formation = formation[0]
    spacing = formation[1]
    equal_spacing = formation[2]
    iec_touching = formation[3]
    orientation = formation[4]
    outer_diameter = cable.calc_outer_diameter(log=log)

    # single isolated cable

    if equal_spacing != iec.EQUAL:
        raise IEC60287Exception('calculating air arrangement but cables not equally spaced')

    if iec_formation == iec.FLAT and orientation == iec.HORIZONTAL and spacing > 1.75 * outer_diameter:
        return_val = iec.AIR_SINGLE_CABLE

    # touching cables

    if return_val is None:
        if iec_touching == iec.TOUCHING:
            touching = True
        elif spacing < 1.5 * outer_diameter:
            touching = True
            log.add_warning('cables not touching but assumed touching for calculation')
        else:
            touching = False

        if touching:
            if number_cables == 2 and orientation == iec.HORIZONTAL:
                return_val = iec.AIR_TWO_CABLES_TOUCHING_HORIZONTAL
            if number_cables == 2 and orientation == iec.VERTICAL:
                return_val = iec.AIR_TWO_CABLES_TOUCHING_VERTICAL
            if number_cables == 2 and return_val is None:
                raise IEC60287Exception(f'calculating air arrangement for 2 touching cables'
                                        f' but orientation {orientation}')
            if number_cables == 3 and orientation == iec.TREFOIL:
                return_val = iec.AIR_THREE_CABLES_TOUCHING_TREFOIL
            if number_cables == 3 and orientation == iec.HORIZONTAL:
                return_val = iec.AIR_THREE_CABLES_TOUCHING_HORIZONTAL
            if number_cables == 3 and orientation == iec.VERTICAL:
                return_val = iec.AIR_THREE_CABLES_TOUCHING_VERTICAL
            if number_cables == 3 and return_val is None:
                raise IEC60287Exception(f'calculating air arrangement for 3 touching cables'
                                        f' but orientation {orientation}')

    if return_val is None:
        if 2 * outer_diameter - 1.0 < spacing < 2 * outer_diameter + 1.0:
            spaced = True
        elif spacing > outer_diameter:
            spaced = True
            log.add_warning('cable separation greater than outer diameter but assumed'
                            ' as equal to outer diameter for calculation')
        else:
            spaced = False

        if spaced:
            if number_cables == 2 and orientation == iec.VERTICAL:
                return_val = iec.AIR_TWO_CABLES_SPACED_DE_VERTICAL
            if number_cables == 3 and orientation == iec.VERTICAL:
                return_val = iec.AIR_THREE_CABLES_SPACED_DE_VERTICAL

    if return_val is None:
        raise IEC60287Exception(f'unable to calculate air arrangement for {iec_formation}, {spacing}mm,'
                                f' touching={iec_touching}, {orientation} cables')

    return QStr(return_val, '', 'IEC 60287-2-1 Table 2',
                description='air arrangement', symbol="air arrangement")


FREE_AIR_CONSTANTS_CLIPPED = {iec.AIR_SINGLE_CABLE:                     (1.69, 0.63, 0.25),
                              iec.AIR_THREE_CABLES_TOUCHING_TREFOIL:    (0.94, 0.79, 0.20)}

ABSORPTION_COEFFICIENT = {iec.SERVING_JUTE:             0.8,
                          iec.SERVING_POLYCHLOPRENE:    0.8,
                          iec.SERVING_PVC:              0.6,
                          iec.SERVING_PE:               0.4,
                          iec.LEAD:                     0.6}


@LogSection("duct U")
def find_duct_u(cable_set: AutoCableSet, in_air: bool, log: Log = None) -> QFloat:
    """Get the duct U constants from IEC 60287-2-1 Table 4

    :param cable_set: the cable set
    :param in_air: is the duct installed in air
    :param log: logger used to store results
    :return: insulation thermal resistivity (K.m/W)
    """

    u = find_duct_u_v_y(cable_set, in_air, log=log)[0]

    return QFloat(u, '', 'IEC 60287-2-1 Table 4',
                  description='duct U', symbol="duct_u")


@LogSection("duct V")
def find_duct_v(cable_set: AutoCableSet, in_air: bool, log: Log = None) -> QFloat:
    """Get the duct V constants from IEC 60287-2-1 Table 4

    :param cable_set: the cable set
    :param in_air: is the duct installed in air
    :param log: logger used to store results
    :return: insulation thermal resistivity (K.m/W)
    """

    v = find_duct_u_v_y(cable_set, in_air, log=log)[1]

    return QFloat(v, '', 'IEC 60287-2-1 Table 4',
                  description='duct V', symbol="duct_V")


@LogSection("duct Y")
def find_duct_y(cable_set: AutoCableSet, in_air: bool, log: Log = None) -> QFloat:
    """Get the duct U constants from IEC 60287-2-1 Table 4

    :param cable_set: the cable set
    :param in_air: is the duct installed in air
    :param log: logger used to store results
    :return: insulation thermal resistivity (K.m/W)
    """

    y = find_duct_u_v_y(cable_set, in_air, log=log)[2]

    return QFloat(y, '', 'IEC 60287-2-1 Table 4',
                  description='duct Y', symbol="duct_y")


def find_duct_u_v_y(cable_set: AutoCableSet, in_air: bool, log: Log = None) -> (float, float, float):
    """Get the U, V, and Y constants from IEC 60287-2-1 Table 4

    :param cable_set: the cable set
    :param in_air: is the duct installed in air
    :param log: logger used to store results
    :return: insulation thermal resistivity (K.m/W)
    """

    duct_layout = cable_set.duct_layout.get_value(unit='', log=log)
    if duct_layout == iec.COMMON_WATER_DUCT or duct_layout == iec.INDIVIDUAL_WATER_DUCT:
        duct_mat = duct_layout
    else:
        duct_mat = cable_set.duct_material.get_value(unit='', log=log)
    if in_air:
        duct_inst = iec.IN_AIR
    else:
        duct_inst = iec.BURIED

    u_v_y = DUCT_MAT_U_V_Y[duct_mat][duct_inst]

    return u_v_y


# IEC 60287-1-1 Table 4 Values of constants U, V and Y
#                         material        up to U0, value
DUCT_MAT_U_V_Y = {iec.DUCT_METAL:            {iec.BURIED: (5.2, 1.4, 0.011),
                                              iec.IN_AIR: (5.2, 1.4, 0.011)},
                  iec.DUCT_FIBRE:            {iec.BURIED: (5.2, 0.91, 0.010),
                                              iec.IN_AIR: (5.2, 0.83, 0.006)},
                  iec.DUCT_ASBESTOS:         {iec.BURIED: (5.2, 1.1, 0.011),
                                              iec.IN_AIR: (5.2, 1.2, 0.006)},
                  iec.GAS_PRESSURE_PIPE:     {iec.BURIED: (0.95, 0.46, 0.0021),
                                              iec.IN_AIR: (0.95, 0.46, 0.0021)},
                  iec.OIL_PRESSURE_PIPE:     {iec.BURIED: (0.26, 0.0, 0.0026),
                                              iec.IN_AIR: (0.26, 0.0, 0.0026)},
                  iec.DUCT_PE11:               {iec.BURIED: (1.87, 0.312, 0.0037),
                                                iec.IN_AIR: (1.87, 0.312, 0.0037)},
                  iec.DUCT_PVC:              {iec.BURIED: (1.87, 0.312, 0.0037),
                                              iec.IN_AIR: (1.87, 0.312, 0.0037)},
                  iec.DUCT_EARTHENWARE:      {iec.BURIED: (1.87, 0.28, 0.0036),
                                              iec.IN_AIR: (1.87, 0.28, 0.0036)},
                  iec.INDIVIDUAL_WATER_DUCT: {iec.BURIED: (0.1, 0.03, 0.001),
                                              iec.IN_AIR: (0.1, 0.03, 0.001)},
                  iec.COMMON_WATER_DUCT:     {iec.BURIED: (0.1, 0.03, 0.001),
                                              iec.IN_AIR: (0.1, 0.03, 0.001)}}
