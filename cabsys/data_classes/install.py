import math
import typing
from typing import List, Union, Dict
import copy

import cabsys.data_classes
from cabsys.cigre import cigre_constants as cigre_consts
from cabsys.quantity.serialise import dumps_object, read_xml_tag, loads_obj
import cabsys.iec as iec
from cabsys.quantity.quantity_store import QuantityStore, QFloat, QStr, QBool, QInt
from cabsys.data_classes.auto_cable import AutoCable, Cable, CABLE_CLASSES
from cabsys.quantity.log import Log
from cabsys.data_classes.circuit import Circuit, ScenarioRating
from cabsys.data_classes.auto_current_curve import CurrentCurve, CURRENT_CURVE_CLASSES
from cabsys.data_classes.scenario import Scenario
from cabsys.data_classes import cable_constants as cc
import cabsys.quantity.quantity_constants as dc


class InstallBase(QuantityStore):
    """The base Install class.

    This class adds support for classes that contain Cables or Current Curves."""

    def __init__(self, **kwargs):
        super().__init__()


class PlacedCable(InstallBase):
    """A single cable placed in a location

    Represents a cable placed in a location with an x and y co-ordinate. The phase of the cable is also defined.

    Note: deepcopy is over-ridden so that the deep copy still has the same Cable object as the original PlacedCable
    object. This impacts objects that use PlacedCable, in particular XSec objects that are deep copied will still
    have the original Cable object and not deep copies of the Cable object.
    """

    cable: typing.Optional[Cable]
    _cable_source: str
    x: QFloat
    y: QFloat
    phase: QStr
    u_pe: QFloat
    ambient_theta: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        self.cable = None
        self._cable_source = ''
        # self._info['cable'] = {'unit': 'n/a', 'description': 'cable', 'top': None, 'options': None}
        self.x = QFloat(None, unit='mm', description='x location of cable/duct', source=None, options=None, symbol='x')
        self.y = QFloat(None, unit='mm', description='y location of cable/duct', source=None, options=None, symbol='y')
        phase_options = [iec.RED, iec.YELLOW, iec.BLUE]
        self.phase = QStr(None, unit='', description='phase of cable', source=None, options=phase_options,
                          symbol='phase')
        self.u_pe = QFloat(None, unit='V', description='phase to earth voltage', source=None, options=None,
                           symbol='u_pe')
        self.ambient_theta = QFloat(None, unit='°C', description='ambient temperature override (optional)',
                                    source=None, options=None, symbol='θ_aa')
        # self.state = DataStore()

        super().post_init(**kwargs)

    def re_init(self, sources: List[str]):
        """ re-initialise the placed cable

        Sets all values to None that are have a source that is the same as in the sources list. This can be used to
        re-initialise auto designed cable sets at the start of an auto design.

        :param sources: list of sources that will be set to None
        :return: None
        """
        if self._cable_source in sources:
            self.cable = None
        if self.x.source in sources:
            self.x.value = None
        if self.y.source in sources:
            self.y.source = None
        if self.phase.source in sources:
            self.phase.value = None
        if self.u_pe.source in sources:
            self.phase.value = None
        if self.ambient_theta.source in sources:
            self.ambient_theta.value = None

    def __deepcopy__(self, memo=None):
        # if memo is None:
        #     memo = {}
        new_placed_cable = copy.copy(self)
        return new_placed_cable


class CableSet(InstallBase):
    """A group of cables.

    A group or set of cables, for example three single core cables for 3 phase systems. For 1 cable per phase systems a
    circuit will comprise one cable set."""

    auto_follow_set: QBool
    auto_cable: typing.Optional[Cable]
    auto_cable_source: str
    circuit: typing.Optional[Circuit]
    auto_formation: QStr
    auto_spacing: QFloat
    auto_x: QFloat
    auto_set_spacing: QFloat
    auto_depth: QFloat
    auto_depth_top: QStr
    desired_I: QFloat
    desired_I_change: QBool
    current_curve: typing.Optional[CurrentCurve]
    # current_curve: QuantityBase
    preload_type: QStr
    preload_current: QFloat
    f: QFloat
    cct_type: QStr
    scenarios: Dict[str, ScenarioRating]
    placed_cables: List[PlacedCable]
    num_phases: QStr
    auto_voltage: QFloat
    bonding: QStr
    transposed: QBool
    length1: QFloat
    length2: QFloat
    length3: QFloat
    clipped_to_wall: QBool
    duct_layout: QStr
    duct_material: QStr
    duct_id: QFloat
    duct_od: QFloat
    pipe_x: QFloat
    pipe_y: QFloat
    duct_rho_t: QFloat
    duct_filling_rho_t: QFloat

    air_z: QFloat
    air_e: QFloat
    air_g: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        self.auto_follow_set = QBool(None, unit='', description='follow previous cable set', source=None,
                                     options=None, symbol='auto_follow_set')
        self.auto_cable = None
        self.auto_cable_source = ''
        self.circuit = None
        self.auto_formation = QStr(None, unit='', description='cable formation used by auto design', source=None,
                                   options=cc.AVAILABLE_FORMATION, symbol='formation')
        self.auto_spacing = QFloat(None, unit='mm', description='cable spacing used by auto design', source=None,
                                   options=None, symbol='S')
        self.auto_x = QFloat(None, unit='mm', description='circuit x location used by auto design', source=None,
                             options=None, symbol='auto_x')
        self.auto_set_spacing = QFloat(None, unit='mm', description='cable_set spacing used by auto design',
                                       source=None, options=None, symbol='auto_set_spacing')
        self.auto_depth = QFloat(None, unit='mm', description='circuit depth location used by auto design', source=None,
                                 options=None, symbol='auto_depth')
        self.auto_depth_top = QStr(None, unit='', description='circuit depth to top of cables', source=None,
                                   options=iec.DEPTH_LIST, symbol='auto_depth_top')
        self.desired_I = QFloat(None, unit='A', description='desired current rating', source=None, options=None,
                                symbol='desired_I')
        self.desired_I_change = QBool(None, unit='', description='allow desired rating to change', source=None,
                                      options=None, symbol='desired_I_change')
        self.current_curve = None
        # self.current_curve = QuantityBase(None, unit='', description='current curve for transient ratings',
        #                                   source=None, options=None, symbol='current_curve')
        self.preload_type = QStr(None, unit='', description='type of preload',
                                 source=None, options=iec.PRELOAD_TYPES, symbol='preload type')
        self.preload_current = QFloat(None, unit='A', description='load current prior to transient',
                                      source=None, options=None, symbol='I_pl')
        self.f = QFloat(None, unit='Hz', description='frequency', source=None, options=[50.0, 60.0], symbol='f')
        self.cct_type = QStr(None, unit='', description='number of cables and number of cores', source=None,
                             options=list(iec.CABLE_SET_TYPE_TABLE.keys()), symbol='circuit type')
        self.scenarios = {}
        self.placed_cables = []
        # self._info['placed_cables'] = {'unit': 'n/a', 'description': 'set of placed cables (3 cables for 3 phase)',
        #                                'top': None, 'options': None}
        self.num_phases = QStr(None, unit='', description='number of phases',
                               source=None, options=iec.PHASES_POLES, symbol='num_phases')
        self.auto_voltage = QFloat(None, unit='kV', description='phase to phase voltage', source=None,
                                   options=list(iec.IEC_NOM_TO_U0_VOLTAGE.keys()), symbol='U')
        self.bonding = QStr(None, unit='', description='type of sheath boding and earthing', source=None,
                            options=iec.BONDING_LIST, symbol='bonding')
        self.transposed = QBool(None, unit='', description='are cables transposed', source=None,
                                options=None, symbol='transposed')
        self.length1 = QFloat(None, unit='m', description='section length', source=None,
                              options=None, symbol='Length1')
        self.length2 = QFloat(None, unit='m', description='section length 2 (cross bond)', source=None,
                              options=None, symbol='Length2')
        self.length3 = QFloat(None, unit='m', description='section length 3 (cross bond)', source=None,
                              options=None, symbol='Length3')
        self.clipped_to_wall = QBool(None, unit='', description='air clipped to wall', source=None, options=None,
                                     symbol='clipped')
        self.duct_layout = QStr(None, unit='', description='type of ducts', source=None,
                                options=iec.DUCT_LAYOUT_LIST, symbol='duct_layout')
        """Layout of ducts: (NO_DUCTS, INDIVIDUAL_AIR_DUCTS, COMMON_AIR_DUCT, INDIVIDUAL_WATER_DUCT,
                             COMMON_WATER_DUCT, INDIVIDUAL_FILLED_DUCT, COMMON_FILLED_DUCT)"""
        self.duct_material = QStr(None, unit='', description='duct material', source=None,
                                  options=iec.DUCT_LIST, symbol='duct_material')
        self.duct_id = QFloat(None, unit='mm', description='cable duct inside diameter',
                              source=None, options=None, symbol='D_d')
        self.duct_od = QFloat(None, unit='mm', description='cable duct outside diameter',
                              source=None, options=None, symbol='D_o')
        self.pipe_x = QFloat(None, unit='mm', description='common pipe duct x position',
                             source=None, options=None, symbol='pipe_x')
        self.pipe_y = QFloat(None, unit='mm', description='common pipe or duct y position',
                             source=None, options=None, symbol='pipe_y')
        self.duct_rho_t = QFloat(None, unit='K.m/W', description='cable duct thermal resistivity',
                                 source=None, options=None, symbol='duct_rho_t')
        self.duct_filling_rho_t = QFloat(None, unit='K.m/W', description='cable duct filling thermal resistivity',
                                         source=None, options=None, symbol='duct_filling_rho_t')

        self.air_z = QFloat(None, unit='', description='air const Z', source=None, options=None, symbol='Z')
        self.air_e = QFloat(None, unit='', description='air const E', source=None, options=None, symbol='E')
        self.air_g = QFloat(None, unit='', description='air const g', source=None, options=None, symbol='g')

        super().post_init(**kwargs)

    def find_no_cables(self, log: Log = None) -> int:
        """Find the number of cables in the CableSet.

        Finds the number of cables in a cable set.

        :param log: calculation log
        :return: number of cables
        """

        if log is not None:
            log.start_section('number of cables', 'support function: from cable_set')
        cct_type = self.cct_type.get_value(unit='', log=log)
        try:
            no_cables = iec.CABLE_SET_TYPE_TABLE[cct_type][1]
        except KeyError:
            raise Exception(f'trying to find the number of cables but "{cct_type}" circuit type not recognised')
        if log is not None:
            log.end_section('number of cables', no_cables, 'n/a', 'support function: from cable_set')
        return no_cables

    def find_no_cores(self, cable_no: int, as_int: bool = False,
                      log: Log = None) -> Union[int, str]:
        """Find the number of cores of a cable in a CableSet.

        Normally the return value is a string such as iec.SINGLE_CORE or iec.CONCENTRIC. However, if as_int is True then
        the return will be an integer. For CONCENTRIC the returned integer is 1.

        :param cable_no: cable number for the cable
        :param as_int: return an integer rather than string
        :param log: calculation log
        :return: number of cores in a string format
        """

        if log is not None:
            log.start_section('number of cores', 'support function: from cable_set')
        cable: Cable = self.placed_cables[cable_no].cable
        if cable is None:
            raise Exception(f'trying to find number of cores in cable but cable does not exist')
        no_cores = cable.number_cores.get_value(unit='', log=log)
        cct_type = self.cct_type.get_value(unit='', log=log)
        no_cores_alt = iec.CABLE_SET_TYPE_TABLE[cct_type][0]
        if no_cores != no_cores_alt:
            raise Exception("number of cores of cable and cable set formation do not agree")
        if as_int:
            no_cores = iec.cable_no_cores[no_cores]
        if log is not None:
            log.end_section('number of cores', no_cores, 'n/a', 'support function: from cable_set')
        return no_cores

    def calc_num_cables_in_ducts(self, log: Log = None):
        """Number of cables in a duct (or 1 if no ducts)

        Calculates the number of cables in a duct for a cable set

        :param log:
        :return:
        """
        if log is not None:
            log.start_section('number of cables in common duct', 'support function: from cable_set')
        duct_layout = self.duct_layout.get_value(unit='', log=log)
        if duct_layout in [iec.COMMON_AIR_DUCT, iec.COMMON_WATER_DUCT, iec.COMMON_FILLED_DUCT]:
            n_d = self.find_no_cables(log=log)
        else:
            n_d = 1
        if log is not None:
            log.end_section('number of cables in common duct', n_d, 'n/a',
                            'support function: from cable_set')
        return QInt(n_d, '', 'number of cables in duct',
                    description='number of cables in duct', symbol='n_d')

    def calc_formation_spacing(self, log: Log = None) -> (str, float, str, str, str):
        """Calculate the formation and spacing of the CableSet
    
        The formation is determined by checking if spacings between cables are consistent with the formation,
        for example trefoil formation will have equal spacing between all cables. This consistency check is made to an
        accuracy of 1 mm.
    
        The return is in the form of a tuple:
          * formation: IEC.FLAT, IEC.TREFOIL, IEC.ARBITRARY
          * spacing: see below (mm)
          * is_equal_spacing: IEC.EQUAL, IEC.UNEQUAL
          * is_touching: IEC.SPACED, IEC.TOUCHING, IEC.SOME_TOUCHING
          * orientation: IEC.TREFOIL, IEC.HORIZONTAL, IEC.VERTICAL, IEC.ARBITRARY

    For 3 cables in a cable set, if the cables are in flat formation but
    not equally spaced then the return value is the rms of the 2 spacing values between outer and centre cable. For
    cables in an arbitrary formation the result is the rms of the 3 spacing values. For single cables in a cableset
    the returned value is iec60287definitions.NA.

        :param log: calculation log
        :return: formation and spacing of a cable set in a tuple (see description above)
        """

        if log is not None:
            log.start_section('formation/spacing', 'support function')

        no_cables = self.find_no_cables(log=log)

        if no_cables == 1:
            cable = self.placed_cables[0].cable
            core_spacing = cable.core.get_quantity('spacing', log=log).value
            if core_spacing is None:
                raise Exception('trying to calculate cable spacing for multi-core cable but core_spacing is None')

            result = (iec.NA, core_spacing, iec.NA, iec.NA, iec.NA)
            if log is not None:
                log.end_section('formation/spacing', result, '-, mm, -, -, -', 'support function: formation & spacing')
            return result

        if no_cables == 2:

            try:
                x0 = self.placed_cables[0].x.get_value(unit='mm', log=log)
                x1 = self.placed_cables[1].x.get_value(unit='mm', log=log)
                y0 = self.placed_cables[0].y.get_value(unit='mm', log=log)
                y1 = self.placed_cables[1].y.get_value(unit='mm', log=log)
            except IndexError:
                raise Exception('trying to calculate cable spacing but placed cables missing')

            spacing0to1 = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

            if log is not None:
                log.start_section('are cables touching', 'n/a')
            if self.duct_layout.get_value(unit='', log=log) == iec.NO_DUCTS:
                cable0 = self.placed_cables[0].cable
                cable1 = self.placed_cables[1].cable
                external_dia0 = cable0.calc_outer_diameter(log=log)
                external_dia1 = cable1.calc_outer_diameter(log=log)
                external_dia = (external_dia0 + external_dia1) / 2
            else:
                external_dia = self.duct_od.value
            if spacing0to1 > external_dia + 1.0:
                touching = iec.SPACED
            elif spacing0to1 > external_dia - 1.0:
                touching = iec.TOUCHING
            else:
                raise Exception('cables are overlapping')
            if log is not None:
                log.end_section('are cables touching', touching, '-', 'n/a')

            # check cables are horizontal or vertical
            if abs(y1 - y0) < 1.0:
                orientation = iec.HORIZONTAL
            elif abs(x1 - x0) < 1.0:
                orientation = iec.VERTICAL
            else:
                orientation = iec.ARBITRARY

            result = (iec.FLAT, spacing0to1, iec.NA, touching, orientation)
            if log is not None:
                log.end_section('formation/spacing', result, '-, mm, -, -, -', 'support function: formation & spacing')
            return result

        if no_cables == 3:

            x0 = self.placed_cables[0].x.get_value(unit='mm', log=log)
            x1 = self.placed_cables[1].x.get_value(unit='mm', log=log)
            x2 = self.placed_cables[2].x.get_value(unit='mm', log=log)
            y0 = self.placed_cables[0].y.get_value(unit='mm', log=log)
            y1 = self.placed_cables[1].y.get_value(unit='mm', log=log)
            y2 = self.placed_cables[2].y.get_value(unit='mm', log=log)
            spacing0to1 = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            spacing1to2 = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            spacing2to0 = math.sqrt((x0 - x2) ** 2 + (y0 - y2) ** 2)
            if log is not None:
                log.add_line('spacing0to1', spacing0to1, 'mm', 'calculated distance between cable 0 and cable 1')
                log.add_line('spacing1to2', spacing1to2, 'mm', 'calculated distance between cable 1 and cable 2')
                log.add_line('spacing2to0', spacing2to0, 'mm', 'calculated distance between cable 2 and cable 0')

            if log is not None:
                log.start_section('are cables touching', 'n/a')
            duct_layout = self.duct_layout.get_value(unit='', log=log)
            if duct_layout in [iec.NO_DUCTS, iec.COMMON_FILLED_DUCT, iec.COMMON_WATER_DUCT, iec.COMMON_AIR_DUCT]:
                cable0 = self.placed_cables[0].cable
                cable1 = self.placed_cables[1].cable
                cable2 = self.placed_cables[2].cable
                external_dia0 = cable0.calc_outer_diameter(log=log)
                external_dia1 = cable1.calc_outer_diameter(log=log)
                external_dia2 = cable2.calc_outer_diameter(log=log)
            else:
                external_dia0 = self.duct_od.value
                external_dia1 = self.duct_od.value
                external_dia2 = self.duct_od.value
            # cable 0 touching cable 1?
            cable_dia0to1 = (external_dia0 + external_dia1) / 2
            if spacing0to1 > cable_dia0to1 + 1.0:
                touching0to1 = iec.SPACED
            elif spacing0to1 > cable_dia0to1 - 1.0:
                touching0to1 = iec.TOUCHING
            else:
                raise Exception('cables 0 and 1 are overlapping, cable spacing is {0: .1f}'
                                ' but minimum is {1: .1f} '.format(spacing0to1, cable_dia0to1))
            # cable 1 touching cable 2?
            cable_dia1to2 = (external_dia1 + external_dia2) / 2
            if spacing1to2 > cable_dia1to2 + 1.0:
                touching1to2 = iec.SPACED
            elif spacing1to2 > cable_dia1to2 - 1.0:
                touching1to2 = iec.TOUCHING
            else:
                raise Exception('cables 1 and 2 are overlapping, cable spacing is {0: .1f}'
                                ' but minimum is {1: .1f} '.format(spacing1to2, cable_dia1to2))
            # cable 2 touching cable 0?
            cable_dia2to0 = (external_dia2 + external_dia0) / 2
            if spacing2to0 > cable_dia2to0 + 1.0:
                touching2to0 = iec.SPACED
            elif spacing2to0 > cable_dia2to0 - 1.0:
                touching2to0 = iec.TOUCHING
            else:
                raise Exception('cables 2 and 0 are overlapping, cable spacing is {0: .1f}'
                                ' but minimum is {1: .1f} '.format(spacing2to0, cable_dia2to0))
            if ((touching0to1 == iec.TOUCHING or touching2to0 == iec.TOUCHING) and
                    (touching1to2 == iec.TOUCHING or touching0to1 == iec.TOUCHING) and
                    (touching2to0 == iec.TOUCHING or touching1to2 == iec.TOUCHING)):
                touching = iec.TOUCHING
            elif touching0to1 == iec.SPACED and touching1to2 == iec.SPACED and touching2to0 == iec.SPACED:
                touching = iec.SPACED
            else:
                touching = iec.SOME_TOUCHING
            if log is not None:
                log.end_section('are cables touching', touching, '-', 'n/a')

            if (spacing0to1 - spacing1to2) < 1.0 and (spacing1to2 - spacing2to0) < 1.0 and \
                    (spacing2to0 - spacing0to1) < 1.0:
                spacing = (spacing0to1 + spacing1to2 + spacing2to0) / 3
                result = (iec.TREFOIL, spacing, iec.EQUAL, touching, iec.TREFOIL)
            else:

                # check cables are horizontal or vertical
                if abs(y2 - y1) < 1.0 and abs(y1 - y0) < 1.0 and abs(y0 - y2) < 1.0:
                    orientation = iec.HORIZONTAL
                elif abs(x2 - x1) < 1.0 and abs(x1 - x0) < 1.0 and abs(x0 - x2) < 1.0:
                    orientation = iec.VERTICAL
                else:
                    orientation = iec.ARBITRARY

                spacing = [spacing0to1, spacing1to2, spacing2to0]
                sorted_s = sorted(spacing)
                spacing = (sorted_s[0] + sorted_s[1]) / 2

                if ((sorted_s[0] - spacing) < 1.0 and (sorted_s[1] - spacing) < 1.0 and
                        (0.5 * sorted_s[2] - spacing) < 1.0):
                    result = (iec.FLAT, sorted_s[0], iec.EQUAL, touching, orientation)
                elif (sorted_s[2] - (sorted_s[0] + sorted_s[1])) < 1.0:
                    # TODO: add minimum spacing option
                    # result = (iec.FLAT, math.sqrt(sorted_s[0] * sorted_s[1]), iec.UNEQUAL, touching, orientation)
                    result = (iec.FLAT, min(sorted_s[0], sorted_s[1]), iec.UNEQUAL, touching, orientation)
                else:
                    result = (iec.ARBITRARY,
                              ((sorted_s[0] * sorted_s[1] * sorted_s[2]) ** (1 / 3)),
                              iec.UNEQUAL, touching, orientation)

            if log is not None:
                log.end_section('formation/spacing', result, '-, mm, -, -, -', 'support function: formation & spacing')
            return result


class Elt87Config(QuantityStore):
    """Configuration values for an Electra 87 transient program

    Contains configuration values for an Electra 87 transient program."""

    elt87_boundary_accuracy: QFloat
    elt87_boundary_accuracy2: QInt
    elt87_max_delta_theta: QFloat
    n_i: QInt
    vary_time_step: QStr
    time_step1: QFloat
    time_period1: QFloat
    time_step2: QFloat
    time_period2: QFloat
    elt87_time_step: QFloat
    time_resolution: QFloat
    stabilise_fd: QBool
    screen_layers: QBool
    cyclic_accuracy: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        self.elt87_boundary_accuracy = QFloat(None, unit='°C',
                                              description='Elt 87 Sec. 3.1: temperature accuracy of r_t',
                                              source=None, options=None, symbol='θ_r_t')
        self.elt87_boundary_accuracy2 = QInt(None, unit='',
                                             description='Elt 87 Sec. 3.1: r_t number of decimal points',
                                             source=None, options=None, symbol='acc(θ_r_t)')
        self.n_i = QInt(None, unit='', description='Elt 87 number of insulation slices',
                        source=None, options=None, symbol='n_i')
        self.elt87_max_delta_theta = QFloat(None, unit='°C',
                                            description='max change in temperature without recalculating losses',
                                            source=None, options=None, symbol='acc(θ_c)')
        self.vary_time_step = QStr(None, unit='', description='vary time step depending on transient time',
                                   source=None, options=cigre_consts.TIME_STEPS, symbol='vary_time_step')
        self.time_step1 = QFloat(None, unit='s', description='time step of each iteration for first period',
                                 source=None, options=None, symbol='delta_t')
        self.time_period1 = QFloat(None, unit='s', options=None,
                                   source=None, description='length of time period for first time step')
        self.time_step2 = QFloat(None, unit='s', description='time step of each iteration for second period',
                                 source=None, options=None, symbol='delta_t')
        self.time_period2 = QFloat(None, unit='s', options=None,
                                   source=None, description='length of time period for second time step')
        self.elt87_time_step = QFloat(None, unit='s', description='time step for each iteration',
                                      source=None, options=None, symbol='delta_t')
        self.time_resolution = QFloat(None, unit='s', description='resolution of results recorded',
                                      source=None, options=None, symbol='delta_t')
        self.stabilise_fd = QBool(None, unit='', description='stabilise explicit finite difference method',
                                  source=None, options=None, symbol='stabilise_fd')
        self.screen_layers = QBool(None, unit='', description='separate semi-conducting screen layers',
                                   source=None, options=None, symbol='screen_layers')
        self.cyclic_accuracy = QFloat(None, unit='°C', description='max temperature difference for cyclic calculation',
                                      source=None, options=None, symbol='cyclic_accuracy')
        super().post_init(**kwargs)


class InstallConfig(QuantityStore):
    """Configuration values for current ratings tied to an Install

    Contains configuration values used when current ratings are calculated for the installation."""

    memorise: QBool
    solver_continuous: QStr
    solver_transient: QStr
    auto_calc: QBool
    max_log_count: QInt
    log_iterate: QBool
    debug: QBool
    drawing_scale: QFloat
    max_cond_theta: QBool
    duct_air_accuracy: QFloat
    max_duct_air_iteration: QInt
    iec_60287_1_1_ver: QStr
    iec_60287_2_1_ver: QStr
    capacitance_2023: QBool
    non_metal_screen_isotherm: QBool
    log_level: QInt
    foil_eddy_loss_rt: QFloat
    multi_sheath_lambda: QBool
    combi_sheath_iec: QBool
    calc_c_f_iec: QBool
    always_calc_wd: QBool
    always_calc_c_gs: QBool
    always_calc_delta: QBool
    single_t1_rho: QBool
    ignore_conductor_binder: QBool
    vary_carbon_paper_tr: QBool
    use_touching_t4: QBool
    touching_delta_theta: QBool
    # gm_cable_spacing: QBool
    elt87_config: Elt87Config

    def __init__(self, **kwargs):
        super().__init__()
        self.memorise = QBool(False, unit='', description='speed up calculation by memorising results',
                              source='config init', options=None, symbol='memorise')
        self.solver_continuous = QStr(iec.CALC_TEMPERATURE, unit='',
                                      description='type of continuous rating solver to use',
                                      source='config init', options=iec.CONTINUOUS_SOLVERS, symbol='solver_continuous')
        self.solver_transient = QStr(iec.CALC_TRANSIENT_ELT_87_IMPLICIT_MATRIX, unit='',
                                     description='type of transient rating solver to use', source='config init',
                                     options=iec.TRANSIENT_SOLVERS, symbol='solver_transient')
        self.auto_calc = QBool(False, unit='', description='calculate current rating when changing parameter',
                               source='config init', options=None, symbol='auto_calc')
        self.max_log_count = QInt(500000, unit='', description='maximum number of log entries',
                                  source='config init', options=None, symbol='max_log_count')
        self.log_level = QInt(30, unit='', description='detail of log (1 for no detail to 100 for verbose)',
                              source='config init', options=None, symbol='log_level')
        self.log_iterate = QBool(False, unit='', description='log all the iterations',
                                 source='config init', options=None, symbol='log_iterate')
        """The current rating calculations are iterative and setting this flag to True will cause the log to show all
        the calculations for each iteration. If this flag is False, only the final iteration is shown in the log."""
        self.debug = QBool(False, unit='', description='do not trap exceptions',
                           source='config init', options=None, symbol='debug')
        self.drawing_scale = QFloat(None, unit='', description='cable layout drawing scale',
                                    source='config init', options=None, symbol='drawing_scale')
        """The default drawing scale used for the install drawing"""
        self.drawing_pixel_size = QInt(None, unit='', description='cable layout pixel size for temperature plot',
                                       source='config init', options=None, symbol='drawing_pixel_size')
        """The pixel size used when plotting the cable temperatures on the install drawing. The larger the pixel size
        the faster the plotting."""
        self.max_cond_theta = QBool(False, unit='', description='use maximum conductor temperature',
                                    source='config init', options=None, symbol='max_cond_theta')
        """Use conductor resistance based on the maximum conductor temperature for calculation of losses in line with
        IEC 60287-1-1. For this program, this has been implemented to mean that the conductor resistance of all cables
        in a cable set will be based on the temperature of the hottest cable. The current ratings calculated will then
        agree with IEC 60287, even if the calculation for T4 for spaced flat cables in IEC 60287-2-1 is used.
        """
        self.cond_theta_accuracy = QFloat(None, unit='°C',
                                          description='accuracy of conductor temperature',
                                          source='config init', options=None, symbol='cond_theta_accuracy',
                                          help_id='install_config_rate_accuracy')
        """The current rating calculation will be repeated (iterated) if the difference in conductor temperature is
        greater than the value specified. The iteration may still continue if conductor current (amps) condition
        is not also met."""
        self.amp_accuracy = QFloat(None, unit='A',
                                   description='accuracy of cable current rating',
                                   source='config init', options=None, symbol='amp_accuracy',
                                   help_id='install_config_rate_accuracy')
        """The current rating calculation will be repeated (iterated) if the difference in current rating is greater
        than the value specified. The iteration may still continue if the conductor temperature condition
        is not also met."""
        self.max_rate_iteration = QInt(None, unit='',
                                       description='max number of rating iterations',
                                       source='config init', options=None, symbol='max_rate_iteration',
                                       help_id='install_config_rate_accuracy')
        """The maximum number of current rating iterations allowed."""
        self.duct_air_accuracy = QFloat(None, unit='°C',
                                        description='accuracy of duct air temperature',
                                        source='config init', options=None, symbol='duct_air_accuracy',
                                        help_id='install_config_duct_air_accuracy')
        self.max_duct_air_iteration = QInt(None, unit='',
                                           description='max number of duct air temperature iterations',
                                           source='config init', options=None, symbol='max_duct_air_iteration',
                                           help_id='install_config_duct_air_accuracy')
        self.iec_60287_1_1_ver = QStr(iec.IEC60287_1_1_ED3, unit='',
                                      description='IEC 60287-1-1 version to use',
                                      source='config init', options=iec.IEC60287_1_1_VERS, symbol='iec60287-1-1_ver')
        self.iec_60287_2_1_ver = QStr(iec.IEC60287_2_1_ED3, unit='',
                                      description='IEC 60287-2-1 version to use',
                                      source='config init', options=iec.IEC60287_2_1_VERS, symbol='iec60287-2-1_ver')
        self.capacitance_2023 = QBool(True, unit='',
                                      description='use cable capacitance equation in IEC 60287-1-1:2023',
                                      source='config init', options=None, symbol='C_2023')
        self.non_metal_screen_isotherm = QBool(False, unit='',
                                               description='non-metal screen isothermal for T1 and T3 (to IEC)',
                                               source='config init', options=None, symbol='mon_metal_screen_isotherm',
                                               help_id='install_config_non_metal_screen_isotherm')
        self.foil_eddy_loss_rt = QFloat(0.25, unit='mm',
                                        description='ignore foil eddy currents less than thickness',
                                        source='config init', options=None, symbol='foil_eddy_loss_rt',
                                        help_id='install_config_foil_eddy_loss_rt')
        self.multi_sheath_lambda = QBool(False, unit='', description='multiple sheath/screen heat loss',
                                         source='config init', options=None, symbol='multi_sheath_lambda',
                                         help_id='install_config_multi_sheath_lambda')
        self.multi_sheath_accuracy = QFloat(0.00001, unit='°C',
                                            description='accuracy of sheath/screen temperature if multi sheath',
                                            source='config init', options=None, symbol='multi_sheath_accuracy',
                                            help_id='install_config_multi_sheath_accuracy')
        self.combi_sheath_iec = QBool(True, unit='', description='combined sheath/screen heat loss to IEC',
                                      source='config init', options=None, symbol='multi_sheath_lambda',
                                      help_id='install_config_combi_sheath_iec')
        self.calc_c_f_iec = QBool(True, unit='', description='calculate C_F only as required by IEC',
                                  source='config init', options=None, symbol='always calc C_F')
        """Calculate C_F when required by IEC 60287-1-1. When False, always calculate sheath eddy current losses (λ'')
        including all solidly bonded cables as required by CIGRE TB 880."""
        self.always_calc_wd = QBool(True, unit='', description='always calculate Wd even if not required by IEC',
                                    source='config init', options=None, symbol='always calc wd')
        self.always_calc_c_gs = QBool(True, unit='',
                                      description='always calculate C_gs even if not required by IEC',
                                      source='config init', options=None, symbol='always calc Cgs',
                                      help_id='install_config_always_calc_c_gs')
        self.always_calc_delta = QBool(True, unit='',
                                       description='always calculate delta even if not required by IEC',
                                       source='config init', options=None, symbol='always calc delta',
                                       help_id='install_config_always_calc_delta')
        self.single_t1_rho = QBool(True, unit='', description='calculate T1 with a single thermal resistivity',
                                   source='config init', options=None, symbol='single T1 rho',
                                   help_id='install_config_single_t1_rho')
        """Calculate T1 with a single thermal resistivity in line with the old IEC 60287-2-1 (still an optio in the
        new IEC 60287-2-1). The alternative is calculate T1 due to each layer as recommended in TB 880."""
        self.vary_carbon_paper_tr = QBool(True, unit='',
                                          description='carbon / metalised paper has single thermal resistivity or vary',
                                          source='config init', options=None, symbol='vary carbon paper TR',
                                          help_id='install_config_vary_carbon_paper_tr')
        """In order to follow the guidance in CIGRE TB 880 the carbon paper thermal resistivity has to vary for PPL
        type cables depending on voltage. For this flag to work, single_t1_rho has to be False."""
        self.ignore_conductor_binder = QBool(False, unit='',
                                             description='ignore conductor binder (insulation temperature limit)',
                                             source='config init', options=None, symbol='ignore conductor binder')
        """The temperature limit of the cable is set by the conductor screen temperature and this can be calculated
        ignoring the conductor binder when calculating T1, while IEC 60287 calculates the conductor temperature."""
        self.use_touching_t4 = QBool(True, unit='', description='use IEC touching cables T4',
                                     source='config init', options=None, symbol='use_touching_t4')
        """Use IEC formula for touching cables when calculating T4, rather than calculating T4 for single isolated
        cable and temperature rise for other touching cables in cable set."""
        self.touching_delta_theta = QBool(False, unit='',
                                          description='calculate touching cable delta theta as single heat source',
                                          source='config init', options=None, symbol='touching_delta_theta')
        """Calculate temperature rise of other cable sets that are touching as a single heat source rather than the
        temperature rise of each individual cable in a touching cable set."""
        # self.gm_cable_spacing = QBool(False, unit='',
        #                               description='use geometric mean spacing for unequal spacings',
        #                               source='config init', options=None, symbol='gm_cable_spacing')
        """Use geometric mean spacing for unequal spacing, used for calculation of sheath losses. The alternative is to
        use the minimum spacing for unequal spacing. Note for flat spaced, the 2 spacings between outer and centre cable
        is used, while for other formations the 3 spacings between all cables is used."""
        self.elt87_config = Elt87Config()
        super().post_init(**kwargs)


class Install(InstallBase):
    """An installation cross-section.

    Contains all the information for an installation cross-section, for example a trench cross-section."""

    name: typing.Optional[str]
    config: InstallConfig
    kind: QStr
    rating_type: QStr
    end_time: QFloat
    cycle_time: QFloat
    ambient_theta: QFloat
    ground_tr: QFloat
    ground_tr_dry: QFloat
    theta_critical: QFloat
    solar_radiation: QFloat
    ground_v_s_heat: QFloat
    ground_thermal_diffusivity: QFloat
    selected_scenario: QStr
    auto_number_sets: QInt
    auto_spacing: QFloat
    cable_sets: List[CableSet]
    scenarios: Dict[str, Scenario]

    def __init__(self, **kwargs):
        super().__init__()

        self.name = None
        self.config = InstallConfig()
        self.kind = QStr(None, unit='', description='kind of installation, e.g. laid direct buried',
                         source=None, options=iec.INSTALL_KIND_LIST, symbol='install kind')
        self.rating_type = QStr(None, unit='', description='rating type, e.g. continuous',
                                source=None, options=iec.RATING_TYPES, symbol='rating_type', help_id='rating_type')
        self.end_time = QFloat(None, unit='s', description='time transient calculation ends',
                               source=None, options=None, symbol='t_e')
        self.cycle_time = QFloat(None, unit='s', description='length of time for a cycle in cyclic rating',
                                 source=None, options=None, symbol='cycle_time')
        self.ambient_theta = QFloat(None, unit='°C', description='ambient temperature', source=None,
                                    options=[10.0, 15.0], symbol='θ_a')
        self.ground_tr = QFloat(None, unit='K.m/W', description='soil thermal resistivity', source=None,
                                options=[1.0, 1.2], symbol='ρ', help_id='soil-rho_T')
        self.ground_tr_dry = QFloat(None, unit='K.m/W', description='soil thermal resistivity (dry)', source=None,
                                    options=[1.0, 1.2, 2.7, 3.0], symbol='ρ_d', help_id='soil-rho_d')
        """Soil thermal resistivity (dry)"""
        self.theta_critical = QFloat(None, unit='°C', description='soil dry out critical temperature', source=None,
                                     options=[50.0, 55.0], symbol='θ_x')
        """Soil critical temperature, inside the given temperature isotherm is considered to be liable to ground dry
         out"""
        self.solar_radiation = QFloat(None, unit='W/m²', description='solar radiation intensity', source=None,
                                      options=[1000], symbol='H')
        self.ground_v_s_heat = QFloat(None, unit='J/K/m³', description='ground volumetric specific heat',
                                      source=None, options=None, symbol='σ_T')
        self.ground_thermal_diffusivity = QFloat(None, unit='m²/s', description='ground diffusivity',
                                                 source=None, options=None, symbol='δ_T')
        self.auto_number_sets = QInt(None, unit='mm', description='number of cable sets',
                                     source=None, options=None, symbol='auto_number_sets')
        self.auto_spacing = QFloat(None, unit='mm', description='set spacing used by auto design', source=None,
                                   options=None, symbol='auto_spacing')
        self.cable_sets = []
        self.scenarios = {}
        self.selected_scenario = QStr(None, unit='', description='selected scenario',
                                      source=None, options=None, symbol='auto_scenario')
        self.selected_scenario.options = list(self.scenarios.keys())

        super().post_init(**kwargs)

    def insert_cable_set(self, cable_set_index: int, cable_set: typing.Optional[CableSet] = None):
        """Insert cable set into installation

        A cable set is inserted at the cable set index given and all cable sets at or after the index given will be
        shifted to make space.

        :param cable_set_index:
        :param cable_set:
        :return:
        """
        if cable_set is None:
            cable_set = CableSet()
        if cable_set_index == 0:
            cable_set.auto_cable = self.cable_sets[0].auto_cable
            cable_set.auto_cable_source = 'inserted auto cable set'
            cable_set.auto_follow_set = False
        self.cable_sets.insert(cable_set_index, cable_set)
        self.auto_number_sets.set_value(self.auto_number_sets.value + 1, source=dc.ATTR_USER_SET)

    def delete_cable_set(self, cable_set_index: int):
        """Delete cable set from installation

        A cable set is deleted at the cable set index given and all cable sets at or after the index given will be
        shifted.

        :param cable_set_index:
        :return:
        """
        del self.cable_sets[cable_set_index]
        self.auto_number_sets.set_value(self.auto_number_sets.value - 1, source=dc.ATTR_USER_SET)

    def dumps_install(self, name: str = ''):
        s = '<?xml version="1.0" encoding="UTF-8"?>\n'
        s = s + '<InstallPack>'
        # dump cables first
        cable_list = []
        for cable_set in self.cable_sets:
            for placed_cable in cable_set.placed_cables:
                cable = placed_cable.cable
                if cable not in cable_list:
                    default_o = type(cable)()
                    s = dumps_object(cable, cable.name, s, 1, default_o)
                    cable_list.append(cable)
        # dump current curves
        current_curve_list = []
        for cable_set in self.cable_sets:
            current_curve = cable_set.current_curve
            if current_curve not in current_curve_list and current_curve is not None:
                default_o = type(current_curve)()
                s = dumps_object(current_curve, current_curve.name, s, 1, default_o)
                current_curve_list.append(current_curve)
        # dump installation cross-section object
        default_o = type(self)()
        s = dumps_object(self, name, s, 1, default_o, [Cable, CurrentCurve])
        s = s + '</InstallPack>'
        return s

    def find_extents(self) -> (float, float, float, float):
        """Find the extent of the installation (mm)

        Finds the minimum x, minimum y, maximum x and maximum y extent of all cables in the installation taking account
        of the cable outer diameter (but not any ducts).

        :return: min x, min y, max x, max y extent of installation (mm)
        """
        min_x = min_y = math.inf
        max_x = max_y = -math.inf
        for cable_set in self.cable_sets:
            for placed_cable in cable_set.placed_cables:
                min_x = min(min_x, placed_cable.x.get_value(unit='mm') - placed_cable.cable.calc_outer_diameter() / 2)
                max_x = max(max_x, placed_cable.x.get_value(unit='mm') + placed_cable.cable.calc_outer_diameter() / 2)
                min_y = min(min_y, placed_cable.y.get_value(unit='mm') - placed_cable.cable.calc_outer_diameter() / 2)
                max_y = max(max_y, placed_cable.y.get_value(unit='mm') + placed_cable.cable.calc_outer_diameter() / 2)
        return min_x, min_y, max_x, max_y

    # rating type

    def get_q_rating_type(self, scenario_name: str) -> QStr:
        """Rating type of the installation for the given scenario

        The rating type (for example continuous) of the installation is returned as a quantity for the specified
        scenario. If the scenario does not exist in the installation the base rating type for the installation
        is returned.

        :param scenario_name: name of the scenario
        :return: rating type as a quantity
        """
        if scenario_name not in self.scenarios.keys():
            q_rating_type = self.rating_type
        else:
            q_rating_type = self.scenarios[self.selected_scenario.value].rating_type
        return q_rating_type

    def get_rating_type(self, scenario_name: str, log: Log = None) -> str:

        q_rating_type = self.get_q_rating_type(scenario_name)
        rating_type = q_rating_type.get_value(unit='', log=log)
        return rating_type

    def get_q_end_time(self, scenario_name: str) -> QFloat:
        """Transient end time of the installation for the given scenario

        The transient end time of the installation is returned as a quantity for the specified
        scenario. If the scenario does not exist in the installation the base rating type for the installation
        is returned.

        :param scenario_name: name of the scenario
        :return:
        """
        if scenario_name not in self.scenarios.keys():
            q_end_time = self.end_time
        else:
            q_end_time = self.scenarios[self.selected_scenario.value].end_time
        return q_end_time

    def get_end_time(self, scenario_name: str, unit: str = None, log: Log = None) -> float:

        q_end_time = self.get_q_end_time(scenario_name)
        end_time = q_end_time.get_value(unit=unit, log=log)
        return end_time

    def get_q_cycle_time(self, scenario_name: str) -> QFloat:
        """Length of cycle for cyclic rating of the installation for the given scenario

        The length of time of a single cycle of the installation is returned as a quantity for the specified
        scenario. If the scenario does not exist in the installation the cycle time for the base installation
        is returned.

        :param scenario_name: name of the scenario
        :return:
        """
        if scenario_name not in self.scenarios.keys():
            q_cycle_time = self.cycle_time
        else:
            q_cycle_time = self.scenarios[self.selected_scenario.value].cycle_time
        return q_cycle_time

    def get_cycle_time(self, scenario_name: str, unit: str = None, log: Log = None) -> float:

        q_cycle_time = self.get_q_cycle_time(scenario_name)
        cycle_time = q_cycle_time.get_value(unit=unit, log=log)
        return cycle_time

    # ambient temperature
    def get_q_ambient_temperature(self, selected_scenario_name: str,
                                  cable_set_no: int = None, cable_no: int = None) -> QFloat:
        """Ambient temperature of the installation for the given scenario

        The ambient temperature of the installation is returned as a quantity for the specified scenario.

        The ambient temperature give will be given in the following priority order:
          * if a cable set number and cable number is given and an ambient temperature is specified in the base
            installation, the ambient temperature specified in the placed cable this quantity,
          * if the scenario does not exist in the installation the base ambient temperature for the installation,
          * the ambient temperature in the installation scenario.

        :param selected_scenario_name:
        :param cable_set_no:
        :param cable_no:
        :return:
        """
        if cable_set_no is not None and cable_no is not None:
            cable_set = self.cable_sets[cable_set_no]
            placed_cable = cable_set.placed_cables[cable_no]
            q_ambient_temperature = placed_cable.ambient_theta
            ambient_temperature = q_ambient_temperature.value
        else:
            q_ambient_temperature = None  # this line is not needed but linter required this
            ambient_temperature = None
        if ambient_temperature is None:
            if selected_scenario_name not in self.scenarios.keys():
                q_ambient_temperature = self.ambient_theta
            elif self.kind.value == iec.IN_AIR_EXPOSED or self.kind.value == iec.IN_AIR_PROTECTED:
                q_ambient_temperature = self.scenarios[self.selected_scenario.value].in_air.ambient_theta
            elif self.kind.value == iec.BURIED:
                q_ambient_temperature = self.scenarios[self.selected_scenario.value].buried.ambient_theta
            elif self.kind.value == iec.TUNNEL:
                q_ambient_temperature = self.scenarios[self.selected_scenario.value].tunnel.ambient_theta
            else:
                raise Exception(f'trying to get ambient temperature but installation kind "{self.kind.value}" '
                                f'not recognised')
        return q_ambient_temperature

    def get_ambient_temperature(self, selected_scenario_name: str, cable_set_no: int, cable_no: int,
                                unit: str = None,
                                log: Log = None) -> float:
        q_ambient_temperature = self.get_q_ambient_temperature(selected_scenario_name, cable_set_no, cable_no)
        ambient_temperature = q_ambient_temperature.get_value(unit, log)
        return ambient_temperature

    # ground thermal resistance

    def get_q_ground_tr(self, selected_scenario_name: str) -> QFloat:
        """Ground thermal resistance of the installation for the given scenario

        The ground thermal resistance of the installation is returned as a quantity for the specified scenario.

        The thermal resistance will be given in the following priority order:
          * if the scenario does not exist in the installation the value for the base installation,
          * the value in the installation scenario.

        :param selected_scenario_name:
        :return:
        """
        if selected_scenario_name not in self.scenarios.keys():
            q_ground_tr = self.ground_tr
        elif self.kind.value == iec.IN_AIR_EXPOSED or self.kind.value == iec.IN_AIR_PROTECTED:
            raise Exception(f'trying to get ground thermal resistance for a {self.kind.value} installation')
        elif self.kind.value == iec.BURIED:
            q_ground_tr = self.scenarios[self.selected_scenario.value].buried.ground_tr
        elif self.kind.value == iec.TUNNEL:
            q_ground_tr = self.scenarios[self.selected_scenario.value].tunnel.ground_tr
        else:
            raise Exception(f'trying to get ground_tr but installation kind "{self.kind.value}" '
                            f'not recognised')
        return q_ground_tr

    def get_ground_tr(self, selected_scenario_name: str,
                      unit: str = None,
                      log: Log = None) -> float:
        q_ground_tr = self.get_q_ground_tr(selected_scenario_name)
        ground_tr = q_ground_tr.get_value(unit=unit, log=log)
        return ground_tr

    def get_q_ground_v_s_heat(self, selected_scenario_name: str) -> QFloat:
        """Ground volumetric specific heat of the installation for the given scenario

        The ground volumetric specific heat of the installation is returned as a quantity for the specified scenario.

        The volumetric specific heat will be given in the following priority order:
          * if the scenario does not exist in the installation the value for the base installation,
          * the value in the installation scenario.

        :param selected_scenario_name:
        :return:
        """
        if selected_scenario_name not in self.scenarios.keys():
            q_ground_vs = self.ground_v_s_heat
        elif self.kind.value == iec.IN_AIR_EXPOSED or self.kind.value == iec.IN_AIR_PROTECTED:
            raise Exception(f'trying to get ground volumetric specific heat for a {self.kind.value} installation')
        elif self.kind.value == iec.BURIED:
            q_ground_vs = self.scenarios[self.selected_scenario.value].buried.ground_v_s_heat
        elif self.kind.value == iec.TUNNEL:
            q_ground_vs = self.scenarios[self.selected_scenario.value].tunnel.ground_v_s_heat
        else:
            raise Exception(f'trying to get ground volumetric specific heat but installation kind "{self.kind.value}" '
                            f'not recognised')
        return q_ground_vs

    def get_ground_v_s_heat(self, selected_scenario_name: str,
                            unit: str = None,
                            log: Log = None) -> float:
        q_ground_vs = self.get_q_ground_v_s_heat(selected_scenario_name)
        ground_vs = q_ground_vs.get_value(unit=unit, log=log)
        return ground_vs

    def get_q_ground_thermal_diffusivity(self, selected_scenario_name: str) -> QFloat:
        """Ground thermal diffusivity of the installation for the given scenario

        The ground thermal diffusivity of the installation is returned as a quantity for the specified scenario.

        The thermal diffusivity will be given in the following priority order:
          * if the scenario does not exist in the installation the value for the base installation,
          * the value in the installation scenario.

        :param selected_scenario_name:
        :return:
        """
        if selected_scenario_name not in self.scenarios.keys():
            q_ground_td = self.ground_thermal_diffusivity
        elif self.kind.value == iec.IN_AIR_EXPOSED or self.kind.value == iec.IN_AIR_PROTECTED:
            raise Exception(f'trying to get ground thermal diffusivity for a {self.kind.value} installation')
        elif self.kind.value == iec.BURIED:
            q_ground_td = self.scenarios[self.selected_scenario.value].buried.ground_thermal_diffusivity
        elif self.kind.value == iec.TUNNEL:
            raise Exception(f'trying to get ground thermal diffusivity for a {self.kind.value} installation')
        else:
            raise Exception(f'trying to get ground thermal diffusivity but installation kind "{self.kind.value}" '
                            f'not recognised')
        return q_ground_td

    def get_ground_thermal_diffusivity(self, selected_scenario_name: str,
                                       unit: str = None,
                                       log: Log = None) -> float:
        q_ground_td = self.get_q_ground_thermal_diffusivity(selected_scenario_name)
        ground_td = q_ground_td.get_value(unit=unit, log=log)
        return ground_td


INSTALL_CLASSES = {**CABLE_CLASSES, **CURRENT_CURVE_CLASSES,
                   'Elt87Config': Elt87Config,
                   'InstallConfig': InstallConfig,
                   'XSecConfig':    InstallConfig,
                   'Install': Install,
                   'XSec': Install,
                   'CableSet': CableSet,
                   'PlacedCable': PlacedCable,
                   }


def loads_install(serial: str, install_classes=None):

    if serial.startswith('<?xml version="1.0" encoding="UTF-8"?>\n'):
        serial = serial[len('<?xml version="1.0" encoding="UTF-8"?>\n'):]
    else:
        raise Exception('file read error: not an XML file')
    serial = serial.strip('')

    tag, attr_name, attr_value, serial = read_xml_tag(serial)
    if tag != 'InstallPack' and tag != 'XSecPack':
        raise Exception(f'file read error: file is a {tag} file, not a Install file')

    cable_dict = {}
    tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)
    while tag in CABLE_CLASSES.keys():
        cable, cable_name, serial = loads_obj(serial, load_classes=cabsys.data_classes.auto_cable.CABLE_CLASSES)
        if not isinstance(cable, Cable):
            raise Exception('file is not a cable')
        cable_dict[cable_name] = cable
        tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)

    current_curve_dict = {}
    tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)
    while tag in CURRENT_CURVE_CLASSES.keys():
        load_classes = cabsys.data_classes.auto_current_curve.CURRENT_CURVE_CLASSES
        current_curve, current_curve_name, serial = loads_obj(serial, load_classes=load_classes)
        if not isinstance(current_curve, cabsys.data_classes.auto_current_curve.CurrentCurve):
            raise Exception('file is not a current curve')
        current_curve_dict[current_curve_name] = current_curve
        tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)

    if install_classes is None:
        install_classes = INSTALL_CLASSES
    install, install_name, serial = loads_obj(serial, stop_at={**cable_dict, **current_curve_dict},
                                              load_classes=install_classes)
    if not isinstance(install, Install):
        raise Exception(f'{install_name} file is not an install')

    if serial != '</InstallPack>' and serial != '</XSecPack>':
        raise Exception('install serial stream load has remaining serial to decode')

    return cable_dict, current_curve_dict, install, install_name
