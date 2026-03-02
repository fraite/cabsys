from typing import Union, Optional, List

from cabsys.quantity.quantity_store import QuantityStore, QFloat, QStr, QBool, QInt, QuantityBase
from cabsys.data_classes.install import Install
from cabsys.data_classes.node import Node


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


class ConnectedPlacedCable(QuantityStore):

    conductor: List[ConnectedConductor]

    def __init__(self, **kwargs):
        super().__init__()
        self.conductor = [ConnectedConductor(), ConnectedConductor()]

        super().post_init(**kwargs)


class ConnectedCableSets(QuantityStore):

    section_connected: QBool
    section_circuit_number: QInt
    cable_set_number: QInt
    placed_cables: List[ConnectedPlacedCable]

    def __init__(self, **kwargs):
        super().__init__()

        self.section_connected = QBool(None, unit='', description='connected to section? (alt circuit)',
                                       source=None, options=[True, False], symbol='')
        self.section_circuit_number = QInt(None, unit='', description='connected section or circuit number',
                                           source=None, options=None, symbol='')
        self.cable_set_number = QInt(None, unit='', description='connected cable set number', source=None,
                                     options=None, symbol='')
        self.placed_cables = []
        super().post_init(**kwargs)


class Section(QuantityStore):
    """A cable installation section.

    Contains all the information for a cable installation section."""

    name: Optional[str]
    install: Optional[Install]
    length: QFloat
    left_node: Optional[Node]
    left_cable_sets: List[ConnectedCableSets]
    right_node: Optional[Node]
    right_cable_sets: List[ConnectedCableSets]

    def __init__(self, **kwargs):
        super().__init__()

        self.name = None
        self.install = None
        self.length = QFloat(None, unit='m', description='length of section', source=None,
                             options=None, symbol='L')
        self.left_node = None
        self.left_cable_sets = []
        self.right_node = None
        self.right_cable_sets = []

        super().post_init(**kwargs)

    def config_connections(self):
        if self.install is None:
            self.left_cable_sets = []
            self.right_cable_sets = []
        else:
            self.left_cable_sets = len(self.install.cable_sets) * [ConnectedCableSets()]
            self.right_cable_sets = len(self.install.cable_sets) * [ConnectedCableSets()]
            for index, cable_set in enumerate(self.install.cable_sets):
                self.left_cable_sets[index].placed_cables = len(cable_set.placed_cables) * [ConnectedPlacedCable()]
                self.right_cable_sets[index].placed_cables = len(cable_set.placed_cables) * [ConnectedPlacedCable()]