"""IEC 60228: 2005 Conductors of insulated cables


"""
from cabsys import Cable, Log, IEC60287Exception
from cabsys.iec import iec_constants as iec
from cabsys.quantity.log import LogSection
from cabsys.quantity.quantity_store import QFloat

# TODO: save reference with conductor size in cable save file otherwise old cable designs will pick up new resistances
# IEC 60228 Resistance of conductors
#                                  size,      material, resistance, diameter, top. size (for IEC 60949)
conductor_resistance_table = {iec.IEC_95MM2: {iec.COPPER: [193.0E-6, 11.2, 'IEC 60228:2023 Table 4', 95.0],
                                              iec.ALUMINIUM: [320.0E-6, 11.2, 'IEC 60228:2023 Table 4', 95.0]},
                              iec.IEC_120MM2: {iec.COPPER: [153.0E-6, 12.8, 'IEC 60228:2023 Table 4', 120.0],
                                               iec.ALUMINIUM: [253.0E-6, 12.8, 'IEC 60228:2023 Table 4', 120.0]},
                              iec.IEC_150MM2: {iec.COPPER: [124.0E-6, 14.2, 'IEC 60228:2023 Table 4', 150.0],
                                               iec.ALUMINIUM: [206.0E-6, 14.2, 'IEC 60228:2023 Table 4', 150.0]},
                              iec.IEC_185MM2: {iec.COPPER: [99.1E-6, 15.9, 'IEC 60228:2023 Table 4', 185.0],
                                               iec.ALUMINIUM: [164.0E-6, 15.9, 'IEC 60228:2023 Table 4', 185.0]},
                              iec.IEC_240MM2: {iec.COPPER: [75.4E-6, 18.0, 'IEC 60228:2023 Table 4', 240.0],
                                               iec.ALUMINIUM: [125.0E-6, 18.0, 'IEC 60228:2023 Table 4', 240.0]},
                              iec.IEC_300MM2: {iec.COPPER: [60.1E-6, 20.5, 'IEC 60228:2023 Table 4', 300.0],
                                               iec.ALUMINIUM: [100.0E-6, 20.5, 'IEC 60228:2023 Table 4', 300.0]},
                              iec.IEC_400MM2: {iec.COPPER: [47.0E-6, 23.1, 'IEC 60228:2023 Table 4', 400.0],
                                               iec.ALUMINIUM: [77.8E-6, 23.1, 'IEC 60228:2023 Table 4', 400.0]},
                              iec.IEC_500MM2: {iec.COPPER: [36.6E-6, 26.4, 'IEC 60228:2023 Table 4', 500.0],
                                               iec.ALUMINIUM: [60.5E-6, 26.4, 'IEC 60228:2023 Table 4', 500.0]},
                              iec.IEC_630MM2: {iec.COPPER: [28.3E-6, 30.2, 'IEC 60228:2023 Table 4', 630.0],
                                               iec.ALUMINIUM: [46.9E-6, 30.2, 'IEC 60228:2023 Table 4', 630.0]},
                              iec.IEC_800MM2: {iec.COPPER: [22.1E-6, 33.9, 'IEC 60228:2023 Table 4', 800.0],
                                               iec.ALUMINIUM: [36.7E-6, 33.9, 'IEC 60228:2023 Table 4', 800.0]},
                              iec.IEC_1000MM2: {iec.COPPER: [17.6E-6, 37.9, 'IEC 60228:2023 Table 4', 1000.0],
                                                iec.ALUMINIUM: [29.1E-6, 37.9, 'IEC 60228:2023 Table 4',1000.0]},
                              iec.IEC_1200MM2: {iec.COPPER: [15.1E-6, 44.0, 'IEC 60228:2023 Table 4', 1200.0],
                                                iec.ALUMINIUM: [24.7E-6, 44.0, 'IEC 60228:2023 Table 4', 1200.0]},
                              iec.IEC_1400MM2: {iec.COPPER: [12.9E-6, 48.8, 'IEC 60228:2023 Table 4', 1400.0],
                                                iec.ALUMINIUM: [21.2E-6, 48.8, 'IEC 60228:2023 Table 4', 1400.0]},
                              iec.IEC_1600MM2: {iec.COPPER: [11.3E-6, 52.0, 'IEC 60228:2023 Table 4', 1600.0],
                                                iec.ALUMINIUM: [18.6E-6, 52.0, 'IEC 60228:2023 Table 4', 1600.0]},
                              iec.IEC_1800MM2: {iec.COPPER: [10.1E-6, 54.0, 'IEC 60228:2023 Table 4', 1800.0],
                                                iec.ALUMINIUM: [16.5E-6, 54.0, 'IEC 60228:2023 Table 4', 1800.0]},
                              iec.IEC_2000MM2: {iec.COPPER: [9.0E-6, 56.0, 'IEC 60228:2023 Table 4', 2000.0],
                                                iec.ALUMINIUM: [14.9E-6, 56.0, 'IEC 60228:2023 Table 4', 2000.0]},
                              iec.IEC_2500MM2_2005: {iec.COPPER: [7.2E-6, 66.0, 'IEC 60228:2005 Table 2', 2500.0],
                                                     iec.ALUMINIUM: [12.7E-6, 66.0, 'IEC 60228:2005 Table 2', 2500.0]},
                              iec.IEC_2500MM2: {iec.COPPER: [7.2E-6, 66.0, 'IEC 60228:2023 Table 4', 2500.0],
                                                iec.ALUMINIUM: [11.9E-6, 66.0, 'IEC 60228:2023 Table 4', 2500.0]},
                              iec.IEC_3000MM2: {iec.COPPER: [6.0E-6, 72.3, 'IEC 60228:2023 Table 4', 3000.0],
                                                iec.ALUMINIUM: [9.9E-6, 72.3, 'IEC 60228:2023 Table 4', 3000.0]},
                              iec.IEC_3200MM2: {iec.COPPER: [5.6E-6, 74.6, 'IEC 60228:2023 Table 4', 3200.0],
                                                iec.ALUMINIUM: [9.3E-6, 74.6, 'IEC 60228:2023 Table 4', 3200.0]},
                              iec.IEC_3500MM2: {iec.COPPER: [5.1E-6, 76.1, 'IEC 60228:2023 Table 4', 3500.0],
                                                iec.ALUMINIUM: [8.5E-6, 76.1, 'IEC 60228:2023 Table 4', 3500.0]},
                              iec.ICEA_250KCMIL: {iec.COPPER: [13.9E-6, 13.2, 'ICEA S-97-682', None],
                                                  iec.ALUMINIUM: [22.8E-6, 13.2, 'ICEA S-97-682', None]}
                              }


@LogSection('R0')
def find_r0(cable: Cable, log: Log = None) -> QFloat:
    """Find dc resistance at 20°C for a cable conductor

    :param cable: cable with conductor
    :param log: calculation log
    :return: dc resistance of cable conductor at 20 °C (ohm/m)
    """

    cond_size = cable.conductor.size.get_value(unit='', log=log)
    cond_mat = cable.conductor.material.get_value(unit='', log=log)
    try:
        rho = conductor_resistance_table[cond_size][cond_mat][0]
        rho_ref = conductor_resistance_table[cond_size][cond_mat][2]
    except KeyError:
        raise IEC60287Exception(f'could not get resistance for conductor material "{cond_mat}" and size "{cond_size}"')

    return QFloat(rho, 'Ω/m', rho_ref,
                  description='dc resistance at 20°C', symbol='R0')


def find_s(cable: Cable, log: Log = None) -> QFloat:
    """Find the cross-section in mm² for a cable conductor

    :param cable: cable with conductor
    :param log: calculation log
    :return: cross-section (mm²)
    """

    cond_size = cable.conductor.size.get_value(unit='', log=log)
    cond_mat = cable.conductor.material.get_value(unit='', log=log)
    try:
        s = conductor_resistance_table[cond_size][cond_mat][3]
        s_ref = conductor_resistance_table[cond_size][cond_mat][2]
    except KeyError:
        raise IEC60287Exception(f'could not get resistance for conductor material "{cond_mat}" and size "{cond_size}"')

    return QFloat(s, 'mm²', s_ref,
                  description='conductor cross section in mm²', symbol='S')