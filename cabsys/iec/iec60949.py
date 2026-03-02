"""IEC 60949: 2008 Calculation of thermally permissible short circuit currents

The equations found in IEC 60949 are implemented. The inputs to the functions are given as a Cable objects.

Some of the equations have been modified. The logger notes where the changes have been made.
"""

import math
from cabsys.quantity.log import Log, LogSection
from cabsys.data_classes.cable import Cable
from cabsys.quantity.quantity_store import QFloat
import cabsys.iec.iec_constants as iec
import cabsys.iec.iec60228 as iec60228


class IEC60949Exception(Exception):
    pass


def calc_cond_short_cct(cable: Cable, theta_i=None, theta_f=None, log: Log = None) -> QFloat:
    """Calculate the conductor short circuit current rating

    The default initial conductor temperature (theta_i) is 90°C if a value is not given.

    If the maximum conductor short circuit temperature (theta_f) is not given then the default value will be, in order
    of precedence:
       * the value given in the cable objects, or if not specified
       * the default value given in IEC standards

    :param cable: the cable that the short circuit is being calculated for
    :param log: logger used to store results
    :param theta_i: initial conductor temperature
    :param theta_f: maximum conductor short circuit temperature
    :return: conductor short circuit current rating
    """

    # TODO: do this properly by referencing a table with up to date IEC references
    # Assign initial conductor temperature
    if theta_i is None:
        # TODO: get the temperature from IEC 60287
        theta_i = 90.0
    # Assign maximum short circuit temperatures
    if theta_f is None:
        theta_f = cable.max_cond_short_cct_temp.get_value(unit='°C', default=None, log=log)
    if theta_f is None:
        if cable.core.insulation_material.get_value(unit='', log=log) in (iec.INS_PAPER_SCOF, iec.INS_XLPE_FILLED,
                                                                            iec.INS_XLPE_UNFILLED, iec.INS_EPR,
                                                                            iec.INS_PPL):
            theta_f = 250
        else:
            theta_f = None
    if theta_f is None:
        # TODO: rather than raise exception, allocate 160 °C and change source
        raise IEC60949Exception(f'theta_f cannot be found for "{cable.core.insulation_material.value}" insulation')

    k = find_cond_k(cable).value
    beta = find_cond_beta(cable).value
    s = iec60228.find_s(cable).get_value(unit='mm²', log=log)

    i_ad = math.sqrt(k**2 * s**2 * math.log((theta_f + beta) / (theta_i + beta)))

    return QFloat(i_ad, 'A', f'not done yet',
                  description='conductor short circuit current rating', symbol="I_AD")


def calc_sheath_short_cct(cable: Cable, foil_rt: float = None, theta_i: float = None, theta_f: float = None,
                          log: Log = None) -> QFloat:
    """Calculate the metal sheath short circuit current rating

    The default initial sheath temperature is 80°C.

    :param cable: the cable that the short circuit is being calculated for
    :param foil_rt: the sheath radial thickness below which the sheath is considered a foil laminate
    :param log: logger used to store results
    :param theta_i: initial metal sheath temperature
    :param theta_f: maximum metal sheath short circuit temperature
    :return: conductor short circuit current rating
    """

    # TODO: do this properly by referencing a table with up to date IEC references
    # Assign initial conductor temperature
    if theta_i is None:
        # TODO: get temperature from IEC 60287 - 10°C or so!
        theta_i = 80.0
    # Assign maximum short circuit temperatures
    if theta_f is None:
        theta_f = cable.max_cond_short_cct_temp.get_value(unit='°C', default=None, log=log)
    if theta_f is None:
        if cable.core.insulation_material.get_value(unit='', log=log) in (iec.INS_PAPER_SCOF, iec.INS_XLPE_FILLED,
                                                                            iec.INS_XLPE_UNFILLED, iec.INS_EPR,
                                                                            iec.INS_PPL):
            if foil_rt is None:
                foil_rt = 0.25
            if log is not None:
                log.add_line('foil_rt', foil_rt, 'mm', 'foil if radial thickness of sheath less than value')
            if cable.serving.material.get_value(unit='', log=log) in (iec.SERVING_PVC, iec.SERVING_PVC_CAS):
                if cable.sheath.thickness.get_value(unit='mm', log=log) >= foil_rt:
                    theta_f = 200.0
                else:
                    theta_f = 160.0
            elif cable.serving.material.get_value(unit='', log=log) == iec.SERVING_PE:
                if cable.sheath.thickness.get_value(unit='mm', log=log) >= foil_rt:
                    theta_f = 180.0
                else:
                    theta_f = 150.0
            else:
                theta_f = None
        else:
            theta_f = None
    if theta_f is None:
        # TODO: rather than raise exception, allocate 160 °C and change source
        raise IEC60949Exception(f'theta_f cannot be found for "{cable.serving.material.value}" serving')

    if cable.wire_screen.material.get_value(unit='', log=log) != iec.NONE:
        raise IEC60949Exception(f'cables with wire screens not implemented but "{cable.wire_screen.material.value}" found')
    if cable.sheath.material.get_value(unit='', log=log) in (iec.NONE, None):
        raise IEC60949Exception('Sheath short circuit only implemented for metal sheaths')
    else:
        k = find_sheath_k(cable).value
        beta = find_sheath_beta(cable).value
        # TODO: transfer area to a function of cable.sheath
        sheath_dia = cable.sheath.dia.get_value(unit='mm', log=log)
        dia_under_sheath = cable.sheath.dia_under_sheath.get_value('mm', log=log)
        sheath_thickness = cable.sheath.thickness.get_value(unit='mm', log=log)
        s = (sheath_dia + dia_under_sheath) / 2 * sheath_thickness * math.pi

        i_ad = math.sqrt(k**2 * s**2 * math.log((theta_f + beta) / (theta_i + beta)))

    return QFloat(i_ad, 'A', f'not done yet',
                  description='conductor short circuit current rating', symbol="I_AD")


@LogSection('K')
def find_cond_k(cable: Cable, log: Log = None) -> QFloat:
    """Get K for conductor from IEC 60949 Table 1

    :param cable: the cable
    :param log: logging object used to track results
    :return: k: K value
    """
    cond_mat = cable.conductor.material.get_value(unit='', log=log)
    k = IEC_60949_COND_CONSTS[cond_mat][0]
    return QFloat(k, '-', 'IEC 60949:2008 Table 1, K',
                  description='K value', symbol='K')


@LogSection('β')
def find_cond_beta(cable: Cable, log: Log = None) -> QFloat:
    """Get beta for conductor from IEC 60949 Table 1

    :param cable: the cable
    :param log: logging object used to track results
    :return: beta: beta value
    """
    cond_mat = cable.conductor.material.get_value(unit='', log=log)
    k = IEC_60949_COND_CONSTS[cond_mat][1]
    return QFloat(k, '-', 'IEC 60949:2008 Table 1, β',
                  description='beta value', symbol='beta')


# IEC 60949 Table 1 ***********
#                 conductor material:   K,     beta, sigma_c, rho_20
IEC_60949_COND_CONSTS = {iec.COPPER: (226.0, 234.5, 3.45e6, 1.7241e-8),
                         iec.ALUMINIUM: (148.0, 228.0, 2.5e6, 2.8264e-8)}

@LogSection('K')
def find_sheath_k(cable: Cable, log: Log = None) -> QFloat:
    """Get K for metal sheath from IEC 60949 Table 1

    :param cable: the cable
    :param log: logging object used to track results
    :return: k: K value
    """
    sheath_mat = cable.sheath.material.get_value(unit='', log=log)
    k = IEC_60949_SHEATH_CONSTS[sheath_mat][0]
    return QFloat(k, '-', 'IEC 60949:2008 Table 1, K',
                  description='K value', symbol='K')


@LogSection('β')
def find_sheath_beta(cable: Cable, log: Log = None) -> QFloat:
    """Get beta for metal sheath from IEC 60949 Table 1

    :param cable: the cable
    :param log: logging object used to track results
    :return: beta: beta value
    """
    sheath_mat = cable.sheath.material.get_value(unit='', log=log)
    k = IEC_60949_SHEATH_CONSTS[sheath_mat][1]
    return QFloat(k, '-', 'IEC 60949:2008 Table 1, β',
                  description='beta value', symbol='beta')


# IEC 60949 Table 1 ***********
#                     sheath material:   K,     beta, sigma_c, rho_20
IEC_60949_SHEATH_CONSTS = {iec.LEAD: (41.0, 230.0, 1.45e6, 21.4e-8),
                           iec.COPPER: (226.0, 234.5, 3.45e6, 1.7241e-8),
                           iec.ALUMINIUM: (148.0, 228.0, 2.5e6, 2.84e-8)}