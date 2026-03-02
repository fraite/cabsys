import cabsys.iec.iec_constants as iec


# types of cable
SINGLE_CORE = iec.SINGLE_CORE
MULTI_CORE = 'multi-core'
BELTED = 'belted'
SEPARATE_SHEATH = 'separate sheath'
COMMON_NO_SHEATH = 'common sheath'

# Insulation material names and default sheath materials
# material, IEC name
INSULATION_MAT_TABLE = {iec.INS_PAPER_SOLID: (None, None),
                        iec.INS_PAPER_SCOF: (3.5, 0.0024),
                        iec.INS_PPL: (2.7, 0.001),
                        iec.INS_XLPE_UNFILLED: (None, None)}

# Voltage: nom, max cond stress, max insu stress, U0
INSULATION_TABLE = {iec.INS_PAPER_SCOF: {220.0: (0.0, 14.3, 14.3, 220.0),
                                         190.0: (0.0, 12.4, 12.4, 190.0),
                                         160.0: (0.0, 12.4, 12.4, 160.0),
                                         127.0: (0.0, 12.4, 12.4, 127.0),
                                         87.0: (0.0, 10.5, 10.5, 87.0),
                                         76.0: (0.0, 10.5, 10.5, 76.0),
                                         64.0: (0.0, 10.5, 10.5, 76.0),
                                         36.0: (0.0, 9.5, 9.5, 36.0),
                                         18.0: (0.0, 8.5, 8.5, 18.0)},
                    iec.INS_PPL: {220.0: (0.0, 14.3, 14.3, 220.0),
                                  190.0: (0.0, 12.4, 12.4, 190.0),
                                  160.0: (0.0, 12.4, 12.4, 160.0),
                                  127.0: (0.0, 12.4, 12.4, 127.0),
                                  87.0: (0.0, 10.5, 10.5, 87.0),
                                  76.0: (0.0, 10.5, 10.5, 76.0),
                                  64.0: (0.0, 10.5, 10.5, 76.0),
                                  36.0: (0.0, 9.5, 9.5, 36.0),
                                  18.0: (0.0, 8.5, 8.5, 18.0)},
                    iec.INS_PAPER_SOLID: {18.0: (4.8, 99.0, 99.0, 18.0),
                                          6.0: (2.8, 99.0, 99.0, 6.0)},
                    iec.INS_PVC: {0.0: (0.0, 99.0, 99.0, 0.0)},
                    iec.INS_XLPE_UNFILLED: {290.0: (27.0, 13.43, 6.28, 290.0),
                                            220.0: (26.0, 13.43, 6.28, 220.0),
                                            190.0: (23.0, 12.2, 4.7, 190.0),
                                            160.0: (22.0, 12.2, 4.7, 160.0),
                                            127.0: (22.0, 12.2, 4.7, 127.0),
                                            87.0: (15.8, 7.5, 3.8, 87.0),
                                            76.0: (15.0, 7.5, 3.8, 76.0),
                                            64.0: (15.0, 7.5, 3.8, 76.0),
                                            36.0: (12.0, 5.6, 2.8, 36.0),
                                            18.0: (8.0, 99.0, 99.0, 18.0),
                                            12.0: (5.5, 99.0, 99.0, 12.0),
                                            8.7: (4.5, 99.0, 99.0, 8.7),
                                            6.0: (3.4, 99.0, 99.0, 6.0)}}


SPIRAL_TABLE = [iec.NONE, iec.STEEL, iec.STAINLESS_STEEL]


XLPE_CONDUCTOR_TABLE = {iec.IEC_95MM2: (iec.ROUND_STRANDED_EXTRUDED, 11.2, 0.0, None),
                        iec.IEC_120MM2: (iec.ROUND_STRANDED_EXTRUDED, 12.8, 0.0, None),
                        iec.IEC_150MM2: (iec.ROUND_STRANDED_EXTRUDED, 14.2, 0.0, None),
                        iec.IEC_185MM2: (iec.ROUND_STRANDED_EXTRUDED, 15.9, 0.0, None),
                        iec.IEC_240MM2: (iec.ROUND_STRANDED_EXTRUDED, 18.0, 0.0, None),
                        iec.IEC_300MM2: (iec.ROUND_STRANDED_EXTRUDED, 20.5, 0.0, None),
                        iec.IEC_400MM2: (iec.ROUND_STRANDED_EXTRUDED, 23.1, 0.0, None),
                        iec.IEC_500MM2: (iec.ROUND_STRANDED_EXTRUDED, 26.4, 0.0, None),
                        iec.IEC_630MM2: (iec.ROUND_STRANDED_EXTRUDED, 30.2, 0.0, None),
                        iec.IEC_800MM2: (iec.ROUND_STRANDED_EXTRUDED, 33.9, 0.0, None),
                        iec.IEC_1000MM2: (iec.ROUND_STRANDED_EXTRUDED, 37.9, 0.0, None),
                        iec.IEC_1200MM2: (iec.ROUND_MILLIKEN_BARE_BI_EXTRUDED, 44.0, 0.0, None),
                        iec.IEC_1600MM2: (iec.ROUND_MILLIKEN_BARE_BI_EXTRUDED, 52.0, 0.0, None),
                        iec.IEC_2000MM2: (iec.ROUND_MILLIKEN_BARE_BI_EXTRUDED, 56.0, 0.0, None),
                        iec.IEC_2500MM2_2005: (iec.ROUND_MILLIKEN_INSULATED_EXTRUDED, 66.0, 0.0, None),
                        iec.IEC_2500MM2: (iec.ROUND_MILLIKEN_INSULATED_EXTRUDED, 66.0, 0.0, None),
                        iec.IEC_3000MM2: (iec.ROUND_MILLIKEN_INSULATED_EXTRUDED, 72.3, 0.0, None),
                        iec.IEC_3200MM2: (iec.ROUND_MILLIKEN_INSULATED_EXTRUDED, 74.6, 0.0, None),
                        iec.IEC_3500MM2: (iec.ROUND_MILLIKEN_INSULATED_EXTRUDED, 76.1, 0.0, None),
                        # iec.IEC_3000MM2: ("Round, Milliken, oxidised wires, not impregnated", 72.0),
                        # iec.IEC_3250MM2: ("Round, Milliken, enamelled wires, not impregnated", 79.0),
                        # iec.IEC_3500MM2: ("Round, Milliken, enamelled wires, not impregnated", 86.0),
                        # iec.IEC_1200MM2: ("Round, Milliken, insulated wires, not impregnated", 44.0),
                        # iec.IEC_1600MM2: ("Round, Milliken, insulated wires, not impregnated", 52.0),
                        # iec.IEC_2000MM2: ("Round, Milliken, insulated wires, not impregnated", 56.0),
                        # iec.IEC_2500MM2: ("Round, Milliken, insulated wires, not impregnated", 66.0),
                        # iec.ICEA_3: ("Round, stranded, not impregnated", 10.7),
                        # iec.ICEA_4: ("Round, stranded, not impregnated", 12.1),
                        iec.ICEA_250KCMIL: ("Round, stranded, not impregnated", 13.2, 0.0, None)  # ,
                        # iec.ICEA_300KCMIL: ("Round, stranded, not impregnated", 14.5),
                        # iec.ICEA_350KCMIL: ("Round, stranded, not impregnated", 15.6),
                        # iec.ICEA_500KCMIL: ("Round, stranded, not impregnated", 18.7),
                        # iec.ICEA_750KCMIL: ("Round, stranded, not impregnated", 23.0),
                        # iec.ICEA_1000KCMIL: ("Round, stranded, not impregnated", 26.9),
                        # iec.ICEA_1250KCMIL: ("Round, stranded, not impregnated", 30.2),
                        # iec.ICEA_1500KCMIL: ("Round, stranded, not impregnated", 33.5),
                        # iec.ICEA_1750KCMIL: ("Round, stranded, not impregnated", 36.2),
                        # iec.ICEA_2000KCMIL: ("Round, stranded, not impregnated", 38.0),
                        # iec.ICEA_2500KCMIL: ("Round, Milliken, bare wires, not impregnated", 45.0),
                        # iec.ICEA_3000KCMIL: ("Round, Milliken, bare wires, not impregnated", 48.0),
                        # iec.ICEA_3500KCMIL: ("Round, Milliken, bare wires, not impregnated", 52.5),
                        # iec.ICEA_4000KCMIL: ("Round, Milliken, bare wires, not impregnated", 55.0)
                        }

FF_CONDUCTOR_TABLE = {
    #                default conductor makeup,    conductor diameter, duct diameter, conductor spiral dia
    iec.IEC_120MM2: (iec.ROUND_STRANDED_IMPREGNATED, 11.8, 0.0, None),
    iec.IEC_150MM2: (iec.ROUND_STRANDED_IMPREGNATED, 13.0, 0.0, None),
    iec.IEC_185MM2: (iec.ROUND_STRANDED_IMPREGNATED, 14.4, 0.0, None),
    iec.IEC_240MM2: (iec.ROUND_STRANDED_IMPREGNATED, 18.4, 0.0, None),
    iec.IEC_300MM2: (iec.ROUND_STRANDED_IMPREGNATED, 20.2, 0.0, None),
    iec.IEC_400MM2: (iec.ROUND_STRANDED_IMPREGNATED, 22.4, 0.0, None),
    iec.IEC_500MM2: (iec.ROUND_STRANDED_IMPREGNATED, 24.8, 0.0, None),
    iec.IEC_630MM2: (iec.ROUND_STRANDED_IMPREGNATED, 29.0, 0.0, None),
    iec.IEC_800MM2: (iec.ROUND_STRANDED_IMPREGNATED, 31.5, 0.0, None),
    iec.IEC_1000MM2: (iec.ROUND_STRANDED_IMPREGNATED, 35.4, 0.0, None)}

SCFF_CONDUCTOR_TABLE = {
    iec.IEC_120MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 14.8, 8.0, None),
    iec.IEC_150MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 16.0, 8.0, None),
    iec.IEC_185MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 17.4, 8.0, None),
    iec.IEC_240MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 21.4, 12.0, None),
    iec.IEC_300MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 23.2, 12.0, None),
    iec.IEC_400MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 25.4, 12.0, None),
    iec.IEC_500MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 27.8, 12.0, None),
    iec.IEC_630MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 31.0, 12.0, None),
    iec.IEC_800MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 34.5, 12.0, None),
    iec.IEC_1000MM2: (iec.HOLLOW_KEYSTONE_IMPREGNATED, 38.4, 12.0, None),
    iec.IEC_1150MM2: (iec.ROUND_MILLIKEN_IMPREGNATED, 46.6, 12.0, 1.5),
    iec.IEC_1300MM2: (iec.ROUND_MILLIKEN_IMPREGNATED, 49.4, 12.0, 1.5),
    iec.IEC_1600MM2: (iec.ROUND_MILLIKEN_IMPREGNATED, 55.0, 12.0, 1.5),
    iec.IEC_2000MM2: (iec.ROUND_MILLIKEN_IMPREGNATED, 60.2, 12.0, 1.5),
    iec.IEC_2250MM2: (iec.ROUND_MILLIKEN_IMPREGNATED, 62.9, 12.0, 1.5),
    iec.IEC_2500MM2_2005: (iec.ROUND_MILLIKEN_IMPREGNATED, 70.3, 25.0, 1.5)}

PVC_CONDUCTOR_TABLE = {
    #                default conductor makeup,    conductor diameter, duct diameter, conductor spiral dia
    iec.IEC_120MM2: (iec.ROUND_STRANDED_IMPREGNATED, 14.4, 0.0, None),
    iec.IEC_240MM2: (iec.ROUND_STRANDED_IMPREGNATED, 19.8, 0.0, None),
    iec.IEC_300MM2: (iec.ROUND_STRANDED_IMPREGNATED, 22.6, 0.0, None),
    iec.IEC_500MM2: (iec.ROUND_STRANDED_IMPREGNATED, 29.5, 0.0, None)}

CONDUCTOR_TABLE = {iec.INS_PAPER_SCOF: {SINGLE_CORE: SCFF_CONDUCTOR_TABLE, MULTI_CORE: FF_CONDUCTOR_TABLE},
                   iec.INS_PPL: {SINGLE_CORE: SCFF_CONDUCTOR_TABLE, MULTI_CORE: FF_CONDUCTOR_TABLE},
                   iec.INS_PAPER_SOLID: {SINGLE_CORE: FF_CONDUCTOR_TABLE, MULTI_CORE: FF_CONDUCTOR_TABLE},
                   iec.INS_XLPE_UNFILLED: {SINGLE_CORE: XLPE_CONDUCTOR_TABLE, MULTI_CORE: XLPE_CONDUCTOR_TABLE},
                   iec.INS_PVC: {SINGLE_CORE: PVC_CONDUCTOR_TABLE}}

# compaction ratio is the oil volume / void volume as ratio to overall conductor volume excluding ducts
# used to calculate equivalent solid conductor diameter
COMPACTION_RATIO = {
    iec.ROUND_SOLID: 0.0,
    iec.ROUND_STRANDED_IMPREGNATED: 0.10,
    iec.ROUND_STRANDED_EXTRUDED: 0.10,
    iec.ROUND_MILLIKEN_IMPREGNATED: 0.16,
    iec.ROUND_MILLIKEN_INSULATED_EXTRUDED: 0.16,
    iec.ROUND_MILLIKEN_BARE_BI_EXTRUDED: 0.16,
    iec.HOLLOW_STRANDED_IMPREGNATED: 0.10,
    iec.SECTOR_SHAPED_IMPREGNATED: 0.10,
    iec.SECTOR_SHAPED_EXTRUDED: 0.10,
    iec.HOLLOW_KEYSTONE_IMPREGNATED: 0.03,
    iec.STEEL: 0.75,
    iec.STAINLESS_STEEL: 0.75
}

NONE = iec.NONE
# BINDER_TAPE = 'Semi-conducting tape'

#   material, thickness
BINDER_TABLE = {NONE: 0.0,
                iec.INS_SEMI_CON_TAPE: 0.8}

#   material, thickness
COND_SCREEN_TABLE = {NONE: 0.0,
                     iec.INS_CARBON_PAPER_TAPE_OF: 0.7,
                     iec.INS_CARBON_PAPER_TAPE_MI: 0.7,
                     iec.INS_SEMI_CON_XLPE: 2.0,
                     iec.INS_SEMI_CON_PE: 2.0,
                     iec.INS_SEMI_CON_EPR: 2.0}

#   material, thickness
INSU_SCREEN_TABLE = {NONE: 0.0,
                     iec.INS_CARBON_PAPER_TAPE_MI: 1.2,
                     iec.INS_METAL_PAPER_TAPE_OF: 1.2,
                     iec.INS_SEMI_CON_XLPE: 3.0,
                     iec.INS_SEMI_CON_PE: 3.0,
                     iec.INS_SEMI_CON_EPR: 3.0}

#   material, thickness
CORE_BEDDING_TABLE = [iec.NONE,
                      iec.INS_SEMI_CON_TAPE,
                      iec.INS_WATER_BLOCK_TAPE,
                      iec.INS_CU_FABRIC_TAPE]

CORE_CLEARANCE_TABLE = [iec.NONE,
                        iec.INS_SEMI_CON_TAPE,
                        iec.INS_WATER_BLOCK_TAPE,
                        iec.INS_CU_FABRIC_TAPE,
                        iec.INS_AIR,
                        iec.INS_OIL]

#                 insulation material,  cores,       default sheath
DEFAULT_SHEATH = {iec.INS_PAPER_SOLID: {iec.SINGLE_CORE: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.PB_SHEATH},
                                        iec.TWO_CORE: {SEPARATE_SHEATH: iec.PB_SHEATH, COMMON_NO_SHEATH: iec.PB_SHEATH},
                                        iec.THREE_CORE: {SEPARATE_SHEATH: iec.PB_SHEATH, COMMON_NO_SHEATH: iec.PB_SHEATH},
                                        iec.CONCENTRIC: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.CWS_PB_SHEATH}},
                  iec.INS_PAPER_SCOF: {iec.SINGLE_CORE: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.CAS_SHEATH},
                                       iec.TWO_CORE: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.CAS_SHEATH},
                                       iec.THREE_CORE: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.CAS_SHEATH},
                                       iec.CONCENTRIC: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.CWS_PB_TAPE_SHEATH}},
                  iec.INS_PPL: {iec.SINGLE_CORE: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.CAS_SHEATH},
                                iec.TWO_CORE: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.CAS_SHEATH},
                                iec.THREE_CORE: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.CAS_SHEATH},
                                iec.CONCENTRIC: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.PB_TAPE_SHEATH}},
                  iec.INS_XLPE_UNFILLED: {iec.SINGLE_CORE: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.WELDED_AL_SHEATH},
                                          iec.TWO_CORE: {SEPARATE_SHEATH: iec.TAPE_SHEATH, COMMON_NO_SHEATH: iec.PB_SHEATH},
                                          iec.THREE_CORE: {SEPARATE_SHEATH: iec.TAPE_SHEATH, COMMON_NO_SHEATH: iec.PB_SHEATH},
                                          iec.CONCENTRIC: {SEPARATE_SHEATH: None, COMMON_NO_SHEATH: iec.CWS_SHEATH}}
                  }

#     sheath: bedding: (material, RT)
#             CWS: (mat, binder mat, binder RT)
#             Sheath: clearance RT%, clearance const, sheath RT%, sheath const, sheath corr, (clearance mat, sheath mat)
#             Tape: bedding RT, material, cover

SHEATH_FF = {iec.PB_TAPE_SHEATH: ((iec.INS_CU_FABRIC_TAPE, 0.5),
                                  (iec.NONE, iec.NONE, 0.0),
                                  0.0, 0.1, 3.0, 1.0, 1.0, (iec.INS_OIL, iec.LEAD, iec.BED_BITUMEN_COTTON), 0.3,
                                  (iec.BRONZE, iec.BED_BITUMEN_COTTON), 0.45),
             iec.CWS_PB_TAPE_SHEATH: ((iec.INS_CU_FABRIC_TAPE, 0.5),
                                      (iec.COPPER, iec.NONE, 0.0),
                                      0.0, 0.1, 3.0, 1.0, 1.0, (iec.INS_OIL, iec.LEAD, iec.BED_BITUMEN_COTTON), 0.3,
                                      (iec.BRONZE, iec.BED_BITUMEN_COTTON), 0.45),
             iec.CAS_SHEATH: ((iec.INS_CU_FABRIC_TAPE, 0.4),
                              (iec.NONE, iec.NONE, 0.0),
                              0.0, 0.8, 1.8, 0.5, 3.0, (iec.INS_OIL, iec.ALUMINIUM, iec.NONE), 0.0,
                              (iec.NONE, iec.NONE), 0.0)}

SHEATH_MI = {iec.PB_SHEATH: ((iec.NONE, 0.0),
                             (iec.NONE, iec.NONE, 0.0),
                             0.0, 0.1, 3.0, 1.0, 1.0, (iec.INS_OIL, iec.LEAD, iec.NONE), 0.0,
                             (iec.NONE, iec.NONE), 0.0),
             iec.PB_TAPE_SHEATH: ((iec.NONE, 0.0),
                                  (iec.NONE, iec.NONE, 0.0),
                                  0.0, 0.1, 3.0, 1.0, 1.0, (iec.INS_OIL, iec.LEAD, iec.BED_BITUMEN_COTTON), 0.3,
                                  (iec.STAINLESS_STEEL, iec.BED_BITUMEN_COTTON), 0.45)}

SHEATH_XLPE = {iec.WELDED_AL_SHEATH: ((iec.INS_WATER_BLOCK_TAPE, 0.9),
                                      (iec.NONE, iec.NONE, 0.0),
                                      0.0, 0.0, 0.1, 1.0, 1.0, (iec.NONE, iec.ALUMINIUM, iec.NONE), 0.0,
                                      (iec.NONE, iec.NONE), 0.0),
               iec.CWS_AL_SHEATH: ((iec.INS_WATER_BLOCK_TAPE, 1.0),
                                   (iec.COPPER, iec.INS_WATER_BLOCK_TAPE, 1.0),
                                   0.0, 0.0, 0.1, 1.0, 1.0, (iec.NONE, iec.ALUMINIUM, iec.NONE), 0.0,
                                   (iec.NONE, iec.NONE), 0.0),
               iec.CWS_LAM_SHEATH: ((iec.INS_WATER_BLOCK_TAPE, 1.0),
                                    (iec.COPPER, iec.INS_WATER_BLOCK_TAPE, 1.0),
                                    0.0, 0.0, 0.0, 0.1, 1.0, (iec.NONE, iec.ALUMINIUM, iec.NONE), 0.0,
                                    (iec.NONE, iec.NONE), 0.0),
               iec.LAMINATE_SHEATH: ((iec.INS_WATER_BLOCK_TAPE, 1.0),
                                     (iec.NONE, iec.NONE, 0.0),
                                     0.0, 0.0, 0.0, 0.1, 1.0, (iec.NONE, iec.ALUMINIUM, iec.NONE), 0.0,
                                     (iec.NONE, iec.NONE), 0.0),
               iec.PB_SHEATH: ((iec.INS_WATER_BLOCK_TAPE, 0.5),
                               (iec.NONE, iec.NONE, 0.0),
                               0.0, 0.0, 3.0, 1.0, 1.0, (iec.NONE, iec.LEAD, iec.NONE), 0.0,
                               (iec.NONE, iec.NONE), 0.0),
               iec.CWS_PB_SHEATH: ((iec.INS_WATER_BLOCK_TAPE, 1.0),
                                   (iec.COPPER, iec.INS_WATER_BLOCK_TAPE, 1.0),
                                   0.0, 0.0, 3.0, 1.0, 1.0, (iec.NONE, iec.LEAD, iec.NONE), 0.0,
                                   (iec.NONE, iec.NONE), 0.0),
               iec.CAS_SHEATH: ((iec.INS_WATER_BLOCK_TAPE, 0.8),
                                (iec.NONE, iec.NONE, 0.0),
                                10.0, 1.0, 1.8, 0.5, 3.0, (iec.INS_AIR, iec.ALUMINIUM, iec.NONE), 0.0,
                                (iec.NONE, iec.NONE), 0.0),
               iec.TAPE_SHEATH: ((iec.INS_SEMI_CON_TAPE, 0.8),
                                 (iec.NONE, iec.NONE, 0.0),
                                 0.0, 0.0, 0.0, 0.0, 3.0, (iec.NONE, iec.NONE, iec.NONE), 0.0,
                                 (iec.COPPER, iec.NONE), 0.0),
               iec.CWS_SHEATH: ((iec.INS_SEMI_CON_TAPE, 1.0),
                                (iec.COPPER, iec.NONE, 0.0),
                                0.0, 0.0, 0.0, 0.0, 1.0, (iec.NONE, iec.NONE, iec.NONE), 0.0,
                                (iec.NONE, iec.NONE), 0.0),
               iec.CWS_TAPE_SHEATH: ((iec.INS_SEMI_CON_TAPE, 1.0),
                                     (iec.COPPER, iec.NONE, 0.0),
                                     0.0, 0.0, 0.0, 0.0, 1.0, (iec.NONE, iec.NONE, iec.NONE), 0.0,
                                     (iec.COPPER, iec.BED_BITUMEN_COTTON), 0.0)}

SHEATH_PVC = {iec.NO_SHEATH: ((iec.NONE, 0.0),
                              (iec.NONE, iec.NONE, 0.0),
                              0.0, 0.0, 0.0, 0.0, 0.0, (iec.NONE, iec.NONE, iec.NONE), 0.0,
                              (iec.NONE, iec.NONE), 0.0)}

SHEATH_TABLE = {iec.INS_PAPER_SOLID: SHEATH_MI,
                iec.INS_PAPER_SCOF: SHEATH_FF,
                iec.INS_PPL: SHEATH_FF,
                iec.INS_XLPE_UNFILLED: SHEATH_XLPE,
                iec.INS_PVC: SHEATH_PVC}

WIRE_TABLE = {iec.IEC_11KV: (100, 1.8),
              iec.IEC_33KV: (100, 1.8),
              iec.IEC_66KV: (100, 1.8),
              iec.IEC_132KV: (100, 1.8),
              iec.IEC_275KV: (100, 1.8),
              iec.IEC_400KV: (100, 1.8)}


# serving table
# diameter <=, thickness
SERVING_TABLE = {
    (30.0, 2.2),
    (35.0, 2.4),
    (40.0, 2.6),
    (45.0, 2.9),
    (50.0, 3.1),
    (62.5, 3.3),
    (77.5, 3.6),
    (999.0, 4.0)
}

TREFOIL_TOUCHING = 'trefoil touching'
TREFOIL_SPACED = 'trefoil spaced'
FLAT_TOUCHING = 'flat touching horizontal'
FLAT_SPACED = 'flat spaced horizontal'
VERTICAL_TOUCHING = 'vertical flat touching'
VERTICAL_SPACED = 'vertical flat spaced'
SINGLE_CABLE = 'single cable'

AVAILABLE_FORMATION = (TREFOIL_TOUCHING, TREFOIL_SPACED, FLAT_TOUCHING, FLAT_SPACED, VERTICAL_TOUCHING, VERTICAL_SPACED)
TOUCHING_FORMATION = (TREFOIL_TOUCHING, FLAT_TOUCHING, VERTICAL_TOUCHING)

# Installation seasons
SUMMER = 'summer'
WINTER = 'winter'

AVAILABLE_SEASONS = (SUMMER, WINTER)

SEASON_TABLE = {SUMMER: (15.0, 1.2),
                WINTER: (10.0, 1.05)}
