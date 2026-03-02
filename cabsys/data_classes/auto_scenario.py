from typing import Union
import sys
import traceback

import cabsys.data_classes.scenario
from cabsys.data_classes.scenario import Scenario
from cabsys.quantity.quantity_store import QFloat, QStr, QBool, QInt
import cabsys.iec as iec


# INSTALL_AUTO_DESIGN kept for backward compatibility
SCENARIO_AUTO_DESIGN = 'scenario auto design V0.0'
BURIED_AMBIENT = 15.0
BURIED_TR = 1.2
BURIED_TR_DRY = 2.7
THETA_CRITICAL = 50.0
SOLAR_RADIATION = 1000
V_S_HEAT = 2000000
THERMAL_DIFFUSIVITY = None
AIR_AMBIENT_THETA = 30.0

DEFAULT_SCENARIO = Scenario()
DEFAULT_SCENARIO.rating_type = iec.RATING_CONTINUOUS
DEFAULT_SCENARIO.buried.ambient_theta = BURIED_AMBIENT
DEFAULT_SCENARIO.buried.ground_tr = BURIED_TR
DEFAULT_SCENARIO.buried.ground_tr_dry = BURIED_TR_DRY
DEFAULT_SCENARIO.buried.theta_critical = THETA_CRITICAL
DEFAULT_SCENARIO.buried.solar_radiation = SOLAR_RADIATION
DEFAULT_SCENARIO.buried.ground_v_s_heat = V_S_HEAT
DEFAULT_SCENARIO.buried.ground_thermal_diffusivity = THERMAL_DIFFUSIVITY
DEFAULT_SCENARIO.in_air.ambient_theta = AIR_AMBIENT_THETA
DEFAULT_SCENARIO.in_air.solar_radiation = SOLAR_RADIATION
DEFAULT_SCENARIO.tunnel.ambient_theta = None
DEFAULT_SCENARIO.tunnel.theta_at0 = None
DEFAULT_SCENARIO.tunnel.theta_atL = None
DEFAULT_SCENARIO.tunnel.ground_tr = None
DEFAULT_SCENARIO.tunnel.ground_v_s_heat = None

class DesignScenarioException(Exception):
    pass


def scenario_q_is_not_fixed(quantity: Union[QInt, QBool, QStr, QFloat]) -> bool:
    """Is the quantity value unfixed?

    If the quantity value is not fixed then the Installation auto design function can change the value. For example,
    if the quantity value has been set by the user it should not be changed and is considered fixed. Determining if the
    quantity value is fixed is by looking at the quantity source. The value is not fixed if the source is:
        * None (not defined)
        * scenario auto design
        * "config init"

    :param quantity: quantity being checked
    :return: if quantity is not fixed
    """
    return (quantity.source == SCENARIO_AUTO_DESIGN or
            quantity.source is None or quantity.source == 'config init')


class AutoScenario(Scenario):
    """Parameters for a specific installation kind"""

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

    def auto_design(self):
        """Design the buried scenario

        Fills in the placed cable attributes using information given in the arguments if the values have not been fixed.
        Where values are missing the attributes are calculated (or for placed cable design generally remain unchanged).

        :return: None
        """

        if scenario_q_is_not_fixed(self.rating_type) and self._auto_design:
            self.rating_type.set_value(iec.RATING_CONTINUOUS, unit='', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.end_time) and self._auto_design:
            if self.rating_type.value == iec.RATING_EMERGENCY or self.rating_type.value == iec.RATING_TRANSIENT:
                self.end_time.set_value(864000, unit='s', source=SCENARIO_AUTO_DESIGN)
            else:
                self.end_time.set_value(None, unit='s', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.cycle_time) and self._auto_design:
            if self.rating_type.value == iec.RATING_CYCLIC:
                self.cycle_time.set_value(86400, unit='s', source=SCENARIO_AUTO_DESIGN)
            else:
                self.cycle_time.set_value(None, unit='s', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.buried.ambient_theta) and self._auto_design:
            self.buried.ambient_theta.set_value(BURIED_AMBIENT, unit='°C', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.buried.ground_tr) and self._auto_design:
            self.buried.ground_tr.set_value(BURIED_TR, unit='K.m/W', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.buried.ground_tr_dry) and self._auto_design:
            self.buried.ground_tr_dry.set_value(BURIED_TR_DRY, unit='K.m/W', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.buried.theta_critical) and self._auto_design:
            self.buried.theta_critical.set_value(THETA_CRITICAL, unit='°C', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.buried.solar_radiation) and self._auto_design:
            self.buried.solar_radiation.set_value(SOLAR_RADIATION, unit='W/m²', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.buried.ground_v_s_heat) and self._auto_design:
            self.buried.ground_v_s_heat.set_value(V_S_HEAT, unit='J/K/m³', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.buried.ground_thermal_diffusivity) and self._auto_design:
            self.buried.ground_thermal_diffusivity.set_value(THERMAL_DIFFUSIVITY, unit='m²/s',
                                                             source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.in_air.ambient_theta) and self._auto_design:
            self.in_air.ambient_theta.set_value(AIR_AMBIENT_THETA, unit='°C', source=SCENARIO_AUTO_DESIGN)

        if scenario_q_is_not_fixed(self.in_air.solar_radiation) and self._auto_design:
            self.in_air.solar_radiation.set_value(SOLAR_RADIATION, unit='W/m²', source=SCENARIO_AUTO_DESIGN)

    def auto_design_no_exceptions(self):
        try:
            self.auto_design()
        except DesignScenarioException:
            return sys.exc_info()
        except:
            print(traceback.format_exc())
            self.set_auto_design_status(f'{self.name}: unexpected error during auto_design installation cross-section')
            return sys.exc_info()
        return None


SCENARIO_CLASSES = {**cabsys.data_classes.scenario.SCENARIO_CLASSES,
                    'AutoScenario': AutoScenario}
