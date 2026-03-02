import typing

import cabsys.iec as iec
from cabsys.quantity.quantity_store import QuantityStore, QFloat, QStr
# , QBool, QInt, QuantityBase


class NoEarthMat:
    pass


class ScenarioParametersBuried(QuantityStore):
    """Parameters for a specific installation kind"""

    rating_kind: typing.List[str]  # rating kind that uses buried parameters
    ambient_theta: QFloat
    ground_tr: QFloat
    ground_tr_dry: QFloat
    theta_critical: QFloat
    solar_radiation: QFloat
    ground_v_s_heat: QFloat
    ground_thermal_diffusivity: QFloat

    def __init__(self, **kwargs):
        super().__init__()

        self.rating_kind = ['buried']
        self.ambient_theta = QFloat(None, unit='°C', description='ambient temperature', source=None,
                                    options=[10.0, 15.0], symbol='θ_a')
        self.ground_tr = QFloat(None, unit='K.m/W', description='soil thermal resistivity', source=None,
                                options=[1.0, 1.2], symbol='ρ_T', help_id='soil-rho_T')
        self.ground_tr_dry = QFloat(None, unit='K.m/W', description='soil thermal resistivity (dry)', source=None,
                                    options=[1.0, 1.2, 2.7, 3.0], symbol='ρ_d', help_id='soil-rho_d')
        self.theta_critical = QFloat(None, unit='°C', description='soil dry out critical temperature', source=None,
                                     options=[50.0, 55.0], symbol='θ_x')
        self.solar_radiation = QFloat(None, unit='W/m²', description='solar radiation intensity', source=None,
                                      options=[1000], symbol='H')
        self.ground_v_s_heat = QFloat(None, unit='J/K/m³', description='ground volumetric specific heat',
                                      source=None, options=None, symbol='σ_T')
        self.ground_thermal_diffusivity = QFloat(None, unit='m²/s', description='ground diffusivity',
                                                 source=None, options=None, symbol='δ_T')

        super().post_init(**kwargs)


class ScenarioParametersAir(QuantityStore):
    """Parameters for a specific installation kind"""

    rating_kind: typing.List[str]
    ambient_theta: QFloat
    solar_radiation: QFloat

    def __init__(self, **kwargs):
        super().__init__()

        self.rating_kind = ['in_air_protected', 'in_air_exposed']
        self.ambient_theta = QFloat(None, unit='°C', description='ambient temperature', source=None,
                                    options=[10.0, 15.0], symbol='θ_a')
        self.solar_radiation = QFloat(None, unit='W/m²', description='solar radiation intensity', source=None,
                                      options=[1000], symbol='H')
        super().post_init(**kwargs)


class ScenarioParametersTunnel(QuantityStore):
    """Parameters for a specific installation kind"""

    rating_kind: typing.List[str]
    ambient_theta: QFloat
    ambient_in: QFloat
    ground_tr: QFloat
    ground_v_s_heat: QFloat

    def __init__(self, **kwargs):
        super().__init__()

        self.rating_kind = ['tunnel']
        self.ambient_theta = QFloat(None, unit='°C', description='ambient temperature', source=None,
                                    options=[10.0, 15.0], symbol='θ_a')
        self.theta_at0 = QFloat(None, unit='°C', description='average tunnel inlet temperature ', source=None,
                                options=[20.0, 25.0], symbol='θ_at(0)')
        self.theta_atL = QFloat(None, unit='°C', description='maximum tunnel outlet temperature ', source=None,
                                options=[20.0, 25.0], symbol='θ_at(L)')
        self.ground_tr = QFloat(None, unit='K.m/W', description='soil thermal resistivity', source=None,
                                options=[1.0, 1.2], symbol='ρ_T', help_id='soil-rho_T')
        self.ground_v_s_heat = QFloat(None, unit='J/K/m³', description='ground volumetric specific heat',
                                      source=None, options=None, symbol='σ_T')

        super().post_init(**kwargs)


class Scenario(QuantityStore):
    """A rating scenario for installations

    A rating scenario"""

    # Todo: remove NO_SCENARIO
    NO_SCENARIO = 'no scenario'

    name: typing.Optional[str]
    rating_type: QStr
    end_time: QFloat
    cycle_time: QFloat
    buried: ScenarioParametersBuried
    in_air: ScenarioParametersAir
    tunnel: ScenarioParametersTunnel

    def __init__(self, **kwargs):
        super().__init__()

        self.name = None
        self.rating_type = QStr(None, unit='', description='rating type, e.g. continuous',
                                source=None, options=iec.RATING_TYPES, symbol='rating_type', help_id='rating_type')
        self.end_time = QFloat(None, unit='s', description='time transient calculation ends',
                               source=None, options=None, symbol='t_e')
        self.cycle_time = QFloat(None, unit='s', description='length of time for a cycle in cyclic rating',
                                 source=None, options=None, symbol='cycle_time')
        self.buried = ScenarioParametersBuried()
        self.in_air = ScenarioParametersAir()
        self.tunnel = ScenarioParametersTunnel()

        super().post_init(**kwargs)


class PlacedCableScenario(QuantityStore):
    """A rating scenario for placed cables

    A rating scenario"""

    phase: QStr
    u_pe: QFloat
    ambient_theta: QFloat

    def __init__(self, **kwargs):
        super().__init__()

        self.name = None
        phase_options = [iec.RED, iec.YELLOW, iec.BLUE]
        self.phase = QStr(None, unit='', description='phase of cable', source=None, options=phase_options,
                          symbol='phase')
        self.u_pe = QFloat(None, unit='V', description='phase to earth voltage', source=None, options=None,
                           symbol='u_pe')
        self.ambient_theta = QFloat(None, unit='°C', description='ambient temperature override (optional)',
                                    source=None, options=None, symbol='θ_aa')

        super().post_init(**kwargs)


# classes that can be loaded
SCENARIO_CLASSES = {'ScenarioParametersBuried': ScenarioParametersBuried,
                    'ScenarioParametersAir': ScenarioParametersAir,
                    'ScenarioParametersTunnel': ScenarioParametersTunnel,
                    'Scenario': Scenario,
                    'PlacedCableScenario': PlacedCableScenario}
