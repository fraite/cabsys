from typing import NamedTuple

IEC60287_1_1_ED3 = 'IEC 60287-1-1 ED 3.0 2023-05'
IEC60287_1_1_ED3_STRICT = 'IEC 60287-1-1 ED 3.0 2023-05 strict'
IEC60287_1_1_ED2 = 'IEC 60287-1-1 ED 2.1 2014-11'
CIGRE_TB880_2022 = 'Cigre TB 880 ED 1.0 2022-09'
IEC60287_1_1_VERS = [IEC60287_1_1_ED2, IEC60287_1_1_ED3, IEC60287_1_1_ED3_STRICT, CIGRE_TB880_2022]

IEC60287_2_1_ED3 = 'IEC 60287-2-1 ED 3.0 2023-05'
IEC60287_2_1_ED3_STRICT = 'IEC 60287-2-1 ED 3.0 2023-05 strict'
IEC60287_2_1_ED2 = 'IEC 60287-2-1 ED 2.1 2015-04'
CIGRE_TB880_2022 = 'Cigre TB 880 ED 1.0 2022-09'
IEC60287_2_1_VERS = [IEC60287_2_1_ED2, IEC60287_2_1_ED3, CIGRE_TB880_2022]

RATING_CONTINUOUS = 'continuous rating'
RATING_EMERGENCY = 'emergency rating'
RATING_TRANSIENT = 'transient rating'
RATING_CYCLIC = 'cyclic rating'
RATING_TYPES = [RATING_CONTINUOUS, RATING_EMERGENCY, RATING_TRANSIENT, RATING_CYCLIC]

CALC_TEMPERATURE_CCT = 'cct constant current find temperature'
CALC_TEMPERATURE_NEW = 'new constant current find temperature'
CALC_TEMPERATURE = 'constant current find temperature'
CALC_CURRENT = 'constant temperature find current (IEC 60287)'
CALC_TRANSIENT_ELT_87 = 'transient current find temperature (ELT 87)'
CALC_TRANSIENT_ELT_87_EXPLICIT_MATRIX = 'transient current find temperature (ELT 87 explicit matrix)'
CALC_TRANSIENT_ELT_87_IMPLICIT_MATRIX = 'transient current find temperature (ELT 87 implicit matrix)'
SOLVER_TYPES = [CALC_TEMPERATURE, CALC_CURRENT, CALC_TRANSIENT_ELT_87, CALC_TRANSIENT_ELT_87_EXPLICIT_MATRIX,
                CALC_TRANSIENT_ELT_87_IMPLICIT_MATRIX]
CONTINUOUS_SOLVERS = [CALC_TEMPERATURE, CALC_CURRENT, CALC_TEMPERATURE_NEW, CALC_TEMPERATURE_CCT]
TRANSIENT_SOLVERS = [CALC_TRANSIENT_ELT_87, CALC_TRANSIENT_ELT_87_EXPLICIT_MATRIX,
                     CALC_TRANSIENT_ELT_87_IMPLICIT_MATRIX]


# used for oil volume table in iec60287support
DUCT = 'duct'
DUCT_SPIRAL = 'duct spiral'
INSULATION = 'insulation'
CLEARANCE = 'clearance'
UNDER_CS = 'under corrugated sheath'

SPACED = 'spaced'
TOUCHING = 'touching'
SOME_TOUCHING = 'some touching'
FLAT = 'flat'
TREFOIL = 'trefoil'
HORIZONTAL = 'horizontal'
VERTICAL = 'vertical'
ARBITRARY = 'arbitrary'
EQUAL = 'equal'
UNEQUAL = 'unequal'

CIRCULAR = 'circular'
SHAPED = 'shaped'
OVAL = 'oval'

NONE = 'none'
NA = "n/a"


COPPER = "copper"
ALUMINIUM = "aluminium"
LEAD = "lead or lead alloy"
STEEL = "steel"
BRONZE = "bronze"
STAINLESS_STEEL = "stainless steel"

conductor_material_list = [COPPER, ALUMINIUM]
sheath_material_list = [COPPER, ALUMINIUM, LEAD, STEEL, BRONZE, STAINLESS_STEEL, NONE]


SINGLE_CORE = "single core"
TWO_CORE = "two core"
THREE_CORE = "three core"
CONCENTRIC = "concentric"

# available number of cores of cable
cable_no_cores_list = (SINGLE_CORE,
                       TWO_CORE,
                       THREE_CORE,
                       CONCENTRIC)

cable_no_cores = {SINGLE_CORE: 1, TWO_CORE: 2, THREE_CORE: 3, CONCENTRIC: 1}

IEC_11KV = 6.0
IEC_33KV = 18.0
IEC_66KV = 36.0
IEC_132KV = 76.0
IEC_275KV = 160.0
IEC_400KV = 220.0

IEC_U0_TO_UM_NOM_VOLTAGE = {0.0: (0.0, 0.0),
                            3.6: (7.2, 6.6),
                            6.0: (12.0, 11.0),
                            8.7: (17.5, 15.0),
                            12.0: (24.0, 20.0),
                            18.0: (36.0, 33.0),
                            26.0: (52.0, 45.0),
                            36.0: (72.5, 66.0),
                            64.0: (123.0, 110.0),
                            76.0: (145.0, 132.0),
                            87.0: (170.0, 150.0),
                            127.0: (245.0, 220.0),
                            160.0: (300.0, 275.0),
                            190.0: (362.0, 330.0),
                            220.0: (420.0, 400.0),
                            290.0: (550.0, 500.0)}

IEC_NOM_TO_U0_VOLTAGE = {0.0: 0.0,
                         6.6: 3.6,
                         10.0: 6.0,
                         11.0: 6.0,
                         15.0: 8.7,
                         20.0: 12.0,
                         22.0: 12.0,
                         30.0: 18.0,
                         33.0: 18.0,
                         45.0: 26.0,
                         66.0: 36.0,
                         110.0: 64.0,
                         132.0: 76.0,
                         150.0: 87.0,
                         220.0: 127.0,
                         275.0: 160.0,
                         330.0: 190.0,
                         380.0: 220.0,
                         400.0: 220.0,
                         500.0: 290.0}

SINGLE_PHASE = 'AC single phase'
TWO_PHASE = 'AC two phase'
THREE_PHASE = 'AC three phase'
BIPOLE = 'DC bipole'
MONOPOLE = 'DC monopole'

PHASES_POLES = (SINGLE_PHASE, TWO_PHASE, THREE_PHASE, MONOPOLE, BIPOLE)

TWO_PHASE_TWO_CORE = "two phase, two-core cable"
TWO_PHASE_SINGLE_CORE = "two phase, 2 single-core cables"
THREE_PHASE_THREE_CORE = "three phase, three-core cable"
THREE_PHASE_SINGLE_CORE = "three phase, 3 single-core cables"
SINGLE_PHASE_CONCENTRIC = "single phase, concentric cable"
SINGLE_PHASE_NEUTRAL_RETURN = "single phase, neutral return cable"
BIPOLE_SINGLE_CORE = "DC bipole, 2 single-core cables"
BIPOLE_TWO_CORE = "DC bipole, two-core cable"
MONOPOLE_NEUTRAL_RETURN = "DC monopole, neutral return cable"
MONOPOLE_TWO_CORE = "DC monopole, two-core cable"
MONOPOLE_CONCENTRIC = "DC monopole, concentric cable"

#                                                 cable type, no cables, same cables?, DC circuits?, no phases
CABLE_SET_TYPE_TABLE = {TWO_PHASE_TWO_CORE: (TWO_CORE, 1, True, False, 2),
                        TWO_PHASE_SINGLE_CORE: (SINGLE_CORE, 2, True, False, 2),
                        THREE_PHASE_THREE_CORE: (THREE_CORE, 1, True, False, 3),
                        THREE_PHASE_SINGLE_CORE: (SINGLE_CORE, 3, True, False, 3),
                        SINGLE_PHASE_CONCENTRIC: (CONCENTRIC, 1, True, False, 1),  # not in IEC
                        SINGLE_PHASE_NEUTRAL_RETURN: (SINGLE_CORE, 2, False, False, 1),  # not in IEC
                        BIPOLE_SINGLE_CORE: (SINGLE_CORE, 2, True, True, 0),
                        BIPOLE_TWO_CORE: (TWO_CORE, 1, True, True, 0),
                        MONOPOLE_NEUTRAL_RETURN: (SINGLE_CORE, 2, False, True, 0),
                        MONOPOLE_TWO_CORE: (TWO_CORE, 1, True, True, 0),
                        MONOPOLE_CONCENTRIC: (CONCENTRIC, 1, True, True, 0)}  # not in IEC


IEC_95MM2 = "95 mm2"
IEC_120MM2 = "120 mm2"
IEC_150MM2 = "150 mm2"
IEC_185MM2 = "185 mm2"
IEC_240MM2 = "240 mm2"
IEC_300MM2 = "300 mm2"
IEC_400MM2 = "400 mm2"
IEC_500MM2 = "500 mm2"
IEC_630MM2 = "630 mm2"
IEC_800MM2 = "800 mm2"
IEC_1000MM2 = "1000 mm2"
IEC_1150MM2 = "1150 mm2"
IEC_1200MM2 = "1200 mm2"
IEC_1300MM2 = "1300 mm2"
IEC_1400MM2 = "1400 mm2"
IEC_1600MM2 = "1600 mm2"
IEC_1800MM2 = "1800 mm2"
IEC_2000MM2 = "2000 mm2"
IEC_2250MM2 = "2250 mm2"
IEC_2500MM2_2005 = "2500 mm2 (2005)"
IEC_2500MM2 = "2500 mm2"
IEC_3000MM2 = "3000 mm2"
IEC_3200MM2 = "3200 mm2"
IEC_3500MM2 = "3500 mm2"
ICEA_3AWG = "3/0 AWG"
ICEA_4AWG = "4/0 AWG"
ICEA_250KCMIL = "250 kcmil"
ICEA_300KCMIL = "300 kcmil"
ICEA_350KCMIL = "350 kcmil"
ICEA_500KCMIL = "500 kcmil"
ICEA_750KCMIL = "750 kcmil"
ICEA_1000KCMIL = "1000 kcmil"
ICEA_1250KCMIL = "1250 kcmil"
ICEA_1500KCMIL = "1500 kcmil"
ICEA_1750KCMIL = "1750 kcmil"
ICEA_2000KCMIL = "2000 kcmil"
ICEA_2500KCMIL = "2500 kcmil"
ICEA_3000KCMIL = "3000 kcmil"
ICEA_3500KCMIL = "3500 kcmil"
ICEA_4000KCMIL = "4000 kcmil"

iec_conductor_size_list = [IEC_95MM2, IEC_120MM2, IEC_150MM2, IEC_185MM2, IEC_240MM2, IEC_300MM2, IEC_400MM2,
                           IEC_500MM2,
                           IEC_630MM2, IEC_800MM2, IEC_1000MM2, IEC_1150MM2, IEC_1200MM2, IEC_1300MM2, IEC_1400MM2,
                           IEC_1600MM2, IEC_1800MM2, IEC_2000MM2, IEC_2250MM2, IEC_2500MM2_2005,
                           IEC_2500MM2, IEC_3000MM2, IEC_3200MM2, IEC_3500MM2]
icea_conductor_size_list = [ICEA_3AWG, ICEA_4AWG, ICEA_250KCMIL, ICEA_300KCMIL, ICEA_350KCMIL, ICEA_500KCMIL,
                            ICEA_750KCMIL, ICEA_1000KCMIL, ICEA_1250KCMIL, ICEA_1500KCMIL, ICEA_1750KCMIL,
                            ICEA_2000KCMIL, ICEA_2500KCMIL, ICEA_3000KCMIL, ICEA_3500KCMIL, ICEA_4000KCMIL]
conductor_size_list = iec_conductor_size_list + icea_conductor_size_list


ROUND_SOLID = "Round, Solid"
ROUND_STRANDED_IMPREGNATED = "Round, stranded, impregnated"
ROUND_STRANDED_EXTRUDED = "Round, stranded, extruded"
OVAL_STRANDED_IMPREGNATED = "Oval, stranded, impregnated"
ROUND_MILLIKEN_IMPREGNATED = "Round, Milliken, impregnated"
ROUND_MILLIKEN_INSULATED_EXTRUDED = "Round, Milliken, insulated wires, extruded"
ROUND_MILLIKEN_BARE_UNI_EXTRUDED = "Round, Milliken, bare uni-directional wires, extruded"
ROUND_MILLIKEN_BARE_BI_EXTRUDED = "Round, Milliken, bare bi-directional wires, extruded"
HOLLOW_STRANDED_IMPREGNATED = "Hollow, helical stranded, impregnated"
SECTOR_SHAPED_IMPREGNATED = "Sector-shaped, impregnated"
SECTOR_SHAPED_EXTRUDED = "Sector-shaped, extruded"
HOLLOW_KEYSTONE_IMPREGNATED = "Hollow, keystone, impregnated"

conductor_makeup_dict = {ROUND_SOLID: CIRCULAR,
                         ROUND_STRANDED_IMPREGNATED: CIRCULAR,
                         ROUND_STRANDED_EXTRUDED: CIRCULAR,
                         ROUND_MILLIKEN_IMPREGNATED: CIRCULAR,
                         ROUND_MILLIKEN_INSULATED_EXTRUDED: CIRCULAR,
                         ROUND_MILLIKEN_BARE_UNI_EXTRUDED: CIRCULAR,
                         ROUND_MILLIKEN_BARE_BI_EXTRUDED: CIRCULAR,
                         HOLLOW_STRANDED_IMPREGNATED: CIRCULAR,
                         SECTOR_SHAPED_IMPREGNATED: SHAPED,
                         SECTOR_SHAPED_EXTRUDED: SHAPED,
                         HOLLOW_KEYSTONE_IMPREGNATED: CIRCULAR,
                         OVAL_STRANDED_IMPREGNATED: OVAL}

# list of conductors that are impregnated
conductor_makeup_list_impregnated = (ROUND_STRANDED_IMPREGNATED,
                                     ROUND_MILLIKEN_IMPREGNATED,
                                     HOLLOW_STRANDED_IMPREGNATED,
                                     SECTOR_SHAPED_EXTRUDED,
                                     HOLLOW_KEYSTONE_IMPREGNATED,
                                     OVAL_STRANDED_IMPREGNATED)

# materials used in cables between the conductor and metal sheath/screen
INS_PAPER_SOLID = "paper in solid cables"
INS_PAPER_SCOF = "paper in self contained oil filled cables"
INS_PAPER_OF_PIPE = "paper in pipe oil filled cables"
INS_PAPER_GAS_EXT = "paper in cables with external gas pressure"
INS_PAPER_GAS_INT_PRE = "paper in cables with internal gas pressure pre-impregnated"
INS_PAPER_GAS_INT_MASS = "paper in cables with internal gas pressure mass impregnated"
INS_PE = "PE"
INS_XLPE_UNFILLED = "XLPE unfilled"
INS_XLPE_FILLED = "XLPE filled"
INS_PPL = "PPL"
INS_PVC = "Polyvinyl chloride"
INS_EPR = "EPR"
INS_BUTYL = "butyl rubber"
INS_RUBBER = "Rubber"
INS_OIL = 'oil'                                                   # <- in IEC 60853-2
INS_NITROGEN = 'nitrogen at 15 atmospheres'                       # <- in IEC 60853-2
INS_SEMI_CON_TAPE = 'semi-conducting tape'                        # <- not in IEC but needed
INS_SEMI_CON_XLPE = 'semi-conducting XLPE'
INS_SEMI_CON_PE = 'semi-conducting PE'
INS_SEMI_CON_EPR = 'semi-conducting EPR'
INS_WATER_BLOCK_TAPE = 'semi-con water-block tape'      # <- not in IEC but needed
INS_CU_FABRIC_TAPE = 'copper woven fabric tape'         # <- not in IEC but needed
INS_METAL_PAPER_TAPE_MI = 'metallised paper tape (Solid)'               # <- not in IEC but needed
INS_CARBON_PAPER_TAPE_MI = 'carbon black paper tapes (Solid)'           # <- not in IEC but needed
INS_METAL_PAPER_TAPE_OF = 'metallised paper tape (SCOF)'                                    # <-not in IEC but needed
INS_CARBON_PAPER_TAPE_OF = 'carbon black paper tapes (SCOF)'                                # <-not in IEC but needed
INS_METAL_PAPER_OF_PIPE = "metallised paper in pipe oil filled cables"                      # <-not in IEC but needed
INS_CARBON_PAPER_OF_PIPE = "carbon black paper in pipe oil filled cables"                   # <-not in IEC but needed
INS_METAL_PAPER_GAS_EXT = "metallised paper in cables with external gas pressure"           # <-not in IEC but needed
INS_CARBON_PAPER_GAS_EXT = "carbon black paper in cables with external gas pressure"        # <-not in IEC but needed
INS_METAL_PAPER_GAS_INT_PRE = "metallised paper (internal gas pressure pre-impregnated)"    # <-not in IEC but needed
INS_CARBON_PAPER_GAS_INT_PRE = "carbon black paper (internal gas pressure pre-impregnated)"    # <-not in IEC but needed
INS_METAL_PAPER_GAS_INT_MASS = "metallised paper (internal gas pressure mass impregnated)"     # <-not in IEC but needed
INS_CARBON_PAPER_GAS_INT_MASS = "carbon black paper (internal gas pressure mass impregnated)"  # <-not in IEC but needed
INS_AIR = 'air'                                                                                # <-not in IEC but needed

INS_LIST = (INS_PAPER_SOLID, INS_PAPER_SCOF, INS_PAPER_OF_PIPE, INS_PAPER_GAS_EXT, INS_PAPER_GAS_INT_PRE,
            INS_PAPER_GAS_INT_MASS, INS_PE, INS_XLPE_UNFILLED, INS_XLPE_FILLED, INS_PPL, INS_PVC, INS_EPR, INS_BUTYL,
            INS_RUBBER)

BED_BITUMEN_COTTON = 'bitumen / cotton tape'

BEDDING_LIST = (BED_BITUMEN_COTTON, INS_SEMI_CON_TAPE, NONE)

# sheath types
CWS_SHEATH = 'copper wire screen'
CWS_TAPE_SHEATH = 'copper wire screen & equalisation tape'
PB_SHEATH = 'lead'
PB_TAPE_SHEATH = 'lead with reinforcement'
CAS_SHEATH = 'corrugated aluminium'
WELDED_AL_SHEATH = 'welded aluminium'
LAMINATE_SHEATH = 'laminate'
CWS_LAM_SHEATH = 'copper wire screen & laminate'
CWS_PB_SHEATH = 'copper wire screen & lead'
CWS_PB_TAPE_SHEATH = 'copper wire screen and lead with reinforcement'
CWS_AL_SHEATH = 'copper wire screen & welded aluminium'
TAPE_SHEATH = 'copper tape'
NO_SHEATH = 'no sheath or screen'


class SheathType(NamedTuple):
    """Results from a function"""
    has_cws: bool
    has_sheath: bool
    has_tape: bool


#          sheath type: (has_CWS, has_sheath, has_tape)
SHEATH_TYPES = {CWS_SHEATH: SheathType(True, False, False),
                CWS_TAPE_SHEATH: SheathType(True, False, True),
                PB_SHEATH: SheathType(False, True, False),
                PB_TAPE_SHEATH: SheathType(False, True, True),
                CAS_SHEATH: SheathType(False, True, False),
                WELDED_AL_SHEATH: SheathType(False, True, False),
                LAMINATE_SHEATH: SheathType(False, True, False),
                CWS_LAM_SHEATH: SheathType(True, True, False),
                CWS_PB_SHEATH: SheathType(True, True, False),
                CWS_PB_TAPE_SHEATH: SheathType(True, True, True),
                CWS_AL_SHEATH: SheathType(True, True, False),
                TAPE_SHEATH: SheathType(False, False, True),
                NO_SHEATH: SheathType(False, False, False)}

TAPE_ARMOUR = 'tape armour'
WIRE_ARMOUR = 'wire armour'

ARMOUR_TYPES = (NONE, WIRE_ARMOUR, TAPE_ARMOUR)


SERVING_JUTE = 'Compounded jute and fibrous materials'
SERVING_RUBBER_TAPE = 'Rubber sandwich protection'
SERVING_POLYCHLOPRENE = 'Polychloroprene'
SERVING_PVC = 'PVC'
SERVING_PVC_CAS = 'PVC/bitumen on corrugated aluminium sheaths'
SERVING_PE = 'PE'

# SERVING_PVC_CAS missing as set by program
SERVING_LIST = (SERVING_JUTE, SERVING_RUBBER_TAPE, SERVING_POLYCHLOPRENE, SERVING_PVC, SERVING_PE)

SERVING_SEMI_CON_PE = 'semi-conducting PE'
SERVING_GRAPHITE = 'colloidal graphite'

SERVING_SEMI_CON_LIST = (SERVING_SEMI_CON_PE, SERVING_GRAPHITE)


BURIED = 'buried'
IN_AIR = 'in air'
IN_AIR_PROTECTED = 'in air protected from sun'
IN_AIR_EXPOSED = 'in air exposed to sun'
TUNNEL = 'tunnel'

INSTALL_KIND_LIST = (BURIED, IN_AIR_PROTECTED, IN_AIR_EXPOSED, TUNNEL)

DEPTH_TOP = 'top of cable/duct'
DEPTH_CENTRE = 'centre of cable/duct'
DEPTH_LIST = (DEPTH_TOP, DEPTH_CENTRE)

DUCT_CONCRETE = 'concrete'
DUCT_FIBRE = 'fibre'
DUCT_ASBESTOS = 'asbestos'
DUCT_EARTHENWARE = 'earthenware'
DUCT_PVC = 'PVC'
DUCT_PE11 = 'PE SDR11'
DUCT_METAL = 'metal'

DUCT_LIST = (DUCT_CONCRETE, DUCT_FIBRE, DUCT_ASBESTOS, DUCT_EARTHENWARE, DUCT_PVC, DUCT_PE11, DUCT_METAL)

# available duct layouts
NO_DUCTS = "no ducts"
INDIVIDUAL_AIR_DUCTS = "individual ducts air filled"
COMMON_AIR_DUCT = "common duct air filled"
GAS_PRESSURE_PIPE = 'gas pressure cable in pipe'
OIL_PRESSURE_PIPE = 'oil pressure pipe-type cable'
INDIVIDUAL_WATER_DUCT = 'individual water filled duct'
COMMON_WATER_DUCT = 'common water filled duct'
INDIVIDUAL_FILLED_DUCT = 'individual pump filled duct'
COMMON_FILLED_DUCT = 'common pump filled duct'

DUCT_LAYOUT_LIST = (NO_DUCTS,
                    INDIVIDUAL_AIR_DUCTS,
                    COMMON_AIR_DUCT,
                    INDIVIDUAL_WATER_DUCT,
                    COMMON_WATER_DUCT,
                    INDIVIDUAL_FILLED_DUCT,
                    COMMON_FILLED_DUCT)

# Installation for cables installed in free air, not clipped to wall (De* <= 0.15 m)
AIR_SINGLE_CABLE = 'Single cable'
AIR_TWO_CABLES_TOUCHING_HORIZONTAL = 'Two cables touching, horizontal'
AIR_THREE_CABLES_TOUCHING_TREFOIL = 'Three cables touching, trefoil'
AIR_THREE_CABLES_TOUCHING_HORIZONTAL = 'Three cables touching, horizontal'
AIR_TWO_CABLES_TOUCHING_VERTICAL = 'Two cables touching, vertical'
AIR_TWO_CABLES_SPACED_DE_VERTICAL = 'Two cables spaced, De* vertical'
AIR_THREE_CABLES_TOUCHING_VERTICAL = 'Three cables touching, vertical'
AIR_THREE_CABLES_SPACED_DE_VERTICAL = 'Three cables spaced, De* vertical'
# Installations added by IEC 60287-2-3 tunnels
AIR_THREE_CABLES_SPACED_HORIZONTAL = 'Three cables spaced, horizontal'
AIR_THREE_CABLES_SPACED_VERTICAL = 'Three cables spaced, vertical'

# available bonding and earthing options
SOLID_BONDED = "solidly bonded and earthed"
CROSS_BONDED = "cross bonded"
SINGLE_POINT_BONDED = "single point bonded"

BONDING_LIST = (SOLID_BONDED,
                CROSS_BONDED,
                SINGLE_POINT_BONDED)

RED = 'Red'
BLUE = 'Blue'
YELLOW = 'Yellow'
PHASE_LIST = (RED, BLUE, YELLOW)

PRELOAD_CONST_CURRENT = 'constant current'
PRELOAD_AVE_LOSS = 'average loss'
PRELOAD_OFF = 'cable set off'

PRELOAD_TYPES = [PRELOAD_CONST_CURRENT, PRELOAD_AVE_LOSS, PRELOAD_OFF]
