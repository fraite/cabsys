"""CIGRE TB 283 - Complex Impedance Matrix (CIM)


"""

import math
import time
import copy
from typing import List, Tuple, Optional

import cabsys.data_classes.state
from cabsys.data_classes.state import UseState
import cabsys.quantity.quantity_constants as dc
from cabsys.quantity.quantity_store import QFloat
from cabsys.quantity.log import Log, LogSection, no_log
# from cabsys.data_classes.cable import Cable
from cabsys.data_classes.auto_install import AutoInstall  # , CableSet, CableSetState
from cabsys.data_classes.install import Install
from cabsys import InstallState, IEC60287Exception
# from cabsys.data_classes.project import Project
# from cabsys import CableState
# from cabsys.data_classes.install import CableSet
import cabsys.iec.iec60287support as iec60287support
import cabsys.iec.iec60287_1_1_cct as iec60287_1_1
import cabsys.iec.iec60287_2_1_cct as iec60287_2_1
import cabsys.iec.iec_constants as iec
# import cabsys.cigre.electra087wrapper as elt087
# import cabsys.iec.iec60853_2 as iec60853_2
from cabsys.top.Exception import InvalidInput, SolverException


def cim(install: Install, install_circuit_amps, state: InstallState = None, log: Log = None) -> List[List[List[float]]]:


    if log is None:
        log = no_log
    # TODO: CIM should be done here to split currents correctly
    install_cable_amps = []
    log.start_section('CIM to be implemented', source='CIGRE TB 283 CIM')
    for circuit_num, install_circuit in enumerate(install.install_circuits):
        log.start_section(f'circuit {circuit_num}', source=f'CIGRE TB 283 CIM')
        circuit_cable_amps = []
        for cable_set_num, cable_set in enumerate(install_circuit.cable_sets):
            log.start_section(f'cable set {cable_set_num}', source=f'CIGRE TB 283 CIM')
            set_cable_amps = []
            for cable_num, cable in enumerate(cable_set.placed_cables):
                set_cable_amps.append(install_circuit_amps[circuit_num] / len(install_circuit.cable_sets))
                log.add_line(f'cable {cable_num}', set_cable_amps[-1], unit='A', source=f'CIGRE TB 283 CIM')
            circuit_cable_amps.append(set_cable_amps)
            log.end_section(f'cable set {cable_set_num}', value='', unit='', source=f'CIGRE TB 283 CIM')
        install_cable_amps.append(circuit_cable_amps)
        log.end_section(f'circuit {circuit_num}', value=install_circuit_amps[circuit_num],
                        unit=install_circuit.desired_I.unit, source=f'CIGRE TB 283 CIM')
    log.end_section('CIM to be implemented', value='', unit='', source='CIGRE TB 283 CIM')

    return install_cable_amps