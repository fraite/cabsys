"""IEC 60287-2-1: 2023 Alternative current rating equations and calculation of losses - General

In addition to the function returning a result, the result can be returned in the State object. A bespoke logger
(different to the standard Python logger) can also be used.

Some of the equations have been modified. The logger notes where the changes have been made.
"""


from cabsys.quantity.quantity_store import QFloat
# from cabsys.quantity.log import Log, LogSection
from cabsys import IEC60287Exception
from cabsys.quantity.log import Log, LogSection
from cabsys.data_classes.cable import Cable
# import cabsys.iec.iec60287support as iec60287support
import cabsys.iec.iec60287_2_1 as iec60287_2_1
import cabsys.iec.iec_constants as iec


@LogSection('T_ws')
def calc_t_ws(cable: Cable, log: Log = None) -> QFloat:
    """Calculate the thermal resistance between the wire screen and metal sheath

    The thermal resistance between the wire screen and metal sheath is made up of two parts
        1. wire screen binder
        2. metal sheath bedding

    There are many possible permutations:
        a) If there is no wire screen and no metal sheath T_ws is zero.
        b) If there is no wire screen and a metal sheath T_ws is zero (the metal sheath bedding is part of T1).
        c) If there is a wire screen and metal sheath T_ws is set to the thermal resistance of the wire screen and metal
           sheath bedding.
        d) If there is a wire screen, no metal sheath, but a tape screen T_ws is set to the thermal resistance of wire
           screen binder
        e) if there is a wire screen, no metal sheath and no tape screen then T_ws is zero (the wire screen binder
           becomes part of T3)

    :param cable: cable
    :param log: logger
    :return: thermal resistance between wire screen and metal sheath
    """

    source = 'no source'

    if cable.tape.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating T1 clearance: tape material not defined')
    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating T1 clearance: sheath material not defined')
    if cable.wire_screen.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating T1 clearance: wire screen material not defined')

    # option a and b (no wire screen)
    if cable.wire_screen.material.get_value(unit='') is iec.NONE:
        t_ws = 0.0

    elif cable.sheath.material.get_value(unit='') is iec.NONE:
        if cable.tape.material.get_value(unit='') is iec.NONE:
            # option e (wire screen but no metal sheath or tape screen)
            t_ws = 0.0
        else:
            # option d (wire screen and tape screen but no metal sheath)
            # TR of wire binder
            t_ws = iec60287_2_1.calc_t1_layer_4_1_3(cable.wire_screen.binder_dia,
                                                    cable.wire_screen.dia,
                                                    cable.wire_screen.binder_rho_1,
                                                    cable.wire_screen.binder_material,
                                                    cable.design_volts,
                                                    'wire screen binder',
                                                    log=log).value
    else:
        # option c (wire screen and sheath)
        # TR of wire binder and metal sheath bedding
        t_ws = (iec60287_2_1.calc_t1_layer_4_1_3(cable.wire_screen.binder_dia,
                                                 cable.wire_screen.dia,
                                                 cable.wire_screen.binder_rho_1,
                                                 cable.wire_screen.binder_material,
                                                 cable.design_volts,
                                                 'wire screen binder',
                                                 log=log).value +
                iec60287_2_1.calc_t1_layer_4_1_3(cable.sheath.dia_under_sheath,
                                                 cable.wire_screen.binder_dia,
                                                 cable.sheath.under_sheath_rho_1,
                                                 cable.sheath.under_sheath_material,
                                                 cable.design_volts,
                                                 'sheath bedding/clearance',
                                                 log=log).value)

    return QFloat(t_ws, 'K.m/W', source=source, description='thermal resistance between wire and sheath',
                  symbol='T1_ws')


@LogSection('T_st')
def calc_t_st(cable: Cable, log: Log = None) -> QFloat:
    """Calculate the thermal resistance between the metal sheath and tape screen

    The thermal resistance between the metal sheath and tape screen is made up of two parts
        1. metal sheath binder
        2. tape screen bedding

    There are many possible permutations:
        a) If there is no tape screen and no metal sheath T_st is zero.
        b) If there is no tape screen and a metal sheath T_st is zero (the metal sheath binder is part of T3).
        c) If there is a tape screen and metal sheath T_ts is set to the thermal resistance of the tape screen and metal
           sheath bedding.
        d) If there is a tape screen, no metal sheath, but a wire screen T_ts is set to the thermal resistance of tape
           screen bedding
        e) if there is a tape screen, no metal sheath and no tape screen then T_st is zero (the tape screen bedding
           becomes part of T1)

    :param cable: cable
    :param log: logger
    :return: thermal resistance between wire screen and metal sheath
    """

    source = 'no source'

    if cable.tape.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating T1 clearance: tape material not defined')
    if cable.sheath.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating T1 clearance: sheath material not defined')
    if cable.wire_screen.material.get_value(unit='') is None:
        raise IEC60287Exception('calculating T1 clearance: wire screen material not defined')

    # option a and b (no tape screen)
    if cable.tape.material.get_value(unit='') is iec.NONE:
        t_st = 0.0

    elif cable.sheath.material.get_value(unit='') is iec.NONE:
        if cable.wire_screen.material.get_value(unit='') is iec.NONE:
            # option e (tape screen but no metal sheath or wire screen)
            t_st = 0.0
        else:
            # option d (tape screen and wire screen but no metal sheath)
            # TR of tape bedding
            t_st = iec60287_2_1.calc_t1_layer_4_1_3(cable.tape.dia_under_tape,
                                                    cable.wire_screen.binder_dia,
                                                    cable.tape.under_tape_rho_1,
                                                    cable.tape.under_tape_material,
                                                    cable.design_volts,
                                                    'tape screen bedding',
                                                    log=log).value
    else:
        # option c (tape screen and sheath)
        # TR of tape screen bedding and metal sheath binder
        t_st = (iec60287_2_1.calc_t1_layer_4_1_3(cable.tape.dia_under_tape,
                                                 cable.sheath.binder_dia,
                                                 cable.tape.under_tape_rho_1,
                                                 cable.tape.under_tape_material,
                                                 cable.design_volts,
                                                 'tape screen bedding',
                                                 log=log).value +
                iec60287_2_1.calc_t1_layer_4_1_3(cable.sheath.binder_dia,
                                                 cable.sheath.dia,
                                                 cable.sheath.binder_rho_1,
                                                 cable.sheath.binder_material,
                                                 cable.design_volts,
                                                 'sheath binder',
                                                 log=log).value)

    return QFloat(t_st, 'K.m/W', source=source, description='thermal resistance between sheath and tape',
                  symbol='T1_st')
