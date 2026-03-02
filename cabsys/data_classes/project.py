from typing import Dict, Optional

from cabsys.quantity.serialise import dumps_object, read_xml_tag, loads_obj

from cabsys.data_classes.auto_scenario import Scenario, SCENARIO_CLASSES
from cabsys.data_classes.cable import Cable
from cabsys.data_classes.auto_cable import CABLE_CLASSES
from cabsys.data_classes.install import CableSet, Install, InstallConfig
from cabsys.data_classes.auto_install import INSTALL_CLASSES
from cabsys.data_classes.section import Section
from cabsys.data_classes.node import Node
from cabsys.data_classes.circuit import Circuit, ScenarioRating, CIRCUIT_CLASSES
from cabsys.data_classes.current_curve import CurrentCurve, CURRENT_CURVE_CLASSES
from cabsys.quantity.quantity_store import QuantityStore, QStr
import cabsys.data_classes.auto_scenario


def find_unique_name(old_name: str, list_names: list) -> str:
    unique_name = old_name
    if unique_name in list_names:
        try:
            digit = int(unique_name.split('_')[-1]) + 1
            base = ''
            for split_count in range(len(unique_name.split('_')) - 1):
                base = base + unique_name.split('_')[split_count] + '_'
        except ValueError:
            digit = 0
            base = unique_name
        unique_name = base + str(digit)
        while unique_name in list_names:
            digit = digit + 1
            unique_name = base + str(digit)
    return unique_name


class Project(QuantityStore):
    """Information for the user project."""

    name: Optional[str]
    config: InstallConfig
    scenarios_name: Optional[QStr]
    scenarios: Dict[str, Scenario]
    cables: Dict[str, Cable]
    installs: Dict[str, Install]
    current_curves: Dict[str, CurrentCurve]
    sections: Dict[str, Section]
    nodes: Dict[str, Node]
    circuits: Dict[str, Circuit]

    def __init__(self, **kwargs):
        super().__init__()
        self.name = None
        self.config = InstallConfig()
        self.scenarios_name = QStr(value=None)
        self.scenarios = {}
        self.cables = {}
        self.installs = {}
        self.current_curves = {}
        self.sections = {}
        self.nodes = {}
        self.circuits = {}

        # default_scenario = Scenario(name='no scenario')
        # self.add_scenario(default_scenario)

        super().post_init(**kwargs)

    def clear_project(self):
        self.config = InstallConfig()
        self.scenarios_name = QStr(value=None)
        self.scenarios = {}
        self.cables = {}
        self.installs = {}
        self.current_curves = {}
        self.sections = {}
        self.nodes = {}
        self.circuits = {}

    def add_scenario(self, new_scenario: Scenario = None) -> Scenario:
        """Add scenario to project

        Adds a scenario to the scenario list in the project. If no new scenario is given, a scenario object is
        generated.

        :param new_scenario: new scenario to be added to the scenario list
        :return: scenario added
        """
        # find unique scenario name
        if new_scenario is None or new_scenario.name is None:
            scenario_name = 'scenario_0'
        else:
            scenario_name = new_scenario.name
        new_scenario_name = find_unique_name(scenario_name, list(self.scenarios.keys()))

        # create new scenario and add to project
        if new_scenario is None:
            new_scenario = Scenario(name=new_scenario_name)
        else:
            new_scenario.name = new_scenario_name

        self.scenarios[new_scenario.name] = new_scenario

        # add scenarios to install and circuits
        for install_name in self.installs.keys():
            self.installs[install_name].scenarios[new_scenario_name] = Scenario(name=new_scenario_name)
            self.installs[install_name].selected_scenario.options.append(new_scenario_name)
            for cable_set in self.installs[install_name].cable_sets:
                cable_set.scenarios[new_scenario_name] = ScenarioRating(name=scenario_name)
        for circuit_name in self.circuits.keys():
            self.circuits[circuit_name].scenarios[new_scenario_name] = ScenarioRating(name=new_scenario_name)

        return new_scenario

    def delete_scenario(self, scenario_name: str) -> Optional[Scenario]:
        """delete a scenario from a project

        Deletes a scenario from the scenario dictionary in the project. If only one scenario exists then the scenario
        is not deleted. Scenarios are also deleted from the Installation and Circuit objects.

        :param scenario_name: scenario to be deleted from the scenario list
        :return: scenario deleted or None if no scenario deleted
        """
        if len(self.scenarios) < 1:
            return None

        del_scenario = self.scenarios.pop(scenario_name, None)

        # delete scenarios from install and circuits
        if del_scenario is not None:
            for install_name in self.installs.keys():
                self.installs[install_name].scenarios.pop(scenario_name)
                self.installs[install_name].selected_scenario.options.remove(scenario_name)
                if self.installs[install_name].selected_scenario.value == scenario_name:
                    self.installs[install_name].selected_scenario.set_value(Scenario.NO_SCENARIO)
                for cable_set in self.installs[install_name].cable_sets:
                    cable_set.scenarios.pop(scenario_name)
            for circuit_name in self.circuits.keys():
                self.circuits[circuit_name].scenarios.pop(scenario_name)

        return del_scenario

    def rename_scenario(self, new_name: str, old_name: str) -> None:
        # create new scenarios dictionary with updated keys and then use this as replacement scenarios dictionary
        new_scenarios = {new_name if k == old_name else k: v for k, v in self.scenarios.items()}
        new_scenarios[new_name].name = new_name
        self.scenarios = new_scenarios

        # change scenario name in circuits
        for key, circuit_r in self.circuits.items():
            new_scenarios = {new_name if k == old_name else k: v for k, v in circuit_r.scenarios.items()}
            circuit_r.scenarios = new_scenarios

        # change scenario name in installations
        for key, install_r in self.installs.items():
            # change scenario key in installations
            new_scenarios = {new_name if k == old_name else k: v for k, v in install_r.scenarios.items()}
            new_scenarios[new_name].name = new_name
            install_r.scenarios = new_scenarios
            # change scenario name in selected_scenario and selected_scenario options
            if install_r.selected_scenario.get_value() == old_name:
                install_r.selected_scenario.set_value(new_name)
            new_options = [new_name if v == old_name else v for v in install_r.selected_scenario.options]
            install_r.selected_scenario.options = new_options

        return

    def loads_scenarios(self, serial: str, scenarios_name: str):

        if serial.startswith('<?xml version="1.0" encoding="UTF-8"?>\n'):
            serial = serial[len('<?xml version="1.0" encoding="UTF-8"?>\n'):]
        else:
            raise Exception('file read error: not an XML file')
        serial = serial.strip('')

        tag, attr_name, attr_value, serial = read_xml_tag(serial)
        if tag != 'ScenarioPack':
            raise Exception(f'file read error: file is a {tag} file, not a ScenarioPack file')

        scenarios_dict = {}
        tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)
        while tag in SCENARIO_CLASSES.keys():
            scenario, scenario_name, serial = loads_obj(serial,
                                                        load_classes=cabsys.data_classes.auto_scenario.SCENARIO_CLASSES)
            if not isinstance(scenario, Scenario):
                raise Exception('file is not a scenario')
            scenarios_dict[scenario_name] = scenario
            tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)

        if serial != '</ScenarioPack>':
            raise Exception('install serial stream load has remaining serial to decode')

        self.scenarios_name.set_value(scenarios_name)

        old_scenarios = list(self.scenarios.keys())
        for scenario_name in old_scenarios:
            self.delete_scenario(scenario_name)

        for scenario_name, scenario in scenarios_dict.items():
            self.add_scenario(scenario)

        return

    def dumps_scenarios(self) -> str:
        """Serialises all the scenarios in the project

        Serialises the scenario dictionary in the project, including all the scenarios.

        :return: string representing the scenarios
        """
        s = '<?xml version="1.0" encoding="UTF-8"?>\n'
        s = s + '<ScenarioPack>'
        # dump cables first
        for key, scenario in self.scenarios.items():
            default_o = type(scenario)()
            s = dumps_object(scenario, key, s, 1, default_o)
        s = s + '</ScenarioPack>'
        return s

    def add_cable(self, new_cable: Cable = None) -> Cable:
        """Add cable to project

        Adds a cable to the cable list in the project. If no new cable is given, a cable object is generated.

        :param new_cable: new cable to be added to the cable list
        :return: cable added
        """
        # find unique cable name
        if new_cable is None or new_cable.name is None:
            cable_name = 'cable_0'
        else:
            cable_name = new_cable.name
        new_cable_name = find_unique_name(cable_name, list(self.cables.keys()))

        # create new cable and add to project
        if new_cable is None:
            new_cable = Cable(name=new_cable_name)
        else:
            new_cable.name = new_cable_name

        self.cables[new_cable.name] = new_cable

        return new_cable

    def rename_cable(self, new_name: str, old_name: str) -> None:
        self.cables[new_name] = self.cables[old_name]
        del self.cables[old_name]

        for key, install_r in self.installs.items():
            for cable_set_r in install_r.cable_sets:
                for placed_cable_r in cable_set_r.placed_cables:
                    if placed_cable_r.cable.name == old_name:
                        placed_cable_r.cable.name = new_name
        return

    def add_current_curve(self, new_current_curve: CurrentCurve = None) -> CurrentCurve:
        """Add current_curve to project

        Adds a current_curve to the current_curve list in the project. If no new current_curve is given, a
        current_curve object is generated.

        :param new_current_curve: new current_curve to be added to the current_curve list
        :return: current_curve added
        """
        # find unique current_curve name
        if new_current_curve is None or new_current_curve.name is None:
            current_curve_name = 'current_curve_0'
        else:
            current_curve_name = new_current_curve.name
        new_current_curve_name = find_unique_name(current_curve_name, list(self.current_curves.keys()))

        # create new current_curve and add to project
        if new_current_curve is None:
            new_current_curve = CurrentCurve(name=new_current_curve_name)
        else:
            new_current_curve.name = new_current_curve_name

        self.current_curves[new_current_curve.name] = new_current_curve

        return new_current_curve

    def add_install(self, new_install: Install = None) -> Install:
        """Add installation cross-section to project

        Adds an installation cross-section to the Installs list in the project. If no new install is given, an install
        object is generated.

        :param new_install: new install to be added to the install list
        :return: install added
        """
        # find unique install name
        if new_install is None or new_install.name is None:
            install_name = 'install_0'
        else:
            install_name = new_install.name
        new_install_name = find_unique_name(install_name, list(self.installs.keys()))

        # Create cable sets in install
        if new_install is None:
            new_cable_set = CableSet()
            new_install = Install(name=new_install_name)
            new_install.cable_sets.append(new_cable_set)
        else:
            new_install.name = new_install_name

        self.installs[new_install.name] = new_install

        # add scenarios to the installation
        if new_install.scenarios is None:
            new_install.scenarios = {}
            new_install.selected_scenario.options = []
        if len(self.scenarios) > 0:
            for scenario_name in self.scenarios.keys():
                new_install.scenarios[scenario_name] = Scenario(name=scenario_name)
                new_install.selected_scenario.options.append(scenario_name)
                for cable_set in self.installs[install_name].cable_sets:
                    cable_set.scenarios[scenario_name] = ScenarioRating(name=scenario_name)

        return new_install

    def rename_install(self, new_name: str, old_name: str) -> None:
        new_installs = {}
        for install_key in self.installs.keys():
            if install_key == old_name:
                new_installs[new_name] = self.installs[old_name]
            else:
                new_installs[install_key] = self.installs[install_key]
        self.installs = new_installs

    def add_section(self, new_section: Section = None) -> Section:
        """Add section to project

        Adds a section to the section list in the project. If no new section is given, a section object is generated.

        :param new_section: new section to be added to the section list
        :return: section added
        """
        # find unique section name
        if new_section is None or new_section.name is None:
            section_name = 'section_0'
        else:
            section_name = new_section.name
        new_section_name = find_unique_name(section_name, list(self.sections.keys()))

        # create new section and add to project
        if new_section is None:
            new_section = Section(name=new_section_name)
        else:
            new_section.name = new_section_name

        self.sections[new_section.name] = new_section

        return new_section

    def add_node(self, new_node: Node = None) -> Node:
        """Add node to project

        Adds a node to the node list in the project. If no new node is given, a node object is generated.

        :param new_node: new node to be added to the node list
        :return: node added
        """
        # find unique node name
        if new_node is None or new_node.name is None:
            node_name = 'node_0'
        else:
            node_name = new_node.name
        new_node_name = find_unique_name(node_name, list(self.nodes.keys()))

        # create new node and add to project
        if new_node is None:
            new_node = Node(name=new_node_name)
        else:
            new_node.name = new_node_name

        self.nodes[new_node.name] = new_node

        return new_node

    def add_circuit(self, new_circuit: Circuit = None) -> Circuit:
        """Add circuit to project

        Adds a circuit to the circuit list in the project. If no new circuit is given, a circuit object is generated.

        :param new_circuit: new circuit to be added to the circuit list
        :return: circuit added
        """
        # find unique circuit name
        if new_circuit is None or new_circuit.name is None:
            circuit_name = 'circuit_0'
        else:
            circuit_name = new_circuit.name
        new_circuit_name = find_unique_name(circuit_name, list(self.circuits.keys()))

        # create new circuit and add to project
        if new_circuit is None:
            new_circuit = Circuit(name=new_circuit_name)
        else:
            new_circuit.name = new_circuit_name

        self.circuits[new_circuit.name] = new_circuit

        if len(self.scenarios) > 0:
            new_circuit.scenarios = {}
            for scenario_name in self.scenarios.keys():
                new_circuit.scenarios[scenario_name] = ScenarioRating(name=scenario_name)

        return new_circuit

    def dumps_project(self, name: str = ''):
        s = '<?xml version="1.0" encoding="UTF-8"?>\n'
        s = s + '<ProjectPack>\n'
        # dump scenarios
        for key, scenario in self.scenarios.items():
            default_o = type(scenario)()
            s = dumps_object(scenario, scenario.name, s, 1, default_o)
        # dump circuits
        for key, circuit in self.circuits.items():
            default_o = type(circuit)()
            s = dumps_object(circuit, circuit.name, s, 1, default_o)
        # dump cables first
        for key, cable in self.cables.items():
            default_o = type(cable)()
            s = dumps_object(cable, cable.name, s, 1, default_o)
        # dump current curves
        for key, current_curve in self.current_curves.items():
            if current_curve is not None:
                default_o = type(current_curve)()
                s = dumps_object(current_curve, current_curve.name, s, 1, default_o)
        # dump installation cross-section object
        for key, install in self.installs.items():
            default_o = type(install)()
            s = dumps_object(install, install.name, s, 1, default_o, [Cable, CurrentCurve])

        # dump project object
        default_o = type(self)()
        s = dumps_object(self, name, s, 1, default_o, [Scenario, Circuit, Cable, CurrentCurve, Install])

        s = s + '</ProjectPack>'
        return s


# classes that can be loaded
PROJECT_CLASSES = {**INSTALL_CLASSES,
                   'Project': Project}


def loads_project(serial: str, project_classes=None):

    if serial.startswith('<?xml version="1.0" encoding="UTF-8"?>\n'):
        serial = serial[len('<?xml version="1.0" encoding="UTF-8"?>\n'):]
    else:
        raise Exception('file read error: not an XML file')
    serial = serial.strip('')

    tag, attr_name, attr_value, serial = read_xml_tag(serial)
    if tag != 'ProjectPack':
        raise Exception(f'file read error: file is a {tag} file, not a Project file')

    scenario_dict = {}
    tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)
    while tag in SCENARIO_CLASSES.keys():
        scenario, scenario_name, serial = loads_obj(serial, load_classes=SCENARIO_CLASSES)
        if not isinstance(scenario, Scenario):
            raise Exception('file is not a scenario')
        scenario_dict[scenario_name] = scenario
        tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)

    circuit_dict = {}
    tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)
    while tag in CIRCUIT_CLASSES.keys():
        circuit, circuit_name, serial = loads_obj(serial, load_classes=CIRCUIT_CLASSES)
        if not isinstance(circuit, Circuit):
            raise Exception('file is not a circuit')
        circuit_dict[circuit_name] = circuit
        tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)

    cable_dict = {}
    tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)
    while tag in CABLE_CLASSES.keys():
        cable, cable_name, serial = loads_obj(serial, load_classes=CABLE_CLASSES)
        if not isinstance(cable, Cable):
            raise Exception('file is not a cable')
        cable_dict[cable_name] = cable
        tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)

    current_curve_dict = {}
    tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)
    while tag in CURRENT_CURVE_CLASSES.keys():
        current_curve, current_curve_name, serial = loads_obj(serial, load_classes=CURRENT_CURVE_CLASSES)
        if not isinstance(current_curve, CurrentCurve):
            raise Exception('file is not a current curve')
        current_curve_dict[current_curve_name] = current_curve
        tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)

    install_dict = {}
    tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)
    while tag in INSTALL_CLASSES.keys():
        install, install_name, serial = loads_obj(serial, stop_at={**cable_dict, **current_curve_dict,
                                                                   **scenario_dict, **circuit_dict},
                                                  load_classes=INSTALL_CLASSES)
        if not isinstance(install, Install):
            raise Exception('file is not an install')
        install_dict[install_name] = install
        tag, _attr_name, _attr_value, _serial = read_xml_tag(serial)

    if project_classes is None:
        project_classes = PROJECT_CLASSES

    project, project_name, serial = loads_obj(serial, stop_at={**cable_dict, **current_curve_dict,
                                                               **scenario_dict, **circuit_dict, **install_dict},
                                              load_classes=project_classes)
    if not isinstance(project, Project):
        raise Exception(f'{project_name} file is not a project')

    if serial != '</ProjectPack>':
        raise Exception('install serial stream load has remaining serial to decode')

    return scenario_dict, circuit_dict, cable_dict, current_curve_dict, install_dict, project, project_name
