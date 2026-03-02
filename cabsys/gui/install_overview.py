import tkinter
from tkinter import ttk
from tkinter import messagebox
from typing import Dict, Optional, Union
from collections.abc import Callable

from cabsys.gui.overview_widgets import EntryInt, ComboboxBool, ComboboxString, CheckbuttonBool
# from cabsys.gui.install_drawing import InstallDrawingFrame
# import cabsys.quantity.quantity_store as quant_store

from cabsys.data_classes.install import Install, CableSet
from cabsys.data_classes.circuit import Circuit
from cabsys.data_classes.cable import Cable
from cabsys.data_classes.current_curve import CurrentCurve
from cabsys.data_classes.auto_install import AutoInstall
from cabsys.data_classes.auto_cable import AutoCable
from cabsys.data_classes.scenario import Scenario
# from cabsys.data_classes.scenario import Scenario
import cabsys.iec.iec_constants as iec
import cabsys.data_classes.cable_constants as cable_constants

MAX_CABLE_SET_TABS = 15


class InstallOverviewFrame(tkinter.Frame):
    """binder for GuiCollection"""

    def __init__(self, parent: Union[tkinter.Toplevel, tkinter.Tk, tkinter.Frame, tkinter.Tk, tkinter.PanedWindow,
                                     ttk.Notebook],
                 install: Install, circuit_options:Dict[str, Circuit], cable_options: Dict[str, Cable],
                 current_curve_options: Dict[str, CurrentCurve],
                 scenarios: Dict[str, Scenario] = None,
                 **kw):
        self.install = install
        self.cable_options = cable_options
        self.scenarios = scenarios
        super().__init__(parent, **kw)

        self.rowconfigure(0, minsize="0", weight=0, pad="0")
        self.rowconfigure(1, minsize="0", weight=0, pad="0")
        self.rowconfigure(2, minsize="0", weight=0, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="0", weight=0, pad="0")
        self.columnconfigure(1, minsize="0", weight=0, pad="0")
        self.columnconfigure(2, minsize="0", weight=0, pad="0")
        self.columnconfigure(3, minsize="0", weight=0, pad="0")
        # self.config(height="0")
        # self.config(width="0")
        self.config(relief="flat")

        # frame for all installation inputs
        self.common_frame = CommonFrame(self, self.install, cable_options, self.is_install_auto_design)
        self.common_frame.grid(column=0, row=0)
        self.common_frame.grid(sticky="EW")
        self.common_frame.bind('<<Q_change>>', self.q_change)
        # frame for transient ratings
        self.transient_frame = TransientFrame(self, self.install, cable_options, self.is_install_auto_design)
        self.transient_frame.grid(column=0, row=1)
        self.transient_frame.grid(sticky='EW')
        self.transient_frame.bind('<<Q_change>>', self.q_change)
        # frame for buried installation cross-sections
        self.buried_frame = BuriedFrame(self, self.install, circuit_options, cable_options, current_curve_options,
                                        self.is_install_auto_design)
        self.buried_frame.grid(column=0)
        self.buried_frame.grid(row=2)
        self.buried_frame.grid(sticky="EW")
        self.buried_frame.bind('<<Q_change>>', self.q_change)

    def is_install_auto_design(self):
        if isinstance(self.install, AutoInstall):
            return self.install.is_auto_design()
        else:
            return None

    def update_frame(self):
        q_rating_type = self.install.get_q_rating_type(self.install.selected_scenario.value)
        self.common_frame.update_frame()
        if q_rating_type == iec.RATING_CONTINUOUS:
            self.transient_frame.grid_remove()
        else:
            self.transient_frame.grid()
            self.transient_frame.update_frame()
        self.transient_frame.update_frame()
        self.buried_frame.update_frame()

    def q_change(self, _event):
        try:
            if isinstance(self.install, AutoInstall) and self.install.is_auto_design():
                self.install.auto_design(proj_scenarios=self.scenarios)
        finally:
            self.update_frame()
            self.event_generate("<<Q_change>>", when="tail")


class CommonFrame(tkinter.Frame):
    """Frame showing common installation cross-section parameters"""

    def __init__(self, container: tkinter.Frame, install: Install, cable_options: Dict[str, Cable],
                 is_install_auto_design: Callable, **kw):
        self.container = container
        self.install = install
        super().__init__(container, **kw)
        #
        if isinstance(install, AutoInstall):
            auto_design: Callable = install.is_auto_design
        else:
            auto_design: Callable = lambda: None
        self.rowconfigure(0, minsize="0", weight=1, pad="0")
        self.rowconfigure(1, minsize="0", weight=1, pad="0")
        self.rowconfigure(2, minsize="0", weight=1, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="150", weight=0, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        self.columnconfigure(2, minsize="0", weight=0, pad="0")
        self.columnconfigure(3, minsize="0", weight=0, pad="0")
        self.config(height="0", width="0", borderwidth=2, relief="groove")

        # Combobox Scenario
        self.ttk_label_scenario = ttk.Label(self)
        self.ttk_label_scenario.grid(column=0, row=0, sticky="w")
        self.ttk_label_scenario.config(width=0, anchor="w", text="Scenario", underline=0)
        # new_widget(Combobox)
        self.scenario_combobox = ComboboxString(self, install.selected_scenario, is_install_auto_design)
        self.scenario_combobox.grid(column=1)
        self.scenario_combobox.grid(row=0)
        self.scenario_combobox.grid(sticky='W')
        self.scenario_combobox.config(width=30, state="readonly")

        # Combobox installation Kind
        self.ttk_label_type8 = ttk.Label(self)
        self.ttk_label_type8.grid(column=0, row=1, sticky="w")
        self.ttk_label_type8.config(width=0, anchor="e", text="Install kind", underline=0)
        # new_widget(Combobox)
        self.kind_combobox = ComboboxString(self, self.install.kind, is_install_auto_design)
        self.kind_combobox.grid(column=1)
        self.kind_combobox.grid(row=1)
        self.kind_combobox.grid(sticky='W')
        self.kind_combobox.config(width=30, state="readonly")

        # Combobox Rating Kind
        q_rating_type = install.get_q_rating_type(install.selected_scenario.value)
        self.ttk_label_rating_type = ttk.Label(self)
        self.ttk_label_rating_type.grid(column=0, row=2, sticky="w")
        self.ttk_label_rating_type.config(width=0, anchor="w", text="Rating type", underline=0)
        # new_widget(Combobox)
        self.rating_combobox = ComboboxString(self, q_rating_type, is_install_auto_design)
        self.rating_combobox.grid(column=1)
        self.rating_combobox.grid(row=2)
        self.rating_combobox.grid(sticky='W')
        self.rating_combobox.config(width=30, state="readonly")
        self.auto_calc_checkbutton = CheckbuttonBool(self, self.install.config.auto_calc, is_install_auto_design,
                                                     text='auto_calc')
        self.auto_calc_checkbutton.grid(column=2, row=1, sticky='w')

        # Ambient temperature
        self.ttk_label_6 = ttk.Label(self)
        self.ttk_label_6.grid(column=0, row=11, sticky="W")
        self.ttk_label_6.config(width=0, anchor="e", text="Ambient temperature", underline=-1)
        # Entry Box
        q_ambient_theta = install.get_q_ambient_temperature(self.install.selected_scenario.value)
        self.ttk_entry_ambient_temp = EntryInt(self, q_ambient_theta, auto_design)
        self.ttk_entry_ambient_temp.grid(column=1, row=11, sticky="W")
        self.ttk_entry_ambient_temp.config(width=30)
        # °C Label
        self.ttk_label_7 = ttk.Label(self)
        self.ttk_label_7.grid(column=2, row=11, sticky="W")
        self.ttk_label_7.config(width=0, anchor="e", text="°C", underline=-1)

        # Thermal resistivity label
        self.ttk_label9 = ttk.Label(self)
        self.ttk_label9.grid(column=0, row=12, sticky="W")
        self.ttk_label9.config(width=0, anchor="e", text="Thermal resistivity", underline=0)
        # Entry box
        q_ground_tr = self.install.get_q_ground_tr(self.install.selected_scenario.value)
        self.entry_tr = EntryInt(self, q_ground_tr, is_install_auto_design)
        self.entry_tr.grid(column=1, row=12, sticky="W")
        # K.m/W label
        self.ttk_label10 = ttk.Label(self)
        self.ttk_label10.grid(column=2, row=12, sticky="")
        self.ttk_label10.config(width=0, anchor="e", text="K.m/W", underline=0)

    def update_frame(self):
        self.scenario_combobox.update_combobox()
        self.rating_combobox.update_combobox()
        # self.auto_calc_combobox.update_combobox()
        self.auto_calc_checkbutton.update_checkbutton()
        self.kind_combobox.update_combobox()
        # self.ttk_entry_ambient_temp.update_entry()
        q_ambient_theta = self.install.get_q_ambient_temperature(self.install.selected_scenario.value)
        self.ttk_entry_ambient_temp.update_entry(q_ambient_theta)

        if self.install.kind.get_value(unit='') == iec.BURIED:
            self.entry_tr.config(state='normal')
            self.ttk_label9.config(state='normal')
            self.ttk_label10.config(state='normal')
            q_ground_tr = self.install.get_q_ground_tr(self.install.selected_scenario.value)
            self.entry_tr.update_entry(q_ground_tr)
        else:
            self.entry_tr.config(state='disable')
            self.ttk_label9.config(state='disable')
            self.ttk_label10.config(state='disable')
        # self.entry_tr.update_entry()


class TransientFrame(tkinter.Frame):
    """Frame showing transient / cyclic rating parameters"""

    def __init__(self, container: tkinter.Frame, install: Install, cable_options: Dict[str, Cable],
                 is_install_auto_design: Callable, **kw):
        self.container = container
        self.install = install
        self.cable_options = cable_options
        super().__init__(container, **kw)

        self.is_install_auto_design = is_install_auto_design

        self.rowconfigure(0, minsize="0", weight=0, pad="0")
        self.rowconfigure(1, minsize="0", weight=0, pad="0")
        self.rowconfigure(2, minsize="0", weight=0, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="150", weight=0, pad="5")
        self.columnconfigure(1, minsize="0", weight=0, pad="0")
        self.columnconfigure(2, minsize="0", weight=1, pad="0")
        self.columnconfigure(3, minsize="0", weight=1, pad="0")
        self.columnconfigure(4, minsize="0", weight=1, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="groove")

        # End time label
        self.ttk_label1 = ttk.Label(self)
        self.ttk_label1.grid(column=0, row=2, sticky="W")
        self.ttk_label1.config(width=0, anchor="w", text="End time", underline=0)
        # Entry box
        self.entry_end_time = EntryInt(self, self.install.get_q_end_time(self.install.selected_scenario.value),
                                       is_install_auto_design)
        self.entry_end_time.grid(column=1, row=2, sticky="W")
        # K.m/W label
        self.ttk_label10 = ttk.Label(self)
        self.ttk_label10.grid(column=2, row=2, sticky="w")
        self.ttk_label10.config(width=0, anchor="w", text="s", underline=0)

        # cyclic time label
        self.ttk_label2 = ttk.Label(self)
        self.ttk_label2.grid(column=0, row=3, sticky="W")
        self.ttk_label2.config(width=0, anchor="e", text="Cycle time", underline=0)
        # Entry box
        self.entry_cycle_time = EntryInt(self, install.get_q_cycle_time(install.selected_scenario.value),
                                         is_install_auto_design)
        self.entry_cycle_time.grid(column=1, row=3, sticky="W")
        # K.m/W label
        self.ttk_label12 = ttk.Label(self)
        self.ttk_label12.grid(column=2, row=3, sticky="w")
        self.ttk_label12.config(width=0, anchor="w", text="s", underline=0)

    def update_frame(self):
        q_rating_type = self.install.get_q_rating_type(self.install.selected_scenario.value)
        if q_rating_type .get_value(unit='') != iec.RATING_CYCLIC:
            self.entry_end_time.config(state='normal')
            self.ttk_label1.config(state='normal')
            self.ttk_label10.config(state='normal')
            self.entry_cycle_time.config(state='disable')
            self.ttk_label2.config(state='disable')
            self.ttk_label12.config(state='disable')
        else:
            self.entry_end_time.config(state='disable')
            self.ttk_label1.config(state='disable')
            self.ttk_label10.config(state='disable')
            self.entry_cycle_time.config(state='normal')
            self.ttk_label2.config(state='normal')
            self.ttk_label12.config(state='normal')
        self.entry_end_time.update_entry()
        self.entry_cycle_time.update_entry()

    def q_change(self, _event):
        self.event_generate("<<Q_change>>", when="tail")


class BuriedFrame(tkinter.Frame):
    """Frame showing buried cable parameters"""

    def __init__(self, container: tkinter.Frame, install: Install,
                 circuit_options: Dict[str, Circuit],
                 cable_options: Dict[str, Cable],
                 current_curve_options: Dict[str, CurrentCurve],
                 is_install_auto_design: Callable, **kw):
        self.container = container
        self.install = install
        self.circuit_options = circuit_options
        self.cable_options = cable_options
        self.current_curve_options = current_curve_options
        super().__init__(container, **kw)

        self.selected_cs = 0
        self.is_install_auto_design = is_install_auto_design

        self.rowconfigure(0, minsize="0", weight=0, pad="0")
        self.rowconfigure(1, minsize="0", weight=0, pad="0")
        self.rowconfigure(2, minsize="0", weight=0, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="150", weight=0, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        self.columnconfigure(2, minsize="0", weight=0, pad="0")
        self.columnconfigure(3, minsize="0", weight=0, pad="0")
        self.columnconfigure(4, minsize="0", weight=0, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="groove")

        # Number of cable sets label
        self.ttk_label_cs = ttk.Label(self)
        self.ttk_label_cs.grid(column=0, row=3, sticky="W")
        self.ttk_label_cs.config(width=0, anchor="e", text="number of cable sets", underline=0)
        # Entry box
        self.entry_cs = EntryInt(self, self.install.auto_number_sets, is_install_auto_design)
        self.entry_cs.grid(column=1, row=3, sticky="W")
        self.entry_cs.config(width=8)

        # spacing
        self.ttk_label_spacing = ttk.Label(self)
        self.ttk_label_spacing.grid(column=0, row=4, sticky="W")
        self.ttk_label_spacing.config(width=0, anchor="e", text="set spacing", underline=-1)
        # Entry Box
        self.ttk_entry_spacing = EntryInt(self, self.install.auto_spacing, is_install_auto_design)
        self.ttk_entry_spacing.grid(column=1, row=4, sticky="W")
        self.ttk_entry_spacing.config(width=20)
        # °unit Label
        self.ttk_label_spacing_u = ttk.Label(self)
        self.ttk_label_spacing_u.grid(column=3, row=4, sticky="W")
        self.ttk_label_spacing_u.config(width=0, anchor="e", text="mm", underline=-1)

        self.cs_notebook = CableSetNotebook(self, self.install, self.circuit_options, self.cable_options, self.current_curve_options)
        self.cs_notebook.grid(column=0, columnspan=4, row=55)
        self.cs_notebook.bind('<<NotebookTabChanged>>', self.cs_notebook_tab_changed)
        self.cs_frames = []
        for cs_num in range(min(len(self.install.cable_sets), MAX_CABLE_SET_TABS)):
            cs_frame = CableSetFrame(self.cs_notebook, self.install.cable_sets[cs_num],
                                     self.circuit_options,
                                     self.cable_options,
                                     self.current_curve_options,
                                     self.is_install_auto_design)
            cs_frame.bind('<<Q_change>>', self.q_change)
            self.cs_notebook.add(cs_frame, text=f'set {cs_num}')
            self.cs_frames.append(cs_frame)

    def cs_notebook_tab_changed(self, _event):
        self.selected_cs = self.cs_notebook.index(self.cs_notebook.select())

    def update_frame(self):

        if isinstance(self.install, AutoInstall) and self.install.is_auto_design():
            self.ttk_label_cs.config(state='normal')
            self.entry_cs.config(state='normal')
        else:
            self.ttk_label_cs.config(state='disable')
            self.entry_cs.config(state='disable')
        self.entry_cs.update_entry()

        if len(self.install.cable_sets) > 1:
            self.ttk_entry_spacing.config(state='normal')
            self.ttk_label_spacing.config(state='normal')
            self.ttk_label_spacing_u.config(state='normal')
        else:
            self.ttk_entry_spacing.config(state='disable')
            self.ttk_label_spacing.config(state='disable')
            self.ttk_label_spacing_u.config(state='disable')
        self.ttk_entry_spacing.update_entry()
        # update cable set frames inside notebook
        if (len(self.cs_notebook.tabs()) == len(self.install.cable_sets) or
                (len(self.cs_notebook.tabs()) == MAX_CABLE_SET_TABS and
                 len(self.install.cable_sets) > MAX_CABLE_SET_TABS)):
            for cs_num in range(min(len(self.install.cable_sets), MAX_CABLE_SET_TABS)):
                self.cs_frames[cs_num].update_frame(self.install.cable_sets[cs_num])
        else:
            self.cs_notebook.destroy()
            self.cs_notebook = CableSetNotebook(self, self.install, self.circuit_options, self.cable_options, self.current_curve_options)
            self.cs_notebook.grid(column=0, columnspan=4, row=55)
            self.cs_frames = []
            for cs_num in range(min(len(self.install.cable_sets), MAX_CABLE_SET_TABS)):
                cs_frame = CableSetFrame(self.cs_notebook, self.install.cable_sets[cs_num],
                                         self.circuit_options,
                                         self.cable_options,
                                         self.current_curve_options,
                                         self.is_install_auto_design)
                cs_frame.bind('<<Q_change>>', self.q_change)
                self.cs_notebook.add(cs_frame, text=f'set {cs_num}')
                self.cs_frames.append(cs_frame)
            self.cs_notebook.select(self.selected_cs)
            self.cs_notebook.bind('<<NotebookTabChanged>>', self.cs_notebook_tab_changed)
            self.event_generate("<<Q_change>>", when="tail")

    def q_change(self, _event):
        self.event_generate("<<Q_change>>", when="tail")


class CableSetNotebook(ttk.Notebook):
    """Frame showing buried cable parameters"""

    def __init__(self, container: BuriedFrame, install: Install,
                 circuit_options: Dict[str, Circuit],
                 cable_options: Dict[str, Cable],
                 current_curve_options: Dict[str, CurrentCurve], **kw):
        self.container = container
        self.install = install
        self.cable_options = cable_options
        self.current_curve_options = current_curve_options
        super().__init__(container, **kw)

        self.cs_notebook_popup_menu = tkinter.Menu(self, tearoff=0)
        self.cs_notebook_popup_menu.add_command(label="Add cable set", command=self.cs_notebook_add)
        self.cs_notebook_popup_menu.add_command(label="Insert cable set", command=self.cs_notebook_insert)
        self.cs_notebook_popup_menu.add_command(label="Delete cable set", command=self.cs_notebook_delete)
        self.bind("<Button-3>", self.cs_notebook_popup)

    def cs_notebook_popup(self, event):
        try:
            self.cs_notebook_popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.cs_notebook_popup_menu.grab_release()

    def cs_notebook_add(self):
        self.install.insert_cable_set(len(self.install.cable_sets))
        self.container.selected_cs = len(self.install.cable_sets) - 1
        self.container.update_frame()

    def cs_notebook_insert(self):
        self.install.insert_cable_set(self.index(self.select()))
        self.container.update_frame()

    def cs_notebook_delete(self):
        if len(self.install.cable_sets) > 1:
            # selected_cable_set = self.install.cable_sets[self.container.selected_cs]
            self.install.delete_cable_set(self.index(self.select()))
            if self.container.selected_cs == len(self.install.cable_sets):
                self.container.selected_cs = len(self.install.cable_sets) - 1
            self.container.update_frame()
        else:
            tkinter.messagebox.showerror('Delete Cable Set', 'Can not delete last cable set')


class CableSetFrame(tkinter.Frame):
    """Frame showing cable set parameters"""

    def __init__(self, container: Union[tkinter.Frame, ttk.Notebook], cable_set: CableSet,
                 circuit_options: Dict[str, Circuit],
                 cable_options: Dict[str, Cable],
                 current_curve_options: Dict[str, CurrentCurve],
                 is_install_auto_design: Callable, **kw):
        self.container = container
        self.cable_set = cable_set
        super().__init__(container, **kw)
        #
        self.rowconfigure(0, minsize="0", weight=1, pad="0")
        self.rowconfigure(1, minsize="0", weight=1, pad="0")
        self.rowconfigure(2, minsize="0", weight=1, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="150", weight=0, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="5")
        self.columnconfigure(2, minsize="0", weight=1, pad="5")
        self.columnconfigure(3, minsize="0", weight=1, pad="5")
        self.columnconfigure(4, minsize="0", weight=0, pad="0")
        self.columnconfigure(5, minsize="0", weight=0, pad="0")
        self.columnconfigure(6, minsize="0", weight=0, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="groove")

        # Combobox Circuit
        self.ttk_label_cct = ttk.Label(self)
        self.ttk_label_cct.grid(column=0, row=2, sticky="w")
        self.ttk_label_cct.config(width=0, anchor="e", text="Circuit", underline=0)
        # new_widget(Combobox)
        self.circuit_combobox = ComboboxCableSetCircuit(self, self.cable_set, circuit_options)
        self.circuit_combobox.grid(column=1, columnspan=3)
        self.circuit_combobox.grid(row=2)
        self.circuit_combobox.grid(sticky="EW")
        self.circuit_combobox.config(width=32, state="normal")

        # follow previous set
        self.ttk_label_fcs = ttk.Label(self)
        self.ttk_label_fcs.grid(column=0, row=3, sticky="W")
        self.ttk_label_fcs.config(width=0, anchor="w", text="follow cable set", underline=0)
        # Entry box
        self.combo_bool_follow_cs = ComboboxBool(self, cable_set.auto_follow_set, is_install_auto_design)
        self.combo_bool_follow_cs.grid(column=1, row=3, sticky="W")
        self.combo_bool_follow_cs.config(width=8)
        # K.m/W label
        # self.ttk_label_fcs2 = ttk.Label(self)
        # self.ttk_label_fcs2.grid(column=2, row=2, sticky="")
        # self.ttk_label_fcs2.config(width=0, anchor="e", text="", underline=0)

        # Combobox Cable
        self.ttk_label8 = ttk.Label(self)
        self.ttk_label8.grid(column=0, row=4, sticky="w")
        self.ttk_label8.config(width=0, anchor="e", text="Cable", underline=0)
        # new_widget(Combobox)
        self.cable_combobox = ComboboxCableSetCable(self, self.cable_set, cable_options)
        self.cable_combobox.grid(column=1, columnspan=3)
        self.cable_combobox.grid(row=4)
        self.cable_combobox.grid(sticky="EW")
        self.cable_combobox.config(width=32, state="normal")
        # cable size
        self.cable_frame = CableFrame(self, self.cable_set.auto_cable)
        self.cable_frame.grid(column=0, row=5, columnspan=7)
        self.cable_frame.grid(sticky="EW")
        self.cable_frame.bind('<<Q_change>>', self.q_change)

        # Combobox current curve
        self.ttk_label8cc = ttk.Label(self)
        self.ttk_label8cc.grid(column=0, row=25, sticky="w")
        self.ttk_label8cc.config(width=0, anchor="e", text="Current curve", underline=0)
        # new_widget(Combobox)
        self.current_curve_combobox = ComboboxCableSetCurrentCurve(self, self.cable_set, current_curve_options)
        self.current_curve_combobox.grid(column=1, columnspan=3)
        self.current_curve_combobox.grid(row=25)
        self.current_curve_combobox.grid(sticky="EW")
        self.current_curve_combobox.config(width=32, state="normal")

        # voltage
        self.ttk_label_voltage = ttk.Label(self)
        self.ttk_label_voltage.grid(column=0, row=6, sticky="W")
        self.ttk_label_voltage.config(width=0, anchor="e", text="voltage", underline=-1)
        # Entry Box
        self.ttk_entry_voltage = EntryInt(self, self.cable_set.auto_voltage, is_install_auto_design)
        self.ttk_entry_voltage.grid(column=1, row=6, sticky="W")
        self.ttk_entry_voltage.config(width=8)
        # unit Label
        self.ttk_label_voltage_u = ttk.Label(self)
        self.ttk_label_voltage_u.grid(column=2, row=6, sticky="W")
        self.ttk_label_voltage_u.config(width=0, anchor="w", text="kV", underline=-1)

        # frequency
        self.ttk_label_frequency = ttk.Label(self)
        self.ttk_label_frequency.grid(column=5, row=6, sticky="W")
        self.ttk_label_frequency.config(width=0, anchor="e", text="frequency", underline=-1)
        # Entry Box
        self.ttk_entry_frequency = EntryInt(self, self.cable_set.f, is_install_auto_design)
        self.ttk_entry_frequency.grid(column=6, row=6, sticky="W")
        self.ttk_entry_frequency.config(width=8)
        # unit Label
        self.ttk_label_frequency_u = ttk.Label(self)
        self.ttk_label_frequency_u.grid(column=7, row=6, sticky="W")
        self.ttk_label_frequency_u.config(width=0, anchor="w", text="Hz", underline=-1)

        # desired_I
        self.ttk_label_desired_I = ttk.Label(self)
        self.ttk_label_desired_I.grid(column=0, row=7, sticky="W")
        self.ttk_label_desired_I.config(width=0, anchor="e", text="desired I", underline=-1)
        # Entry Box
        self.ttk_entry_desired_I = EntryInt(self, self.cable_set.desired_I, is_install_auto_design)
        self.ttk_entry_desired_I.grid(column=1, row=7, sticky="W")
        self.ttk_entry_desired_I.config(width=8)
        # unit Label
        self.ttk_label_desired_I_u = ttk.Label(self)
        self.ttk_label_desired_I_u.grid(column=2, row=7, sticky="W")
        self.ttk_label_desired_I_u.config(width=0, anchor="e", text="A", underline=-1)
        # change I
        self.ttk_label_desired_I_change = ttk.Label(self)
        self.ttk_label_desired_I_change.grid(column=5, row=7, sticky="E")
        self.ttk_label_desired_I_change.config(width=0, anchor="e", text="allow change", underline=-1)
        # desired_I_change
        self.desired_I_change_combobox = ComboboxBool(self, self.cable_set.desired_I_change, is_install_auto_design)
        self.desired_I_change_combobox.grid(column=6, row=7, sticky="W")
        self.desired_I_change_combobox.config(width=8)

        # Combobox cct type
        self.ttk_label8 = ttk.Label(self)
        self.ttk_label8.grid(column=0, row=8, sticky="w")
        self.ttk_label8.config(width=0, anchor="e", text="circuit type", underline=0)
        # new_widget(Combobox)
        self.type_combobox = ComboboxString(self, self.cable_set.cct_type, is_install_auto_design)
        self.type_combobox.grid(column=1, columnspan=3)
        self.type_combobox.grid(row=8)
        self.type_combobox.grid(sticky='EW')
        self.type_combobox.config(width=32, state="readonly")

        # Combobox duct layout
        self.ttk_label_duct_layout = ttk.Label(self)
        self.ttk_label_duct_layout.grid(column=0, row=9, sticky="w")
        self.ttk_label_duct_layout.config(width=0, anchor="e", text="duct layout", underline=0)
        # new_widget(Combobox)
        self.duct_layout_combobox = ComboboxString(self, self.cable_set.duct_layout, is_install_auto_design)
        self.duct_layout_combobox.grid(column=1, columnspan=3)
        self.duct_layout_combobox.grid(row=9)
        self.duct_layout_combobox.grid(sticky='EW')
        self.duct_layout_combobox.config(width=32, state="readonly")

        # Duct fill TR
        self.ttk_label_fill_tr = ttk.Label(self)
        self.ttk_label_fill_tr.grid(column=5, row=9, sticky="w")
        self.ttk_label_fill_tr.config(width=0, anchor="e", text="duct fill TR", underline=0)
        # new_widget(Entry)
        self.ttk_entry_fill_tr = EntryInt(self, self.cable_set.duct_filling_rho_t, is_install_auto_design)
        self.ttk_entry_fill_tr.grid(column=6)
        self.ttk_entry_fill_tr.grid(row=9)
        self.ttk_entry_fill_tr.grid(sticky="W")
        self.ttk_entry_fill_tr.config(width=8)
        # unit Label
        self.ttk_label_fill_tr_u = ttk.Label(self)
        self.ttk_label_fill_tr_u.grid(column=7, row=9, sticky="W")
        self.ttk_label_fill_tr_u.config(width=0, anchor="w", text="K.m/W", underline=-1)

        # Duct material
        self.ttk_label_duct_mat = ttk.Label(self)
        self.ttk_label_duct_mat.grid(column=0, row=10, sticky="w")
        self.ttk_label_duct_mat.config(width=0, anchor="e", text="duct material", underline=0)
        # new_widget(Combobox)
        self.duct_mat_combobox = ComboboxString(self, self.cable_set.duct_material, is_install_auto_design)
        self.duct_mat_combobox.grid(column=1, columnspan=3)
        self.duct_mat_combobox.grid(row=10)
        self.duct_mat_combobox.grid(sticky="EW")
        self.duct_mat_combobox.config(width=10, state="readonly")

        # duct id / od
        self.ttk_label_duct_id = ttk.Label(self)
        self.ttk_label_duct_id.grid(column=0, row=12, sticky="W")
        self.ttk_label_duct_id.config(width=0, anchor="e", text="duct ID / OD", underline=-1)
        # Entry Box
        self.ttk_entry_duct_id = EntryInt(self, self.cable_set.duct_id, is_install_auto_design)
        self.ttk_entry_duct_id.grid(column=1, row=12, sticky="W")
        self.ttk_entry_duct_id.config(width=8)
        self.ttk_entry_duct_od = EntryInt(self, self.cable_set.duct_od, is_install_auto_design)
        self.ttk_entry_duct_od.grid(column=2, row=12, sticky="W")
        self.ttk_entry_duct_od.config(width=8)
        # mm Label
        self.ttk_label_duct_id_u = ttk.Label(self)
        self.ttk_label_duct_id_u.grid(column=3, row=12, sticky="W")
        self.ttk_label_duct_id_u.config(width=0, anchor="e", text="mm", underline=-1)

        # Combobox bonding
        self.ttk_label_bonding = ttk.Label(self)
        self.ttk_label_bonding.grid(column=0, row=13, sticky="w")
        self.ttk_label_bonding.config(width=0, anchor="e", text="bonding", underline=0)
        # new_widget(Combobox)
        self.bonding_combobox = ComboboxString(self, self.cable_set.bonding, is_install_auto_design)
        self.bonding_combobox.grid(column=1, columnspan=3)
        self.bonding_combobox.grid(row=13)
        self.bonding_combobox.grid(sticky="EW")
        self.bonding_combobox.config(width=32, state="readonly")

        # lengths
        self.ttk_label_length1 = ttk.Label(self)
        self.ttk_label_length1.grid(column=0, row=14, sticky="W")
        self.ttk_label_length1.config(width=0, anchor="e", text="Section lengths", underline=-1)
        # Entry Box length 1
        self.ttk_entry_length1 = EntryInt(self, self.cable_set.length1, is_install_auto_design)
        self.ttk_entry_length1.grid(column=1, row=14, sticky="W")
        self.ttk_entry_length1.config(width=8)
        # Entry Box length 2
        self.ttk_entry_length2 = EntryInt(self, self.cable_set.length2, is_install_auto_design)
        self.ttk_entry_length2.grid(column=2, row=14, sticky="W")
        self.ttk_entry_length2.config(width=8)
        # Entry Box length 3
        self.ttk_entry_length3 = EntryInt(self, self.cable_set.length3, is_install_auto_design)
        self.ttk_entry_length3.grid(column=3, row=14, sticky="W")
        self.ttk_entry_length3.config(width=8)
        # unit Label
        self.ttk_label_length1_u = ttk.Label(self)
        self.ttk_label_length1_u.grid(column=4, row=14, sticky="W")
        self.ttk_label_length1_u.config(width=0, anchor="e", text="m", underline=-1)

        # Combobox formation
        self.ttk_label_formation = ttk.Label(self)
        self.ttk_label_formation.grid(column=0, row=15, sticky="w",)
        self.ttk_label_formation.config(width=0, anchor="e", text="formation", underline=0)
        # new_widget(Combobox)
        self.formation_combobox = ComboboxString(self, self.cable_set.auto_formation, is_install_auto_design)
        self.formation_combobox.grid(column=1, columnspan=3)
        self.formation_combobox.grid(row=15)
        self.formation_combobox.grid(sticky="EW")
        self.formation_combobox.config(width=32, state="readonly")

        # spacing
        self.ttk_label_spacing = ttk.Label(self)
        self.ttk_label_spacing.grid(column=0, row=16, sticky="W")
        self.ttk_label_spacing.config(width=0, anchor="e", text="cable spacing", underline=-1)
        # Entry Box
        self.ttk_entry_spacing = EntryInt(self, self.cable_set.auto_spacing, is_install_auto_design)
        self.ttk_entry_spacing.grid(column=1, row=16, sticky="W")
        self.ttk_entry_spacing.config(width=8)
        # °unit Label
        self.ttk_label_spacing_u = ttk.Label(self)
        self.ttk_label_spacing_u.grid(column=2, row=16, sticky="W")
        self.ttk_label_spacing_u.config(width=0, anchor="e", text="mm", underline=-1)
        # transposed
        self.ttk_label_transposed = ttk.Label(self)
        self.ttk_label_transposed.grid(column=5, row=16, sticky="E")
        self.ttk_label_transposed.config(width=0, anchor="e", text="transposed", underline=-1)
        # desired_I_change
        self.transposed_combobox = ComboboxBool(self, self.cable_set.transposed, is_install_auto_design)
        self.transposed_combobox.grid(column=6, row=16, sticky="W")
        self.transposed_combobox.config(width=8)

        # depth
        self.ttk_label_depth = ttk.Label(self)
        self.ttk_label_depth.grid(column=0, row=17, sticky="W")
        self.ttk_label_depth.config(width=0, anchor="e", text="depth", underline=-1)
        # Entry Box
        self.ttk_entry_depth = EntryInt(self, self.cable_set.auto_depth, is_install_auto_design)
        self.ttk_entry_depth.grid(column=1, row=17, sticky="W")
        self.ttk_entry_depth.config(width=8)
        # unit Label
        self.ttk_label_depth_u = ttk.Label(self)
        self.ttk_label_depth_u.grid(column=2, row=17, sticky="W")
        self.ttk_label_depth_u.config(width=0, anchor="e", text="mm", underline=-1)
        # allow change
        self.ttk_entry_depth_top = ComboboxString(self, self.cable_set.auto_depth_top, is_install_auto_design)
        self.ttk_entry_depth_top.grid(column=5, row=17, sticky="W", columnspan=2)
        self.ttk_entry_depth_top.config(width=20, state='readonly')

        # x location
        self.ttk_label_auto_x = ttk.Label(self)
        self.ttk_label_auto_x.grid(column=0, row=18, sticky="W")
        self.ttk_label_auto_x.config(width=0, anchor="e", text="cable_set x", underline=-1)
        # Entry Box
        self.ttk_entry_auto_x = EntryInt(self, self.cable_set.auto_x, is_install_auto_design)
        self.ttk_entry_auto_x.grid(column=1, row=18, sticky="W")
        self.ttk_entry_auto_x.config(width=8)
        # unit Label
        self.ttk_label_auto_x_u = ttk.Label(self)
        self.ttk_label_auto_x_u.grid(column=2, row=18, sticky="W")
        self.ttk_label_auto_x_u.config(width=0, anchor="e", text="mm", underline=-1)

    def update_frame(self, cable_set: CableSet):
        # self
        self.cable_set = cable_set
        self.cable_combobox.update_combobox(cable_set)
        self.current_curve_combobox.update_combobox(cable_set)
        self.combo_bool_follow_cs.update_combobox(cable_set.auto_follow_set)
        self.ttk_entry_voltage.update_entry(cable_set.auto_voltage)
        self.ttk_entry_frequency.update_entry(cable_set.f)
        self.ttk_entry_desired_I.update_entry(cable_set.desired_I)
        self.desired_I_change_combobox.update_combobox(cable_set.desired_I_change)
        self.type_combobox.update_combobox(cable_set.cct_type)
        self.duct_layout_combobox.update_combobox(cable_set.duct_layout)
        if cable_set.duct_layout.get_value() == iec.NO_DUCTS:
            self.ttk_label_duct_mat.config(state='disable')
            self.duct_mat_combobox.config(state='disable')
            self.ttk_entry_duct_id.config(state='disable')
            self.ttk_label_duct_id.config(state='disable')
            self.ttk_label_duct_id_u.config(state='disable')
            self.ttk_entry_duct_od.config(state='disable')

        else:
            self.ttk_label_duct_mat.config(state='enable')
            self.duct_mat_combobox.config(state='enable')
            self.ttk_label_duct_id.config(state='enable')
            self.ttk_label_duct_id_u.config(state='enable')
            self.ttk_entry_duct_id.config(state='enable')
            self.ttk_entry_duct_od.config(state='enable')
        if cable_set.duct_layout.get_value() in [iec.COMMON_FILLED_DUCT, iec.INDIVIDUAL_FILLED_DUCT]:
            self.ttk_label_fill_tr.config(state='enable')
            self.ttk_entry_fill_tr.config(state='enable')
            self.ttk_label_fill_tr_u.config(state='enable')
        else:
            self.ttk_label_fill_tr.config(state='disable')
            self.ttk_entry_fill_tr.config(state='disable')
            self.ttk_label_fill_tr_u.config(state='disable')
        self.duct_mat_combobox.update_combobox(cable_set.duct_material)
        self.ttk_entry_fill_tr.update_entry(cable_set.duct_filling_rho_t)
        self.ttk_entry_duct_id.update_entry(cable_set.duct_id)
        self.ttk_entry_duct_od.update_entry(cable_set.duct_od)
        self.bonding_combobox.update_combobox(cable_set.bonding)
        if cable_set.bonding.get_value() == iec.CROSS_BONDED:
            self.ttk_entry_length2.config(state='enable')
            self.ttk_entry_length3.config(state='enable')
        else:
            self.ttk_entry_length2.config(state='disable')
            self.ttk_entry_length3.config(state='disable')
        self.ttk_entry_length1.update_entry(cable_set.length1)
        self.ttk_entry_length2.update_entry(cable_set.length2)
        self.ttk_entry_length3.update_entry(cable_set.length3)
        self.formation_combobox.update_combobox(cable_set.auto_formation)
        if cable_set.auto_formation.get_value() in cable_constants.TOUCHING_FORMATION:
            self.ttk_entry_spacing.config(state='disable')
            self.ttk_label_spacing.config(state='disable')
            self.ttk_label_spacing_u.config(state='disable')
        else:
            self.ttk_entry_spacing.config(state='enable')
            self.ttk_label_spacing.config(state='enable')
            self.ttk_label_spacing_u.config(state='enable')
        self.ttk_entry_spacing.update_entry(cable_set.auto_spacing)
        self.transposed_combobox.update_combobox(cable_set.transposed)
        self.ttk_entry_depth.update_entry(cable_set.auto_depth)
        self.ttk_entry_depth_top.update_combobox(cable_set.auto_depth_top)
        self.ttk_entry_auto_x.update_entry(cable_set.auto_x)

        self.cable_frame.update_frame(self.cable_set.auto_cable)
        if isinstance(self.cable_set.auto_cable, AutoCable) and self.cable_set.auto_cable.is_auto_design():
            self.cable_frame.ttk_label_volt.config(state='enable')
            self.cable_frame.cable_volt_combobox.config(state='enable')
            self.cable_frame.ttk_label_cond.config(state='enable')
            self.cable_frame.cable_size_combobox.config(state='enable')
            self.cable_frame.cond_mat_combobox.config(state='enable')
            self.cable_frame.cond_makeup_combobox.config(state='enable')
            self.cable_frame.ttk_label_ins.config(state='enable')
            self.cable_frame.insu_mat_combobox.config(state='enable')
        else:
            self.cable_frame.ttk_label_volt.config(state='disable')
            self.cable_frame.cable_volt_combobox.config(state='disabled')
            self.cable_frame.ttk_label_cond.config(state='disable')
            self.cable_frame.cable_size_combobox.config(state='disabled')
            self.cable_frame.cond_mat_combobox.config(state='disabled')
            self.cable_frame.cond_makeup_combobox.config(state='disabled')
            self.cable_frame.ttk_label_ins.config(state='disable')
            self.cable_frame.insu_mat_combobox.config(state='disabled')

    def q_change(self, _event):
        if isinstance(self.cable_set.auto_cable, AutoCable):
            self.cable_set.auto_cable.auto_design()
        self.event_generate("<<Q_change>>", when="tail")


class CableFrame(tkinter.Frame):
    """Frame showing cable parameters"""

    def __init__(self, container: tkinter.Frame, cable: Cable, **kw):
        self.container = container
        if isinstance(cable, Cable):
            self.cable = cable
        else:
            self.cable = Cable()
        super().__init__(container, **kw)
        #
        self.rowconfigure(0, minsize="0", weight=0, pad="0")
        self.columnconfigure(0, minsize="150", weight=0, pad="0")
        self.columnconfigure(1, minsize="0", weight=0, pad="5")
        self.columnconfigure(2, minsize="0", weight=0, pad="5")
        self.columnconfigure(3, minsize="0", weight=0, pad="5")
        self.columnconfigure(4, minsize="0", weight=0, pad="0")
        self.columnconfigure(5, minsize="0", weight=0, pad="0")
        self.columnconfigure(6, minsize="0", weight=0, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="flat")

        # voltage
        self.ttk_label_volt = ttk.Label(self)
        self.ttk_label_volt.grid(column=0, row=6, sticky="W")
        self.ttk_label_volt.config(width=0, anchor="e", text="voltage", underline=-1)
        # volt (Combobox)
        self.cable_volt_combobox = ComboboxString(self, self.cable.nominal_volts, lambda: True)
        self.cable_volt_combobox.grid(column=1)
        self.cable_volt_combobox.grid(row=6)
        self.cable_volt_combobox.grid(sticky='EW')
        self.cable_volt_combobox.config(width=13, state="readonly")

        # conductor
        self.ttk_label_cond = ttk.Label(self)
        self.ttk_label_cond.grid(column=0, row=7, sticky="W")
        self.ttk_label_cond.config(width=0, anchor="e", text="conductor", underline=-1)
        # size (Combobox)
        self.cable_size_combobox = ComboboxString(self, self.cable.conductor.size, lambda: True)
        self.cable_size_combobox.grid(column=1)
        self.cable_size_combobox.grid(row=7)
        self.cable_size_combobox.grid(sticky='EW')
        self.cable_size_combobox.config(width=13, state="readonly")
        # material (Combobox)
        self.cond_mat_combobox = ComboboxString(self, self.cable.conductor.material, lambda: True)
        self.cond_mat_combobox.grid(column=2)
        self.cond_mat_combobox.grid(row=7)
        self.cond_mat_combobox.grid(sticky='EW')
        self.cond_mat_combobox.config(width=10, state="readonly")
        # makeup (Combobox)
        self.cond_makeup_combobox = ComboboxString(self, self.cable.conductor.makeup, lambda: True)
        self.cond_makeup_combobox.grid(column=1, columnspan=2)
        self.cond_makeup_combobox.grid(row=8)
        self.cond_makeup_combobox.grid(sticky='EW')
        self.cond_makeup_combobox.config(width=55, state="readonly")

        # Insulation
        self.ttk_label_ins = ttk.Label(self)
        self.ttk_label_ins.grid(column=0, row=9, sticky="W")
        self.ttk_label_ins.config(width=0, anchor="e", text="insulation", underline=-1)
        # insulation material
        self.insu_mat_combobox = ComboboxString(self, self.cable.core.insulation_material, lambda: True)
        self.insu_mat_combobox.grid(column=1, columnspan=3)
        self.insu_mat_combobox.grid(row=9)
        self.insu_mat_combobox.grid(sticky='EW')
        self.insu_mat_combobox.config(width=55, state="readonly")

    def update_frame(self, cable: Cable):
        if isinstance(cable, Cable):
            self.cable = cable
        else:
            self.cable = Cable()
        self.cable_volt_combobox.update_combobox(self.cable.nominal_volts)
        self.cable_size_combobox.update_combobox(self.cable.conductor.size)
        self.cond_makeup_combobox.update_combobox(self.cable.conductor.makeup)
        self.insu_mat_combobox.update_combobox(self.cable.core.insulation_material)
        self.cond_mat_combobox.update_combobox(self.cable.conductor.material)

    def q_change(self, _event):
        self.event_generate("<<Q_change>>", when="tail")


class ComboboxCableSetCable(ttk.Combobox):
    """Combobox for values tied to cable in a cable set"""

    def __init__(self, container, cable_set: CableSet, options: Dict[str, Optional[Cable]], **kw):
        super().__init__(container, **kw)
        self.container = container
        self.cable_set = cable_set
        self.cable_options = options.copy()
        self.cable_options['<None>'] = None

        option_names = list(self.cable_options.keys())
        self.config(values=option_names)

        self.string_var = tkinter.StringVar()
        if self.cable_set.auto_cable is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(self.cable_set.auto_cable.name)

        self.config(textvariable=self.string_var)

        self.bind('<<ComboboxSelected>>', lambda
                  event: self.selected_callback(event)
                  )

    def update_combobox(self, cable_set: CableSet):
        self.cable_set = cable_set
        if self.cable_set.auto_cable is None:
            value = None
        else:
            value = self.cable_set.auto_cable.name
        if value is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(value)

    def selected_callback(self, _event):
        try:
            str_value = str(self.string_var.get())
            self.cable_set.auto_cable = self.cable_options[str_value]
            self.cable_set.auto_cable_source = 'overview set'
            # self.string_var.set(self.data_store.get_value())
            self.container.event_generate("<<Q_change>>", when="tail")
        except ValueError:
            self.string_var.set(self.cable_set.auto_cable.name)


class ComboboxCableSetCurrentCurve(ttk.Combobox):
    """Combobox for values tied to cable in a cable set"""

    def __init__(self, container, cable_set: CableSet, options: Dict[str, Optional[CurrentCurve]], **kw):
        super().__init__(container, **kw)
        self.container = container
        self.cable_set = cable_set
        self.combobox_options = options.copy()
        self.combobox_options['<None>'] = None

        option_names = list(self.combobox_options.keys())
        self.config(values=option_names)

        self.string_var = tkinter.StringVar()
        if self.cable_set.current_curve is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(self.cable_set.current_curve.name)

        self.config(textvariable=self.string_var)

        self.bind('<<ComboboxSelected>>', lambda
                  event: self.selected_callback(event)
                  )

    def update_combobox(self, cable_set: CableSet):
        self.cable_set = cable_set
        if self.cable_set.current_curve is None:
            value = None
        else:
            value = self.cable_set.current_curve.name
        if value is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(value)

    def selected_callback(self, _event):
        try:
            str_value = str(self.string_var.get())
            self.cable_set.current_curve = self.combobox_options[str_value]
            # self.cable_set.auto_cable_source = 'overview set'
            # self.string_var.set(self.data_store.get_value())
            self.container.event_generate("<<Q_change>>", when="tail")
        except ValueError:
            self.string_var.set(self.cable_set.current_curve.name)


class ComboboxCableSetCircuit(ttk.Combobox):
    """Combobox for values tied to cable in a cable set"""

    def __init__(self, container, cable_set: CableSet, options: Dict[str, Optional[Circuit]], **kw):
        super().__init__(container, **kw)
        self.container = container
        self.cable_set = cable_set
        self.combobox_options = options.copy()
        self.combobox_options['<None>'] = None

        option_names = list(self.combobox_options.keys())
        self.config(values=option_names)

        self.string_var = tkinter.StringVar()
        if self.cable_set.circuit is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(self.cable_set.circuit.name)

        self.config(textvariable=self.string_var)

        self.bind('<<ComboboxSelected>>', lambda
                  event: self.selected_callback(event)
                  )

    def update_combobox(self, cable_set: CableSet):
        self.cable_set = cable_set
        if self.cable_set.circuit is None:
            value = None
        else:
            value = self.cable_set.circuit.name
        if value is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(value)

    def selected_callback(self, _event):
        try:
            str_value = str(self.string_var.get())
            self.cable_set.circuit = self.combobox_options[str_value]
            # self.cable_set.auto_cable_source = 'overview set'
            # self.string_var.set(self.data_store.get_value())
            self.container.event_generate("<<Q_change>>", when="tail")
        except ValueError:
            self.string_var.set(self.cable_set.circuit.name)
