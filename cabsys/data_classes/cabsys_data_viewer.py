import tkinter
from tkinter import ttk
from typing import Dict, Union, List

import cabsys.quantity.quantity_store_viewer as quant_store_viewer
from cabsys.data_classes.project import Project
from cabsys.data_classes.cable import Cable
from cabsys.data_classes.install import Install
from cabsys.data_classes.auto_install import AutoInstall
from cabsys.data_classes.auto_cable import AutoCable, DesignCableException
from cabsys.data_classes.scenario import Scenario
from cabsys.data_classes.auto_scenario import AutoScenario
from cabsys.data_classes.auto_circuit import AutoCircuit
from cabsys.data_classes.section import Section
from cabsys.data_classes.node import Node
from cabsys.data_classes.circuit import Circuit
from cabsys.data_classes.state import InstallState
from cabsys.data_classes.state_cct import InstallState as InstallStateCCT
from cabsys.data_classes.auto_current_curve import AutoCurrentCurve
from cabsys.data_classes.current_curve import CurrentCurve
from cabsys.quantity.quantity_store import QuantityBase


class CabSysDataFrame(quant_store_viewer.QuantFrame):

    def __init__(self, parent: Union[tkinter.Toplevel, tkinter.Tk, tkinter.Frame, tkinter.Tk, tkinter.PanedWindow],
                 instance: Union[Cable, AutoCable, Install, AutoInstall, Scenario, AutoScenario, Section, Node,
                                 Circuit, AutoCircuit,
                                 CurrentCurve, AutoCurrentCurve, InstallState, Project],
                 edit_name: bool = True, show_name: bool = True,
                 is_auto_design: bool = False,
                 end_attr_name: List[str] = None, end_options: Union[List[Dict[str, object]], List[None]] = None,
                 scenarios: Dict[str, Scenario] = None,
                 **kw) -> None:
        """Creates a ttk_Frame that contains a representation of a DataStore object

        Creates a frame that shows all the attributes of the given instance object. Where the attributes are quantities,
        the unit, source and description are also shown as well as the value. Where the attributes are simple Python
        classes such as Float, Strings or Integers, the value will be shown. These values can be changed by the user.

        Where an attribute is another DataStore or List, a tree view shows all these attributes. By selecting the
        DataStore or List item in the TreeView the attributes for the item in the TreeView will be shown.

        If a end_attr_name is given, the tree widget will not show the object given by name and the object will be
        shown as an attribute instead. The available options are defined in the end_options, with the key being the
        option names, and the object being the objects relating to the name.

        The name attribute can be used by other objects to identify an object and in these cases changing the name of
        the object can cause problems. By resetting edit_name or show_name to false, this allows the name either to be
        shown but not allowed to be edited, or not show the name attribute at all.

        For an installation, auto designing the scenario may need access to the available scenarios. For example
        the ambient temperature default will be contained in the named scenario. A pointer to the scenarios object
        will enable the auto design to pick out the default scenario parameter.

        :param parent:  tkinter widget parent that the data_store_ttk_frame is to be inserted into
        :param instance: DataStore object that is to be shown
        :param edit_name: allow 'name' attribute to be edited
        :param show_name: allow 'name' attribute to be shown
        :param is_auto_design: if true the DataStore object will update its design after an attribute is changed
        :param end_attr_name: a list of attribute names that stop the viewer from showing sub attributes
        :param end_options: the options to show an end attribute
        :param scenarios: scenarios available to an installation
        """

        self.scenarios = scenarios
        super().__init__(parent, instance, edit_name, show_name, is_auto_design, end_attr_name, end_options, **kw)

    def update_viewer(self, proj_scenarios: Dict[str, Scenario] = None) -> None:

        super().update_viewer()

        if isinstance(self.instance, (Project, Cable, Install, InstallState, InstallStateCCT, Scenario,
                                      Section, Node, Circuit, CurrentCurve)):
            try:
                if self.is_auto_design and isinstance(self.instance, (AutoCable, AutoCurrentCurve,
                                                                      AutoScenario, AutoCircuit, AutoInstall)):
                    if isinstance(self.instance, AutoInstall):
                        self.instance.auto_design(proj_scenarios=self.scenarios)
                    else:
                        self.instance.auto_design()
            except DesignCableException:
                # If cable design fails, the design is still safe to display so can ignore Exception
                pass
            finally:
                self.attr_frame_update(self.chosen_instance_in_tree)
        else:
            raise Exception(f'cabsys_data_viewer trying to display {type(self.instance)}')

    def attr_combobox_changed_callback2(self, _event, attr_name: str, combobox: ttk.Combobox,
                                        fixed_combobox: ttk.Combobox):
        self.combobox_key_pressed = False
        value = combobox.get()
        new_value = self.change_chosen_attr_value2(attr_name, value)

        # change value in Combobox to reflect correct value
        combobox.set(new_value)

        # changed fixed_combobox
        if isinstance(getattr(self.chosen_instance_in_tree, attr_name, None), QuantityBase):
            if self.chosen_instance_in_tree.get_source(attr_name) is None:
                fixed_combobox.set('<None>')
            else:
                fixed_combobox.set(self.chosen_instance_in_tree.get_source(attr_name))

        if self.is_auto_design and isinstance(self.instance, (AutoCable, AutoCurrentCurve, AutoScenario,
                                                              AutoCircuit, AutoInstall)):
            try:
                if isinstance(self.instance, AutoInstall):
                    self.instance.auto_design(proj_scenarios=self.scenarios)
                else:
                    self.instance.auto_design()
            finally:
                self.attr_frame_update(self.chosen_instance_in_tree)
                self.nav_tree_rebuild()
                combobox.selection_range(0, tkinter.END)
                self.event_generate("<<Q_change>>", when="tail")

        else:
            combobox.selection_range(0, tkinter.END)
            self.event_generate("<<Q_change>>", when="tail")


class _CabSysDataWindow:
    """DataStore Window

    used by data_store_show function
    """

    def __init__(self, instance, parent=None,
                 edit_name: bool = True, show_name: bool = True, is_auto_design: bool = True,
                 end_attr_name: List[str] = None, end_class_options: List[str] = None,
                 scenarios: Dict[str, Scenario] = None,):
        # work out if viewer standalone or is tkinter already running
        self.parent = parent
        self.instance = instance

        if parent is not None:
            self.top_level = tkinter.Toplevel(parent)
        else:
            self.top_level = tkinter.Tk()

        self.top_level.protocol("WM_DELETE_WINDOW", self.win_close)

        # construct title bar
        try:
            title = f'{instance.name} [{type(instance)}] - DataStore viewer'
        except AttributeError:
            title = f'[unnamed] [{type(instance)}] - DataStore viewer'
        self.top_level.title(title)
        self.top_level.columnconfigure(1, weight=1)
        self.top_level.rowconfigure(1, weight=1)
        # attr_frame = ttk.Frame(self.top_level)
        attr_frame = CabSysDataFrame(self.top_level, instance=instance,
                                     edit_name=edit_name, show_name=show_name, is_auto_design=is_auto_design,
                                     end_attr_name=end_attr_name, end_options=end_class_options,
                                     scenarios=scenarios)
        attr_frame.grid(column=1, row=1, sticky='NEWS')
        attr_frame.columnconfigure(1, weight=1)
        attr_frame.rowconfigure(1, weight=1)
        # DataStoreViewer(attr_frame, instance, cable_options, curve_options, edit_name, show_name, is_auto_design)
        self.top_level.grab_set()

    def win_close(self):
        self.top_level.destroy()


def cabsys_data_show(instance, parent=None,
                     edit_name: bool = True, show_name: bool = True, is_auto_design: bool = False,
                     scenarios: Dict[str, Scenario] = None,):
    """Show a DataStore object

    Displays a tkinter window with the details of the DataStore object. The attributes of the DataStore object can
    be modified by the user if required. If a parent tkinter window is passed the window will be a child window,
    otherwise a new tkinter root window is used.

    If a stop_at class is given, the tree widget showing attributes will not show any attributes of the child objects
    with the given class (although the object with the stop_at class will be shown. If stop_at_options are given,
    then in place of the attributes of the class, a selection of the given objects will be presented.

    The name attribute can be used by other objects to identify an object and in these cases changing the name of the
    object can cause problems. By resetting edit_name or show_name to false, this allows the name either to be shown
    but not allowed to be edited, or not show the name attribute at all.

    :param instance: Quants object that is to be shown
    :param parent:  tkinter widget parent that the data_store_ttk_frame is to be inserted into
    :param edit_name: allow 'name' attribute to be edited
    :param show_name: allow 'name' attribute to be shown
    :param is_auto_design: if True then the DataStore object will design itself each time an attribute is changed
    :param scenarios: scenarios available to an installation
    """

    dsw = _CabSysDataWindow(instance, parent, edit_name, show_name, is_auto_design, scenarios=scenarios)

    if parent is None:
        dsw.top_level.mainloop()
