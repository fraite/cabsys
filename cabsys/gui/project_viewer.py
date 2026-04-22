import csv
import tkinter
from typing import Union, Optional, cast
# from types import SimpleNamespace
from tkinter import filedialog, simpledialog, messagebox
import copy
import os
from tkinter import ttk
import threading
import inspect
import webbrowser

import cabsys
import cabsys.data_classes.auto_cable
import cabsys.data_classes.auto_current_curve
import cabsys.quantity.serialise as canning
from cabsys.quantity.quantity_store import QBool
from cabsys.top.Exception import InvalidInput, SolverException
from cabsys.data_classes.project import Project, loads_project
from cabsys.data_classes.scenario import Scenario
from cabsys.data_classes.auto_scenario import AutoScenario
from cabsys.data_classes.install import Install
from cabsys.data_classes.auto_install import AutoInstall, AutoCableSet, loads_install_sec, AutoInstallCircuit
from cabsys.data_classes.auto_install import DesignInstallException, DesignCableSetException
from cabsys.data_classes.state import InstallState
from cabsys.data_classes.state_cct import InstallState as InstallStateCCT
from cabsys.quantity.log import Log
from cabsys.data_classes.cable import Cable
from cabsys.data_classes.auto_cable import AutoCable, DesignCableException
from cabsys.data_classes.section import Section
from cabsys.data_classes.node import Node
from cabsys.data_classes.circuit import Circuit
from cabsys.data_classes.auto_circuit import AutoCircuit
from cabsys.data_classes.auto_current_curve import AutoCurrentCurve
from cabsys.data_classes.current_curve import CurrentCurve, TransientCurrentPoint
import cabsys.gui.install_overview as install_overview
import cabsys.gui.install_drawing as install_drawing
import cabsys.gui.cable_overview as cable_overview
import cabsys.gui.current_curve_overview as current_curve_overview
from cabsys.gui.result_frame import ResultFrame
import cabsys.gui.overview_widgets as overview_widgets
from cabsys.gui.transient_graph import GraphFrame
from cabsys.quantity.log_viewer import LogViewer
import cabsys.top.solver as solver
import cabsys.data_classes.cabsys_data_viewer as cabsys_data_viewer
from cabsys.quantity import quantity_constants as qc
from cabsys.quantity.quantity_store_viewer import QuantityCombobox
import cabsys.iec.iec_constants as iec
from cabsys.iec.details import results as iec_details

# TODO: implement mirrored layout
# TODO: implement circuit level data structure
# TODO: move ground temperature calculations from GUI code to IEC 60287-support
# TODO: Consider drawing the entire layout in a canvas and using tkinter scroll bars. This would need to work out view port to plot dried out zone.
# TODO: make ProjectViewer a subclass of Frame


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


class ProjectViewer:
    """Project GUI"""

    def __init__(self, project: Project):
        super().__init__()

        self.project = project
        self.rate_running = False

        self.ignore_cable_select_counter = 0
        self.displayed_object: Union[None, AutoCable, Install, AutoInstall, AutoCurrentCurve, AutoScenario,
                                     Cable, Install, CurrentCurve, Scenario, Project, Section, Node,
                                     Circuit] = None
        self.install_state = None

        self.root = tkinter.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.root.quit)
        self.root.minsize(1000, 700)

        style = ttk.Style(self.root)
        style.configure('Placeholder.TEntry', foreground='grey50')
        style.configure('Placeholder.TCombobox', foreground='grey50')
        style.configure('Placeholder.TCheckbutton', indicatorcolor='grey75')  # does not seem to do anything

        if project.name is not None:
            self.root.title(project.name)

        self.working_dir = os.getcwd()
        # self.solving_rating = False
        self.result: Optional[str] = 'no result'
        self.result_error: bool = False
        """Contains the results of the current rating calculation in a single line"""
        self.cond_thetas_list = []
        """Contains the conductor temperature (°C) for each cable following a current rating calculation"""
        self.amp_list = []
        """Contains the current (A) for each cable following in a current rating calculation"""
        self.transient_result = None
        self.message = tkinter.StringVar()
        self.after_job = None
        self.dlg = None

        self.menu_bar = tkinter.Menu(self.root)
        # project menu
        self.project_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.project_menu.add_command(label='View project', command=self.view_project)
        self.project_menu.add_command(label='Clear project', command=self.clear_project)
        self.project_menu.add_command(label='Load project', command=self.load_project)
        self.project_menu.add_command(label='Save project', command=self.save_project)
        self.project_menu.add_separator()
        # add quit
        self.project_menu.add_separator()
        self.project_menu.add_command(label='Quit', command=self.root.quit)
        self.menu_bar.add_cascade(label='Project', menu=self.project_menu)

        # scenario menu
        self.scenario_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.scenario_menu.add_command(label='New auto scenario', command=self.new_auto_scenario)
        self.scenario_menu.add_command(label='New blank auto scenario', command=self.new_blank_scenario)
        self.scenario_menu.add_command(label='New scenario', command=self.add_scenario)
        self.scenario_menu.add_separator()
        self.scenario_menu.add_command(label='Delete scenario', command=self.delete_scenario)
        self.scenario_menu.add_separator()
        self.scenario_menu.add_command(label='Load scenarios', command=self.load_scenarios)
        self.scenario_menu.add_command(label='Save scenarios', command=self.save_scenarios)
        self.scenario_menu.add_separator()
        self.scenario_menu.add_command(label='Rename', command=self.rename_scenario)
        # self.section_menu.add_command(label='Duplicate install', command=self.duplicate_install)
        # self.scenario_menu.add_separator()
        # self.section_menu.add_command(label='Delete install', command=self.delete_install)
        self.menu_bar.add_cascade(label='Scenario', menu=self.scenario_menu)
        # add project > circuit menu
        self.circuit_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.circuit_menu.add_command(label='New auto circuit', command=self.new_auto_circuit)
        self.circuit_menu.add_command(label='New blank auto circuit', command=self.new_blank_circuit)
        self.circuit_menu.add_command(label='New circuit', command=self.add_circuit)
        self.menu_bar.add_cascade(label='Circuit', menu=self.circuit_menu)

        # Install menu
        self.install_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.install_menu.add_command(label='New auto install', command=self.new_auto_install)
        self.install_menu.add_command(label='New blank auto install', command=self.new_blank_install)
        self.install_menu.add_command(label='New install', command=self.add_install)
        self.install_menu.add_separator()
        self.install_menu.add_command(label='Load install', command=self.load_install)
        self.install_menu.add_command(label='Save install', command=self.save_install)
        self.install_menu.add_separator()
        self.install_menu.add_command(label='Rename', command=self.rename_install)
        self.install_menu.add_command(label='Duplicate install', command=self.duplicate_install)
        self.install_menu.add_separator()
        self.install_menu.add_command(label='Delete install', command=self.delete_install)
        self.install_menu.add_separator()
        self.install_menu.add_command(label='Insert cable set', command=self.insert_cable_set)
        self.install_menu.add_command(label='Delete cable set', command=self.delete_cable_set)
        self.menu_bar.add_cascade(label='Install', menu=self.install_menu)
        # cable menu
        self.cable_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.cable_menu.add_command(label='New auto cable', command=self.new_auto_cable)
        self.cable_menu.add_command(label='New blank auto cable', command=self.new_blank_cable)
        self.cable_menu.add_command(label='New cable', command=self.add_cable)
        self.cable_menu.add_separator()
        self.cable_menu.add_command(label='Load cable', command=self.load_cable)
        self.cable_menu.add_command(label='Save cable', command=self.save_cable)
        self.cable_menu.add_separator()
        self.cable_menu.add_command(label='Rename cable', command=self.rename_cable)
        self.cable_menu.add_command(label='Duplicate cable', command=self.duplicate_cable)
        self.cable_menu.add_separator()
        self.cable_menu.add_command(label='Delete cable', command=self.delete_cable)
        self.menu_bar.add_cascade(label='Cable', menu=self.cable_menu)
        # current curves menu
        self.cc_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.cc_menu.add_command(label='New auto current curve', command=self.new_auto_current_curve)
        self.cc_menu.add_command(label='New blank auto current curve', command=self.new_blank_current_curve)
        self.cc_menu.add_command(label='New current curve', command=self.add_current_curve)
        self.cc_menu.add_separator()
        self.cc_menu.add_command(label='Load current curve', command=self.load_current_curve)
        self.cc_menu.add_command(label='Save current curve', command=self.save_current_curve)
        self.cc_menu.add_command(label='import current curve', command=self.import_current_curve)
        self.cc_menu.add_separator()
        # self.cc_menu.add_command(label='Rename', command=self.rename_cable)
        self.cc_menu.add_command(label='Duplicate current curve', command=self.duplicate_current_curve)
        self.cc_menu.add_separator()
        self.cc_menu.add_command(label='Delete current curve', command=self.delete_current_curve)
        self.menu_bar.add_cascade(label='Current curve', menu=self.cc_menu)
        # section menu
        self.section_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        # self.section_menu.add_command(label='New auto install', command=self.new_auto_install)
        # self.section_menu.add_command(label='New blank install', command=self.new_blank_install)
        self.section_menu.add_command(label='New section', command=self.add_section)
        # self.section_menu.add_separator()
        # self.section_menu.add_command(label='Load install', command=self.load_install)
        # self.section_menu.add_command(label='Save install', command=self.save_install)
        # self.section_menu.add_separator()
        # self.install_menu.add_command(label='Rename', command=self.rename_cable)
        # self.section_menu.add_command(label='Duplicate install', command=self.duplicate_install)
        # self.install_menu.add_separator()
        # self.section_menu.add_command(label='Delete install', command=self.delete_install)
        self.menu_bar.add_cascade(label='Section', menu=self.section_menu)
        # node menu
        self.node_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        # self.section_menu.add_command(label='New auto install', command=self.new_auto_install)
        # self.section_menu.add_command(label='New blank install', command=self.new_blank_install)
        self.node_menu.add_command(label='New node', command=self.add_node)
        # self.section_menu.add_separator()
        # self.section_menu.add_command(label='Load install', command=self.load_install)
        # self.section_menu.add_command(label='Save install', command=self.save_install)
        # self.section_menu.add_separator()
        # self.install_menu.add_command(label='Rename', command=self.rename_cable)
        # self.section_menu.add_command(label='Duplicate install', command=self.duplicate_install)
        # self.install_menu.add_separator()
        # self.section_menu.add_command(label='Delete install', command=self.delete_install)
        self.menu_bar.add_cascade(label='Node', menu=self.node_menu)
        # help menu
        self.help_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label='View Help', command=self.display_help)
        self.menu_bar.add_cascade(label='Help', menu=self.help_menu)
        # configure menu
        self.root.config(menu=self.menu_bar)

        self.application_pane = ttk.Panedwindow(self.root, orient=tkinter.HORIZONTAL)  # type: ignore[arg-type]
        self.application_pane.grid(column=1, row=1, sticky='NEWS')
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        # configure left side of screen
        left_projects_frame = ttk.Frame(self.application_pane)
        left_projects_frame.grid(column=1, row=1, sticky='NEWS')
        left_projects_frame.columnconfigure(1, weight=1)
        self.application_pane.add(left_projects_frame)

        scenario_frame = ttk.Frame(left_projects_frame)
        scenario_frame.grid(column=1, row=1, sticky='NEWS')
        scenario_frame.columnconfigure(1, weight=1)
        scenario_frame.rowconfigure(2, weight=1)
        scenario_lab = ttk.Label(scenario_frame, text='scenario:', anchor=tkinter.W)  # type: ignore[arg-type]
        scenario_lab.grid(column=1, row=1, sticky='W')
        # scenarios_name_frame = ttk.Frame(scenario_frame)
        # scenarios_name_frame.grid(column=1, row=2, sticky='NEWS')
        # scenarios_name_frame.columnconfigure(2, weight=1)
        # scenarios_name_frame.rowconfigure(2, weight=1)
        # scenarios_name_lab = ttk.Label(scenarios_name_frame, text='  name:', anchor=tkinter.W)
        # scenarios_name_lab.grid(column=1, row=2, sticky='W')
        # self.scenarios_name_string_var = tkinter.StringVar(self.root)
        # self.scenarios_name_string_var.trace_add('write', self.scenarios_name_change)
        # scenarios_name_entry = ttk.Entry(scenarios_name_frame, textvariable=self.scenarios_name_string_var)
        # scenarios_name_entry.grid(column=2, row=2, sticky='NEWS')
        self.scenario_tree = ScenarioTreeview(scenario_frame, self, takefocus=True,
                                              selectmode=tkinter.BROWSE, show='tree')
        self.scenario_tree.grid(column=1, row=4, sticky='NSEW')
        self.scenario_tree.columnconfigure(1, weight=1)
        self.scenario_tree.rowconfigure(1, weight=1)

        # self.scenario_tree.tag_bind('scenario', '<Double-1>', self.scenario_tree_select_callback)
        scenario_frame.grid(column=1, row=1, sticky='NEWS')
        # add scenarios to scenario_tree and display in edit pane
        self.scenario_tree.configure(height=len(self.project.scenarios.keys())+1)
        for name in self.project.scenarios.keys():
            self.scenario_tree.insert('', tkinter.END, name, text=name, tags='scenario')  # type: ignore[arg-type]
            self.scenario_tree.focus(name)
            self.scenario_tree.selection_set(name)

        circuit_frame = ttk.Frame(left_projects_frame)
        circuit_frame.grid(column=1, row=2, sticky='NEWS')
        circuit_frame.columnconfigure(1, weight=1)
        circuit_frame.rowconfigure(2, weight=1)
        circuit_lab = ttk.Label(circuit_frame, text='circuits:', anchor=tkinter.W)  # type: ignore[arg-type]
        circuit_lab.grid(column=1, row=1, sticky='W')
        self.circuit_tree = ttk.Treeview(circuit_frame, takefocus=True, selectmode=tkinter.BROWSE, show='tree')  # type: ignore[arg-type]
        self.circuit_tree.grid(column=1, row=2, sticky='NSEW')
        self.circuit_tree.columnconfigure(1, weight=1)
        self.circuit_tree.rowconfigure(1, weight=1)
        self.circuit_tree.tag_bind('circuit', '<Double-1>', self.circuit_tree_select_callback)
        # add circuits to circuit_tree
        self.circuit_tree.configure(height=len(self.project.circuits.keys())+1)
        for name in self.project.circuits.keys():
            self.circuit_tree.insert('', tkinter.END, name, text=name, tags='circuit')  # type: ignore[arg-type]
            self.circuit_tree.focus(name)
            self.circuit_tree.selection_set(name)

        install_frame = ttk.Frame(left_projects_frame)
        install_frame.grid(column=1, row=3, sticky='NEWS')
        install_frame.columnconfigure(1, weight=1)
        install_frame.rowconfigure(2, weight=1)
        install_lab = ttk.Label(install_frame, text='installations:', anchor=tkinter.W)  # type: ignore[arg-type]
        install_lab.grid(column=1, row=1, sticky='W')
        self.install_tree = InstallTreeview(install_frame, self, takefocus=True, selectmode=tkinter.BROWSE, show='tree')
        self.install_tree.grid(column=1, row=2, sticky='NSEW')
        self.install_tree.columnconfigure(1, weight=1)
        self.install_tree.rowconfigure(1, weight=1)
        self.install_tree.configure(height=len(self.project.installs.keys())+1)
        # left_rating_pane.add(install_frame)

        cable_frame = ttk.Frame(left_projects_frame)
        cable_frame.grid(column=1, row=4, sticky='NEWS')
        cable_frame.columnconfigure(1, weight=1)
        cable_frame.rowconfigure(2, weight=1)
        cable_lab = ttk.Label(cable_frame, text='cables:', anchor=tkinter.W)  # type: ignore[arg-type]
        cable_lab.grid(column=1, row=1, sticky='W')
        self.cable_tree = CableTreeview(cable_frame, self, takefocus=True, selectmode=tkinter.BROWSE, show='tree')
        self.cable_tree.grid(column=1, row=2, sticky='NSEW')
        self.cable_tree.columnconfigure(1, weight=1)
        self.cable_tree.rowconfigure(2, weight=1)
        self.cable_tree.configure(height=len(self.project.cables.keys())+1)
        # left_rating_pane.add(cable_frame)

        current_curve_frame = ttk.Frame(left_projects_frame)
        current_curve_frame.grid(column=1, row=5, sticky='NEWS')
        current_curve_frame.columnconfigure(1, weight=1)
        current_curve_frame.rowconfigure(2, weight=1)
        current_curve_lab = ttk.Label(current_curve_frame, text='current curves:', anchor=tkinter.W)  # type: ignore[arg-type]
        current_curve_lab.grid(column=1, row=1, sticky='W')
        self.current_curve_tree = CurrentCurveTreeview(current_curve_frame, self,
                                                       takefocus=True, selectmode=tkinter.BROWSE, show='tree')
        self.current_curve_tree.grid(column=1, row=2, sticky='NSEW')
        self.current_curve_tree.columnconfigure(1, weight=1)
        self.current_curve_tree.rowconfigure(1, weight=1)
        self.current_curve_tree.configure(height=len(self.project.current_curves.keys())+1)
        # left_rating_pane.add(current_curve_frame)

        section_frame = ttk.Frame(left_projects_frame)
        section_frame.grid(column=1, row=6, sticky='NEWS')
        section_frame.columnconfigure(1, weight=1)
        section_frame.rowconfigure(2, weight=1)
        section_lab = ttk.Label(section_frame, text='sections:', anchor=tkinter.W)  # type: ignore[arg-type]
        section_lab.grid(column=1, row=1, sticky='W')
        self.section_tree = ttk.Treeview(section_frame, takefocus=True, selectmode=tkinter.BROWSE, show='tree')  # type: ignore[arg-type]
        self.section_tree.grid(column=1, row=2, sticky='NSEW')
        self.section_tree.columnconfigure(1, weight=1)
        self.section_tree.rowconfigure(1, weight=1)
        self.section_tree.tag_bind('section', '<Double-1>', self.section_tree_select_callback)
        self.section_tree.configure(height=len(self.project.sections.keys())+1)
        # left_cim_pane.add(section_frame)

        node_frame = ttk.Frame(left_projects_frame)
        node_frame.grid(column=1, row=7, sticky='NEWS')
        node_frame.columnconfigure(1, weight=1)
        node_frame.rowconfigure(2, weight=1)
        node_lab = ttk.Label(node_frame, text='node:', anchor=tkinter.W)  # type: ignore[arg-type]
        node_lab.grid(column=1, row=1, sticky='W')
        self.node_tree = ttk.Treeview(node_frame, takefocus=True, selectmode=tkinter.BROWSE, show='tree')  # type: ignore[arg-type]
        self.node_tree.grid(column=1, row=2, sticky='NSEW')
        self.node_tree.columnconfigure(1, weight=1)
        self.node_tree.rowconfigure(1, weight=1)
        self.node_tree.tag_bind('node', '<Double-1>', self.node_tree_select_callback)
        self.node_tree.configure(height=len(self.project.nodes.keys())+1)
        # left_cim_pane.add(node_frame)

        # configure frame for editing objects

        self.edit_frame = ttk.Frame(self.application_pane, relief=tkinter.GROOVE, borderwidth=2)  # type: ignore[arg-type]
        self.edit_frame.grid(column=1, row=1, sticky='NEWS')
        self.edit_frame.columnconfigure(1, weight=1)
        self.edit_frame.rowconfigure(1, weight=1)
        self.application_pane.add(self.edit_frame, weight=1)

        # check to see if forgetting and re-adding panes works
        # m1.forget(left_rating_pane)
        # m1.forget(edit_frame)
        # m1.add(left_rating_pane)
        # m1.add(edit_frame)

        for cable_key, cable_item in project.cables.items():
            self.cable_tree.insert('', tkinter.END, cable_key, text=cable_key, tags='cable')  # type: ignore[arg-type]
        self.cable_tree.configure(height=len(self.project.cables.keys())+1)
        for install_key, install_item in project.installs.items():
            self.install_tree.insert('', tkinter.END, install_key, text=install_key, tags='install')  # type: ignore[arg-type]
        self.install_tree.configure(height=len(self.project.installs.keys())+1)
        for circuit_key, circuit_item in project.circuits.items():
            self.current_curve_tree.insert('', tkinter.END, circuit_key, text=circuit_key, tags='circuit')  # type: ignore[arg-type]
        self.current_curve_tree.configure(height=len(self.project.current_curves.keys())+1)

        self.auto_design = tkinter.BooleanVar()
        self.auto_design.set(False)
        self.auto_design.trace_add('write', self.auto_design_callback)

        self.obj_name = tkinter.StringVar()
        self.obj_name.set('blank')
        # self.obj_name.trace('w', self.name_change_callback)

        self.dsf_frame = tkinter.Frame(self.edit_frame)
        self.dsf_obj_frame = None
        self.dsf_name_frame = None
        self.show_displayed_object()

        self.log_frame: Optional[Union[cabsys_data_viewer.CabSysDataFrame, LogViewer]] = None
        self.dsf_state2_frame: Optional[cabsys_data_viewer.CabSysDataFrame] = None

        tkinter.mainloop()

    # def scenarios_name_change(self, var, index, mode):
    #     self.project.scenarios_name.set_value(self.scenarios_name_string_var.get())

    def scenario_tree_select_callback(self, _event):
        self.displayed_object = self.project.scenarios[self.scenario_tree.focus()]
        self.show_displayed_object()

    def cable_tree_select_callback(self, _event):
        # if new cable is created for a new install then don't react to tree select
        if self.ignore_cable_select_counter > 0:
            self.ignore_cable_select_counter = self.ignore_cable_select_counter - 1
            return
        self.displayed_object = self.project.cables[self.cable_tree.focus()]
        self.show_displayed_object()

    def install_tree_select_callback(self, _event):
        # self.displayed_object = self.project.installs[self.install_tree.focus()]
        self.show_displayed_object(self.project.installs[self.install_tree.focus()])
        if self.displayed_object.config.auto_calc.value:
            self.rate()

    def current_curves_tree_select_callback(self, _event):
        self.displayed_object = self.project.current_curves[self.current_curve_tree.focus()]
        self.show_displayed_object()

    def section_tree_select_callback(self, _event):
        self.displayed_object = self.project.sections[self.section_tree.focus()]
        self.show_displayed_object()

    def node_tree_select_callback(self, _event):
        self.displayed_object = self.project.nodes[self.node_tree.focus()]
        self.show_displayed_object()

    def circuit_tree_select_callback(self, _event):
        self.displayed_object = self.project.circuits[self.circuit_tree.focus()]
        self.show_displayed_object()

    def view_project(self) -> None:
        """View project

        View the project

        :return: none
        """

        self.displayed_object = self.project
        self.show_displayed_object()

        return

    def clear_project(self, check=True):

        if check:
            are_you_sure = messagebox.askyesno(
                title='Clear Project',
                message='Are you sure you want to delete this project?'
            )
        else:
            are_you_sure = True

        if not are_you_sure:
            return

        self.project.clear_project()

        for child_id in self.scenario_tree.get_children():
            self.scenario_tree.delete(child_id)
        for child_id in self.circuit_tree.get_children():
            self.circuit_tree.delete(child_id)
        for child_id in self.install_tree.get_children():
            self.install_tree.delete(child_id)
        for child_id in self.cable_tree.get_children():
            self.cable_tree.delete(child_id)
        for child_id in self.current_curve_tree.get_children():
            self.current_curve_tree.delete(child_id)
        for child_id in self.section_tree.get_children():
            self.section_tree.delete(child_id)
        for child_id in self.node_tree.get_children():
            self.node_tree.delete(child_id)

        self.view_project()

    def save_project(self):
        save_project = self.project
        save_name: str = filedialog.asksaveasfilename(initialdir=self.working_dir, title='Save file',
                                                      filetypes=(('xml files', "*.xml"), ('all files', '*.*')),
                                                      initialfile=save_project.name, defaultextension='.xml')
        if save_name is None or save_name == '':
            return

        # make the save directory the new default working directory
        save_dir = save_name.rpartition('/')
        self.working_dir = save_dir[0]
        # add the .xml suffix, if required
        if save_name.partition('.')[1] != '.':
            save_name = save_name + '.xml'
        # save selected installation
        serial = save_project.dumps_project(name=save_project.name)
        with open(save_name, 'w', encoding='utf-8') as save_file:
            save_file.write(serial)

    def load_project(self):
        load_name: str = filedialog.askopenfilename(initialdir=self.working_dir, title='Load file',
                                                    filetypes=(('xml files', "*.xml"), ('all files', '*.*')))
        if load_name == '':
            return

        self.clear_project(check=False)

        # make the load directory the new default working directory
        load_dir = load_name.rpartition('/')
        self.working_dir = load_dir[0]
        # load the selected file and add it to cables list
        with open(load_name, 'r', encoding='utf-8') as load_file:
            serial = ''
            for line in load_file:
                serial = serial + line
        new_scenarios, new_circuits, new_cables, new_current_curves, new_installs, proj, _name = loads_project(serial)

        for key, scenario in new_scenarios.items():
            self.add_scenario(new_scenario=scenario)

        for key, circuit in new_circuits.items():
            self.add_circuit(new_circuit=circuit)

        for key, cable in new_cables.items():
            self.new_auto_cable(new_cable=cable)

        for key, current_curve in new_current_curves.items():
            self.new_auto_current_curve(new_current_curve=current_curve)

        for key, install in new_installs.items():
            self.add_install(new_install=install)

        self.project = proj

        self.view_project()

    def new_blank_scenario(self) -> None:
        """Add blank auto scenario to project

        Adds a new blank auto scenario to the project and updates viewer.

        :return: None
        """

        self.new_auto_scenario(auto=False)

    def new_auto_scenario(self, new_scenario: Scenario = None, auto: bool = True):
        """Add auto scenario to project

        Adds a scenario to the project and updates viewer. If no scenario is given a new scenario
        is generated.

        :param new_scenario: new scenario to be added to project
        :param auto: does the new scenario have automatic design turned on
        :return: new scenario name
        """

        if new_scenario is None:
            new_scenario = AutoScenario()
            new_scenario.name = "scenario_0"
            new_scenario.set_auto_design(auto)

        added_scenario_name = self.add_scenario(new_scenario)
        return added_scenario_name

    def add_scenario(self, new_scenario: Scenario = None) -> str:
        """Add scenario to project

        Adds a scenario to the project and updates viewer. If no scenario is given a new scenario is generated.

        :param new_scenario: new scenario to be added to project
        :return: new scenario name
        """
        new_scenario = self.project.add_scenario(new_scenario)

        # add scenario to scenario_tree and display in edit pane
        self.scenario_tree.insert('', tkinter.END, new_scenario.name, text=new_scenario.name, tags='scenario')  # type: ignore[arg-type]
        self.scenario_tree.focus(new_scenario.name)
        self.scenario_tree.selection_set(new_scenario.name)

        self.displayed_object = self.project.scenarios[self.scenario_tree.focus()]
        self.scenario_tree.configure(height=len(self.project.scenarios.keys()) + 1)
        self.show_displayed_object()

        return new_scenario.name

    def delete_scenario(self) -> None:
        """Delete scenario from a project

        Deletes a scenario to the project and updates viewer. If only one scenario exists, then the scenario will not
        be deleted and a message will be displayed instead. Scenarios will also be deleted from Install and Circuit
        objects.

        :return: None
        """
        if len(self.project.scenarios) < 1:
            tkinter.messagebox.showwarning('Delete Scenario', 'Must be at least one scenario in project')
            return
        scenario_name = self.scenario_tree.focus()

        del_scenario = self.project.delete_scenario(scenario_name)

        if del_scenario is not None:
            # delete scenario to scenario_tree
            focus_scenario_iid = self.scenario_tree.next(scenario_name)
            if focus_scenario_iid == '':
                focus_scenario_iid = self.scenario_tree.prev(scenario_name)

            self.scenario_tree.configure(height=len(self.project.scenarios.keys()) + 1)
            self.scenario_tree.focus(focus_scenario_iid)
            self.scenario_tree.selection_set(focus_scenario_iid)
            self.scenario_tree.delete(scenario_name)

            if focus_scenario_iid != '':
                self.displayed_object = self.project.scenarios[focus_scenario_iid]
            else:
                self.displayed_object = None
            self.show_displayed_object()
        else:
            tkinter.messagebox.showwarning('Delete Scenario', f'Problem deleting scenario {scenario_name}')

        return

    def load_scenarios(self):
        load_name: str = filedialog.askopenfilename(initialdir=self.working_dir, title='Load file',
                                                    filetypes=(('xml files', "*.xml"), ('all files', '*.*')))
        if load_name == '':
            return
        # make the load directory the new default working directory
        load_dir = load_name.rpartition('/')
        self.working_dir = load_dir[0]
        # load the selected file and add it to cables list
        with open(load_name, 'r', encoding='utf-8') as load_file:
            serial = ''
            for line in load_file:
                serial = serial + line

        self.project.loads_scenarios(serial, load_dir[2])

        # delete existing scenarios from the scenario_tree
        for item in self.scenario_tree.get_children():
            self.scenario_tree.delete(item)

        # add scenario to scenario_tree and display in edit pane
        key = None
        for key in self.project.scenarios.keys():
            self.scenario_tree.insert('', tkinter.END, key, text=key, tags='scenario')  # type: ignore[arg-type]

        if key is not None:
            self.scenario_tree.focus(key)
            self.scenario_tree.selection_set(key)
            self.displayed_object = self.project.scenarios[self.scenario_tree.focus()]
            self.scenario_tree.configure(height=len(self.project.scenarios.keys()) + 1)
        else:
            self.displayed_object = None

        self.show_displayed_object()

    def rename_scenario(self):
        rename_scenario = self.project.scenarios[self.scenario_tree.focus()]
        new_name = simpledialog.askstring("Rename scenario", "New scenario name?",
                                          initialvalue=rename_scenario.name)
        if new_name is None:
            return
        old_name = rename_scenario.name
        if new_name == old_name:
            return
        for scenario_r in self.project.scenarios:
            if scenario_r == new_name:
                messagebox.showerror("Rename scenario", f"Cannot rename scenario to {new_name} \n"
                                     f" as name already being used in project")
                return
        # rename_scenario.name = new_name
        self.project.rename_scenario(new_name, old_name)
        scenario_index = self.scenario_tree.index(self.scenario_tree.focus())
        self.scenario_tree.insert('', scenario_index, new_name, text=new_name, tags='scenario')
        self.scenario_tree.delete(old_name)
        self.scenario_tree.focus(new_name)
        self.scenario_tree.selection_set(new_name)
        self.show_displayed_object()

    def save_scenarios(self):
        initial_save_name_abs = self.project.scenarios_name.get_value()
        if initial_save_name_abs is None:
            initial_save_name = 'Scenarios'
        else:
            initial_save_dir = initial_save_name_abs.rpartition('/')
            self.working_dir = initial_save_dir[0]
            initial_save_name = initial_save_dir[2]
        save_name: str = filedialog.asksaveasfilename(initialdir=self.working_dir, title='Save file',
                                                      filetypes=(('xml files', "*.xml"), ('all files', '*.*')),
                                                      initialfile=initial_save_name, defaultextension='.inst')
        if save_name is None or save_name == '':
            return

        # make the save directory the new default working directory
        save_dir = save_name.rpartition('/')
        self.working_dir = save_dir[0]
        # add the .inst suffix, if required
        if save_name.partition('.')[1] != '.':
            save_name = save_name + '.xml'
        serial = self.project.dumps_scenarios()
        with open(save_name, 'w', encoding='utf-8') as save_file:
            save_file.write(serial)
        self.project.scenarios_name.set_value(value=save_name)

    def add_install(self, new_install: Install = None) -> str:
        """Add installation to project

        Adds an installation cross-section to the project and updates viewer. If no installation is given a new
        installation is generated.

        :param new_install: new installation to be added to project
        :return: new installation name
        """
        new_install = self.project.add_install(new_install)
        # add install to install_tree and display in edit pane
        self.install_tree.insert('', tkinter.END, new_install.name, text=new_install.name, tags='install')  # type: ignore[arg-type]
        self.install_tree.focus(new_install.name)
        self.install_tree.selection_set(new_install.name)
        self.install_tree.configure(height=len(self.project.installs.keys())+1)

        try:
            if isinstance(new_install, AutoInstall):
                new_install.auto_design(proj_scenarios=self.project.scenarios)
        finally:
            self.displayed_object = self.project.installs[self.install_tree.focus()]
            self.show_displayed_object()
            # self.left_notebook.select(1)

        return new_install.name

    def new_blank_install(self):
        new_cable_set = AutoCableSet()
        new_install = AutoInstall()
        # new_install.auto_number_sets = 1
        new_install.cable_sets.append(new_cable_set)
        new_install.set_auto_design(False)
        self.add_install(new_install)

    def duplicate_install(self):
        new_install = copy.deepcopy(self.project.installs[self.install_tree.focus()])
        self.add_install(new_install)

    def rename_install(self):
        rename_install = self.project.installs[self.install_tree.focus()]
        new_name = simpledialog.askstring("Rename installation", "New installation name?",
                                          initialvalue=rename_install.name, parent=self.root)
        if new_name is None:
            return
        old_name = rename_install.name
        if new_name == old_name:
            return
        for install_r in self.project.installs:
            if install_r == new_name:
                messagebox.showerror("Rename installation", f"Cannot rename installation to {new_name} \n"
                                     f" as name already being used in project")
                return
        rename_install.name = new_name
        self.project.rename_install(new_name, old_name)
        install_index = self.install_tree.index(self.install_tree.focus())
        self.install_tree.insert('', install_index, new_name, text=new_name, tags='install')
        self.install_tree.delete(old_name)
        self.install_tree.focus(new_name)
        self.install_tree.selection_set(new_name)
        self.show_displayed_object()

    def new_auto_install(self):
        if self.cable_tree.focus() == '':
            cable_name = self.new_auto_cable()
            # self.ignore_cable_select_counter = self.ignore_cable_select_counter + 1
        else:
            cable_name = self.cable_tree.focus()
        new_cable_set = AutoCableSet()
        new_cable_set.auto_cable = self.project.cables[cable_name]
        new_cable_set.auto_cable_source = 'new install'
        new_cable_set.auto_follow_set = QBool(False)
        # if self.scenario_tree.focus() == "":
        #     scenario_name = self.add_scenario()
        # else:
        #     scenario_name = self.scenario_tree.focus()

        new_install_cable_set = AutoCableSet()
        new_install_cable_set.auto_cable = self.project.cables[cable_name]
        new_install_cable_set.auto_cable_source = 'new install'
        new_install_circuit = AutoInstallCircuit()
        new_install_circuit.auto_number_sets.set_value(1, source=None)
        new_install_circuit.cable_sets.append(new_install_cable_set)

        new_install = AutoInstall()
        new_install.auto_number_sets.set_value(1, source=None)
        new_install.cable_sets.append(new_cable_set)
        # new_install.scenarios[scenario_name] = self.project.scenarios[scenario_name]
        new_install.auto_number_circuits.set_value(1, source=None)
        new_install.install_circuits.append(new_install_circuit)

        new_install.set_auto_design(True)
        self.add_install(new_install)

    def delete_install(self):
        if len(self.project.installs) < 1:
            tkinter.messagebox.showwarning('Delete Install', 'No installation cross-section in project')
            return
        deleted_install_iid = self.install_tree.focus()
        # check installation not used
        sections = list(self.project.sections.values())
        for section in sections:
            if deleted_install_iid == section.install.name:
                tkinter.messagebox.showwarning('Delete Install', 'Unable to delete as installation being used')
                return

        # delete installation from install_tree
        focus_install_iid = self.install_tree.next(deleted_install_iid)
        if focus_install_iid == '':
            focus_install_iid = self.install_tree.prev(deleted_install_iid)

        self.install_tree.focus(focus_install_iid)
        self.install_tree.selection_set(focus_install_iid)
        self.install_tree.delete(deleted_install_iid)

        if focus_install_iid == '':
            focus_cable_iid = self.cable_tree.focus()
            if focus_cable_iid == '':
                self.displayed_object = None
            else:
                self.displayed_object = self.project.cables[focus_cable_iid]
            self.show_displayed_object()

        del self.project.installs[deleted_install_iid]

        # display selected installation (in case the selected install was the deleted install and selection has changed)
        install_tree_focus = self.install_tree.focus()
        if install_tree_focus != '':
            self.displayed_object = self.project.installs[self.install_tree.focus()]
            self.show_displayed_object()
        self.install_tree.configure(height=len(self.project.installs.keys())+1)

    def insert_cable_set(self):
        if len(self.project.installs) < 1:
            tkinter.messagebox.showwarning('Add Cable Set', 'No installation in project')
            return
        dialog = InsertCableSet(self.root, self)
        self.root.wait_window(dialog)

    def delete_cable_set(self):
        if len(self.project.installs) < 1:
            tkinter.messagebox.showwarning('Delete Cable Set', 'No installation in project')
            return
        install_iid = self.install_tree.focus()
        if len(self.project.installs[install_iid].cable_sets) < 2:
            tkinter.messagebox.showwarning('Delete Cable Set', 'Only 1 cable set in installation')
            return
        dialog = DeleteCableSet(self.root, self)
        self.root.wait_window(dialog)

    def save_install(self):
        save_install = self.project.installs[self.install_tree.focus()]
        save_name: str = filedialog.asksaveasfilename(initialdir=self.working_dir, title='Save file',
                                                      filetypes=(('xml files', "*.xml"), ('all files', '*.*')),
                                                      initialfile=save_install.name, defaultextension='.inst')
        if save_name is None or save_name == '':
            return

        # make the save directory the new default working directory
        save_dir = save_name.rpartition('/')
        self.working_dir = save_dir[0]
        # add the .inst suffix, if required
        if save_name.partition('.')[1] != '.':
            save_name = save_name + '.xml'
        # save selected installation
        serial = save_install.dumps_install(name=save_install.name)
        with open(save_name, 'w', encoding='utf-8') as save_file:
            save_file.write(serial)

    def load_install(self):
        load_name: str = filedialog.askopenfilename(initialdir=self.working_dir, title='Load file',
                                                    filetypes=(('xml files', "*.xml"), ('all files', '*.*')))
        if load_name == '':
            return
        # make the load directory the new default working directory
        load_dir = load_name.rpartition('/')
        self.working_dir = load_dir[0]
        # load the selected file and add it to cables list
        with open(load_name, 'r', encoding='utf-8') as load_file:
            serial = ''
            for line in load_file:
                serial = serial + line
        new_cable_dict, new_current_curve_dict, new_install, _name = loads_install_sec(serial)

        for key, cable in new_cable_dict.items():
            self.new_auto_cable(new_cable=cable)

        for key, current_curve in new_current_curve_dict.items():
            self.new_auto_current_curve(new_current_curve=current_curve)

        new_scenarios = {}
        for scenario_name in new_install.scenarios.keys():
            if scenario_name == Scenario.NO_SCENARIO or scenario_name in self.project.scenarios.keys():
                new_scenarios[scenario_name] = new_install.scenarios[scenario_name]
        new_install.scenarios = new_scenarios

        self.add_install(new_install=new_install)

    def add_cable(self, new_cable: Cable = None) -> str:
        """Add cable to project

        Adds a cable to the project and updates viewer. If no cable is given a new cable is generated.

        :param new_cable: new cable to be added to project
        :return: new cable name
        """
        new_cable = self.project.add_cable(new_cable)
        # add cable to cable_tree and display in edit pane
        self.cable_tree.insert('', tkinter.END, new_cable.name, text=new_cable.name, tags='cable')  # type: ignore[arg-type]
        self.cable_tree.focus(new_cable.name)
        self.cable_tree.selection_set(new_cable.name)
        self.cable_tree.configure(height=len(self.project.cables.keys())+1)

        self.displayed_object = self.project.cables[self.cable_tree.focus()]
        self.show_displayed_object()
        # self.left_notebook.select(1)

        return new_cable.name

    def new_auto_cable(self, new_cable: Cable = None, auto: bool = True) -> str:
        """Add auto cable to project

        Adds a cable to the project and updates viewer. If no cable is given a new auto cable is generated.

        :param new_cable: new cable to be added to project
        :param auto: does the new cable have automatic design turned on
        :return: new cable name
        """

        if new_cable is None:
            new_cable = cabsys.AutoCable()
            new_cable.name = 'cable_0'
            new_cable.set_auto_design(auto)

        added_cable_name = self.add_cable(new_cable)

        return added_cable_name

    def new_blank_cable(self) -> None:
        """Add blank auto cable to project

        Adds a new blank auto cable to the project and updates viewer.

        :return: None
        """

        self.new_auto_cable(auto=False)

    def duplicate_cable(self) -> None:
        """Copy cable selected to new cable

        Copies selected cable to a new cable object

        :return: None
        """
        if len(self.project.cables) < 1:
            tkinter.messagebox.showwarning('Copy Cable', 'No cable in project')
            return
        cable_name = self.project.cables[self.cable_tree.focus()].name
        new_cable_name = find_unique_name(cable_name, list(self.project.cables.keys()))
        new_cable = copy.deepcopy(self.project.cables[self.cable_tree.focus()])
        new_cable.name = new_cable_name
        self.new_auto_cable(new_cable=new_cable)

    def delete_cable(self) -> None:
        """Delete selected cable from poject

        :return: None
        """
        if len(self.project.cables) < 1:
            tkinter.messagebox.showwarning('Delete Cable', 'No cable in project')
            return
        deleted_cable_iid = self.cable_tree.focus()
        # check cable not used
        installs = list(self.project.installs.values())
        for install in installs:
            for cable_set in install.cable_sets:
                for placed_cable in cable_set.placed_cables:
                    if deleted_cable_iid == placed_cable.cable.name:
                        tkinter.messagebox.showwarning('Delete Cable', 'Unable to delete as cable being used')
                        return

        # delete cable from cable_tree
        focus_cable_iid = self.cable_tree.next(deleted_cable_iid)
        if focus_cable_iid == '':
            focus_cable_iid = self.cable_tree.prev(deleted_cable_iid)

        self.cable_tree.focus(focus_cable_iid)
        self.cable_tree.selection_set(focus_cable_iid)
        self.cable_tree.delete(deleted_cable_iid)

        if focus_cable_iid == '':
            focus_install_iid = self.install_tree.focus()
            if focus_install_iid == '':
                self.displayed_object = None
            else:
                self.displayed_object = self.project.installs[focus_cable_iid]
            self.show_displayed_object()

        del self.project.cables[deleted_cable_iid]
        # display selected cable (in case selected cable was the deleted cable and selection has changed)
        cable_tree_focus = self.cable_tree.focus()
        if cable_tree_focus != '':
            self.displayed_object = self.project.cables[self.cable_tree.focus()]
            self.show_displayed_object()

        self.cable_tree.configure(height=len(self.project.cables.keys())+1)

    def save_cable(self):
        save_cable = self.project.cables[self.cable_tree.focus()]
        save_name: str = filedialog.asksaveasfilename(initialdir=self.working_dir, title='Save file',
                                                      filetypes=(('xml files', "*.xml"), ('all files', '*.*')),
                                                      initialfile=save_cable.name, defaultextension='.xml')
        if save_name is None or save_name == '':
            return
        # make the save directory the new default working directory
        save_dir = save_name.rpartition('/')
        self.working_dir = save_dir[0]
        # add the .cabs suffix, if required
        if save_name.partition('.')[1] != '.':
            save_name = save_name + '.xml'
        # save selected cable
        serial = canning.dumps(save_cable, name=save_cable.name)
        with open(save_name, 'w', encoding='utf-8') as save_file:
            save_file.write(serial)

    def load_cable(self):
        load_name: str = filedialog.askopenfilename(initialdir=self.working_dir, title='Load file',
                                                    filetypes=(('xml files', "*.xml"), ('all files', '*.*')))
        if load_name == '':
            return
        # make the load directory the new default working directory
        load_dir = load_name.rpartition('/')
        self.working_dir = load_dir[0]
        # load the selected file and add it to cables list
        with open(load_name, 'r', encoding='utf-8') as load_file:
            serial = ''
            for line in load_file:
                serial = serial + line
        new_cable, _name, _remaining_serial = cabsys.data_classes.auto_cable.loads_auto_cable(serial)

        self.new_auto_cable(new_cable=new_cable)

    def rename_cable(self):
        rename_cable = self.project.cables[self.cable_tree.focus()]
        new_name = simpledialog.askstring("Rename cable", "New cable name?",
                                          initialvalue=rename_cable.name, parent=self.root)
        if new_name is None:
            return
        old_name = rename_cable.name
        if new_name == old_name:
            return
        for cable_r in self.project.cables:
            if cable_r == new_name:
                messagebox.showerror("Rename cable", f"Cannot rename cable to {new_name} \n"
                                     f" as name already being used in project")
                return
        rename_cable.name = new_name
        self.project.rename_cable(new_name, old_name)
        cable_index = self.cable_tree.index(self.cable_tree.focus())
        self.cable_tree.insert('', cable_index, new_name, text=new_name, tags='cable')
        self.cable_tree.delete(old_name)
        self.cable_tree.focus(new_name)
        self.cable_tree.selection_set(new_name)
        self.show_displayed_object()

    def add_section(self, new_section: Section = None) -> str:
        """Add section to project

        Adds a section to the project and updates viewer. If no section is given a new section is generated.

        :param new_section: new section to be added to project
        :return: new section name
        """
        new_section = self.project.add_section(new_section)
        if self.install_tree.focus() == '':
            pass
        else:
            install_name = self.install_tree.focus()
            new_section.install = self.project.installs[install_name]
            new_section.config_connections()

        # add section to section_tree and display in edit pane
        self.section_tree.insert('', tkinter.END, new_section.name, text=new_section.name, tags='section')  # type: ignore[arg-type]
        self.section_tree.focus(new_section.name)
        self.section_tree.selection_set(new_section.name)

        self.displayed_object = self.project.sections[self.section_tree.focus()]
        self.show_displayed_object()
        self.section_tree.configure(height=len(self.project.sections.keys())+1)
        # self.left_notebook.select(1)

        return new_section.name

    def add_node(self, new_node: Node = None) -> str:
        """Add node to project

        Adds a node to the project and updates viewer. If no node is given a new node is generated.

        :param new_node: new node to be added to project
        :return: new node name
        """
        new_node = self.project.add_node(new_node)

        # add node to node_tree and display in edit pane
        self.node_tree.insert('', tkinter.END, new_node.name, text=new_node.name, tags='node')  # type: ignore[arg-type]
        self.node_tree.focus(new_node.name)
        self.node_tree.selection_set(new_node.name)

        self.displayed_object = self.project.nodes[self.node_tree.focus()]
        self.show_displayed_object()
        self.node_tree.configure(height=len(self.project.nodes.keys()) + 1)

        return new_node.name

    def add_circuit(self, new_circuit: Circuit = None) -> str:
        """Add circuit to project

        Adds a circuit to the project and updates viewer. If no circuit is given a new circuit is generated.

        :param new_circuit: new circuit to be added to project
        :return: new circuit name
        """
        new_circuit = self.project.add_circuit(new_circuit)

        # add circuit to circuit_tree and display in edit pane
        self.circuit_tree.insert('', tkinter.END, new_circuit.name, text=new_circuit.name, tags='circuit')  # type: ignore[arg-type]
        self.circuit_tree.configure(height=len(self.project.circuits.keys()) + 1)
        self.circuit_tree.focus(new_circuit.name)
        self.circuit_tree.selection_set(new_circuit.name)

        self.displayed_object = self.project.circuits[self.circuit_tree.focus()]
        self.show_displayed_object()

        return new_circuit.name

    def new_blank_circuit(self) -> None:
        """Add blank auto circuit to project

        Adds a new blank auto circuit to the project and updates viewer.

        :return: None
        """

        self.new_auto_circuit(auto=False)

    def new_auto_circuit(self, new_circuit: Circuit = None, auto: bool = True):
        """Add auto circuit to project

        Adds a circuit to the project and updates viewer. If no circuit is given a new auto circuit
        is generated.

        :param new_circuit: new current curve to be added to project
        :param auto: does the new current curve have automatic design turned on
        :return: new circuit name
        """

        if new_circuit is None:
            new_circuit = AutoCircuit()
            new_circuit.name = "circuit_0"
            new_circuit.set_auto_design(auto)

        added_circuit_name = self.add_circuit(new_circuit)
        return added_circuit_name

    def display_help(self):
        cabsys_path = os.path.dirname(inspect.getfile(cabsys))  # + r'\docs\todo.html'
        cabsys3_path = os.path.realpath(cabsys_path + r"\..")
        widget = self.root.focus_get()
        if isinstance(widget, (cabsys.gui.overview_widgets.EntryInt,
                               cabsys.gui.overview_widgets.ComboboxString,
                               cabsys.gui.overview_widgets.ComboboxBool,
                               cabsys.gui.overview_widgets.CheckbuttonBool,
                               QuantityCombobox)):
            help_id = widget.get_quantity().help_id
            if help_id is not None:
                webbrowser.open('file:///' + os.path.realpath(cabsys3_path) + r'\docs\context_help'"\\" +
                                help_id + '.html', new=1)
            else:
                tkinter.messagebox.showwarning('Context Help',
                                               f'Sorry, no context help for "{widget.get_quantity().symbol}"'
                                               f' ({widget.get_quantity().description})')
        else:
            tkinter.messagebox.showwarning('Context Help',
                                           f'Sorry, no context help available. Select an input.')

    def auto_design_callback(self, _var, _index, _mode):
        if not isinstance(self.displayed_object, (AutoCable, AutoInstall, AutoCurrentCurve, AutoScenario, AutoCircuit)):
            return
        self.displayed_object.set_auto_design(self.auto_design.get())
        try:
            if self.displayed_object.is_auto_design():
                if isinstance(self.displayed_object, AutoInstall):
                    self.displayed_object.auto_design(proj_scenarios=self.project.scenarios)
                else:
                    self.displayed_object.auto_design()
        finally:
            self.update_cab_sys_tabs(None)
        # self.display_object()

    def show_displayed_object(self,
                              display_object: Union[None, AutoCable, Install, AutoInstall, AutoCurrentCurve,
                                                    AutoScenario, AutoCircuit] = 'empty'):

        if display_object != 'empty':
            self.displayed_object = display_object

        if isinstance(self.displayed_object, Install):
            self.install_menu.entryconfig('Insert cable set', state=tkinter.NORMAL)
        else:
            self.install_menu.entryconfig('Insert cable set', state=tkinter.DISABLED)

        if isinstance(self.displayed_object, Install):    # and len(self.displayed_object.cable_sets) > 1
            self.install_menu.entryconfig('Delete cable set', state=tkinter.NORMAL)
        else:
            self.install_menu.entryconfig('Delete cable set', state=tkinter.DISABLED)

        self.dsf_frame.destroy()
        self.dsf_frame = tkinter.Frame(self.edit_frame, width=1200)
        self.dsf_frame.grid(column=1, row=1, sticky='NEWS')
        self.dsf_frame.columnconfigure(1, weight=1)
        self.dsf_frame.rowconfigure(1, weight=1)

        if self.displayed_object is None:
            return

        self.dsf_name_frame = tkinter.Frame(self.dsf_frame)
        dsf_class_label = tkinter.Label(self.dsf_name_frame,
                                        text=str(type(self.displayed_object)).split('.')[-1][:-2])
        dsf_class_label.grid(column=1, row=1)
        tkinter.Label(self.dsf_name_frame, text='name').grid(column=2, row=1)
        entry = tkinter.Entry(self.dsf_name_frame, textvariable=self.obj_name, state=tkinter.DISABLED)  # type: ignore[arg-type]
        entry.grid(column=3, row=1, sticky='EW')
        self.status_label = tkinter.Label(self.dsf_name_frame, text='result')
        self.status_label.grid(column=4, row=1)
        self.rate_button = tkinter.Button(self.dsf_name_frame, text='rate', command=self.rate_button_callback)
        self.rate_button.grid(column=5, row=1)
        auto_checkbutton = tkinter.Checkbutton(self.dsf_name_frame, text='auto design', variable=self.auto_design)
        if not isinstance(self.displayed_object, (AutoCable, AutoInstall, AutoCurrentCurve, AutoScenario, AutoCircuit)):
            auto_checkbutton.config(state='disabled')
        auto_checkbutton.grid(column=6, row=1, sticky='W')
        self.dsf_name_frame.grid(column=1, row=0, sticky='EW')
        self.dsf_name_frame.columnconfigure(3, weight=1)

        self.dsf_notebook = ttk.Notebook(self.dsf_frame)
        self.dsf_notebook.grid(column=1, row=1, sticky='NSEW')
        self.dsf_notebook.columnconfigure(1, weight=1)
        self.dsf_notebook.rowconfigure(1, weight=1)
        self.dsf_notebook.bind('<<NotebookTabChanged>>', lambda
                               event: self.update_cab_sys_tabs(event)
                               )

        self.dsf_details_frame = tkinter.Frame(self.dsf_notebook)
        self.dsf_details_frame.grid(column=1, row=1, sticky='NEWS')
        self.dsf_details_frame.columnconfigure(1, weight=1)
        self.dsf_details_frame.rowconfigure(2, weight=1)

        # display details tab
        if isinstance(self.displayed_object, Project):
            self.dsf_obj_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_details_frame, self.displayed_object,
                                                                    show_name=False, edit_name=False,
                                                                    is_auto_design=False,
                                                                    end_attr_name=['cables', 'scenarios',
                                                                                   'current_curves', 'x_secs'
                                                                                   'sections', 'nodes',
                                                                                   'circuits', 'installs'],
                                                                    end_options=[None, None,
                                                                                 None, None,
                                                                                 None, None,
                                                                                 None, None
                                                                                 ]
                                                                    )
            self.status_label.config(text='')
            self.rate_button.config(state='disabled')

        elif isinstance(self.displayed_object, Cable):
            self.dsf_obj_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_details_frame, self.displayed_object,
                                                                    show_name=False, edit_name=False,
                                                                    is_auto_design=isinstance(self.displayed_object,
                                                                                             AutoCable))
            if isinstance(self.displayed_object, AutoCable):
                self.status_label.config(text=self.displayed_object.get_auto_design_status())
            else:
                self.status_label.config(text='')
            self.rate_button.config(state='disabled')

        elif isinstance(self.displayed_object, Install):
            self.dsf_obj_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_details_frame, self.displayed_object,
                                                                    is_auto_design=isinstance(self.displayed_object,
                                                                                              AutoInstall),
                                                                    show_name=False, edit_name=False,
                                                                    end_attr_name=['cable', 'auto_cable',
                                                                                   'current_curve', 'circuit'],
                                                                    end_options=[self.project.cables,
                                                                                 self.project.cables,
                                                                                 self.project.current_curves,
                                                                                 self.project.circuits],
                                                                    scenarios=self.project.scenarios)
            self.rate_button.config(state='normal')
        elif isinstance(self.displayed_object, Section):
            self.dsf_obj_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_details_frame, self.displayed_object,
                                                                    is_auto_design=False,
                                                                    show_name=False, edit_name=False,
                                                                    end_attr_name=['install', 'left_node',
                                                                                   'right_node', 'x_sec'],
                                                                    end_options=[self.project.installs,
                                                                                 self.project.nodes,
                                                                                 self.project.nodes,
                                                                                 self.project.installs])
            self.rate_button.config(state='disabled')
        elif isinstance(self.displayed_object, Node):
            self.dsf_obj_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_details_frame, self.displayed_object,
                                                                    is_auto_design=False,
                                                                    show_name=False, edit_name=False,
                                                                    end_attr_name=None,
                                                                    end_options=None)
            self.rate_button.config(state='disabled')
        elif isinstance(self.displayed_object, Circuit):
            self.dsf_obj_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_details_frame, self.displayed_object,
                                                                    is_auto_design=isinstance(self.displayed_object,
                                                                                              AutoCircuit),
                                                                    show_name=False, edit_name=False,
                                                                    end_attr_name=None,
                                                                    end_options=None)
            self.rate_button.config(state='disabled')
        elif isinstance(self.displayed_object, CurrentCurve):
            self.dsf_obj_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_details_frame, self.displayed_object,
                                                                    show_name=False, edit_name=False,
                                                                    is_auto_design=isinstance(self.displayed_object,
                                                                                              AutoCurrentCurve))
            self.rate_button.config(state='disabled')
        elif isinstance(self.displayed_object, Scenario):
            self.dsf_obj_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_details_frame, self.displayed_object,
                                                                    is_auto_design=isinstance(self.displayed_object,
                                                                                              AutoScenario),
                                                                    show_name=False, edit_name=False,
                                                                    end_attr_name=None,
                                                                    end_options=None)
            self.rate_button.config(state='disabled')
        else:
            raise Exception(f'Trying to display detail frame but display object is {type(self.displayed_object)}')
        self.dsf_obj_frame.bind('<<Q_change>>', self.update_rating)
        self.dsf_obj_frame.grid(column=1, row=2, sticky='NEWS')
        self.dsf_obj_frame.columnconfigure(1, weight=1)
        self.dsf_obj_frame.rowconfigure(1, weight=1)

        # Frame that contains results
        if isinstance(self.displayed_object, Install):
            self.install_results_frame2 = ResultFrame(self.dsf_details_frame, result='')
            self.install_results_frame2.grid(column=1, row=1, sticky='NEWS')

        self.dsf_notebook.add(self.dsf_details_frame, text='details')

        # display overview tab
        if isinstance(self.displayed_object, CurrentCurve):
            self.current_curve_overview_frame = current_curve_overview.CurrentCurveOverviewFrame(self.displayed_object)
            self.dsf_notebook.insert(0, self.current_curve_overview_frame, text='overview')
            self.current_curve_overview_frame.bind('<<Q_change>>', self.update_rating)
            self.dsf_notebook.select(0)
        elif isinstance(self.displayed_object, Cable):
            foil_rt = self.project.config.foil_eddy_loss_rt.value
            self.cable_overview_frame = cable_overview.CableOverviewFrame(cable=self.displayed_object, foil_rt=foil_rt)
            self.dsf_notebook.insert(0, self.cable_overview_frame, text='overview')
            self.cable_overview_frame.bind('<<Q_change>>', self.update_rating)
            self.dsf_notebook.select(0)
        elif isinstance(self.displayed_object, Install):
            # self.install_overview_tab = ttk.Frame()
            self.install_overview_draw_frame = ttk.Frame(self.dsf_notebook)
            self.install_overview_draw_frame.columnconfigure(2, weight=1)
            self.install_overview_draw_frame.rowconfigure(2, weight=1)
            self.dsf_notebook.insert(0, self.install_overview_draw_frame, text='overview and drawing')
            # self.install_overview_dia_frame.bind('<<Q_change>>', self.update_rating)

            self.install_overview_frame = install_overview.InstallOverviewFrame(self.install_overview_draw_frame,
                                                                                install=self.displayed_object,
                                                                                circuit_options=self.project.circuits,
                                                                                cable_options=self.project.cables,
                                                                                current_curve_options=self.project.current_curves,
                                                                                scenarios=self.project.scenarios)
            # self.dsf_notebook.insert(0, self.install_overview_frame, text='overview')
            self.install_overview_frame.grid(column=1, row=1, rowspan=2, sticky='NEWS')
            self.install_overview_frame.bind('<<Q_change>>', self.update_rating)

            # Frame that contains results
            self.install_results_frame = ResultFrame(self.install_overview_draw_frame, result='')
            self.install_results_frame.grid(column=2, row=1, sticky='NEWS')

            # Frame that contains a drawing of the installation
            self.install_draw_frame = install_drawing.InstallDrawingFrame(self.install_overview_draw_frame,
                                                                          install=self.displayed_object,
                                                                          install_state=self.install_state,
                                                                          cond_thetas_list=self.cond_thetas_list)
            self.install_draw_frame.grid(column=2, row=2, sticky='NEWS')

            self.graph_frame = GraphFrame(self.dsf_notebook)
            # graph_show(frame=self.graph_frame)
            self.dsf_notebook.insert(1, self.graph_frame, text='graph')

            self.dsf_state_frame = tkinter.Frame(self.dsf_notebook)
            self.dsf_state_frame.grid(column=1, row=1, sticky='NEWS')
            self.dsf_state_frame.columnconfigure(1, weight=1)
            self.dsf_state_frame.rowconfigure(1, weight=1)
            self.install_state = InstallState(self.displayed_object)
            if self.dsf_state2_frame is not None:
                self.dsf_state2_frame.destroy()
            self.dsf_state2_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_state_frame, self.install_state,
                                                                       is_auto_design=False,
                                                                       show_name=False, edit_name=False,
                                                                       scenarios=self.project.scenarios)
            self.dsf_state2_frame.grid(column=1, row=1, sticky='NEWS')
            self.dsf_state2_frame.columnconfigure(1, weight=1)
            self.dsf_state2_frame.rowconfigure(1, weight=1)
            self.dsf_notebook.add(self.dsf_state_frame, text='state')

            self.dsf_result_frame = tkinter.Frame(self.dsf_notebook)

            self.dsf_result_frame.columnconfigure(2, weight=1)
            self.dsf_result_frame.rowconfigure(1, weight=1)
            # LogViewer(self.log_frame, log)
            self.dsf_notebook.add(self.dsf_result_frame, text='log')

            self.dsf_notebook.select(0)

            self.install_draw_frame.draw(cond_thetas_list=self.cond_thetas_list,
                                         amp_list=self.amp_list)

        elif isinstance(self.displayed_object, Scenario):
            pass
            # self.section_overview_frame = ttk.Frame()
            # self.dsf_notebook.insert(0, self.section_overview_frame, text='overview')
            # self.current_curve_overview_frame.bind('<<Q_change>>', self.update_rating)
            # self.dsf_notebook.select(0)

        elif isinstance(self.displayed_object, Section):
            self.section_overview_frame = ttk.Frame()
            self.dsf_notebook.insert(0, self.section_overview_frame, text='overview')
            # self.current_curve_overview_frame.bind('<<Q_change>>', self.update_rating)
            # self.dsf_notebook.select(0)
        elif isinstance(self.displayed_object, Node):
            self.node_overview_frame = ttk.Frame()
            self.dsf_notebook.insert(0, self.node_overview_frame, text='overview')
            # self.current_curve_overview_frame.bind('<<Q_change>>', self.update_rating)
            # self.dsf_notebook.select(0)
        elif isinstance(self.displayed_object, Circuit):
            self.circuit_overview_frame = ttk.Frame()
            self.dsf_notebook.insert(0, self.circuit_overview_frame, text='overview')
            # self.current_curve_overview_frame.bind('<<Q_change>>', self.update_rating)
            # self.dsf_notebook.select(0)
        elif isinstance(self.displayed_object, Project):
            self.project_overview_frame = ttk.Frame()
            self.dsf_notebook.insert(0, self.project_overview_frame, text='overview')
            # self.current_curve_overview_frame.bind('<<Q_change>>', self.update_rating)
            # self.dsf_notebook.select(0)
        else:
            raise Exception(f'Trying to display overview frame but displayed object is {type(self.displayed_object)}')

        self.auto_design.set(isinstance(self.displayed_object, (AutoCable, AutoInstall,
                                                                AutoCurrentCurve, AutoScenario, AutoCircuit)) and
                             self.displayed_object.is_auto_design())
        self.obj_name.set(self.displayed_object.name)

        if isinstance(self.displayed_object, Install) and self.displayed_object.config.auto_calc.value:
            self.rate()

    def add_current_curve(self, new_current_curve: CurrentCurve = None) -> str:
        """Add current_curve to project

        Adds a current_curve to the project and updates viewer. If no current_curve is given a new current_curve is
        generated.

        :param new_current_curve: new current_curve to be added to project
        :return: new current_curve name
        """
        if new_current_curve is None:
            new_current_curve = CurrentCurve()
            new_point = TransientCurrentPoint()
            new_point.time.set_value(value=0, unit='s', source='project viewer')
            new_point.current.set_value(value=0, unit='A', source='project viewer')
            new_current_curve.points.append(new_point)

        new_current_curve = self.project.add_current_curve(new_current_curve)
        # add current curve to current_curve_tree and display in edit pane
        self.current_curve_tree.insert('', tkinter.END, new_current_curve.name, text=new_current_curve.name,    # type: ignore[arg-type]
                                       tags='current_curve')
        self.current_curve_tree.focus(new_current_curve.name)
        self.current_curve_tree.selection_set(new_current_curve.name)
        self.current_curve_tree.configure(height=len(self.project.current_curves.keys())+1)

        self.displayed_object = self.project.current_curves[self.current_curve_tree.focus()]
        self.show_displayed_object()
        # self.left_notebook.select(1)

        return new_current_curve.name

    def new_blank_current_curve(self) -> None:
        """Add blank auto current curve to project

        Adds a new blank auto current curve to the project and updates viewer.

        :return: None
        """

        self.new_auto_current_curve(auto=False)

    def new_auto_current_curve(self, new_current_curve: CurrentCurve = None, auto: bool = True):
        """Add auto current curve to project

        Adds a current curve to the project and updates viewer. If no current curve is given a new auto current curve
        is generated.

        :param new_current_curve: new current curve to be added to project
        :param auto: does the new current curve have automatic design turned on
        :return: new current curve name
        """

        if new_current_curve is None:
            new_current_curve = AutoCurrentCurve()
            new_current_curve.name = "current_curve_0"
            new_current_curve.set_auto_design(auto)

        added_current_curve_name = self.add_current_curve(new_current_curve)
        return added_current_curve_name

    def duplicate_current_curve(self):
        """Copy current_curve selected to new current_curve

        Copies selected current_curve to a new current_curve object

        :return: None
        """
        # self.new_auto_current_curve(copy_current_curve=True)
        if len(self.project.current_curves) < 1:
            tkinter.messagebox.showwarning('Copy Current Curve', 'No current curve in project')
            return
        existing_current_curve = self.project.current_curves[self.current_curve_tree.focus()]
        current_curve_name = existing_current_curve.name
        new_current_curve_name = find_unique_name(current_curve_name, list(self.project.current_curves.keys()))
        new_current_curve = copy.deepcopy(existing_current_curve)
        new_current_curve.name = new_current_curve_name
        self.new_auto_current_curve(new_current_curve=new_current_curve)

    def delete_current_curve(self) -> None:
        """Delete selected current curve from project

        :return: None
        """
        if len(self.project.current_curves) < 1:
            tkinter.messagebox.showwarning('Delete Current Curve', 'No current curve in project')
            return
        deleted_current_curve_iid = self.current_curve_tree.focus()
        # check current_curve not used
        installs = list(self.project.installs.values())
        for install in installs:
            for cable_set in install.cable_sets:
                if cable_set.current_curve is not None and deleted_current_curve_iid == cable_set.current_curve.name:
                    tkinter.messagebox.showwarning('Delete Current Curve', 'Unable to delete as current curve'
                                                                           ' being used')
                    return

        # delete current_curve from cable_tree
        focus_current_curve_iid = self.current_curve_tree.next(deleted_current_curve_iid)
        if focus_current_curve_iid == '':
            focus_current_curve_iid = self.current_curve_tree.prev(deleted_current_curve_iid)

        self.current_curve_tree.focus(focus_current_curve_iid)
        self.current_curve_tree.selection_set(focus_current_curve_iid)
        self.current_curve_tree.delete(deleted_current_curve_iid)

        if focus_current_curve_iid == '':
            focus_install_iid = self.install_tree.focus()
            if focus_install_iid == '':
                self.displayed_object = None
            else:
                self.displayed_object = self.project.installs[focus_install_iid]
            self.show_displayed_object()

        del self.project.current_curves[deleted_current_curve_iid]
        # display selected current_curve (in case selected cc was the deleted cc and selection has changed)
        current_tree_focus = self.current_curve_tree.focus()
        if current_tree_focus != '':
            self.displayed_object = self.project.current_curves[self.current_curve_tree.focus()]
            self.show_displayed_object()

        self.current_curve_tree.configure(height=len(self.project.current_curves.keys())+1)

    def save_current_curve(self):
        save_cc = self.project.current_curves[self.current_curve_tree.focus()]
        save_name: str = filedialog.asksaveasfilename(initialdir=self.working_dir, title='Save file',
                                                      filetypes=(('xml files', "*.xml"), ('all files', '*.*')),
                                                      initialfile=save_cc.name, defaultextension='.xml')
        if save_name is None or save_name == '':
            return
        # make the save directory the new default working directory
        save_dir = save_name.rpartition('/')
        self.working_dir = save_dir[0]
        # add the .cabs suffix, if required
        if save_name.partition('.')[1] != '.':
            save_name = save_name + '.xml'
        # save selected cable
        serial = canning.dumps(save_cc, name=save_cc.name)
        with open(save_name, 'w', encoding='utf-8') as save_file:
            save_file.write(serial)

    def load_current_curve(self):
        load_name: str = filedialog.askopenfilename(initialdir=self.working_dir, title='Load file',
                                                    filetypes=(('xml files', "*.xml"), ('all files', '*.*')))
        if load_name == '':
            return
        # make the load directory the new default working directory
        load_dir = load_name.rpartition('/')
        self.working_dir = load_dir[0]
        # load the selected file and add it to cables list
        with open(load_name, 'r', encoding='utf-8') as load_file:
            serial = ''
            for line in load_file:
                serial = serial + line
        new_cc, _name, _remaining_serial = cabsys.data_classes.auto_current_curve.loads_current_curve(serial)

        self.new_auto_current_curve(new_current_curve=new_cc)

    def import_current_curve(self):
        load_name: str = filedialog.askopenfilename(initialdir=self.working_dir, title='Import file',
                                                    filetypes=(('csv files', "*.csv"), ('all files', '*.*')))
        if load_name == '':
            return
        # make the load directory the new default working directory
        load_dir = load_name.rpartition('/')
        self.working_dir = load_dir[0]
        # load the selected file and add it to cables list
        with open(load_name, 'r', encoding='utf-8') as csvfile:
            current_curve_reader = csv.reader(csvfile)
            imported_auto_current_curve = AutoCurrentCurve()
            for row in current_curve_reader:
                if len(row) != 2:
                    raise Exception('importing csv current curve but row has more than 2 items')
                time_point = float(row[0])
                current_point = float(row[1])
                point = TransientCurrentPoint()
                point.time.set_value(time_point, unit='s', source=qc.ATTR_IMPORTED_CSV)
                point.current.set_value(current_point, unit='A', source=qc.ATTR_IMPORTED_CSV)
                imported_auto_current_curve.points.append(point)

            imported_auto_current_curve.auto_number_points.set_value(len(imported_auto_current_curve.points),
                                                                     source=qc.ATTR_IMPORTED_CSV)
            imported_auto_current_curve.auto_kind.set_value('Imported CSV', source=qc.ATTR_IMPORTED_CSV)
            imported_auto_current_curve.auto_comment.set_value('Imported CSV', source=qc.ATTR_IMPORTED_CSV)
            imported_auto_current_curve.set_auto_design(True)
            imported_auto_current_curve.name = load_name.rpartition('/')[2]

        self.new_auto_current_curve(new_current_curve=imported_auto_current_curve)

    def update_rating(self, _event):
        if isinstance(self.displayed_object, Install):
            self.install_draw_frame.draw(cond_thetas_list=self.cond_thetas_list,
                                         amp_list=self.amp_list)
            # TODO: remove InstallState once InstallStateCCT works properly
            if self.displayed_object.config.solver_continuous.value == iec.CALC_TEMPERATURE_CCT:
                self.install_state = InstallStateCCT(self.displayed_object)
            else:
                self.install_state = InstallState(self.displayed_object)
            # print(self.displayed_object.auto_ambient_theta.value)
            if self.displayed_object.config.auto_calc.value:
                self.rate()
            else:
                self.status_label.config(text='press rate')
                self.install_results_frame.new_result(f'')
                self.install_results_frame2.new_result(f'')
                self.install_draw_frame.draw(cond_thetas_list=self.cond_thetas_list,
                                             amp_list=self.amp_list)
                log = Log()
                if self.log_frame is not None:
                    self.log_frame.destroy()
                self.log_frame = LogViewer(self.dsf_result_frame, log, self.working_dir,
                                           self.displayed_object.name + '_log')
                self.log_frame.columnconfigure(1, weight=1)
                self.log_frame.rowconfigure(1, weight=1)
                self.log_frame.grid(column=2, row=1, sticky='NEWS')
                state = InstallState(self.displayed_object)
                # DataStoreViewer(self.dsf_state2_frame, state)
                if self.dsf_state2_frame is not None:
                    self.dsf_state2_frame.destroy()
                self.dsf_state2_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_state_frame, state,
                                                                           is_auto_design=False,
                                                                           show_name=False, edit_name=False,
                                                                           scenarios=self.project.scenarios)
                self.dsf_state2_frame.grid(column=1, row=1, sticky='NEWS')
                self.dsf_state2_frame.columnconfigure(1, weight=1)
                self.dsf_state2_frame.rowconfigure(1, weight=1)
                self.dsf_notebook.add(self.dsf_state_frame, text='state')
        elif isinstance(self.displayed_object, (AutoCable, AutoCurrentCurve)):
            # check if an auto_cable, that it has been properly designed
            if self.displayed_object.get_auto_design_status() == '':
                self.status_label.config(text='')
            else:
                self.status_label.config(text=self.displayed_object.get_auto_design_status())
            # self.install_results_frame.new_result(f'')
            # self.install_results_frame2.new_result(f'')

    def update_cab_sys_tabs(self, _event):
        if isinstance(self.displayed_object, Install):
            self.install_overview_frame.update_frame()
            self.dsf_obj_frame.update_viewer(self.project.scenarios)
        elif isinstance(self.displayed_object, Cable):
            self.cable_overview_frame.update_frame()
            self.dsf_obj_frame.update_viewer()
        elif isinstance(self.displayed_object, CurrentCurve):
            self.current_curve_overview_frame.update_frame()
            self.dsf_obj_frame.update_viewer()
        else:
            self.dsf_obj_frame.update_viewer()

    def rate_button_callback(self):
        self.rate()

    def rate(self):
        if isinstance(self.displayed_object, Install):

            dis_install = self.displayed_object

            if self.rate_running:
                return
            self.rate_running = True

            log = Log(required_log_level=dis_install.config.log_level.value,
                      max_log_count=dis_install.config.max_log_count.value)
            try:
                # design installation cross-section if auto_design to check that it is properly designed
                if isinstance(dis_install, AutoInstall):
                    try:
                        if dis_install.selected_scenario.value in self.project.scenarios.keys():
                            selected_scenario = self.project.scenarios[dis_install.selected_scenario.value]
                        else:
                            selected_scenario = None
                        dis_install.auto_design(scenario=selected_scenario, proj_scenarios=self.project.scenarios)
                    except (DesignInstallException, DesignCableSetException) as e:
                        self.status_label.config(text=f'design installation failed: {e}')
                        self.install_results_frame.new_result(f'design installation failed: {e}')
                        self.install_results_frame2.new_result(f'design installation failed: {e}')
                        raise

                self.rate_button['state'] = 'disabled'
                self.status_label.config(text='calculating result')
                self.dlg = ProgressDialog(self.root, self.message, self.cancel_solver)
                self.install_state.progress = 'start calculation'
                self.message.set('start calculation')
                x = threading.Thread(target=self.solver_thread, args=(log,))
                x.start()
                self.after_job = self.root.after(1000, lambda: self.main_thread_loop())
                self.dlg.wait_window()

                if not self.result_error and dis_install.rating_type.value == iec.RATING_CONTINUOUS:
                    if dis_install.config.solver_continuous.value == iec.CALC_TEMPERATURE_CCT:
                        pass
                    else:
                        iec_details(dis_install, self.install_state, log)

                self.status_label.config(text='updating display')
                self.root.update()

                # LogViewer(self.log_frame, log)
                if self.log_frame is not None:
                    self.log_frame.destroy()
                self.log_frame = LogViewer(self.dsf_result_frame, log, self.working_dir,
                                           self.displayed_object.name + '_log')
                self.log_frame.columnconfigure(1, weight=1)
                self.log_frame.rowconfigure(1, weight=1)
                self.log_frame.grid(column=2, row=1, sticky='NEWS')
                if self.dsf_state2_frame is not None:
                    self.dsf_state2_frame.destroy()
                self.dsf_state2_frame = cabsys_data_viewer.CabSysDataFrame(self.dsf_state_frame, self.install_state,
                                                                           is_auto_design=False,
                                                                           show_name=False, edit_name=False,
                                                                           scenarios=self.project.scenarios)
                self.dsf_state2_frame.grid(column=1, row=1, sticky='NEWS')
                self.dsf_state2_frame.columnconfigure(1, weight=1)
                self.dsf_state2_frame.rowconfigure(1, weight=1)
                self.dsf_notebook.add(self.dsf_state_frame, text='state')
                if self.result_error:
                    self.status_label.config(text='Calculation failed')
                    self.install_results_frame.new_result(self.result)
                    self.install_results_frame2.new_result(self.result)
                    self.cond_thetas_list = []
                    self.amp_list = []
                    self.install_draw_frame.draw(cond_thetas_list=self.cond_thetas_list,
                                                 amp_list=self.amp_list)
                else:
                    self.status_label.config(text="Calculation successful")

                    if (self.displayed_object.rating_type.value == iec.RATING_CONTINUOUS and
                        dis_install.config.solver_continuous.value != iec.CALC_TEMPERATURE_CCT):
                        table_result = 'Circuit:  '
                        for i_cct in range(len(self.cond_thetas_list)):
                            table_result += f'  cct {i_cct: 2.0f} '
                        table_result += '\n'
                        table_result += 'θ_C (°C): '
                        for i_cct in range(len(self.cond_thetas_list)):
                            table_result += f'  {round(max(self.cond_thetas_list[i_cct]), 1): 3.2f} '
                        table_result += '\n'
                        table_result += 'I (A):   '
                        for i_cct in range(len(self.cond_thetas_list)):
                            table_result += f' {round(self.amp_list[i_cct], 1): 4.1f} '
                        table_result += '\n'
                    else:
                        table_result = self.result
                    self.install_results_frame.new_result(table_result)
                    self.install_results_frame2.new_result(table_result)
                    self.install_draw_frame.draw(cond_thetas_list=self.cond_thetas_list,
                                                 amp_list=self.amp_list)

            finally:

                self.rate_button['state'] = 'normal'
                self.graph_frame.update_graph(self.transient_result)
                self.rate_running = False

        else:
            raise Exception(f'Trying to do a current rating but displayed object is {type(self.displayed_object)}')

    def cancel_thread(self):
        pass

    def solver_thread(self, log):

        if self.displayed_object.config.debug.value:
            exceptions = ()
        else:
            exceptions = (SolverException, InvalidInput, DesignCableException,
                          DesignInstallException, DesignCableSetException,
                          cabsys.IEC60287Exception)

        self.result = None

        try:
            # TODO: remove the if statement once no_scenarnio fixed
            if self.displayed_object.selected_scenario.value == Scenario.NO_SCENARIO:
                (self.result, self.cond_thetas_list, self.amp_list,
                 self.transient_result) = solver.solve(self.displayed_object,None,
                                                       state=self.install_state, log=log)
            else:
                (self.result, self.cond_thetas_list, self.amp_list,
                 self.transient_result) = solver.solve(self.displayed_object,
                                                       self.displayed_object.selected_scenario.value,
                                                       state=self.install_state, log=log)

            # TODO: improve format of self.result
            # TODO: add short short circuit ratings
            self.result_error = False

        except exceptions as solver_exception:
            self.result_error = True
            self.result = f'{type(solver_exception).__name__}: {solver_exception.args[0]}'
            # self.result = None
            log.close_sections('Exception raised', f'{type(solver_exception).__name__}', '', solver_exception.args[0])
            # self.result = f'exception: {sys.exc_info()[1]}'
            # traceback.print_tb(sys.exc_info()[2])
            # traceback.print_tb(sys.exc_info()[1])
        finally:
            if self.result is None:
                self.result = 'Calculation failed, probably due to an exception'
                self.result_error = True
            if self.after_job is not None:
                self.root.after_cancel(self.after_job)
            self.install_state.progress = ''
            self.dlg.destroy()

    def main_thread_loop(self):
        if self.install_state.progress != '':
            self.message.set(self.install_state.progress)
            self.after_job = self.root.after(300, lambda: self.main_thread_loop())

    def cancel_solver(self):
        self.install_state.cancel = True


class ScenarioTreeview(ttk.Treeview):

    def __init__(self, parent, project_viewer: ProjectViewer, **kw):
        super().__init__(parent, **kw)
        self.popup_menu = tkinter.Menu(self, tearoff=0)
        self.popup_menu.add_command(label='New auto scenario', command=project_viewer.new_auto_scenario)
        # self.popup_menu.add_command(label='New blank install', command=project_viewer.new_blank_install)
        self.popup_menu.add_command(label='New Scenario', command=project_viewer.add_scenario)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Load scenarios', command=project_viewer.load_scenarios)
        self.popup_menu.add_command(label='Save scenarios', command=project_viewer.save_scenarios)
        # self.popup_menu.add_command(label='Save install', command=project_viewer.save_install)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Rename', command=project_viewer.rename_scenario)
        # self.popup_menu.add_command(label='Duplicate install', command=project_viewer.duplicate_install)
        # self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Delete Scenario', command=project_viewer.delete_scenario)
        self.bind("<Button-3>", self.notebook_popup)
        self.tag_bind('scenario', '<Double-1>', project_viewer.scenario_tree_select_callback)

    def notebook_popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()


class InstallTreeview(ttk.Treeview):

    def __init__(self, parent, project_viewer: ProjectViewer, **kw):
        super().__init__(parent, **kw)
        self.popup_menu = tkinter.Menu(self, tearoff=0)
        self.popup_menu.add_command(label='New auto install', command=project_viewer.new_auto_install)
        self.popup_menu.add_command(label='New blank install', command=project_viewer.new_blank_install)
        self.popup_menu.add_command(label='New install', command=project_viewer.add_install)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Load install', command=project_viewer.load_install)
        self.popup_menu.add_command(label='Save install', command=project_viewer.save_install)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Rename', command=project_viewer.rename_install)
        self.popup_menu.add_command(label='Duplicate install', command=project_viewer.duplicate_install)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Delete install', command=project_viewer.delete_install)
        self.bind("<Button-3>", self.notebook_popup)
        self.tag_bind('install', '<Double-1>', project_viewer.install_tree_select_callback)

    def notebook_popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()


class CableTreeview(ttk.Treeview):

    def __init__(self, parent, project_viewer: ProjectViewer, **kw):
        super().__init__(parent, **kw)
        self.popup_menu = tkinter.Menu(self, tearoff=0)
        self.popup_menu.add_command(label='New auto cable', command=project_viewer.new_auto_cable)
        self.popup_menu.add_command(label='New blank auto cable', command=project_viewer.new_blank_cable)
        self.popup_menu.add_command(label='New cable', command=project_viewer.add_cable)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Load cable', command=project_viewer.load_cable)
        self.popup_menu.add_command(label='Save cable', command=project_viewer.save_cable)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Rename cable', command=project_viewer.rename_cable)
        self.popup_menu.add_command(label='Duplicate cable', command=project_viewer.duplicate_cable)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Delete cable', command=project_viewer.delete_cable)
        self.bind("<Button-3>", self.notebook_popup)
        self.tag_bind('cable', '<Double-1>', project_viewer.cable_tree_select_callback)

    def notebook_popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()


class CurrentCurveTreeview(ttk.Treeview):

    def __init__(self, parent, project_viewer: ProjectViewer, **kw):
        super().__init__(parent, **kw)
        self.popup_menu = tkinter.Menu(self, tearoff=0)
        self.popup_menu.add_command(label='New auto current curve', command=project_viewer.new_auto_current_curve)
        self.popup_menu.add_command(label='New blank auto current curve',
                                    command=project_viewer.new_blank_current_curve)
        self.popup_menu.add_command(label='New current curve', command=project_viewer.add_current_curve)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Load current curve', command=project_viewer.load_current_curve)
        self.popup_menu.add_command(label='Save current curve', command=project_viewer.save_current_curve)
        self.popup_menu.add_command(label='import current curve', command=project_viewer.import_current_curve)
        self.popup_menu.add_separator()
        # self.cc_menu.add_command(label='Rename', command=self.rename_cable)
        self.popup_menu.add_command(label='Duplicate current curve', command=project_viewer.duplicate_current_curve)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='Delete current curve', command=project_viewer.delete_current_curve)
        self.bind("<Button-3>", self.notebook_popup)
        self.tag_bind('current_curve', '<Double-1>', project_viewer.current_curves_tree_select_callback)

    def notebook_popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()


class ProgressDialog(tkinter.Toplevel):

    def __init__(self, parent, message, cancel_function):
        super().__init__(parent)
        self.root = cast(tkinter.Toplevel, parent)
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        height = self.root.winfo_height()
        width = self.root.winfo_width()
        geom = "+%d+%d" % (x + width / 2, y + height / 3)
        self.geometry(geom)
        self.attributes("-topmost", 1)
        self.frame = ttk.Frame(self)
        self.frame['padding'] = (5, 10)
        self.frame.pack()
        self.message_label = ttk.Label(self.frame, textvariable=message, width=80)
        self.message_label.grid(row=0, column=1, padx=5, pady=5)
        self.cancel_button = ttk.Button(self.frame, text='cancel', default='active', command=cancel_function)
        self.cancel_button.grid(row=1, column=1, padx=5, pady=5)
        # self.dlg.transient(self.root)
        self.protocol("WM_DELETE_WINDOW", cancel_function)
        self.resizable(False, False)
        self.wait_visibility()
        self.grab_set()
        self.focus()


class InsertCableSet(tkinter.Toplevel):

    def __init__(self, parent, project_viewer: ProjectViewer):
        super().__init__(parent)
        self.project_viewer = project_viewer
        self.root = cast(tkinter.Toplevel, parent)
        self.title('Insert cable set')
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        height = self.root.winfo_height()
        width = self.root.winfo_width()
        geom = "+%d+%d" % (x + width / 2, y + height / 3)
        self.geometry(geom)
        self.attributes("-topmost", 1)
        self.dialog_frame = ttk.Frame(self)
        # self.frame.config(relief="raised")
        self.dialog_frame['padding'] = (5, 10)
        self.dialog_frame.pack()
        # self.message_label = ttk.Label(self.frame, textvariable=message, width=80)
        self.message_label = ttk.Label(self.dialog_frame, text='Position (before):')
        self.message_label.grid(row=0, column=0, padx=5, pady=5, sticky='NW')

        selected_install_iid = self.project_viewer.install_tree.focus()
        self.selected_install = self.project_viewer.project.installs[selected_install_iid]
        num_cs = len(self.selected_install.cable_sets)
        self.cs_treeview_frame = ttk.Frame(self.dialog_frame)
        # self.cs_treeview_frame.config(relief=tkinter.RIDGE)
        self.cs_treeview_frame.grid(row=0, column=1, sticky='NSEW')
        self.cs_treeview = ttk.Treeview(self.cs_treeview_frame, takefocus=True, selectmode=tkinter.BROWSE, show='tree',    # type: ignore[arg-type]
                                        height=min(num_cs+1, 10))
        self.cs_treeview.pack(side='left')
        self.cs_treeview_scrollbar = ttk.Scrollbar(self.cs_treeview_frame, orient='vertical',
                                                   command=self.cs_treeview.yview)
        self.cs_treeview_scrollbar.pack(side='right', fill='y')
        self.cs_treeview.config(yscrollcommand=self.cs_treeview_scrollbar.set)
        # self.cs_treeview.columnconfigure(1, weight=1)
        # self.cs_treeview.rowconfigure(1, weight=1)
        for cs_key, cs in enumerate(self.selected_install.cable_sets):
            self.cs_treeview.insert('', tkinter.END, str(cs_key), text=f'set {cs_key}', tags='cs')    # type: ignore[arg-type]
        self.cs_treeview.insert('', tkinter.END, str(num_cs), text=f'at end', tags='cs')     # type: ignore[arg-type]
        self.cs_treeview.selection_set(str(num_cs))
        self.cs_treeview.focus(str(num_cs))
        self.cs_treeview.see(str(num_cs))

        self.button_frame = ttk.Frame(self.dialog_frame)
        self.button_frame.grid(row=1, column=1)
        self.ok_button = ttk.Button(self.button_frame, text='OK', width=10, command=self.ok_function)
        self.ok_button.grid(row=1, column=0, padx=5, pady=5)
        self.cancel_button = ttk.Button(self.button_frame, text='cancel', width=10, command=self.cancel_function)
        # self.cancel_button = ttk.Button(self.frame, text='cancel', default='active', command=cancel_function)
        self.cancel_button.grid(row=1, column=1, padx=5, pady=5)
        self.transient(self.root)
        self.protocol("WM_DELETE_WINDOW", self.cancel_function)
        self.resizable(False, False)
        self.wait_visibility()
        self.grab_set()
        self.focus()

    def cancel_function(self):
        self.destroy()

    def ok_function(self):
        # new_cs = AutoCableSet()
        new_cs_index = int(self.cs_treeview.focus())
        # if new_cs_index == 0:
        #     new_cs.auto_cable = self.selected_install.cable_sets[0].auto_cable
        #     new_cs.auto_cable_source = 'inserted cable set'
        # self.selected_install.cable_sets.insert(new_cs_index, new_cs)
        # self.selected_install.auto_number_sets.set_value(self.selected_install.auto_number_sets.value + 1, source=dc.ATTR_USER_SET)
        # if isinstance(self.selected_install, AutoInstall) and self.selected_install.is_auto_design():
        #     self.selected_install.auto_design()
        self.selected_install.insert_cable_set(new_cs_index)
        self.project_viewer.show_displayed_object()
        self.destroy()


class DeleteCableSet(tkinter.Toplevel):

    def __init__(self, parent, project_viewer: ProjectViewer):
        super().__init__(parent)
        self.project_viewer = project_viewer
        self.root = cast(tkinter.Toplevel, parent)
        self.title('Delete cable set')
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        height = self.root.winfo_height()
        width = self.root.winfo_width()
        geom = "+%d+%d" % (x + width / 2, y + height / 3)
        self.geometry(geom)
        self.attributes("-topmost", 1)
        self.dialog_frame = ttk.Frame(self)
        # self.frame.config(relief="raised")
        self.dialog_frame['padding'] = (5, 10)
        self.dialog_frame.pack()
        # self.message_label = ttk.Label(self.frame, textvariable=message, width=80)
        self.message_label = ttk.Label(self.dialog_frame, text='Cable set:')
        self.message_label.grid(row=0, column=0, padx=5, pady=5, sticky='NW')

        selected_install_iid = self.project_viewer.install_tree.focus()
        self.selected_install = self.project_viewer.project.installs[selected_install_iid]
        num_cs = len(self.selected_install.cable_sets)
        self.cs_treeview_frame = ttk.Frame(self.dialog_frame)
        # self.cs_treeview_frame.config(relief=tkinter.RIDGE)
        self.cs_treeview_frame.grid(row=0, column=1, sticky='NSEW')
        self.cs_treeview = ttk.Treeview(self.cs_treeview_frame, takefocus=True, selectmode=tkinter.BROWSE, show='tree',     # type: ignore[arg-type]
                                        height=min(num_cs, 10))
        self.cs_treeview.pack(side='left')
        self.cs_treeview_scrollbar = ttk.Scrollbar(self.cs_treeview_frame, orient='vertical',
                                                   command=self.cs_treeview.yview)
        self.cs_treeview_scrollbar.pack(side='right', fill='y')
        self.cs_treeview.config(yscrollcommand=self.cs_treeview_scrollbar.set)
        # self.cs_treeview.columnconfigure(1, weight=1)
        # self.cs_treeview.rowconfigure(1, weight=1)
        for cs_key, cs in enumerate(self.selected_install.cable_sets):
            self.cs_treeview.insert('', tkinter.END, str(cs_key), text=f'set {cs_key}', tags='cs')    # type: ignore[arg-type]
        self.cs_treeview.selection_set(str(num_cs-1))
        self.cs_treeview.focus(str(num_cs-1))
        self.cs_treeview.see(str(num_cs-1))

        self.button_frame = ttk.Frame(self.dialog_frame)
        self.button_frame.grid(row=1, column=1)
        self.ok_button = ttk.Button(self.button_frame, text='OK', width=10, command=self.ok_function)
        self.ok_button.grid(row=1, column=0, padx=5, pady=5)
        self.cancel_button = ttk.Button(self.button_frame, text='cancel', width=10, command=self.cancel_function)
        # self.cancel_button = ttk.Button(self.frame, text='cancel', default='active', command=cancel_function)
        self.cancel_button.grid(row=1, column=1, padx=5, pady=5)
        self.transient(self.root)
        self.protocol("WM_DELETE_WINDOW", self.cancel_function)
        self.resizable(False, False)
        self.wait_visibility()
        self.grab_set()
        self.focus()

    def cancel_function(self):
        self.destroy()

    def ok_function(self):
        cs_index = int(self.cs_treeview.focus())
        self.selected_install.delete_cable_set(cs_index)
        self.project_viewer.show_displayed_object()
        self.destroy()
