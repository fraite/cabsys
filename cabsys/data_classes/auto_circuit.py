from typing import Union
import cabsys.iec as iec

# import cabsys.data_classes.circuit

from cabsys.quantity.quantity_store import QFloat, QStr, QBool, QInt

from cabsys.data_classes.circuit import Circuit


class AutoCircuit(Circuit):
    """Transient current curve"""

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

    def auto_design(self) -> None:
        """Design the circuit

        When the _auto_design attribute is True, quantity attributes of the circuit (for example voltage) will
        be set to a calculated value if the source of the quantity is:
           * None or
           * CIRCUIT_AUTO_DESIGN

        The design of armoured cable has not yet been implemented.

        :return:
        """

        self.set_auto_design_status('')

        # set all unset attributes to None
        if circuit_q_is_not_fixed(self.num_phases) and self.is_auto_design():
            self.num_phases.set_value(iec.THREE_PHASE, unit=None, source=CIRCUIT_AUTO_DESIGN)
        if circuit_q_is_not_fixed(self.auto_voltage) and self.is_auto_design():
            self.auto_voltage.set_value(400.0, unit='kV', source=CIRCUIT_AUTO_DESIGN)
        if circuit_q_is_not_fixed(self.f) and self.is_auto_design():
            self.f.set_value(50.0, unit='Hz', source=CIRCUIT_AUTO_DESIGN)
        if circuit_q_is_not_fixed(self.desired_I) and self.is_auto_design():
            self.desired_I.set_value(1000.0, unit='A', source=CIRCUIT_AUTO_DESIGN)
        if circuit_q_is_not_fixed(self.desired_I_change) and self.is_auto_design():
            self.desired_I_change.set_value(True, unit=None, source=CIRCUIT_AUTO_DESIGN)

        for key, scenario in self.scenarios.items():
            if circuit_q_is_not_fixed(scenario.num_phases) and self.is_auto_design():
                scenario.num_phases.set_value(self.num_phases.value, unit=None, source=CIRCUIT_AUTO_DESIGN)
            if circuit_q_is_not_fixed(scenario.auto_voltage) and self.is_auto_design():
                scenario.auto_voltage.set_value(self.auto_voltage.value, unit='kV', source=CIRCUIT_AUTO_DESIGN)
            if circuit_q_is_not_fixed(scenario.f) and self.is_auto_design():
                scenario.f.set_value(self.f.value, unit='Hz', source=CIRCUIT_AUTO_DESIGN)
            if circuit_q_is_not_fixed(scenario.desired_I) and self.is_auto_design():
                scenario.desired_I.set_value(self.desired_I.value, unit='A', source=CIRCUIT_AUTO_DESIGN)
            if circuit_q_is_not_fixed(scenario.desired_I_change) and self.is_auto_design():
                scenario.desired_I_change.set_value(self.desired_I_change.value, unit=None, source=CIRCUIT_AUTO_DESIGN)


CIRCUIT_AUTO_DESIGN = 'circuit auto design'


def circuit_q_is_not_fixed(quantity: Union[QInt, QBool, QStr, QFloat]) -> bool:
    return quantity.source == CIRCUIT_AUTO_DESIGN or quantity.source is None
