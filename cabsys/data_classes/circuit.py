from typing import Optional, Dict

from cabsys.quantity.quantity_store import QuantityStore, QFloat, QStr, QBool, QInt
import cabsys.iec as iec
from cabsys.data_classes.current_curve import CurrentCurve
from cabsys.data_classes.scenario import Scenario


class ConnectedConductor(QuantityStore):
    placed_cable_number: QInt
    core_number: QInt

    def __init__(self, **kwargs):
        super().__init__()

        self.placed_cable_number = QInt(None, unit='', description='inner connected placed cable number',
                                        source=None, options=None, symbol='')
        self.core_number = QInt(None, unit='', description='outer connected placed cable number',
                                source=None, options=None, symbol='')

        super().post_init(**kwargs)


class ScenarioRating(QuantityStore):
    """Parameters for a specific installation kind"""

    num_phases: QStr
    auto_voltage: QFloat
    f: QFloat
    desired_I: QFloat
    desired_I_change: QBool
    current_curve: Optional[CurrentCurve]
    # current_curve: QuantityBase
    preload_type: QStr
    preload_current: QFloat
    short_cct: Optional[QFloat]

    def __init__(self, **kwargs):
        super().__init__()

        self.num_phases = QStr(None, unit='', description='number of phases',
                               source=None, options=iec.PHASES_POLES, symbol='num_phases')
        self.auto_voltage = QFloat(None, unit='kV', description='phase to phase voltage', source=None,
                                   options=list(iec.IEC_NOM_TO_U0_VOLTAGE.keys()), symbol='U')
        self.f = QFloat(None, unit='Hz', description='frequency', source=None, options=[50.0, 60.0], symbol='f')
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
        self.short_cct = QFloat(None, unit='kA', description='short circuit rating', source=None,
                                options=None, symbol='short_cct')
        super().post_init(**kwargs)


class Circuit(QuantityStore):
    """A cable installation section.

    Contains all the information for a cable installation section."""

    name: Optional[str]
    num_phases: QStr
    auto_voltage: QFloat
    f: QFloat
    desired_I: QFloat
    desired_I_change: QBool
    current_curve: Optional[CurrentCurve]
    # current_curve: QuantityBase
    preload_type: QStr
    preload_current: QFloat
    short_cct: Optional[QFloat]
    scenarios: Dict[str, ScenarioRating]

    def __init__(self, **kwargs):
        super().__init__()

        self.name = None
        self.num_phases = QStr(None, unit='', description='number of phases',
                               source=None, options=iec.PHASES_POLES, symbol='num_phases')
        self.auto_voltage = QFloat(None, unit='kV', description='phase to phase voltage', source=None,
                                   options=list(iec.IEC_NOM_TO_U0_VOLTAGE.keys()), symbol='U')
        self.f = QFloat(None, unit='Hz', description='frequency', source=None, options=[50.0, 60.0], symbol='f')
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
        self.short_cct = QFloat(None, unit='kA', description='short circuit rating', source=None,
                                options=None, symbol='short_cct')
        self.scenarios = {}

        super().post_init(**kwargs)


# classes that can be loaded
CIRCUIT_CLASSES = {'Circuit': Circuit}
