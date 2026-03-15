import math
import typing
from typing import List, Union, Optional, Dict

from cabsys.data_classes.install import PlacedCable, CableSet, Elt87Config, InstallConfig, Install
from cabsys.data_classes.install import loads_install
from cabsys.cigre import cigre_constants as cigre_consts
from cabsys.iec import iec_constants as iec
from cabsys.quantity.quantity_store import QFloat, QStr, QBool, QInt, QuantityBase
from cabsys.data_classes.auto_cable import AutoCable, CABLE_AUTO_DESIGN, Cable, CABLE_CLASSES
from cabsys.data_classes.auto_current_curve import CurrentCurve, AutoCurrentCurve, CURRENT_CURVE_CLASSES
from cabsys.data_classes.scenario import Scenario, ScenarioParametersBuried, ScenarioParametersAir
from cabsys.data_classes.scenario import ScenarioParametersTunnel
import cabsys.data_classes.auto_scenario as auto_scenario
from cabsys.data_classes import cable_constants as cc
from cabsys.data_classes.auto_scenario import DEFAULT_SCENARIO


class DesignInstallException(Exception):
    pass


PLACED_CABLE_AUTO_DESIGN = 'placed cable auto design'


class AutoPlacedCable(PlacedCable):
    """A single cable placed in a location

    Represents a cable placed in a location with an x and y co-ordinate. The phase of the cable is also defined.

    Note: deepcopy is over-ridden so that the deep copy still has the same Cable object as the original PlacedCable
    object. This impacts objects that use PlacedCable, in particular installation objects that are deep copied
    will still have the original Cable object and not deep copies of the Cable object.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def design(self, cable: Cable = None, x: float = None, y: float = None, phase: str = None,
               u_pe: float = None):
        """Design the placed cable

        Fills in the placed cable attributes using information given in the arguments if the values have not been fixed.
        Where values are missing the attributes are calculated (or for placed cable design generally remain unchanged).

        :param cable: cable in placed cable
        :param x: x location of cable
        :param y: y location of cable
        :param phase: phase of cable
        :param u_pe: phase to earth voltage (V)
        :return: None
        """
        if (cable is not None and
                (self._cable_source == PLACED_CABLE_AUTO_DESIGN or self.cable is None or self._cable_source is None)):
            self.cable = cable
            self._cable_source = PLACED_CABLE_AUTO_DESIGN

        if (x is not None and
                (self.x.source == PLACED_CABLE_AUTO_DESIGN or self.x.source is None)):
            self.x.value = x
            self.x.source = PLACED_CABLE_AUTO_DESIGN
            self.x.unit = 'mm'

        if (y is not None and
                (self.y.source == PLACED_CABLE_AUTO_DESIGN or self.y.source is None)):
            self.y.value = y
            self.y.source = PLACED_CABLE_AUTO_DESIGN
            self.y.unit = 'mm'

        if (phase is not None and
                (self.phase.source == PLACED_CABLE_AUTO_DESIGN or self.phase.source is None)):
            self.phase.value = phase
            self.phase.source = PLACED_CABLE_AUTO_DESIGN
            self.phase.unit = ''

        if (u_pe is not None and
                (self.u_pe.source == PLACED_CABLE_AUTO_DESIGN or self.u_pe.source is None)):
            self.u_pe.value = u_pe
            self.u_pe.source = PLACED_CABLE_AUTO_DESIGN
            self.u_pe.unit = 'V'


class AutoCableSet(CableSet):
    """A group of cables.

    A group or set of cables, three for 3 phase systems. For 1 cable per phase systems a circuit will comprise one
    cable set."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def re_init(self, sources: List[str]):
        """ re-initialise the cable set

        Sets all values to None that are have a source that is the same as in the sources list. This can be used to
        re-initialise auto designed cable sets at the start of an auto design.

        :param sources: list of sources that will be set to None
        :return: None
        """
        if self.auto_follow_set.source in sources:
            self.auto_follow_set.value = None
        if self.auto_cable_source in sources:
            self.auto_cable = None
        if self.auto_formation.source in sources:
            self.auto_formation.value = None
        if self.auto_spacing.source in sources:
            self.auto_spacing.value = None
        if self.auto_x.source in sources:
            self.auto_x.value = None
        if self.auto_set_spacing.source in sources:
            self.auto_set_spacing.value = None
        if self.auto_depth.source in sources:
            self.auto_depth.value = None
        if self.auto_depth_top.source in sources:
            self.auto_depth_top.value = None
        if self.desired_I.source in sources:
            self.desired_I.value = None
        if self.desired_I_change.source in sources:
            self.desired_I_change.value = None
        if self.preload_type.source in sources:
            self.preload_type.value = None
        if self.preload_current.source in sources:
            self.preload_current.value = None
        if self.f.source in sources:
            self.f.value = None
        if self.cct_type.source in sources:
            self.cct_type.value = None

        for placed_cable in self.placed_cables:
            placed_cable.re_init(sources)

        if self.auto_voltage.source in sources:
            self.auto_voltage.value = None
        if self.bonding.source in sources:
            self.bonding.value = None
        if self.transposed.source in sources:
            self.transposed.value = None
        if self.length1.source in sources:
            self.length1.value = None
        if self.length2.source in sources:
            self.length2.value = None
        if self.length3.source in sources:
            self.length3.value = None
        if self.clipped_to_wall.source in sources:
            self.clipped_to_wall.value = None
        if self.duct_layout.source in sources:
            self.duct_layout.value = None
        if self.duct_material.source in sources:
            self.duct_material.value = None
        if self.duct_id.source in sources:
            self.duct_id.value = None
        if self.duct_od.source in sources:
            self.duct_od.value = None
        if self.pipe_x.source in sources:
            self.pipe_x.value = None
        if self.pipe_y.source in sources:
            self.pipe_y.value = None
        if self.duct_rho_t.source in sources:
            self.duct_rho_t.set_value(None, unit='k.m/W', source=CABLE_SET_AUTO_DESIGN)
        if self.duct_filling_rho_t.source in sources:
            self.duct_filling_rho_t.set_value(None, unit='K.m/W', source=CABLE_SET_AUTO_DESIGN)
        if self.air_z.source in sources:
            self.air_z.value = None
        if self.air_e.source in sources:
            self.air_e.value = None
        if self.air_g.source in sources:
            self.air_g.value = None

    def auto_design(self,
                    follow_set=None,
                    auto_cable: Cable = None,
                    auto_cable_source: str = '',
                    transient_solver: str = None) -> None:

        if (self.auto_cable_source == CABLE_AUTO_DESIGN or
                self.auto_cable_source == INSTALL_AUTO_DESIGN or
                self.auto_cable_source == X_SEC_AUTO_DESIGN or
                self.auto_cable_source == CABLE_SET_AUTO_DESIGN or
                self.auto_cable_source is None or
                self.auto_cable_source == '' or
                self.auto_cable_source == '-'):
            if follow_set is None:
                self.auto_cable = auto_cable
                self.auto_cable_source = auto_cable_source
            else:
                self.auto_cable = follow_set.auto_cable
                self.auto_cable_source = CABLE_SET_AUTO_DESIGN
        if self.auto_cable is None:
            raise DesignCableSetException(f'designing cable_set but no auto-cable in cable_set')
        if isinstance(self.auto_cable, AutoCable) and self.auto_cable.get_auto_design_status() != '':
            raise DesignCableSetException(f'cable set design: {self.auto_cable.get_auto_design_status()}')

        if cable_set_q_is_not_fixed(self.cct_type):
            if self.auto_cable.number_cores.get_value(unit='') == iec.SINGLE_CORE:
                self.cct_type.set_value(iec.THREE_PHASE_SINGLE_CORE, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                raise DesignCableSetException(f'trying to design cable set but cable is'
                                              f' {self.auto_cable.number_cores.value}. '
                                              f'only single core implemented')
        # check that circuit type and cables match
        if self.cct_type.value not in (iec.THREE_PHASE_SINGLE_CORE, iec.TWO_PHASE_SINGLE_CORE):
            raise DesignCableSetException(f'trying to design cable set but cable is'
                                          f' {self.auto_cable.number_cores.value}. '
                                          f'only single core implemented')

        if cable_set_q_is_not_fixed(self.desired_I):
            if follow_set is None:
                self.desired_I.set_value(1000.0, unit='A', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.desired_I.set_value(follow_set.desired_I.value, unit='A', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.desired_I_change):
            if follow_set is None:
                if transient_solver in iec.TRANSIENT_SOLVERS:
                    self.desired_I_change.set_value(False, unit='', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.desired_I_change.set_value(True, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.desired_I_change.set_value(follow_set.desired_I_change.value,
                                                unit='', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.preload_type):
            if follow_set is None:
                if isinstance(self.current_curve, AutoCurrentCurve):
                    if self.current_curve.cyclic:
                        self.preload_type.set_value(iec.PRELOAD_AVE_LOSS, unit='', source=CABLE_SET_AUTO_DESIGN)
                    else:
                        self.preload_type.set_value(iec.PRELOAD_OFF, unit='', source=CABLE_SET_AUTO_DESIGN)
                else:
                    if transient_solver in iec.TRANSIENT_SOLVERS:
                        self.preload_type.set_value(iec.PRELOAD_OFF, unit='', source=CABLE_SET_AUTO_DESIGN)
                    else:
                        self.preload_type.set_value(None, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.preload_type.set_value(follow_set.preload_type.value, unit='', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.preload_current):
            if follow_set is None:
                if self.preload_type.value == iec.PRELOAD_CONST_CURRENT:
                    self.preload_current.set_value(self.desired_I.value / 2, unit='A',
                                                   source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.preload_current.set_value(None, unit='A', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.preload_current.set_value(follow_set.preload_current.value, unit='A',
                                               source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.f):
            if follow_set is None:
                self.f.set_value(50.0, unit='Hz', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.f.set_value(follow_set.f.value, unit='Hz', source=CABLE_SET_AUTO_DESIGN)

        # if number of cables has changed, create a blank placed cable for the number of cables defined in cct_type
        number_cables = iec.CABLE_SET_TYPE_TABLE[self.cct_type.value][1]
        if len(self.placed_cables) != number_cables:
            self.placed_cables = []
            for counter in range(number_cables):
                pc = AutoPlacedCable()
                pc.cable = None
                pc._cable_source = None
                self.placed_cables.append(pc)

        number_cables = self.find_no_cables()
        # cable_outer_dia = iec60287support.calc_outer_diameter(cable)

        if cable_set_q_is_not_fixed(self.num_phases):
            if follow_set is None:
                self.num_phases.set_value(iec.THREE_PHASE, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.num_phases.set_value(follow_set.num_phases.value, unit='', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.auto_voltage):
            if follow_set is None:
                cable = self.auto_cable
                voltage = cable.nominal_volts.value
                self.auto_voltage.set_value(voltage, unit='kV', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.auto_voltage.set_value(follow_set.auto_voltage.value,
                                            unit=follow_set.auto_voltage.unit, source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.duct_layout):
            # if duct_layout is None:
            #     cable_set.duct_layout.set_value(iec.NO_DUCTS, unit='', source=CABLE_SET_AUTO_DESIGN)
            # else:
            #     cable_set.duct_layout.set_value(duct_layout, unit='', source=CABLE_SET_AUTO_DESIGN)
            if follow_set is None:
                self.duct_layout.set_value(iec.NO_DUCTS, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.duct_layout.set_value(follow_set.duct_layout.value, unit='', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.duct_material):
            if follow_set is None:
                if self.duct_layout.value == iec.NO_DUCTS:
                    self.duct_material.set_value(None, unit='', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.duct_material.set_value(iec.DUCT_PVC, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.duct_material.set_value(follow_set.duct_material.value, unit='', source=CABLE_SET_AUTO_DESIGN)

        # calculate default duct sizes
        if self.duct_layout.value == iec.NO_DUCTS:
            if cable_set_q_is_not_fixed(self.duct_id):
                self.duct_id.set_value(None, unit='mm', source=CABLE_SET_AUTO_DESIGN)
            if cable_set_q_is_not_fixed(self.duct_od):
                self.duct_od.set_value(None, unit='mm', source=CABLE_SET_AUTO_DESIGN)
        else:
            de = self.auto_cable.calc_outer_diameter()
            if (self.duct_layout.value in [iec.INDIVIDUAL_WATER_DUCT, iec.INDIVIDUAL_AIR_DUCTS,
                                           iec.INDIVIDUAL_FILLED_DUCT]):
                min_duct_id = 1.5 * de
            elif (self.duct_layout.value in [iec.COMMON_WATER_DUCT, iec.COMMON_AIR_DUCT,
                                             iec.COMMON_FILLED_DUCT]):
                min_duct_id = 1.5 * (de + 2 * de / math.sqrt(3))
            else:
                raise DesignCableSetException(f'duct layout "{self.duct_layout}" not recognised')
            duct_id = duct_od = None
            if self.duct_material.value == iec.DUCT_PVC:
                PVC_DUCT_DATA = {68.0: 75.0,
                                 82.0: 88.9,
                                 89.0: 96.5,
                                 102.0: 110.0,
                                 117.0: 125.0,
                                 131.0: 140.0,
                                 150.0: 160.0,
                                 169.0: 180.0,
                                 188.0: 200.0,
                                 213.0: 225.0,
                                 237.0: 250.0}
                for key in PVC_DUCT_DATA:
                    if min_duct_id < key:
                        duct_id = key
                        duct_od = PVC_DUCT_DATA[duct_id]
                        break
            elif self.duct_material.value == iec.DUCT_PE11:
                PE11_DUCT_DATA = {60.7: 75.0,
                                  72.9: 90.0,
                                  89.2: 110.0,
                                  101.4: 125.0,
                                  113.6: 140.0,
                                  129.8: 160.0,
                                  146.2: 180.0,
                                  162.6: 200.0,
                                  182.9: 225.0,
                                  203.5: 250.0,
                                  227.0: 280.0,
                                  254.0: 315.0}
                for key in PE11_DUCT_DATA:
                    if min_duct_id < key:
                        duct_id = key
                        duct_od = PE11_DUCT_DATA[duct_id]
                        break
            if cable_set_q_is_not_fixed(self.duct_id):
                if follow_set is None:
                    self.duct_id.set_value(duct_id, unit='mm', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.duct_id.set_value(follow_set.duct_id.value, unit='mm', source=CABLE_SET_AUTO_DESIGN)
            if cable_set_q_is_not_fixed(self.duct_od):
                if follow_set is None:
                    self.duct_od.set_value(duct_od, unit='mm', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.duct_od.set_value(follow_set.duct_od.value, unit='mm', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.duct_filling_rho_t):
            if follow_set is None:
                if self.duct_layout.value == [iec.COMMON_FILLED_DUCT, iec.INDIVIDUAL_FILLED_DUCT]:
                    self.duct_filling_rho_t.set_value(None, unit='K.m/W', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.duct_filling_rho_t.set_value(0.8, unit='K.m/W', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.duct_filling_rho_t.set_value(follow_set.duct_filling_rho_t.value,
                                                  unit=follow_set.duct_filling_rho_t.unit,
                                                  source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.bonding):
            if follow_set is None:
                if number_cables != 3:
                    raise DesignCableSetException('automatic cable set design only implemented 3 cables so far')
                cable = self.auto_cable
                cond_dia = cable.conductor.dia.value if cable.conductor.dia.value is not None else 0.0
                if cond_dia >= 33.9:
                    self.bonding.set_value(iec.CROSS_BONDED, unit='', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.bonding.set_value(iec.SOLID_BONDED, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.bonding.set_value(follow_set.bonding.value, unit='', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.transposed):
            if follow_set is None:
                self.transposed.set_value(True, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.transposed.set_value(follow_set.transposed.value, unit='', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.length1):
            if follow_set is None:
                self.length1.set_value(1000.0, unit='m', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.length1.set_value(follow_set.length1.value, unit='m', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.length2):
            if follow_set is None:
                if self.bonding.value == iec.CROSS_BONDED:
                    self.length2.set_value(1000.0, unit='m', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.length2.set_value(None, unit='m', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.length2.set_value(follow_set.length2.value, unit='m', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.length3):
            if follow_set is None:
                if self.bonding.value == iec.CROSS_BONDED:
                    self.length3.set_value(1200.0, unit='m', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.length3.set_value(None, unit='m', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.length3.set_value(follow_set.length3.value, unit='m', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.auto_formation):
            if number_cables != 3:
                raise DesignCableSetException('automatic cable set design only implemented 3 cables so far')
            if follow_set is None:
                if (self.bonding.value == iec.SOLID_BONDED or self.duct_layout.value in [iec.COMMON_WATER_DUCT,
                                                                                         iec.COMMON_AIR_DUCT,
                                                                                         iec.COMMON_FILLED_DUCT]):
                    self.auto_formation.set_value(cc.TREFOIL_TOUCHING, unit='', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.auto_formation.set_value(cc.FLAT_SPACED, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.auto_formation.set_value(follow_set.auto_formation.value, unit='',
                                              source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.auto_spacing):
            if number_cables != 3:
                raise DesignCableSetException('automatic cable set design only implemented 3 cables so far')
            if follow_set is None:
                cable = self.auto_cable
                if (self.auto_formation.value == cc.TREFOIL_TOUCHING or
                        self.auto_formation.value == cc.FLAT_TOUCHING or
                        self.auto_formation.value == cc.VERTICAL_TOUCHING):
                    if (self.duct_layout.value in [iec.INDIVIDUAL_WATER_DUCT, iec.INDIVIDUAL_AIR_DUCTS,
                                                   iec.INDIVIDUAL_FILLED_DUCT]):
                        spacing = self.duct_od.value
                    else:
                        spacing = cable.calc_outer_diameter()
                else:
                    cond_dia = cable.conductor.dia.value
                    if cond_dia < 54.0:
                        spacing = 300.0
                    else:
                        spacing = 500.0
                self.auto_spacing.set_value(spacing, unit='mm', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.auto_spacing.set_value(follow_set.auto_spacing.value, unit='mm', source=CABLE_SET_AUTO_DESIGN)

        if cable_set_q_is_not_fixed(self.auto_x):
            self.auto_x.set_value(0, unit='mm', source=CABLE_SET_AUTO_DESIGN)
        if cable_set_q_is_not_fixed(self.auto_depth):
            if follow_set is None:
                self.auto_depth.set_value(-900.0, unit='mm', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.auto_depth.set_value(follow_set.auto_depth.value, unit='mm', source=CABLE_SET_AUTO_DESIGN)
        if cable_set_q_is_not_fixed(self.auto_depth_top):
            if follow_set is None:
                self.auto_depth_top.set_value(iec.DEPTH_TOP, unit='', source=CABLE_SET_AUTO_DESIGN)
            else:
                self.auto_depth_top.set_value(follow_set.auto_depth_top.value, unit='',
                                              source=CABLE_SET_AUTO_DESIGN)

        # design the placed cables
        for pc in self.placed_cables:
            if isinstance(self.auto_voltage.value, float):
                u_pe = self.auto_voltage.value * 1000 / math.sqrt(3)
            else:
                u_pe = None

            pc.design(cable=self.auto_cable, u_pe=u_pe)

        sqrt3 = math.sqrt(3)
        if number_cables != 3:
            raise DesignCableSetException('automatic cable set design only implemented 3 cables so far')
        cable = self.auto_cable
        if self.auto_formation.value == cc.FLAT_SPACED or self.auto_formation.value == cc.FLAT_TOUCHING:
            if self.auto_depth_top.value == iec.DEPTH_TOP:
                if self.duct_layout.value == iec.NO_DUCTS:
                    depth = self.auto_depth.value - cable.calc_outer_diameter() / 2
                elif (self.duct_layout.value in [iec.INDIVIDUAL_WATER_DUCT, iec.INDIVIDUAL_AIR_DUCTS,
                                                 iec.INDIVIDUAL_FILLED_DUCT]):
                    depth = self.auto_depth.value - self.duct_od.value / 2
                else:
                    raise DesignCableSetException(f'flat spaced or flat touching cable but installed'
                                                  f' in {self.duct_layout}')
            else:
                depth = self.auto_depth.value
            self.placed_cables[0].design(x=self.auto_x.value, y=depth, phase=iec.YELLOW)
            self.placed_cables[1].design(x=self.auto_x.value - self.auto_spacing.value, y=depth,
                                         phase=iec.RED)
            self.placed_cables[2].design(x=self.auto_x.value + self.auto_spacing.value, y=depth,
                                         phase=iec.BLUE)
        elif self.auto_formation.value == cc.VERTICAL_SPACED or self.auto_formation.value == cc.VERTICAL_TOUCHING:
            if self.auto_depth_top.value == iec.DEPTH_TOP:
                if self.duct_layout.value == iec.NO_DUCTS:
                    depth = (self.auto_depth.value -
                             self.auto_spacing.value - cable.calc_outer_diameter() / 2)
                elif (self.duct_layout.value in [iec.INDIVIDUAL_WATER_DUCT, iec.INDIVIDUAL_AIR_DUCTS,
                                                 iec.INDIVIDUAL_FILLED_DUCT]):
                    depth = (self.auto_depth.value -
                             self.auto_spacing.value - self.duct_od.value / 2)
                else:
                    raise DesignCableSetException(f'flat spaced or flat touching cable but installed'
                                                  f' in {self.duct_layout}')
            else:
                depth = self.auto_depth.value
            self.placed_cables[0].design(x=self.auto_x.value, y=depth, phase=iec.YELLOW)
            self.placed_cables[1].design(x=self.auto_x.value, y=depth - self.auto_spacing.value,
                                         phase=iec.RED)
            self.placed_cables[2].design(x=self.auto_x.value, y=depth + self.auto_spacing.value,
                                         phase=iec.BLUE)
        elif self.auto_formation.value == cc.TREFOIL_SPACED or self.auto_formation.value == cc.TREFOIL_TOUCHING:
            duct_layout = self.duct_layout.get_value(unit='')
            if self.auto_depth_top.value == iec.DEPTH_TOP:
                if duct_layout == iec.NO_DUCTS:
                    depth = (self.auto_depth.value -
                             self.auto_spacing.value / sqrt3 - cable.calc_outer_diameter() / 2)
                elif duct_layout in [iec.INDIVIDUAL_WATER_DUCT, iec.INDIVIDUAL_AIR_DUCTS, iec.INDIVIDUAL_FILLED_DUCT]:
                    depth = (self.auto_depth.value -
                             self.auto_spacing.value / sqrt3 - self.duct_od.value / 2)
                elif self.auto_formation.value == cc.TREFOIL_TOUCHING:
                    # duct formation must be common
                    duct_od = self.duct_od.get_value(unit='mm')
                    auto_depth = self.auto_depth.get_value(unit='mm')
                    depth = auto_depth - duct_od / 2
                else:
                    raise DesignCableSetException(f'trefoil spaced cable but installed in {duct_layout}')
            else:
                depth = self.auto_depth.value
            self.placed_cables[0].design(x=self.auto_x.value,
                                         y=depth + self.auto_spacing.value / sqrt3,
                                         phase=iec.YELLOW)
            self.placed_cables[1].design(x=self.auto_x.value - 0.5 * self.auto_spacing.value,
                                         y=depth - self.auto_spacing.value * (sqrt3 / 2 - 1 / sqrt3),
                                         phase=iec.RED)
            self.placed_cables[2].design(x=self.auto_x.value + 0.5 * self.auto_spacing.value,
                                         y=depth - self.auto_spacing.value * (sqrt3 / 2 - 1 / sqrt3),
                                         phase=iec.BLUE)
        else:
            raise DesignCableSetException(f'auto cable set design formation {self.auto_formation.value} '
                                          f'not recognised')

        duct_layout = self.duct_layout.get_value(unit='')
        if duct_layout in [iec.COMMON_WATER_DUCT, iec.COMMON_AIR_DUCT, iec.COMMON_FILLED_DUCT]:
            if cable_set_q_is_not_fixed(self.pipe_x):
                self.pipe_x.set_value(self.auto_x.value, unit='mm', source=CABLE_SET_AUTO_DESIGN)
            if cable_set_q_is_not_fixed(self.pipe_y):
                if follow_set is None:
                    self.pipe_y.set_value(depth, unit='mm', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.pipe_y.set_value(follow_set.pipe_y.value, unit='mm', source=CABLE_SET_AUTO_DESIGN)
        else:
            if cable_set_q_is_not_fixed(self.pipe_x):
                if follow_set is None:
                    self.pipe_x.set_value(None, unit='mm', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.pipe_x.set_value(follow_set.pipe_x.value, unit='mm', source=CABLE_SET_AUTO_DESIGN)
            if cable_set_q_is_not_fixed(self.pipe_y):
                if follow_set is None:
                    self.pipe_y.set_value(None, unit='mm', source=CABLE_SET_AUTO_DESIGN)
                else:
                    self.pipe_y.set_value(follow_set.pipe_y.value, unit='mm', source=CABLE_SET_AUTO_DESIGN)

        for _name, rating_scenario in self.scenarios.items():

            if cable_set_q_is_not_fixed(rating_scenario.num_phases):
                rating_scenario.num_phases.set_value(self.num_phases.value, unit=self.num_phases.unit,
                                                     source=CABLE_SET_AUTO_DESIGN)

            if cable_set_q_is_not_fixed(rating_scenario.auto_voltage):
                rating_scenario.auto_voltage.set_value(self.auto_voltage.value, unit=self.auto_voltage.unit,
                                                       source=CABLE_SET_AUTO_DESIGN)

        return


class AutoInstall(Install):
    """An automatic Installation.

    An automatic Installation cross-section that extends an Installation object with automatic design features. The auto
    design features can be mostly disabled by using the set_auto_design to false, but some automatic design still
    occurs."""

    name: Optional[str]
    config: InstallConfig
    auto_number_sets: QInt
    auto_spacing: QFloat
    kind: QStr

    cable_sets: List[AutoCableSet]

    def __init__(self, **kwargs):
        super().__init__()
        self._auto_design: bool = False
        self._auto_design_status: str = ''
        super().post_init(**kwargs)

    def is_auto_design(self):
        return self._auto_design

    def set_auto_design(self, value: bool):
        self._auto_design = value

    def set_auto_design_status(self, status: str):
        self._auto_design_status = status

    def get_auto_design_status(self):
        return self._auto_design_status

    def auto_design(self, auto_cable: Cable = None, auto_cable_source: str = '',
                    scenario: Scenario = None,
                    proj_scenarios: Dict[str, Scenario] = None) -> None:
        """ Design an installation cross-section

        The installation cross-section is auto designed with values that are not fixed (generally by the user) changed
        to typical values. For example the bonding and earthing will be set to cross bonded for large cables but solidly
        bonded for smaller cables.

        Where values are not used, these are set to None. Should there be problem designing the installation
        cross-section a DesignInstallException is raised, which may leave a number of values left at None.

        :param auto_cable:
        :param auto_cable_source:
        :param scenario: the scenario being designed (should match selected_scenario)
        :param proj_scenarios: list of scenarios
        :return:
        """

        if install_q_is_not_fixed(self.selected_scenario) or self.selected_scenario.value is None:
            # self.selected_scenario.set_value(self.NO_SCENARIO, unit='', source=INSTALL_AUTO_DESIGN)
            self.selected_scenario.set_value("no scenario", source=INSTALL_AUTO_DESIGN)
        # TODO: delete q_rating_type, q_end_time and q_cycle_time once end time and cycle time loop through scenarios
        q_rating_type = self.get_q_rating_type(self.selected_scenario.value)
        q_end_time = self.get_q_end_time(self.selected_scenario.value)
        q_cycle_time = self.get_q_cycle_time(self.selected_scenario.value)
        # q_buried_ambient_theta = self.scenarios[self.selected_scenario.value].buried.ambient_theta
        # q_in_air_ambient_theta = self.scenarios[self.selected_scenario.value].in_air.ambient_theta

        # q_ground_tr = self.scenarios[self.selected_scenario.value].buried.ground_tr
        # q_ground_v_s_heat = self.scenarios[self.selected_scenario.value].buried.ground_v_s_heat
        # q_ground_thermal_diffusivity = self.scenarios[self.selected_scenario.value].buried.ground_thermal_diffusivity

        if self.is_auto_design():

            # clear existing Installation design
            if install_q_is_not_fixed(self.config.memorise):
                self.config.memorise.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.touching_delta_theta):
                self.config.touching_delta_theta.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)
            # if install_q_is_not_fixed(self.config.gm_cable_spacing):
            #     self.config.gm_cable_spacing.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.elt87_boundary_accuracy):
                self.config.elt87_config.elt87_boundary_accuracy.set_value(0.1, unit='°C', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.elt87_boundary_accuracy2):
                self.config.elt87_config.elt87_boundary_accuracy2.set_value(3, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.n_i):
                self.config.elt87_config.n_i.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.elt87_max_delta_theta):
                self.config.elt87_config.elt87_max_delta_theta.set_value(0.0, unit='°C', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.rating_type):
                self.rating_type.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)

            # setting attributed to None in case auto design fails, so that old values are not mistakenly used
            if install_q_is_not_fixed(self.config.solver_continuous):
                self.config.solver_continuous.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.vary_time_step):
                self.config.elt87_config.vary_time_step.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.time_step1):
                self.config.elt87_config.time_step1.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.time_period1):
                self.config.elt87_config.time_period1.set_value(None, 's', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.time_step2):
                self.config.elt87_config.time_step2.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.time_period2):
                self.config.elt87_config.time_period2.set_value(None, 's', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.time_resolution):
                self.config.elt87_config.time_resolution.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.stabilise_fd):
                self.config.elt87_config.stabilise_fd.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.screen_layers):
                self.config.elt87_config.screen_layers.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.elt87_config.cyclic_accuracy):
                self.config.elt87_config.cyclic_accuracy.set_value(None, unit='°C', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.auto_calc):
                self.config.auto_calc.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.max_log_count):
                self.config.max_log_count.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.log_level):
                self.config.log_level.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.log_iterate):
                self.config.log_iterate.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.debug):
                self.config.debug.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.max_cond_theta):
                self.config.max_cond_theta.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.duct_air_accuracy):
                self.config.duct_air_accuracy.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.max_duct_air_iteration):
                self.config.max_duct_air_iteration.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.iec_60287_1_1_ver):
                if (self.config.iec_60287_2_1_ver.value == iec.CIGRE_TB880_2022 and
                        not install_q_is_not_fixed(self.config.iec_60287_2_1_ver)):
                    self.config.iec_60287_1_1_ver.set_value(iec.CIGRE_TB880_2022, unit='', source=INSTALL_AUTO_DESIGN)
                elif (self.config.iec_60287_2_1_ver.value == iec.IEC60287_2_1_ED2 and
                        not install_q_is_not_fixed(self.config.iec_60287_2_1_ver)):
                    self.config.iec_60287_1_1_ver.set_value(iec.IEC60287_1_1_ED2, unit='', source=INSTALL_AUTO_DESIGN)
                elif (self.config.iec_60287_2_1_ver.value == iec.IEC60287_2_1_ED3_STRICT and
                        not install_q_is_not_fixed(self.config.iec_60287_2_1_ver)):
                    self.config.iec_60287_1_1_ver.set_value(iec.IEC60287_1_1_ED3_STRICT, unit='', source=INSTALL_AUTO_DESIGN)
                else:
                    self.config.iec_60287_1_1_ver.set_value(iec.IEC60287_1_1_ED3, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.iec_60287_2_1_ver):
                if (self.config.iec_60287_1_1_ver.value == iec.CIGRE_TB880_2022 and
                        not install_q_is_not_fixed(self.config.iec_60287_1_1_ver)):
                    self.config.iec_60287_2_1_ver.set_value(iec.CIGRE_TB880_2022, unit='', source=INSTALL_AUTO_DESIGN)
                elif (self.config.iec_60287_1_1_ver.value == iec.IEC60287_1_1_ED2 and
                        not install_q_is_not_fixed(self.config.iec_60287_1_1_ver)):
                    self.config.iec_60287_2_1_ver.set_value(iec.IEC60287_2_1_ED2, unit='', source=INSTALL_AUTO_DESIGN)
                elif (self.config.iec_60287_1_1_ver.value == iec.IEC60287_1_1_ED3_STRICT and
                        not install_q_is_not_fixed(self.config.iec_60287_1_1_ver)):
                    self.config.iec_60287_2_1_ver.set_value(iec.IEC60287_2_1_ED3_STRICT, unit='',
                                                            source=INSTALL_AUTO_DESIGN)
                else:
                    self.config.iec_60287_2_1_ver.set_value(iec.IEC60287_2_1_ED3, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.capacitance_2023):
                self.config.capacitance_2023.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.non_metal_screen_isotherm):
                self.config.non_metal_screen_isotherm.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.foil_eddy_loss_rt):
                self.config.foil_eddy_loss_rt.set_value(None, unit='mm', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.multi_sheath_lambda):
                self.config.multi_sheath_lambda.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.multi_sheath_accuracy):
                self.config.multi_sheath_accuracy.set_value(None, unit='°C', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.combi_sheath_iec):
                self.config.combi_sheath_iec.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.always_calc_wd):
                self.config.always_calc_wd.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.calc_c_f_iec):
                self.config.calc_c_f_iec.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.always_calc_c_gs):
                self.config.always_calc_c_gs.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.always_calc_delta):
                self.config.always_calc_delta.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.single_t1_rho):
                self.config.single_t1_rho.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.config.single_t3_rho):
                self.config.single_t3_rho.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)

            if install_q_is_not_fixed(self.kind):
                self.kind.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            # if install_q_is_not_fixed(q_buried_ambient_theta):
            #     q_buried_ambient_theta.set_value(None, unit='°C', source=INSTALL_AUTO_DESIGN)
            # if install_q_is_not_fixed(q_in_air_ambient_theta):
            #     q_in_air_ambient_theta.set_value(None, unit='°C', source=INSTALL_AUTO_DESIGN)
            # if install_q_is_not_fixed(q_ground_thermal_diffusivity):
            #     q_ground_thermal_diffusivity.set_value(None, source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.auto_number_sets):
                self.auto_number_sets.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(self.auto_spacing):
                self.auto_spacing.set_value(None, unit='mm', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(q_end_time):
                q_end_time.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(q_cycle_time):
                q_cycle_time.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)
            # if install_q_is_not_fixed(q_ground_tr):
            #     q_ground_tr.set_value(None, 'K.m/W', source=INSTALL_AUTO_DESIGN)
            # if install_q_is_not_fixed(q_ground_v_s_heat):
            #     q_ground_v_s_heat.set_value(None, unit='J/K/m**3', source=INSTALL_AUTO_DESIGN)
            for cable_set_index, cable_set in enumerate(self.cable_sets):
                cable_set.re_init([CABLE_AUTO_DESIGN, INSTALL_AUTO_DESIGN, CABLE_SET_AUTO_DESIGN,
                                   PLACED_CABLE_AUTO_DESIGN, None])

        # start designing installation

        if install_q_is_not_fixed(self.config.drawing_scale):
            self.config.drawing_scale.set_value(0.6, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.drawing_pixel_size):
            self.config.drawing_pixel_size.set_value(2, unit='', source=INSTALL_AUTO_DESIGN)

        # TODO: how does setting config relate to config in Projects?
        if install_q_is_not_fixed(self.rating_type):
            self.rating_type.set_value(iec.RATING_CONTINUOUS, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.solver_continuous):
            self.config.solver_continuous.set_value(iec.CALC_TEMPERATURE, unit='', source=INSTALL_AUTO_DESIGN)
        if install_q_is_not_fixed(self.config.solver_transient):
            self.config.solver_transient.set_value(iec.CALC_TRANSIENT_ELT_87_IMPLICIT_MATRIX,
                                                   unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.vary_time_step):
            self.config.elt87_config.vary_time_step.set_value(cigre_consts.TIME_STEP_ELT_87,
                                                              unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.elt87_time_step):
            if self.config.solver_continuous.value not in iec.TRANSIENT_SOLVERS:
                self.config.elt87_config.elt87_time_step.set_value(None, 's', source=INSTALL_AUTO_DESIGN)
            elif self.config.elt87_config.vary_time_step.value == cigre_consts.TIME_STEP_USER_VARY:
                self.config.elt87_config.elt87_time_step.set_value(360, unit='s', source=INSTALL_AUTO_DESIGN)
            elif self.config.elt87_config.vary_time_step.value == cigre_consts.TIME_STEP_CONSTANT:
                self.config.elt87_config.elt87_time_step.set_value(10.0, unit='s', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.elt87_config.elt87_time_step.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.time_step1):
            if self.config.elt87_config.vary_time_step.value == cigre_consts.TIME_STEP_USER_VARY:
                self.config.elt87_config.time_step1.set_value(60, unit='s', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.elt87_config.time_step1.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.time_period1):
            if self.config.elt87_config.vary_time_step.value == cigre_consts.TIME_STEP_USER_VARY:
                self.config.elt87_config.time_period1.set_value(360, 's', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.elt87_config.time_period1.set_value(None, 's', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.time_step2):
            if self.config.elt87_config.vary_time_step.value == cigre_consts.TIME_STEP_USER_VARY:
                self.config.elt87_config.time_step2.set_value(180, unit='s', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.elt87_config.time_step2.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.time_period2):
            if self.config.elt87_config.vary_time_step.value == cigre_consts.TIME_STEP_USER_VARY:
                self.config.elt87_config.time_period2.set_value(4680, 's', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.elt87_config.time_period2.set_value(None, 's', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.time_resolution):
            self.config.elt87_config.time_resolution.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.stabilise_fd):
            self.config.elt87_config.stabilise_fd.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.screen_layers):
            self.config.elt87_config.screen_layers.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.elt87_config.cyclic_accuracy):
            self.config.elt87_config.cyclic_accuracy.set_value(0.05, unit='°C', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.auto_calc) and self._auto_design:
            if self.rating_type.value in iec.RATING_CONTINUOUS and self.config.memorise.value:
                self.config.auto_calc.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.auto_calc.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.max_log_count):
            self.config.max_log_count.set_value(500000, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.log_level):
            if (self.rating_type.value == iec.RATING_CONTINUOUS and self.config.memorise.value and
                    (self.auto_number_sets.value is not None and self.auto_number_sets.value < 5)):
                self.config.log_level.set_value(30, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.log_level.set_value(5, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.log_iterate) and self._auto_design:
            self.config.log_iterate.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.debug) and self._auto_design:
            self.config.debug.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.max_cond_theta) and self._auto_design:
            self.config.max_cond_theta.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.cond_theta_accuracy) and self._auto_design:
            self.config.cond_theta_accuracy.set_value(0.01, unit='°C', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.amp_accuracy) and self._auto_design:
            self.config.amp_accuracy.set_value(0.01, unit='A', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.max_rate_iteration) and self._auto_design:
            self.config.max_rate_iteration.set_value(100, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.duct_air_accuracy) and self._auto_design:
            self.config.duct_air_accuracy.set_value(0.1, unit='°C', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.max_duct_air_iteration) and self._auto_design:
            self.config.max_duct_air_iteration.set_value(100, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.capacitance_2023):
            if self.config.iec_60287_1_1_ver.value in [iec.IEC60287_1_1_ED2, iec.CIGRE_TB880_2022]:
                self.config.capacitance_2023.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.capacitance_2023.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.non_metal_screen_isotherm):
            if self.config.iec_60287_2_1_ver.value == iec.IEC60287_2_1_ED3_STRICT:
                self.config.non_metal_screen_isotherm.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.non_metal_screen_isotherm.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.foil_eddy_loss_rt):
            self.config.foil_eddy_loss_rt.set_value(0.25, unit='mm', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.multi_sheath_lambda):
            if self.config.iec_60287_1_1_ver.value == iec.CIGRE_TB880_2022:
                self.config.multi_sheath_lambda.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.multi_sheath_lambda.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.multi_sheath_accuracy):
            if self.config.multi_sheath_lambda.value:
                self.config.multi_sheath_accuracy.set_value(0.000001, unit='°C', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.multi_sheath_accuracy.set_value(None, unit='°C', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.combi_sheath_iec):
            if self.config.iec_60287_1_1_ver.value == iec.CIGRE_TB880_2022 or self.config.multi_sheath_lambda.value:
                self.config.combi_sheath_iec.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.combi_sheath_iec.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.calc_c_f_iec):
            if self.config.iec_60287_1_1_ver.value == iec.CIGRE_TB880_2022:
                self.config.calc_c_f_iec.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.calc_c_f_iec.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.always_calc_wd):
            self.config.always_calc_wd.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.always_calc_c_gs):
            self.config.always_calc_c_gs.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.always_calc_delta):
            self.config.always_calc_delta.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.single_t1_rho):
            if self.config.iec_60287_2_1_ver.value == iec.CIGRE_TB880_2022:
                self.config.single_t1_rho.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.single_t1_rho.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.single_t3_rho):
            if self.config.iec_60287_2_1_ver.value == iec.CIGRE_TB880_2022:
                self.config.single_t3_rho.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.single_t3_rho.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.vary_carbon_paper_tr):
            if self.config.iec_60287_2_1_ver.value == iec.CIGRE_TB880_2022:
                self.config.vary_carbon_paper_tr.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.vary_carbon_paper_tr.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.ignore_conductor_binder):
            if self.config.iec_60287_2_1_ver.value == iec.CIGRE_TB880_2022:
                self.config.ignore_conductor_binder.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.config.ignore_conductor_binder.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.config.use_touching_t4):
            self.config.use_touching_t4.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.kind):
            self.kind.set_value(iec.BURIED, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.ambient_theta):
            if self.kind.value == iec.BURIED:
                self.ambient_theta.set_value(auto_scenario.DEFAULT_SCENARIO.buried.ambient_theta.value,
                                             auto_scenario.DEFAULT_SCENARIO.buried.ambient_theta.unit,
                                             source=INSTALL_AUTO_DESIGN)
            elif self.kind.value == iec.TUNNEL:
                self.ambient_theta.set_value(auto_scenario.DEFAULT_SCENARIO.tunnel.ambient_theta.value,
                                             auto_scenario.DEFAULT_SCENARIO.tunnel.ambient_theta.unit,
                                             source=INSTALL_AUTO_DESIGN)
            else:
                self.ambient_theta.set_value(auto_scenario.DEFAULT_SCENARIO.in_air.ambient_theta.value,
                                             unit='°C', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.ground_tr):
            if self.kind.value == iec.BURIED:
                self.ground_tr.set_value(auto_scenario.DEFAULT_SCENARIO.buried.ground_tr.value,
                                         auto_scenario.DEFAULT_SCENARIO.buried.ground_tr.unit,
                                         source=INSTALL_AUTO_DESIGN)
            elif self.kind.value == iec.TUNNEL:
                self.ground_tr.set_value(auto_scenario.DEFAULT_SCENARIO.tunnel.ground_tr.value,
                                         auto_scenario.DEFAULT_SCENARIO.tunnel.ground_tr.unit,
                                         source=INSTALL_AUTO_DESIGN)
            else:
                self.ground_tr.set_value(None,
                                         unit='K.m/W', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.theta_critical):
            self.theta_critical.set_value(50.0, unit='°C', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.ground_v_s_heat):
            if self.kind.value == iec.BURIED:
                self.ground_v_s_heat.set_value(auto_scenario.DEFAULT_SCENARIO.buried.ground_v_s_heat.value,
                                               auto_scenario.DEFAULT_SCENARIO.buried.ground_v_s_heat.unit,
                                               source=INSTALL_AUTO_DESIGN)
            elif self.kind.value == iec.TUNNEL:
                self.ground_v_s_heat.set_value(auto_scenario.DEFAULT_SCENARIO.tunnel.ground_v_s_heat.value,
                                               auto_scenario.DEFAULT_SCENARIO.tunnel.ground_v_s_heat.unit,
                                               source=INSTALL_AUTO_DESIGN)
            else:
                self.ground_v_s_heat.set_value(None,
                                               unit='J/m³.K', source=INSTALL_AUTO_DESIGN)

        if proj_scenarios is None:
            proj_scenarios = {}
        for install_scenario_key in self.scenarios.keys():
            install_scenario = self.scenarios[install_scenario_key]
            # TODO: remove this check once no_scenario has been removed
            if install_scenario_key in proj_scenarios.keys():
                proj_scenario = proj_scenarios[install_scenario_key]
            else:
                # TODO: remove this once default scenarios have been remove
                proj_scenario = DEFAULT_SCENARIO
            if install_q_is_not_fixed(install_scenario.rating_type):
                install_scenario.rating_type.set_value(proj_scenario.rating_type.value, unit='',
                                                       source=INSTALL_AUTO_DESIGN)
            install_ambient_theta = self.scenarios[install_scenario_key].buried.ambient_theta
            for x_sec_type in ('buried', 'in_air', 'tunnel'):
                install_x_sec_type = getattr(install_scenario, x_sec_type)
                # print(install_x_sec_type)
                for install_attr_key in vars(install_x_sec_type):
                    if install_attr_key[0] == '_':
                        continue
                    install_attr = getattr(install_x_sec_type, install_attr_key)
                    if isinstance(install_attr, QuantityBase):

                        # print(f'{install_scenario_key}, {x_sec_type}, {install_attr_key}, {install_attr}')
                        if install_scenario_key in proj_scenarios.keys():
                            proj_x_sec_type = getattr(proj_scenarios[install_scenario_key], x_sec_type)
                            proj_attr = getattr(proj_x_sec_type, install_attr_key)
                            # print(f'{install_scenario_key}, {x_sec_type}, {install_attr_key}, {proj_attr}')

                            # proj_ambient_thea = proj_scenarios[install_scenario_key].buried.ambient_theta
                            # if install_q_is_not_fixed(install_ambient_theta) and self._auto_design:
                            #     install_ambient_theta.set_value(proj_ambient_thea.value, unit=proj_ambient_thea.unit,
                            #                                     source= 'scenario: ' + proj_ambient_thea.source)

                            if ((install_q_is_not_fixed(install_attr) or install_attr.source[:9] == 'scenario:') and
                                    self._auto_design):
                                install_attr.set_value(proj_attr.value, unit=proj_attr.unit,
                                                       source= 'scenario: ' + str(proj_attr.source))

        if install_q_is_not_fixed(self.auto_number_sets):
            if self._auto_design:
                self.auto_number_sets.set_value(1, unit='', source=INSTALL_AUTO_DESIGN)
            else:
                self.auto_number_sets.set_value(1, unit='', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(self.auto_spacing):
            if self.auto_number_sets.value == 1:
                self.auto_spacing.set_value(None, unit='mm', source=INSTALL_AUTO_DESIGN)
            else:
                self.auto_spacing.set_value(3000, unit='mm', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(q_end_time):
            if q_rating_type.value == iec.RATING_EMERGENCY or q_rating_type.value == iec.RATING_TRANSIENT:
                q_end_time.set_value(24 * 60 * 60, unit='s', source=INSTALL_AUTO_DESIGN)
            else:
                q_end_time.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)

        if install_q_is_not_fixed(q_cycle_time):
            if q_rating_type.value == iec.RATING_CYCLIC:
                cycle_time = 0.0
                for cable_set in self.cable_sets:
                    if cable_set.current_curve is None or not cable_set.current_curve.cyclic.value:
                        ct = 0.0
                    else:
                        ct = cable_set.current_curve.cycle_time.value
                    cycle_time = max(ct, cycle_time)
                for cable_set in self.cable_sets:
                    if cable_set.current_curve is not None and cable_set.current_curve.cyclic.value:
                        if cycle_time % cable_set.current_curve.cycle_time.value != 0.0:
                            raise DesignInstallException('cyclic times for curves do not match')
                if cycle_time == 0.0:
                    raise DesignInstallException('no load curves with cyclic curves specified')
                q_cycle_time.set_value(cycle_time, unit='s', source=INSTALL_AUTO_DESIGN)
            else:
                q_cycle_time.set_value(None, unit='s', source=INSTALL_AUTO_DESIGN)

        # delete cable_sets if auto_number_sets has been decreased
        if self.auto_number_sets.value < 1:
            # self.auto_number_sets.value = len(self.cable_sets)
            # install_auto_design_status = 'Cannot set auto_number_sets to 0'
            # self.set_auto_design_status(install_auto_design_status)
            # raise DesignInstallException(self.get_auto_design_status())
            # self.auto_number_sets.value = 1
            raise DesignInstallException('number of cable sets must be 1 or greater')
            # self.cable_sets = []
        while len(self.cable_sets) > self.auto_number_sets.value:
            self.cable_sets = self.cable_sets[:-1]

        # add extra cable_sets if auto_number_sets has been increased
        while len(self.cable_sets) < self.auto_number_sets.value:
            if len(self.cable_sets) == 0:
                cable_set = AutoCableSet()
                self.cable_sets.append(cable_set)
            else:
                cable_set = AutoCableSet()
                self.cable_sets.append(cable_set)

        for cable_set_index, cable_set in enumerate(self.cable_sets):
            if install_q_is_not_fixed(cable_set.auto_follow_set):
                cable_set.auto_follow_set.set_value(True, unit='', source=INSTALL_AUTO_DESIGN)

            if install_q_is_not_fixed(cable_set.auto_set_spacing):
                if cable_set_index == 0:
                    cable_set.auto_set_spacing.set_value(None, unit='mm', source=INSTALL_AUTO_DESIGN)
                else:
                    if not cable_set.auto_follow_set.value:
                        cable_set.auto_set_spacing.set_value(3000.0, unit='mm', source=INSTALL_AUTO_DESIGN)
                    else:
                        follow_cable_set = self.cable_sets[cable_set_index - 1]
                        cable_set.auto_set_spacing.set_value(follow_cable_set.auto_set_spacing.value,
                                                             unit='mm', source=INSTALL_AUTO_DESIGN)

            if install_q_is_not_fixed(cable_set.auto_x):
                if cable_set_index == 0:
                    cable_set.auto_x.set_value(0.0, unit='mm', source=INSTALL_AUTO_DESIGN)
                elif self.auto_spacing.value is not None:
                    cable_set.auto_x.set_value(self.cable_sets[cable_set_index - 1].auto_x.value +
                                               self.auto_spacing.value, unit='mm',
                                               source=INSTALL_AUTO_DESIGN)
                else:
                    raise DesignInstallException(f'trying to design auto_x_sec but auto_spacing is None')
            if install_q_is_not_fixed(cable_set.clipped_to_wall):
                if self.kind.value == iec.IN_AIR_PROTECTED or iec.IN_AIR_EXPOSED or self.kind == iec.TUNNEL:
                    cable_set.clipped_to_wall.set_value(False, unit='', source=INSTALL_AUTO_DESIGN)
                else:
                    cable_set.clipped_to_wall.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(cable_set.air_z):
                cable_set.air_z.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(cable_set.air_e):
                cable_set.air_e.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)
            if install_q_is_not_fixed(cable_set.air_g):
                cable_set.air_g.set_value(None, unit='', source=INSTALL_AUTO_DESIGN)

        for cable_set_index, cable_set in enumerate(self.cable_sets):
            if cable_set_index == 0:
                follow_set = None
            elif not cable_set.auto_follow_set.value:
                follow_set = None
            else:
                follow_set = self.cable_sets[cable_set_index - 1]
            try:
                cable_set.auto_design(follow_set=follow_set,
                                      auto_cable=auto_cable,
                                      auto_cable_source=auto_cable_source,
                                      transient_solver=self.config.solver_continuous.value)
            except (DesignCableSetException, DesignInstallException) as e:
                design_status = str(e)
                self.set_auto_design_status(design_status)
                return

        # for cable_set in self.cable_sets:
        #     if install_q_is_not_fixed(cable_set.duct_filling_rho_t):
        #         if cable_set.duct_layout.value in [iec.COMMON_FILLED_DUCT, iec.INDIVIDUAL_FILLED_DUCT]:
        #             cable_set.duct_filling_rho_t.set_value(self.ground_tr.value, unit='K.m/W',
        #                                                    source=INSTALL_AUTO_DESIGN)
        #         else:
        #             cable_set.duct_filling_rho_t.set_value(None, unit='K.m/W', source=INSTALL_AUTO_DESIGN)

        # if install_q_is_not_fixed(q_ground_tr):
        #     if self.kind.value == iec.IN_AIR_PROTECTED or self.kind.value == iec.IN_AIR_EXPOSED:
        #         q_ground_tr.set_value(None, 'K.m/W', source=INSTALL_AUTO_DESIGN)
        #     else:
        #         q_ground_tr.set_value(Scenario.BURIED_TR, 'K.m/W', source=INSTALL_AUTO_DESIGN)

        # if install_q_is_not_fixed(q_ground_v_s_heat):
        #     if self.kind.value == iec.IN_AIR_PROTECTED or self.kind.value == iec.IN_AIR_EXPOSED:
        #         q_ground_v_s_heat.set_value(None, unit='J/K/m**3', source=INSTALL_AUTO_DESIGN)
        #     else:
        #         q_ground_v_s_heat.set_value(2e6, unit='J/K/m³', source=INSTALL_AUTO_DESIGN)

        return

    def insert_cable_set(self, cable_set_index: int, cable_set: typing.Optional[AutoCableSet] = None):
        """Insert cable set into auto-installation

        A cable set is installed at the cable set index given and all cable sets at or after the index given will be
        shifted to make space.

        :param cable_set_index:
        :param cable_set:
        :return:
        """
        if cable_set is None:
            cable_set = AutoCableSet()
        super().insert_cable_set(cable_set_index, cable_set)
        if self.is_auto_design():
            self.auto_design()


CABLE_SET_AUTO_DESIGN = 'cable set auto design V0.0'


def cable_set_q_is_not_fixed(quantity: Union[QInt, QBool, QStr, QFloat]) -> bool:
    return (quantity.source == CABLE_AUTO_DESIGN or
            quantity.source == CABLE_SET_AUTO_DESIGN or quantity.source is None)


class DesignCableSetException(Exception):
    pass


# INSTALL_AUTO_DESIGN kept for backward compatibility
INSTALL_AUTO_DESIGN = 'install auto design V0.0'
X_SEC_AUTO_DESIGN = 'cross-section auto design V0.0'


def install_q_is_not_fixed(quantity: Union[QInt, QBool, QStr, QFloat, QuantityBase]) -> bool:
    """Is the quantity value unfixed?

    If the quantity value is not fixed then the Installation auto design function can change the value. For example,
    if the quantity value has been set by the user it should not be changed and is considered fixed. Determining if the
    quantity value is fixed is by looking at the quantity source. The value is not fixed if the source is:
        * None (not defined)
        * install auto design
        * cable set auto design
        * cable auto design
        * "config init"

    This function is backward compatible for objects that use "X_SEC" (cross-section) instead of "INSTALL"

    :param quantity: quantity being checked
    :return: if quantity is not fixed
    """
    return (quantity.source == CABLE_AUTO_DESIGN or quantity.source == X_SEC_AUTO_DESIGN or
            quantity.source == INSTALL_AUTO_DESIGN or
            quantity.source == CABLE_SET_AUTO_DESIGN or quantity.source is None or quantity.source == 'config init')


# TODO: check when install class loaded, all classes are not auto, and displayed correctly
INSTALL_CLASSES = {**CABLE_CLASSES, **CURRENT_CURVE_CLASSES,
                   'Elt87Config': Elt87Config,
                   'InstallConfig': InstallConfig,
                   'XSecConfig': InstallConfig,
                   'Install': Install,
                   'XSec': Install,
                   'CableSet': CableSet,
                   'PlacedCable': PlacedCable,
                   'AutoInstall': AutoInstall,
                   'AutoXSec': AutoInstall,
                   'AutoCableSet': AutoCableSet,
                   'AutoPlacedCable': AutoPlacedCable,
                   'Scenario': Scenario,
                   'ScenarioParametersBuried': ScenarioParametersBuried,
                   'ScenarioParametersAir': ScenarioParametersAir,
                   'ScenarioParametersTunnel': ScenarioParametersTunnel,
                   }


def loads_install_sec(serial: str):

    cable_dict, current_curve_dict, install, install_name = loads_install(serial, INSTALL_CLASSES)

    return cable_dict, current_curve_dict, install, install_name


# classes that can be loaded
INSTALL_CLASSES2 = {'Install': Install, 'AutoInstall': AutoInstall}
