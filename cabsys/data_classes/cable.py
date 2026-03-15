import math

from cabsys.iec import iec_constants as iec
from cabsys.quantity.quantity_store import QuantityStore, QFloat, QStr, QInt, QBool
from cabsys.quantity.log import Log
import cabsys.data_classes.cable_constants as cc
import typing


class CableConductor(QuantityStore):
    """A cable conductor."""

    duct_dia: QFloat
    spiral_dia: QFloat
    dia: QFloat
    effective_dia: QFloat
    major_dia: QFloat
    minor_dia: QFloat
    size: QStr
    material: QStr
    makeup: QStr
    spiral_material: QStr

    # parameters
    compaction: QFloat
    dc_resistance20: QFloat
    dc_resistivity20: QFloat
    alpha20: QFloat
    ks: QFloat
    kp: QFloat
    dc_dash_dia: QFloat
    duct_v_s_heat: QFloat
    conductor_v_s_heat: QFloat
    conductor_volume: QFloat
    beta0: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        self.duct_dia = QFloat(None, unit='mm', source=None, options=None, description='duct diameter', symbol='D_d')
        self.spiral_dia = QFloat(None, unit='mm', description='duct spiral diameter', source=None,
                                 options=None, symbol='d_spiral')
        self.dia = QFloat(None, unit='mm', source=None, options=None, description='conductor diameter', symbol='d_c')
        self.effective_dia = QFloat(unit='mm', description='effective diameter for shaped conductors', source=None,
                                    options=None, symbol="d_x")
        self.major_dia = QFloat(None, unit='mm', description='major diameter for oval conductors', source=None,
                                options=None, symbol='d_M')
        self.minor_dia = QFloat(None, unit='mm', description='minor diameter for minor conductors', source=None,
                                options=None, symbol='d_m')
        self.size = QStr(None, unit='', source=None, options=iec.iec_conductor_size_list,
                         description='conductor size', symbol='A')
        self.material = QStr(None, unit='', description='conductor material', source=None,
                             options=iec.conductor_material_list, symbol='conductor material')
        self.makeup = QStr(None, unit='', description='conductor makeup', source=None,
                           options=list(iec.conductor_makeup_dict.keys()), symbol='conductor makeup')
        self.spiral_material = QStr(None, unit='', description='duct spiral material', source=None,
                                    options=cc.SPIRAL_TABLE, symbol='conductor spiral material')

        # parameters
        self.compaction = QFloat(None, unit='%', description='degree of conductor compaction', source=None,
                                 options=None, symbol='conductor compaction')
        self.dc_resistance20 = QFloat(None, unit='Ω/m', description='conductor dc resistance at 20°C',
                                      source=None, options=None, symbol='R0')
        self.dc_resistivity20 = QFloat(None, unit='Ω.m', description='conductor dc resistivity at 20°C',
                                       source=None, options=None, symbol='conductor ρ')
        self.alpha20 = QFloat(None, unit='1/K', description='conductor dc coefficient of resistance at 20°C',
                              source=None, options=None, symbol='conductor α₂₀')
        self.ks = QFloat(None, unit='', description='skin effect coefficient', source=None, options=None,
                         symbol='k_s')
        self.kp = QFloat(None, unit='', description='proximity effect coefficient', source=None, options=None,
                         symbol='k_p')
        self.dc_dash_dia = QFloat(None, unit='-', description='equivalent conductor diameter if solid with duct',
                                  source=None, options=None, symbol="d_c'")
        self.duct_v_s_heat = QFloat(None, unit='J/m³.K', description='duct volumetric specific heat',
                                    source=None, options=None, symbol="duct_v_s_heat")
        self.conductor_v_s_heat = QFloat(None, unit='J/m³.K', description='conductor volumetric specific heat',
                                         source=None, options=None, symbol="conductor_v_s_heat")
        self.conductor_volume = QFloat(None, unit='mm³/mm', description='conductor volume',
                                       source=None, options=None, symbol="conductor_volume")
        self.beta0 = QFloat(None, unit='K', description='1 / coefficient of resistance at 0°C',
                            source=None, options=None, symbol='β₀')
        super().post_init(**kwargs)


class Core(QuantityStore):
    """The core of a cable."""

    binder_material: QStr
    binder_dia: QFloat
    cond_screen_material: QStr
    cond_screen_dia: QFloat
    max_cond_stress: QFloat
    max_insu_stress: QFloat
    nom_insu_rt: QFloat
    insu_dia: QFloat
    belt_dia: QFloat
    insulation_material: QStr
    insu_screen_dia: QFloat
    bedding_dia: QFloat
    t1: QFloat
    spacing: QFloat
    permittivity: QFloat
    tan_d: QFloat
    rho_1: QFloat
    binder_rho_1: QFloat
    cond_screen_rho_1: QFloat
    insu_screen_rho_1: QFloat
    bedding_rho_1: QFloat
    v_s_heat: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        self.binder_material = QStr(None, unit='', description='conductor binder material', source=None,
                                    options=cc.BINDER_TABLE, symbol='binder material')
        self.binder_dia = QFloat(None, unit='mm', description='conductor binder diameter', source=None,
                                 options=None, symbol='binder_dia')
        self.cond_screen_material = QStr(None, unit='', description='conductor screen material', source=None,
                                         options=cc.COND_SCREEN_TABLE, symbol='cond_screen_material')
        self.cond_screen_dia = QFloat(None, unit='mm', description='conductor screen diameter', source=None,
                                      options=None, symbol='d_c (cond screen)')
        self.max_cond_stress = QFloat(None, unit='kV/mm', description='maximum conductor stress', source=None,
                                      options=None, symbol='max_cond_stress')
        self.max_insu_stress = QFloat(None, unit='kV/mm', description='maximum insulation stress', source=None,
                                      options=None, symbol='max_insu_stress')
        self.nom_insu_rt = QFloat(None, unit='mm', description='nominal insulation radial thickness',
                                  source=None, options=None, symbol='r_(insu)')
        self.insu_dia = QFloat(None, unit='mm', description='insulation diameter', source=None, options=None,
                               symbol='D_i')
        self.belt_dia = QFloat(None, unit='mm', description='diameter over belted insulation', source=None,
                               options=None, symbol='D_bi')
        self.insulation_material = QStr(None, unit='', description='insulation material', source=None,
                                        options=iec.INS_LIST, symbol='insulation material')
        self.insu_screen_material = QStr(None, unit='', description='insulation screen material', source=None,
                                         options=cc.INSU_SCREEN_TABLE, symbol='insu_screen_material')
        self.insu_screen_dia = QFloat(unit='mm', description='insulation screen diameter', source=None,
                                      options=None, symbol='D_(insu screen)')
        self.bedding_material = QStr(None, unit='', description='bedding material', source=None,
                                     options=cc.CORE_BEDDING_TABLE, symbol='bedding_material')
        self.bedding_dia = QFloat(unit='mm', description='bedding diameter', source=None, options=None,
                                  symbol='D_(core bedding)')
        self.t1 = QFloat(unit='mm', description='thickness between conductor and metal sheath/screen',
                         source=None, options=None, symbol='t_1')
        self.spacing = QFloat(unit='mm', description='distance between cores for multi-core cable',
                              source=None, options=None, symbol='s')
        self.permittivity = QFloat(unit='', description='relative permittivity of insulation',
                                   source=None, options=None, symbol='ε')
        self.tan_d = QFloat(unit='', description='tan delta for insulation material',
                            source=None, options=None, symbol='tan δ')
        self.rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of insulation material',
                            source=None, options=None, symbol='ρ_1 (insulation)')
        self.binder_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of binder',
                                   source=None, options=None, symbol='ρ_1 (binder)')
        self.cond_screen_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of conductor screen',
                                        source=None, options=None, symbol='ρ_1 (cond_screen)')
        self.insu_screen_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of insulation screen',
                                        source=None, options=None, symbol='ρ_1 (insu_screen)')
        self.bedding_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of bedding over core',
                                    source=None, options=None, symbol='ρ_1 (core_bedding)')
        self.v_s_heat = QFloat(None, unit='J/m³.K', description='core volumetric specific heat',
                               source=None, options=None, symbol="core_v_s_heat")
        super().post_init(**kwargs)


class Wire(QuantityStore):
    """The wire screen of a cable."""

    material: QStr
    under_wire_material: QStr
    dia_under_wire: QFloat
    number_wires: QInt
    wire_size: QFloat
    dia: QFloat
    binder_material: QStr
    binder_dia: QFloat

    dc_resistance20: QFloat
    resistivity: QFloat
    alpha20: QFloat
    v_s_heat: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        self.material = QStr(unit='', description='wire screen material', source=None,
                                  options=iec.sheath_material_list, symbol='wire material')
        self.under_wire_material = QStr(unit='', description='under wire screen material', source=None,
                                        options=cc.CORE_BEDDING_TABLE, symbol='under_wire_screen_material')
        self.dia_under_wire = QFloat(unit='mm', description='diameter under wire screen',
                                     source=None, options=None, symbol='d_(under wire)')
        self.number_wires = QInt(unit='', description='number of wires in screen',
                                 source=None, options=None, symbol='n_wires')
        self.wire_size = QFloat(unit='mm', description='wire diameter', source=None, options=None,
                                symbol='d_wires')
        self.dia = QFloat(unit='mm', description='diameter over wire screen', source=None, options=None,
                          symbol='d_(over wires)')
        self.binder_material = QStr(unit='', description='wire screen binder material', source=None,
                                    options=cc.CORE_BEDDING_TABLE, symbol='wire_screen_binder_material')
        self.binder_dia = QFloat(None, unit='mm', description='bedding/binder diameter',
                                 source=None, options=None, symbol='d_(wire binder)')
        self.dc_resistance20 = QFloat(None, unit='Ω/m', description='wire screen dc resistance at 20°C',
                                      source=None, options=None, symbol='R_s20')
        self.resistivity = QFloat(unit='Ω/m', description='resistivity of wire material',
                                  source=None, options=None, symbol='ρ_(wire binder)')
        self.alpha20 = QFloat(None, unit='1/°C', description='coefficient of resistance of tape material',
                              source=None, options=None, symbol='wire α₂₀')
        self.v_s_heat = QFloat(None, unit='J/m³.K', description='wire volumetric specific heat',
                               source=None, options=None, symbol="wire_v_s_heat")
        self.under_wire_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of wire bedding',
                                       source=None, options=None, symbol='ρ_1 (under_wire)')
        self.binder_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of wire binder',
                                   source=None, options=None, symbol='ρ_1 (wire_binder)')
        super().post_init(**kwargs)


class Sheath(QuantityStore):
    """The sheath of a cable."""

    material: QStr
    under_sheath_material: QStr
    dia_under_sheath: QFloat
    thickness: QFloat
    dia: QFloat
    binder_material: QStr
    binder_dia: QFloat

    dc_resistance20: QFloat
    resistivity: QFloat
    alpha20: QFloat
    v_s_heat: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        self.material = QStr(unit='', description='metal sheath material', source=None,
                             options=iec.sheath_material_list, symbol='sheath material')
        self.under_sheath_material = QStr(unit='', description='under sheath material', source=None,
                                          options=cc.CORE_CLEARANCE_TABLE, symbol='under_sheath_material')
        self.dia_under_sheath = QFloat(unit='mm', description='diameter under metal sheath',
                                       source=None, options=None, symbol='D_it')
        self.thickness = QFloat(unit='mm', description='sheath thickness', source=None, options=None,
                                symbol='t_s')
        self.dia = QFloat(unit='mm', description='sheath diameter', source=None, options=None,
                          symbol='D_s')
        self.binder_material = QStr(unit='', description='sheath binder material', source=None,
                                    options=iec.BEDDING_LIST, symbol='sheath_binder_material')
        self.binder_dia = QFloat(None, unit='mm', description='bedding/binder diameter',
                                 source=None, options=None, symbol='d_(sheath binder)')
        self.dc_resistance20 = QFloat(None, unit='Ω/m', description='sheath dc resistance at 20°C',
                                      source=None, options=None, symbol='R_s20')
        self.resistivity = QFloat(unit='Ω/m', description='resistivity of sheath material',
                                  source=None, options=None, symbol='ρ_(sheath)')
        self.alpha20 = QFloat(None, unit='1/°C', description='coefficient of resistance of sheath material',
                              source=None, options=None, symbol='sheath α₂₀')
        self.v_s_heat = QFloat(None, unit='J/m³.K', description='sheath volumetric specific heat',
                               source=None, options=None, symbol="sheath_v_s_heat")
        self.under_sheath_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of clearance',
                                         source=None, options=None, symbol='ρ_1 (under_sheath)')
        self.binder_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of sheath binder',
                                   source=None, options=None, symbol='ρ_1 (sheath_binder)')
        super().post_init(**kwargs)


class Tape(QuantityStore):
    """The tape layer of a cable."""

    material: QStr
    under_tape_material: QStr
    dia_under_tape: QFloat
    number_tapes: QInt
    tape_width: QFloat
    tape_thickness: QFloat
    magnetic: QBool
    angle: QFloat
    number_layers: QInt
    dia: QFloat
    binder_material: QStr
    binder_dia: QFloat

    dc_resistance20: QFloat
    resistivity: QFloat
    alpha20: QFloat
    v_s_heat: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        self.material = QStr(unit='', description='tape material', source=None,
                             options=iec.sheath_material_list, symbol='tape material')
        self.under_tape_material = QStr(unit='', description='under tape material', source=None,
                                        options=cc.CORE_BEDDING_TABLE, symbol='under_tape_material')
        self.dia_under_tape = QFloat(unit='mm', description='diameter under tapes',
                                     source=None, options=None, symbol='d_(under tape)')
        self.number_tapes = QInt(unit='', description='number of tapes', source=None, options=None,
                                 symbol='n_tapes')
        self.tape_width = QFloat(unit='mm', description='tape width', source=None, options=None,
                                 symbol='tape width')
        self.tape_thickness = QFloat(unit='mm', description='tape thickness', source=None, options=None,
                                     symbol='t_tape')
        self.magnetic = QBool(unit='', description='tape magnetic?', source=None, options=[True, False],
                              symbol='magnetic')
        self.angle = QFloat(unit='°', description='angle', source=None, options=None,
                            symbol='tape angle')
        self.number_layers = QInt(unit='', description='number of tape layers', source=None,
                                  options=None, symbol='tape layers')
        self.dia = QFloat(unit='mm', description='tape diameter', source=None, options=None,
                          symbol='d_tape')
        self.binder_material = QStr(unit='', description='tape screen binder material', source=None,
                                    options=iec.BEDDING_LIST, symbol='tape_binder_material')
        self.binder_dia = QFloat(None, unit='mm', description='tape binder diameter',
                                 source=None, options=None, symbol='d_(tape binder)')

        self.dc_resistance20 = QFloat(None, unit='Ω/m', description='tape dc resistance at 20°C',
                                      source=None, options=None, symbol='R_s20')
        self.resistivity = QFloat(unit='Ω/m', description='resistivity of tape material',
                                  source=None, options=None, symbol='ρ_(tape)')
        self.alpha20 = QFloat(None, unit='1/°C', description='coefficient of resistance of tape material',
                              source=None, options=None, symbol='tape α₂₀')
        self.v_s_heat = QFloat(None, unit='J/m³.K', description='tape volumetric specific heat',
                               source=None, options=None, symbol="tape_v_s_heat")
        self.under_tape_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of tape bedding',
                                       source=None, options=None, symbol='ρ_1 (under_tape)')
        self.binder_rho_1 = QFloat(None, unit='K.m/W', description='thermal resistivity of tape binder',
                                   source=None, options=None, symbol='ρ_1 (tape_binder)')
        super().post_init(**kwargs)


class OverSheath(QuantityStore):
    """The non-metal sheath over core of 3 core cable"""

    material: QStr
    dia: QFloat
    t3: QFloat
    rho_t: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        serving_list = list(iec.SERVING_LIST)
        serving_list.append(iec.NONE)
        self.material = QStr(unit='', description='over-sheath material', source=None,
                             options=serving_list, symbol='over-sheath material')
        self.dia = QFloat(unit='mm', description='over-sheath diameter', source=None, options=None,
                          symbol='d_os')
        self.t_os = QFloat(unit='mm', description='thickness of over-sheath',
                           source=None, options=None, symbol='t_os')
        self.rho_t = QFloat(unit='', description='thermal resistivity of over-sheath material',
                            source=None, options=None, symbol='ρ_T (over-sheath)')
        super().post_init(**kwargs)


class ArmourBedding(QuantityStore):
    """The bedding for armour"""

    material: QStr
    dia: QFloat
    t3: QFloat
    rho_t: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        self.material = QStr(unit='', description='armour bedding material', source=None,
                             options=iec.SERVING_LIST, symbol='armour bedding material')
        self.dia = QFloat(unit='mm', description='armour bedding diameter', source=None, options=None,
                          symbol='d_ab')
        self.t_ab = QFloat(unit='mm', description='thickness of armour bedding',
                           source=None, options=None, symbol='t_ab')
        self.rho_t = QFloat(unit='', description='thermal resistivity of armour bedding material',
                            source=None, options=None, symbol='ρ_T (armour bedding)')
        super().post_init(**kwargs)


class Serving(QuantityStore):
    """The serving of a cable."""

    material: QStr
    dia: QFloat
    semicon_mat: QStr
    semicon_dia: QFloat
    t3: QFloat
    rho_t: QFloat
    v_s_heat: QFloat
    semicon_rho_t: QFloat
    semicon_v_s_heat: QFloat

    def __init__(self, **kwargs):
        super().__init__()
        serving_list = list(iec.SERVING_LIST)
        serving_list.append(iec.NONE)
        self.material = QStr(unit='', description='serving material', source=None,
                             options=serving_list, symbol='serving material')
        self.dia = QFloat(unit='mm', description='serving diameter', source=None, options=None,
                          symbol='d_serving')
        serving_semi_con_list = list(iec.SERVING_SEMI_CON_LIST)
        serving_semi_con_list.append(iec.NONE)
        self.semicon_mat = QStr(unit='', description='serving semi conding material', source=None,
                                options=serving_semi_con_list, symbol='serving_semicon_mat')
        self.semicon_dia = QFloat(unit='mm', description='serving semi-conducting diameter', source=None, options=None,
                                  symbol='d_serving_semicon')
        self.t3 = QFloat(unit='mm', description='thickness of serving',
                         source=None, options=None, symbol='t_3')
        self.rho_t = QFloat(unit='K.m/W', description='thermal resistivity of serving material',
                            source=None, options=None, symbol='ρ_T (serving)')
        self.v_s_heat = QFloat(None, unit='J/m³.K', description='serving volumetric specific heat',
                               source=None, options=None, symbol="serving_v_s_heat")
        self.semicon_rho_t = QFloat(unit='K.m/W', description='thermal resistivity of serving semicon material',
                            source=None, options=None, symbol='ρ_T (serving semicon)')
        self.semicon_v_s_heat = QFloat(None, unit='J/m³.K', description='serving semicon volumetric specific heat',
                               source=None, options=None, symbol="serving_semicon_v_s_heat")
        super().post_init(**kwargs)


class Pipe(QuantityStore):
    """The pipe of a pipe type cable."""

    dia: QFloat
    material: QStr

    def __init__(self, **kwargs):
        super().__init__()
        self.material = QStr(unit='', description='pipe material', source=None,
                             options=iec.sheath_material_list, symbol='pipe material')
        self.dia = QFloat(unit='mm', description='pipe outer diameter', source=None, options=None,
                          symbol='d_pipe')
        super().post_init(**kwargs)


class Cable(QuantityStore):
    """A Cable."""

    name: typing.Optional[str]
    nominal_volts: QFloat
    pipe_type: QBool
    belted: QBool
    sheath_type: QStr
    separate_sheath: QBool
    armour: QStr
    number_cores: QStr
    design_volts: QFloat

    sigma: QFloat
    max_cond_temp: QFloat
    max_emergency_cond_temp: QFloat
    max_surface_temp: QFloat
    max_cond_short_cct_temp: QFloat
    max_sheath_short_cct_temp: QFloat

    conductor: CableConductor
    core: Core
    wire_screen: Wire
    sheath: Sheath
    tape: Tape
    over_sheath: OverSheath
    armour_bedding: ArmourBedding
    wire_armour: Wire
    tape_armour: Tape
    serving: Serving
    pipe: Pipe

    def __init__(self, **kwargs):
        super().__init__()
        self.name = None
        # self.name = QStr(unit='', description='cable name', top=None, options=None,
        #                  symbol='cable name')
        self.nominal_volts = QFloat(unit='kV', description='cable nominal voltage phase to phase',
                                    source=None, options=list(iec.IEC_NOM_TO_U0_VOLTAGE.keys()), symbol='auto volts')
        self.pipe_type = QBool(unit='', description='is cable pipe type', source=None,
                               options=[True, False], symbol='pipe type')
        self.belted = QBool(unit='', description='is insulation belted', source=None,
                            options=[True, False], symbol='belted')
        self.sheath_type = QStr(unit='', description='sheath/screen type', source=None,
                                options=list(iec.SHEATH_TYPES.keys()), symbol='sheath type')
        self.separate_sheath = QBool(unit='', description='has separate sheath such as SL cable',
                                     source=None, options=[True, False], symbol='separate sheath')
        self.armour = QStr(unit='', description='type of armour',
                           source=None, options=iec.ARMOUR_TYPES, symbol='n')
        self.number_cores = QStr(unit='', description='number of cores in cable',
                                 source=None, options=iec.cable_no_cores_list, symbol='n')
        self.design_volts = QFloat(unit='kV', description='cable design voltage phase to earth (U0)',
                                   source=None, options=list(iec.IEC_U0_TO_UM_NOM_VOLTAGE.keys()),
                                   symbol='design volts')

        self.sigma = QFloat(unit='K.m/W', description='absorption coefficient of solar radiation',
                            source=None, options=None, symbol='σ')
        self.max_cond_temp = QFloat(unit='°C', description='maximum conductor temperature',
                                    source=None, options=None, symbol='θ max')
        self.max_emergency_cond_temp = QFloat(unit='°C', description='maximum emergency conductor temperature',
                                              source=None, options=None, symbol='θ e_max')
        self.max_surface_temp = QFloat(unit='°C', description='maximum cable surface temperature',
                                       source=None, options=None, symbol='θ_surface max')
        self.max_cond_short_cct_temp = QFloat(unit='°C', description='maximum conductor short circuit temperature',
                                       source=None, options=None, symbol='θ_cond_short_cct')
        self.max_sheath_short_cct_temp = QFloat(unit='°C', description='maximum sheath short circuit temperature',
                                       source=None, options=None, symbol='θ_sheath_short_cct')

        self.conductor = CableConductor()
        self.core = Core()
        self.wire_screen = Wire()
        self.sheath = Sheath()
        self.tape = Tape()
        self.over_sheath = OverSheath()
        self.armour_bedding = ArmourBedding()
        self.wire_armour = Wire()
        self.tape_armour = Tape()
        self.serving = Serving()
        self.pipe = Pipe()

        super().post_init(**kwargs)

    def __str__(self):
        return f'Cable( {self.conductor},\n' \
            f'      {self.sheath})'

    def find_conductor_shape(self, log: Log = None) -> str:
        """Find the shape of the conductor.

        The shape of the conductor (iec.ROUND or iec.SHAPED) is found from the conductor makeup (for example
        iec.ROUND_SOLID).

        :param log: calculation log
        :return: shape of conductor
        """

        if log is not None:
            log.start_section('conductor shape', 'support function')
        cond_makeup = self.conductor.makeup.get_value(unit='', log=log)
        if cond_makeup is None:
            raise Exception(f'trying to find conductor shape but no conductor makeup defined')
        conductor_shape = iec.conductor_makeup_dict[cond_makeup]
        if log is not None:
            log.end_section('conductor shape', conductor_shape, 'n/a', 'support function')
        return conductor_shape

    def calc_outer_diameter(self, log: Log = None) -> float:
        """Calculate the outer diameter of the cable (mm).

        Calculates the outer diameter of the cable. If the cable has no serving, then the outer diameter of the sheath
        is used. If there is no sheath then an exception is raised.

        :param log: calculation log
        :return: outer diameter of cable (mm)
        """

        if log is not None:
            log.start_section('cable external dia', 'cable class function')

        if self.serving.semicon_mat.value is None:
            raise Exception('calculating cable outer diameter but serving semicon material is None')
        if self.serving.semicon_mat.get_value(unit='', log=log) != iec.NONE:
            serving_semicon_dia = self.serving.semicon_dia.get_value(unit='mm', log=log)
            if log is not None:
                log.end_section('cable external dia', serving_semicon_dia, 'mm', 'cable class function')
            if serving_semicon_dia is None:
                raise Exception('calculating cable outer diameter but serving semicon diameter is None')
            return serving_semicon_dia

        if self.serving.material.value is None:
            raise Exception('calculating cable outer diameter but serving material is None')
        if self.serving.material.get_value(unit='', log=log) != iec.NONE:
            serving_dia = self.serving.dia.get_value(unit='mm', log=log)
            if log is not None:
                log.end_section('cable external dia', serving_dia, 'mm', 'cable class function')
            if serving_dia is None:
                raise Exception('calculating cable outer diameter but serving diameter is None')
            return serving_dia

        if self.sheath.material.value is None:
            raise Exception('calculating cable outer diameter but no serving and sheath material is None')
        if (self.serving.material.get_value(unit='', log=log) == iec.NONE and
                self.sheath.material.get_value(unit='', log=log) != iec.NONE):
            if not self.separate_sheath.value:
                common_sheath_dia = self.sheath.dia.get_value(unit='mm', log=log)
                if log is not None:
                    log.end_section('cable external dia', common_sheath_dia, 'mm', 'cable class function')
                if common_sheath_dia is None:
                    raise Exception('calculating cable outer diameter but sheath diameter is None')
                return common_sheath_dia

        raise Exception("calculating cable outer diameter but no serving or common sheath")

    def calc_cond_stress(self, ins_rt: float = None):
        """Calculate conductor screen electrical stress
        
        Calculates the conductor screen stress for the cable. If an insulation radial thickness is given then the given
        value will be used instead of the nominal value stored in self.core.nom_insu_rt. If the value can not be
        calculated, for example because self.design_volts is set to None, then None is returned.
        
        :param ins_rt: value of insulation radial thickness (mm)
        :return: electrical stress at conductor screen (kV/mm)
        """
        volts = self.design_volts.value
        if volts == 0.0:
            return 0.0
        if ins_rt is None:
            ins_rt = self.core.nom_insu_rt.value
        inner_dia_ins = self.core.cond_screen_dia.value
        if volts is None or ins_rt is None or inner_dia_ins is None:
            return None
        outer_dia_ins = inner_dia_ins + 2 * ins_rt
        stress = 2 * volts / (inner_dia_ins * math.log(outer_dia_ins / inner_dia_ins))
        return stress

    def calc_ins_stress(self, ins_rt: float = None):
        """Calculate insulation screen electrical stress

        Calculates the insulation screen stress for the cable. If an insulation radial thickness is given then the given
        value will be used instead of the nominal value stored in self.core.nom_insu_rt. If the value can not be
        calculated, for example because self.design_volts is set to None, then None is returned.

        :param ins_rt: value of insulation radial thickness (mm)
        :return: electrical stress at insulation screen (kV/mm)
        """
        volts = self.design_volts.value
        if volts == 0.0:
            return 0.0
        if ins_rt is None:
            ins_rt = self.core.nom_insu_rt.value
        inner_dia_ins = self.core.cond_screen_dia.value
        if volts is None or ins_rt is None or inner_dia_ins is None:
            return None
        outer_dia_ins = inner_dia_ins + 2 * ins_rt
        stress = 2 * volts / (outer_dia_ins * math.log(outer_dia_ins / inner_dia_ins))
        return stress


CABLE_CLASSES = {'CableConductor': CableConductor,
                 'Core': Core,
                 'Wire': Wire,
                 'Sheath': Sheath,
                 'Tape': Tape,
                 'Serving': Serving,
                 'Pipe': Pipe,
                 'Cable': Cable
                 }
