import tkinter
from tkinter import ttk
from collections.abc import Callable

from cabsys.gui.overview_widgets import EntryInt, ComboboxBool, ComboboxString

from cabsys.data_classes.auto_cable import AutoCable
from cabsys.data_classes.cable import Cable
import cabsys.iec.iec_constants as iec
import cabsys.data_classes.cable_constants as cc
import cabsys.iec.iec60949 as iec60949


class CableOverviewFrame(tkinter.Frame):
    """binder for GuiCollection"""

    def __init__(self, cable: Cable, foil_rt: float = None, **kw):
        self.cable = cable
        if isinstance(cable, AutoCable):
            cable.auto_design()
        super().__init__(**kw)

        self.rowconfigure(0, minsize="0", weight=0, pad="0")
        self.rowconfigure(1, minsize="0", weight=0, pad="0")
        self.rowconfigure(2, minsize="0", weight=0, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="0", weight=0, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        # self.config(height="0")
        # self.config(width="0")
        self.config(relief="flat")

        # frame for all cable
        self.common_frame = CommonFrame(self, self.cable, self.is_cable_auto_design)
        self.common_frame.grid(column=0, row=0)
        self.common_frame.grid(sticky="EW")
        self.common_frame.bind('<<Q_change>>', self.q_change)
        # frame for calculated parameters
        self.calc_frame = CalcFrame(self, self.cable, self.is_cable_auto_design, foil_rt)
        self.calc_frame.grid(column=0)
        self.calc_frame.grid(row=1)
        self.calc_frame.grid(sticky="EW")
        self.calc_frame.bind('<<Q_change>>', self.q_change)
        # frame for cable details
        self.buried_frame = DetailsFrame(self, self.cable, self.is_cable_auto_design)
        self.buried_frame.grid(column=0)
        self.buried_frame.grid(row=2)
        self.buried_frame.grid(sticky="EW")
        self.buried_frame.bind('<<Q_change>>', self.q_change)

    def is_cable_auto_design(self):
        if isinstance(self.cable, AutoCable):
            return self.cable.is_auto_design()
        else:
            return None

    def update_frame(self):
        self.common_frame.update_frame()
        if not isinstance(self.cable, AutoCable) or (isinstance(self.cable, AutoCable) and self.cable.is_auto_design()):
            self.calc_frame.grid()
            self.calc_frame.update_frame()
        else:
            self.calc_frame.grid_remove()
        self.buried_frame.update_frame()

    def q_change(self, _event):
        try:
            if isinstance(self.cable, AutoCable):

                # check that sheath type is available for insulation material, if not reset sheath type to default
                if self.cable.core.insulation_material.value is not None:
                    options = list(cc.SHEATH_TABLE[self.cable.core.insulation_material.value].keys())
                    options.append('<default>')
                    if self.cable.sheath_type.value not in options:
                        self.cable.sheath_type.value = None
                        self.cable.sheath_type.source = None

                self.cable.auto_design()
        finally:
            self.update_frame()
            self.event_generate("<<Q_change>>", when="tail")


class CommonFrame(tkinter.Frame):
    """Frame showing common cableparameters"""

    def __init__(self, container: tkinter.Frame, cable: Cable, is_cable_auto_design: Callable, **kw):
        self.container = container
        self.cable = cable
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
        self.columnconfigure(0, minsize="0", weight=1, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="groove")

        # Combobox Number of cores
        self.ttk_label_type8 = ttk.Label(self)
        self.ttk_label_type8.grid(column=0, row=1, sticky="w")
        self.ttk_label_type8.config(width=0, anchor="e", text="number cores", underline=0)
        # Number of cores (Combobox)
        self.cores_combobox = ComboboxString(self, self.cable.number_cores, is_cable_auto_design)
        self.cores_combobox.grid(column=1)
        self.cores_combobox.grid(row=1)
        self.cores_combobox.grid(sticky="W")
        self.cores_combobox.config(width=20, state="readonly")
        # Belted (label)
        self.ttk_label_belt = ttk.Label(self)
        self.ttk_label_belt.grid(column=2, row=1, sticky="w")
        self.ttk_label_belt.config(width=0, anchor="e", text="belted", underline=0)
        # belted (Combobox)
        self.belt_combobox = ComboboxBool(self, self.cable.belted, is_cable_auto_design)
        self.belt_combobox.grid(column=3)
        self.belt_combobox.grid(row=1)
        self.belt_combobox.grid(sticky="W")
        self.belt_combobox.config(width=10, state="readonly")

        # Combobox Design Voltage
        self.ttk_label_6 = ttk.Label(self)
        self.ttk_label_6.grid(column=0, row=2, sticky="W")
        self.ttk_label_6.config(width=0, anchor="e", text="Nominal voltage", underline=-1)
        # ComboBox
        self.combobox_volts = ComboboxString(self, self.cable.nominal_volts, is_cable_auto_design)
        self.combobox_volts.grid(column=1, row=2, sticky="W")
        self.combobox_volts.config(width=20, state="readonly")
        # °C Label
        self.ttk_label_7 = ttk.Label(self)
        self.ttk_label_7.grid(column=2, row=2, sticky="w")
        self.ttk_label_7.config(width=0, anchor="w", text="kV", underline=-1)

        # Combobox conductor size
        self.ttk_label_type8 = ttk.Label(self)
        self.ttk_label_type8.grid(column=0, row=3, sticky="w")
        self.ttk_label_type8.config(width=0, anchor="e", text="conductor size", underline=0)
        # new_widget(Combobox)
        self.cond_size_combobox = ComboboxString(self, self.cable.conductor.size, is_cable_auto_design)
        self.cond_size_combobox.grid(column=1)
        self.cond_size_combobox.grid(row=3)
        self.cond_size_combobox.grid(sticky="W")
        self.cond_size_combobox.config(width=20, state="readonly")

        # Combobox insulation material
        self.ttk_label_type8 = ttk.Label(self)
        self.ttk_label_type8.grid(column=0, row=4, sticky="w")
        self.ttk_label_type8.config(width=0, anchor="e", text="insulation", underline=0)
        # new_widget(Combobox)
        self.cond_ins_combobox = ComboboxString(self, self.cable.core.insulation_material, is_cable_auto_design)
        self.cond_ins_combobox.grid(column=1, columnspan=3)
        self.cond_ins_combobox.grid(row=4)
        self.cond_ins_combobox.grid(sticky="W")
        self.cond_ins_combobox.config(width=55, state="readonly")

        # metal sheath separate
        self.ttk_label_sep_sheath = ttk.Label(self)
        self.ttk_label_sep_sheath.grid(column=0, row=5, sticky="w")
        self.ttk_label_sep_sheath.config(width=0, anchor="e", text="separate sheath", underline=0)
        # new_widget(Combobox)
        self.sep_sheath_combobox = ComboboxBool(self, self.cable.separate_sheath, is_cable_auto_design)
        self.sep_sheath_combobox.grid(column=1, columnspan=3)
        self.sep_sheath_combobox.grid(row=5)
        self.sep_sheath_combobox.grid(sticky="W")
        self.sep_sheath_combobox.config(width=10, state="readonly")

        # metal sheath / screen type
        self.ttk_label_sheath_type = ttk.Label(self)
        self.ttk_label_sheath_type.grid(column=0, row=6, sticky="w")
        self.ttk_label_sheath_type.config(width=0, anchor="e", text="sheath type", underline=0)
        # new_widget(Combobox)
        self.sheath_type_combobox = ComboboxString(self, self.cable.sheath_type, is_cable_auto_design)
        self.sheath_type_combobox.grid(column=1, columnspan=3)
        self.sheath_type_combobox.grid(row=6)
        self.sheath_type_combobox.grid(sticky="W")
        self.sheath_type_combobox.config(width=45, state="readonly")

        # wire screen
        self.ttk_label_cws_mat = ttk.Label(self)
        self.ttk_label_cws_mat.grid(column=0, row=7, sticky="w")
        self.ttk_label_cws_mat.config(width=0, anchor="e", text="wire screen material", underline=0)
        # material (Combobox)
        self.cws_material_combobox = ComboboxString(self, self.cable.wire_screen.material, is_cable_auto_design)
        self.cws_material_combobox.grid(column=1)
        self.cws_material_combobox.grid(row=7)
        self.cws_material_combobox.grid(sticky="W")
        self.cws_material_combobox.config(width=20, state="readonly")

        # metal sheath
        self.ttk_label_sheath_mat = ttk.Label(self)
        self.ttk_label_sheath_mat.grid(column=0, row=8, sticky="w")
        self.ttk_label_sheath_mat.config(width=0, anchor="e", text="metal sheath material", underline=0)
        # material (Combobox)
        self.sheath_material_combobox = ComboboxString(self, self.cable.sheath.material, is_cable_auto_design)
        self.sheath_material_combobox.grid(column=1)
        self.sheath_material_combobox.grid(row=8)
        self.sheath_material_combobox.grid(sticky="W")
        self.sheath_material_combobox.config(width=20, state="readonly")

        # tape screen
        self.ttk_label_tape_screen_mat = ttk.Label(self)
        self.ttk_label_tape_screen_mat.grid(column=0, row=9, sticky="w")
        self.ttk_label_tape_screen_mat.config(width=0, anchor="e", text="tape_screen material", underline=0)
        # material (Combobox)
        self.tape_screen_material_combobox = ComboboxString(self, self.cable.tape.material, is_cable_auto_design)
        self.tape_screen_material_combobox.grid(column=1)
        self.tape_screen_material_combobox.grid(row=9)
        self.tape_screen_material_combobox.grid(sticky="W")
        self.tape_screen_material_combobox.config(width=20, state="readonly")

    def update_frame(self):
        if not isinstance(self.cable, AutoCable) or (isinstance(self.cable, AutoCable) and self.cable.is_auto_design()):
            self.ttk_label_sheath_type.grid()
            self.sheath_type_combobox.grid()
        else:
            self.ttk_label_sheath_type.grid_remove()
            self.sheath_type_combobox.grid_remove()
        self.cores_combobox.update_combobox()
        if self.cable.number_cores.get_value() == iec.THREE_CORE:
            self.belt_combobox.config(state="readonly")
            self.ttk_label_belt.config(state='enable')
            self.sep_sheath_combobox.config(state="readonly")
            self.ttk_label_sep_sheath.config(state='enable')
        else:
            self.belt_combobox.config(state='disable')
            self.ttk_label_belt.config(state='disable')
            self.sep_sheath_combobox.config(state='disable')
            self.ttk_label_sep_sheath.config(state='disable')
        self.belt_combobox.update_combobox()
        self.cond_size_combobox.update_combobox()
        self.combobox_volts.update_combobox()
        self.cond_ins_combobox.update_combobox()
        self.sep_sheath_combobox.update_combobox()
        if isinstance(self.cable, AutoCable) and self.cable.is_auto_design():
            options = list(cc.SHEATH_TABLE[self.cable.core.insulation_material.value].keys())
            options.append('<default>')
            self.sheath_type_combobox.config(values=options)
            self.sheath_type_combobox.update_combobox()
        self.cws_material_combobox.update_combobox()
        self.sheath_material_combobox.update_combobox()
        self.tape_screen_material_combobox.update_combobox()


class CalcFrame(tkinter.Frame):
    """Frame showing calculated parameters"""

    def __init__(self, container: tkinter.Frame, cable: Cable, is_cable_auto_design: Callable,
                 foil_rt: float = None, **kw):
        self.container = container
        self.cable = cable
        super().__init__(container, **kw)

        self.rowconfigure(0, minsize="0", weight=1, pad="0")
        self.rowconfigure(1, minsize="0", weight=1, pad="0")
        self.rowconfigure(2, minsize="0", weight=1, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="0", weight=1, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        self.columnconfigure(3, minsize="0", weight=1, pad="0")
        self.columnconfigure(4, minsize="0", weight=1, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="groove")

        # short circuit values
        cond_short_cct = '###'
        sheath_short_cct = '###'
        self.ttk_label_sc = ttk.Label(self)
        self.ttk_label_sc.grid(column=0, row=0, sticky="W")
        self.ttk_label_sc.config(width=30, anchor="w", text="short circuit rating (kA)", underline=0)
        # conductor short circuit (Entry box)
        self.ttk_label05 = ttk.Label(self)
        self.ttk_label05.grid(column=1, row=0, sticky="e")
        self.ttk_label05.config(width=0, anchor="e", text="conductor:", underline=0)
        self.ttk_label07 = ttk.Label(self)
        self.ttk_label07.grid(column=2, row=0, sticky="w")
        self.ttk_label07.config(width=0, anchor="w", text=str(cond_short_cct), underline=0, state="disable")
        # sheath short circuit (Entry box)
        self.ttk_label08 = ttk.Label(self)
        self.ttk_label08.grid(column=3, row=0, sticky="e")
        self.ttk_label08.config(width=0, anchor="e", text="sheath:", underline=0)
        self.ttk_label09 = ttk.Label(self)
        self.ttk_label09.grid(column=4, row=0, sticky="w")
        self.ttk_label09.config(width=0, anchor="w", text=str(sheath_short_cct), underline=0, state="disable")

        # Stress label
        self.ttk_label10 = ttk.Label(self)
        self.ttk_label10.grid(column=1, row=1, sticky="e")
        self.ttk_label10.config(width=0, anchor="e", text="max:", underline=0)
        self.ttk_label10 = ttk.Label(self)
        self.ttk_label10.grid(column=3, row=1, sticky="e")
        self.ttk_label10.config(width=0, anchor="e", text="actual:", underline=0)

        # Conductor stress
        self.ttk_label_cs = ttk.Label(self)
        self.ttk_label_cs.grid(column=0, row=1, sticky="W")
        self.ttk_label_cs.config(width=30, anchor="w", text="conductor screen stress (kV/mm)", underline=0)
        # max conductor stress (Entry box)
        self.max_cond_stress_entry = EntryInt(self, self.cable.core.max_cond_stress, is_cable_auto_design)
        self.max_cond_stress_entry.grid(column=2, row=1, sticky="W")
        self.max_cond_stress_entry.config(width=10)
        # actual conductor stress (Entry box)
        if cable.calc_cond_stress() is not None:
            cond_stress = round(cable.calc_cond_stress(), 2)
        else:
            cond_stress = '-'
        self.cond_stress_entry = ttk.Label(self)
        self.cond_stress_entry.grid(column=4, row=1, sticky="W")
        self.cond_stress_entry.config(width=10)
        self.cond_stress_entry.config(state='disabled', text=cond_stress)

        # Stress label
        self.ttk_label20 = ttk.Label(self)
        self.ttk_label20.grid(column=1, row=2, sticky="e")
        self.ttk_label20.config(width=0, anchor="e", text="max:", underline=0)
        self.ttk_label25 = ttk.Label(self)
        self.ttk_label25.grid(column=3, row=2, sticky="e")
        self.ttk_label25.config(width=0, anchor="e", text="actual:", underline=0)

        # insulation screen stress
        self.ttk_label_is = ttk.Label(self)
        self.ttk_label_is.grid(column=0, row=2, sticky="W")
        self.ttk_label_is.config(width=30, anchor="w", text="insulation screen stress (kV/mm)", underline=0)
        # max conductor stress (Entry box)
        self.max_ins_stress_entry = EntryInt(self, self.cable.core.max_insu_stress, is_cable_auto_design)
        self.max_ins_stress_entry.grid(column=2, row=2, sticky="W")
        self.max_ins_stress_entry.config(width=10)
        # actual conductor stress (Entry box)
        if cable.calc_ins_stress() is not None:
            ins_stress = round(cable.calc_ins_stress(), 2)
        else:
            ins_stress = '-'
        self.ins_stress_entry = ttk.Label(self)
        self.ins_stress_entry.grid(column=4, row=2, sticky="W")
        self.ins_stress_entry.config(width=10)
        self.ins_stress_entry.config(state='disabled', text=ins_stress)

        self.update_frame()

    def update_frame(self, foil_rt: float = None):
        try:
            cond_short_cct = round(iec60949.calc_cond_short_cct(self.cable).get_value(unit='A') / 1e3, 1)
        except iec60949.IEC60949Exception:
            cond_short_cct = '###'

        try:
            sheath_short_cct = round(iec60949.calc_sheath_short_cct(self.cable, foil_rt).get_value(unit='A') / 1e3, 1)
        except iec60949.IEC60949Exception:
            sheath_short_cct = '###'

        self.ttk_label07.config(width=0, anchor="w", text=str(cond_short_cct), underline=0, state="disable")
        self.ttk_label09.config(width=0, anchor="w", text=str(sheath_short_cct), underline=0, state="disable")

        self.max_cond_stress_entry.update_entry()
        calc_cond_stress = self.cable.calc_cond_stress()
        if calc_cond_stress is not None:
            cond_stress = round(self.cable.calc_cond_stress(), 2)
        else:
            cond_stress = '<None>'
        self.cond_stress_entry.config(text=cond_stress)
        self.max_ins_stress_entry.update_entry()
        calc_ins_stress = self.cable.calc_ins_stress()
        if calc_ins_stress is not None:
            ins_stress = round(self.cable.calc_ins_stress(), 2)
        else:
            ins_stress = '<None>'
        self.ins_stress_entry.config(text=ins_stress)


class DetailsFrame(tkinter.Frame):
    """Frame showing buried cable parameters"""

    def __init__(self, container: tkinter.Frame, cable: Cable, is_cable_auto_design: Callable, **kw):
        self.container = container
        self.cable = cable
        super().__init__(container, **kw)
        self.rowconfigure(0, minsize="0", weight=0, pad="0")
        self.rowconfigure(1, minsize="0", weight=0, pad="0")
        self.rowconfigure(2, minsize="0", weight=0, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="0", weight=1, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="groove")

        # Diameter label
        self.ttk_label10 = ttk.Label(self)
        self.ttk_label10.grid(column=5, row=0, sticky="")
        self.ttk_label10.config(width=0, anchor="e", text="diameter", underline=0)

        # Duct
        self.ttk_label_duct = ttk.Label(self)
        self.ttk_label_duct.grid(column=0, row=1, sticky="W")
        self.ttk_label_duct.config(width=0, anchor="e", text="duct", underline=0)
        # diameter (Entry box)
        self.duct_dia_entry = EntryInt(self, self.cable.conductor.duct_dia, is_cable_auto_design)
        self.duct_dia_entry.grid(column=5, row=1, sticky="W")
        self.duct_dia_entry.config(width=10)

        # Duct Spiral
        self.ttk_label_spiral = ttk.Label(self)
        self.ttk_label_spiral.grid(column=0, row=2, sticky="W")
        self.ttk_label_spiral.config(width=0, anchor="e", text="spiral", underline=0)
        # makeup (Combobox)
        self.spiral_mat_combobox = ComboboxString(self, self.cable.conductor.spiral_material, is_cable_auto_design)
        self.spiral_mat_combobox.grid(column=1)
        self.spiral_mat_combobox.grid(row=2)
        self.spiral_mat_combobox.grid(sticky="W")
        self.spiral_mat_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.spiral_dia_entry = EntryInt(self, self.cable.conductor.spiral_dia, is_cable_auto_design)
        self.spiral_dia_entry.grid(column=5, row=2, sticky="W")
        self.spiral_dia_entry.config(width=10)

        # Conductor
        self.ttk_label9 = ttk.Label(self)
        self.ttk_label9.grid(column=0, row=3, sticky="W")
        self.ttk_label9.config(width=0, anchor="e", text="conductor", underline=0)
        # material (Combobox)
        self.cond_material_combobox = ComboboxString(self, self.cable.conductor.material, is_cable_auto_design)
        self.cond_material_combobox.grid(column=1)
        self.cond_material_combobox.grid(row=3)
        self.cond_material_combobox.grid(sticky="W")
        self.cond_material_combobox.config(width=25, state="readonly")
        # makeup (Combobox)
        self.cond_makeup_combobox = ComboboxString(self, self.cable.conductor.makeup, is_cable_auto_design)
        self.cond_makeup_combobox.grid(column=2, row=3, columnspan=3)
        self.cond_makeup_combobox.grid(sticky="W")
        self.cond_makeup_combobox.config(width=40, state="readonly")
        # diameter (Entry box)
        self.cond_dia_entry = EntryInt(self, self.cable.conductor.dia, is_cable_auto_design)
        self.cond_dia_entry.grid(column=5, row=3, sticky="W")
        self.cond_dia_entry.config(width=10)

        # Binder
        self.ttk_label_binder = ttk.Label(self)
        self.ttk_label_binder.grid(column=0, row=4, sticky="W")
        self.ttk_label_binder.config(width=0, anchor="e", text="binder", underline=0)
        # material (Combobox)
        self.binder_material_combobox = ComboboxString(self, self.cable.core.binder_material, is_cable_auto_design)
        self.binder_material_combobox.grid(column=1)
        self.binder_material_combobox.grid(row=4)
        self.binder_material_combobox.grid(sticky="W")
        self.binder_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.binder_dia_entry = EntryInt(self, self.cable.core.binder_dia, is_cable_auto_design)
        self.binder_dia_entry.grid(column=5, row=4, sticky="W")
        self.binder_dia_entry.config(width=10)

        # Conductor Screen
        self.ttk_label_cond_screen = ttk.Label(self)
        self.ttk_label_cond_screen.grid(column=0, row=5, sticky="W")
        self.ttk_label_cond_screen.config(width=0, anchor="e", text="screen", underline=0)
        # material (Combobox)
        self.cond_screen_material_combobox = ComboboxString(self, self.cable.core.cond_screen_material,
                                                            is_cable_auto_design)
        self.cond_screen_material_combobox.grid(column=1)
        self.cond_screen_material_combobox.grid(row=5)
        self.cond_screen_material_combobox.grid(sticky="W")
        self.cond_screen_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.cond_screen_dia_entry = EntryInt(self, self.cable.core.cond_screen_dia, is_cable_auto_design)
        self.cond_screen_dia_entry.grid(column=5, row=5, sticky="W")
        self.cond_screen_dia_entry.config(width=10)

        # Insulation
        self.ttk_label_ins = ttk.Label(self)
        self.ttk_label_ins.grid(column=0, row=6, sticky="W")
        self.ttk_label_ins.config(width=0, anchor="e", text="insulation", underline=0)

        # thickness label
        self.ttk_label_rt = ttk.Label(self)
        self.ttk_label_rt.grid(column=2, row=6, sticky="EW")
        self.ttk_label_rt.config(width=0, anchor="w", text="nominal thickness", underline=0)
        # thickness (Entry box)
        self.ins_rt_entry = EntryInt(self, self.cable.core.nom_insu_rt, is_cable_auto_design)
        self.ins_rt_entry.grid(column=3, row=6, sticky="W")
        self.ins_rt_entry.config(width=10)
        # unit
        self.ttk_label_u = ttk.Label(self)
        self.ttk_label_u.grid(column=4, row=6, sticky="E")
        self.ttk_label_u.config(width=0, anchor="e", text="mm", underline=0)
        # diameter (Entry box)
        self.ins_dia_entry = EntryInt(self, self.cable.core.insu_dia, is_cable_auto_design)
        self.ins_dia_entry.grid(column=5, row=6, sticky="W")
        self.ins_dia_entry.config(width=10)

        # Belted Insulation
        self.ttk_label_belt_ins = ttk.Label(self)
        self.ttk_label_belt_ins.grid(column=0, row=7, sticky="W")
        self.ttk_label_belt_ins.config(width=0, anchor="e", text="belted insulation", underline=0)
        # diameter (Entry box)
        self.belt_ins_dia_entry = EntryInt(self, self.cable.core.belt_dia, is_cable_auto_design)
        self.belt_ins_dia_entry.grid(column=5, row=7, sticky="W")
        self.belt_ins_dia_entry.config(width=10)

        # Insulation Screen
        self.ttk_label_ins_screen = ttk.Label(self)
        self.ttk_label_ins_screen.grid(column=0, row=8, sticky="W")
        self.ttk_label_ins_screen.config(width=0, anchor="e", text="screen", underline=0)
        # material (Combobox)
        self.insu_screen_material_combobox = ComboboxString(self, self.cable.core.insu_screen_material,
                                                            is_cable_auto_design)
        self.insu_screen_material_combobox.grid(column=1)
        self.insu_screen_material_combobox.grid(row=8)
        self.insu_screen_material_combobox.grid(sticky="W")
        self.insu_screen_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.ins_screen_dia_entry = EntryInt(self, self.cable.core.insu_screen_dia, is_cable_auto_design)
        self.ins_screen_dia_entry.grid(column=5, row=8, sticky="W")
        self.ins_screen_dia_entry.config(width=10)

        # bedding
        self.ttk_label_bedding = ttk.Label(self)
        self.ttk_label_bedding.grid(column=0, row=9, sticky="W")
        self.ttk_label_bedding.config(width=0, anchor="e", text="bedding", underline=0)
        # material (Combobox)
        self.core_bedding_material_combobox = ComboboxString(self, self.cable.core.bedding_material,
                                                             is_cable_auto_design)
        self.core_bedding_material_combobox.grid(column=1)
        self.core_bedding_material_combobox.grid(row=9)
        self.core_bedding_material_combobox.grid(sticky="W")
        self.core_bedding_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.bedding_dia_entry = EntryInt(self, self.cable.core.bedding_dia, is_cable_auto_design)
        self.bedding_dia_entry.grid(column=5, row=9, sticky="W")
        self.bedding_dia_entry.config(width=10)

        # wire screen bedding
        self.ttk_label_cws_bedding = ttk.Label(self)
        self.ttk_label_cws_bedding.grid(column=0, row=10, sticky="W")
        self.ttk_label_cws_bedding.config(width=0, anchor="e", text="under wire", underline=0)
        # material (Combobox)
        self.cws_bedding_material_combobox = ComboboxString(self, self.cable.wire_screen.under_wire_material,
                                                            is_cable_auto_design)
        self.cws_bedding_material_combobox.grid(column=1)
        self.cws_bedding_material_combobox.grid(row=10)
        self.cws_bedding_material_combobox.grid(sticky="W")
        self.cws_bedding_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.cws_bedding_dia_entry = EntryInt(self, self.cable.wire_screen.dia_under_wire, is_cable_auto_design)
        self.cws_bedding_dia_entry.grid(column=5, row=10, sticky="W")
        self.cws_bedding_dia_entry.config(width=10)

        # wire screen
        self.ttk_label_cws = ttk.Label(self)
        self.ttk_label_cws.grid(column=0, row=11, sticky="W")
        self.ttk_label_cws.config(width=0, anchor="e", text="wire screen", underline=0)
        # wire screen frame
        self.wire_screen_frame = WireScreenFrame(self, self.cable, is_cable_auto_design)
        self.wire_screen_frame.grid(column=2, row=11, columnspan=2)
        self.wire_screen_frame.grid(sticky="EW")
        self.wire_screen_frame.bind('<<Q_change>>', self.q_change)
        # diameter (Entry box)
        self.cws_dia_entry = EntryInt(self, self.cable.wire_screen.dia, is_cable_auto_design)
        self.cws_dia_entry.grid(column=5, row=11, sticky="W")
        self.cws_dia_entry.config(width=10)

        # over wire binder
        self.ttk_label_over_wire = ttk.Label(self)
        self.ttk_label_over_wire.grid(column=0, row=12, sticky="W")
        self.ttk_label_over_wire.config(width=0, anchor="e", text="over wire binder", underline=0)
        # material (Combobox)
        self.cws_binder_material_combobox = ComboboxString(self, self.cable.wire_screen.binder_material,
                                                           is_cable_auto_design)
        self.cws_binder_material_combobox.grid(column=1)
        self.cws_binder_material_combobox.grid(row=12)
        self.cws_binder_material_combobox.grid(sticky="W")
        self.cws_binder_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.over_wire_dia_entry = EntryInt(self, self.cable.wire_screen.binder_dia, is_cable_auto_design)
        self.over_wire_dia_entry.grid(column=5, row=12, sticky="W")
        self.over_wire_dia_entry.config(width=10)

        # under sheath clearance
        self.ttk_label_under_sheath = ttk.Label(self)
        self.ttk_label_under_sheath.grid(column=0, row=13, sticky="W")
        self.ttk_label_under_sheath.config(width=0, anchor="e", text="under metal sheath", underline=0)
        # material (Combobox)
        self.clearance_material_combobox = ComboboxString(self, self.cable.sheath.under_sheath_material,
                                                          is_cable_auto_design)
        self.clearance_material_combobox.grid(column=1)
        self.clearance_material_combobox.grid(row=13)
        self.clearance_material_combobox.grid(sticky="W")
        self.clearance_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.under_sheath_dia_entry = EntryInt(self, self.cable.sheath.dia_under_sheath, is_cable_auto_design)
        self.under_sheath_dia_entry.grid(column=5, row=13, sticky="W")
        self.under_sheath_dia_entry.config(width=10)

        # sheath
        self.ttk_label_sheath = ttk.Label(self)
        self.ttk_label_sheath.grid(column=0, row=14, sticky="W")
        self.ttk_label_sheath.config(width=0, anchor="e", text="metal sheath", underline=0)
        # metal sheath frame
        self.sheath_frame = SheathFrame(self, self.cable, is_cable_auto_design)
        self.sheath_frame.grid(column=2, row=14, columnspan=2)
        self.sheath_frame.grid(sticky="EW")
        self.sheath_frame.bind('<<Q_change>>', self.q_change)
        # diameter (Entry box)
        self.sheath_dia_entry = EntryInt(self, self.cable.sheath.dia, is_cable_auto_design)
        self.sheath_dia_entry.grid(column=5, row=14, sticky="W")
        self.sheath_dia_entry.config(width=10)

        # over sheath
        self.ttk_label_over_sheath = ttk.Label(self)
        self.ttk_label_over_sheath.grid(column=0, row=15, sticky="W")
        self.ttk_label_over_sheath.config(width=0, anchor="e", text="over sheath binder", underline=0)
        # material (Combobox)
        self.sheath_bind_material_combobox = ComboboxString(self, self.cable.sheath.binder_material,
                                                            is_cable_auto_design)
        self.sheath_bind_material_combobox.grid(column=1)
        self.sheath_bind_material_combobox.grid(row=15)
        self.sheath_bind_material_combobox.grid(sticky="W")
        self.sheath_bind_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.over_sheath_dia_entry = EntryInt(self, self.cable.sheath.binder_dia, is_cable_auto_design)
        self.over_sheath_dia_entry.grid(column=5, row=15, sticky="W")
        self.over_sheath_dia_entry.config(width=10)

        # under tape
        self.ttk_label_under_tape_screen = ttk.Label(self)
        self.ttk_label_under_tape_screen.grid(column=0, row=16, sticky="W")
        self.ttk_label_under_tape_screen.config(width=0, anchor="e", text="under tape screen", underline=0)
        # material (Combobox)
        self.under_tape_screen_material_combobox = ComboboxString(self, self.cable.tape.under_tape_material,
                                                                  is_cable_auto_design)
        self.under_tape_screen_material_combobox.grid(column=1)
        self.under_tape_screen_material_combobox.grid(row=16)
        self.under_tape_screen_material_combobox.grid(sticky="W")
        self.under_tape_screen_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.under_tape_screen_dia_entry = EntryInt(self, self.cable.tape.dia_under_tape, is_cable_auto_design)
        self.under_tape_screen_dia_entry.grid(column=5, row=16, sticky="W")
        self.under_tape_screen_dia_entry.config(width=10)

        # tape screen
        self.ttk_label_tape = ttk.Label(self)
        self.ttk_label_tape.grid(column=0, row=17, sticky="W")
        self.ttk_label_tape.config(width=0, anchor="e", text="tape screen", underline=0)
        # tape screen frame
        self.tape_screen_frame = TapeScreenFrame(self, self.cable, is_cable_auto_design)
        self.tape_screen_frame.grid(column=2, row=17, columnspan=2)
        self.tape_screen_frame.grid(sticky="EW")
        self.tape_screen_frame.bind('<<Q_change>>', self.q_change)
        # diameter (Entry box)
        self.tape_dia_entry = EntryInt(self, self.cable.tape.dia, is_cable_auto_design)
        self.tape_dia_entry.grid(column=5, row=17, sticky="W")
        self.tape_dia_entry.config(width=10)

        # tape binder
        self.ttk_label_over_tape_screen = ttk.Label(self)
        self.ttk_label_over_tape_screen.grid(column=0, row=18, sticky="W")
        self.ttk_label_over_tape_screen.config(width=0, anchor="e", text="over tape screen", underline=0)
        # material (Combobox)
        self.over_tape_screen_material_combobox = ComboboxString(self, self.cable.tape.binder_material,
                                                                 is_cable_auto_design)
        self.over_tape_screen_material_combobox.grid(column=1)
        self.over_tape_screen_material_combobox.grid(row=18)
        self.over_tape_screen_material_combobox.grid(sticky="W")
        self.over_tape_screen_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.over_tape_screen_dia_entry = EntryInt(self, self.cable.tape.binder_dia, is_cable_auto_design)
        self.over_tape_screen_dia_entry.grid(column=5, row=18, sticky="W")
        self.over_tape_screen_dia_entry.config(width=10)

        # serving
        self.ttk_label_serving = ttk.Label(self)
        self.ttk_label_serving.grid(column=0, row=19, sticky="W")
        self.ttk_label_serving.config(width=0, anchor="e", text="serving", underline=0)
        # material (Combobox)
        self.serving_material_combobox = ComboboxString(self, self.cable.serving.material, is_cable_auto_design)
        self.serving_material_combobox.grid(column=1)
        self.serving_material_combobox.grid(row=19)
        self.serving_material_combobox.grid(sticky="W")
        self.serving_material_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.serving_dia_entry = EntryInt(self, self.cable.serving.dia, is_cable_auto_design)
        self.serving_dia_entry.grid(column=5, row=19, sticky="W")
        self.serving_dia_entry.config(width=10)

        # serving semiconducting layer
        self.ttk_label_serving_sc = ttk.Label(self)
        self.ttk_label_serving_sc.grid(column=0, row=20, sticky="W")
        self.ttk_label_serving_sc.config(width=0, anchor="e", text="semicon layer", underline=0)
        # material (Combobox)
        self.serving_material_sc_combobox = ComboboxString(self, self.cable.serving.semicon_mat, is_cable_auto_design)
        self.serving_material_sc_combobox.grid(column=1)
        self.serving_material_sc_combobox.grid(row=20)
        self.serving_material_sc_combobox.grid(sticky="W")
        self.serving_material_sc_combobox.config(width=25, state="readonly")
        # diameter (Entry box)
        self.serving_dia_sc_entry = EntryInt(self, self.cable.serving.semicon_dia, is_cable_auto_design)
        self.serving_dia_sc_entry.grid(column=5, row=20, sticky="W")
        self.serving_dia_sc_entry.config(width=10)

    def update_frame(self):
        if ((self.cable.core.insulation_material.get_value() == iec.INS_PAPER_SCOF or
                self.cable.core.insulation_material.get_value() is None) and
                self.cable.number_cores.get_value() == iec.SINGLE_CORE or
                self.cable.number_cores.get_value() is None):
            self.ttk_label_duct.grid(column=0, row=1, sticky="W")
            self.duct_dia_entry.grid(column=5, row=1, sticky="W")
            self.ttk_label_spiral.grid(column=0, row=2, sticky="W")
            self.spiral_mat_combobox.grid(column=1, row=2, sticky='W')
            self.spiral_dia_entry.grid(column=5, row=2, sticky="W")
        else:
            self.ttk_label_duct.grid_forget()
            self.duct_dia_entry.grid_forget()
            self.ttk_label_spiral.grid_forget()
            self.spiral_mat_combobox.grid_forget()
            self.spiral_dia_entry.grid_forget()
        self.duct_dia_entry.update_entry()
        self.spiral_mat_combobox.update_combobox()
        self.spiral_dia_entry.update_entry()
        self.cond_dia_entry.update_entry()
        self.cond_material_combobox.update_combobox()
        self.cond_makeup_combobox.update_combobox()
        self.binder_material_combobox.update_combobox()
        self.binder_dia_entry.update_entry()
        self.cond_screen_material_combobox.update_combobox()
        self.cond_screen_dia_entry.update_entry()
        self.ins_rt_entry.update_entry()
        self.ins_dia_entry.update_entry()
        if self.cable.belted.value or self.cable.belted.value is None:
            self.ttk_label_belt_ins.grid(column=0, row=7, sticky="W")
            self.belt_ins_dia_entry.grid(column=5, row=7, sticky="W")
        else:
            self.ttk_label_belt_ins.grid_forget()
            self.belt_ins_dia_entry.grid_forget()
        self.belt_ins_dia_entry.update_entry()
        self.insu_screen_material_combobox.update_combobox()
        self.ins_screen_dia_entry.update_entry()
        self.core_bedding_material_combobox.update_combobox()
        self.bedding_dia_entry.update_entry()
        if self.cable.wire_screen.material.value != iec.NONE:
            self.ttk_label_cws_bedding.grid(column=0, row=10, sticky="W")
            self.cws_bedding_material_combobox.grid(column=1, row=10, sticky="W")
            self.cws_bedding_dia_entry.grid(column=5, row=10, sticky="W")
            self.ttk_label_cws.grid(column=0, row=11, sticky="W")
            self.wire_screen_frame.grid(column=2, row=11, columnspan=2)
            self.cws_dia_entry.grid(column=5, row=11, sticky="W")
            self.ttk_label_over_wire.grid(column=0, row=12, sticky="W")
            self.cws_binder_material_combobox.grid(column=1, row=12, sticky="W")
            self.over_wire_dia_entry.grid(column=5, row=12, sticky="W")
        else:
            self.ttk_label_cws_bedding.grid_forget()
            self.cws_bedding_material_combobox.grid_forget()
            self.cws_bedding_dia_entry.grid_forget()
            self.ttk_label_cws.grid_forget()
            self.wire_screen_frame.grid_forget()
            self.cws_dia_entry.grid_forget()
            self.ttk_label_over_wire.grid_forget()
            self.cws_binder_material_combobox.grid_forget()
            self.over_wire_dia_entry.grid_forget()
        self.cws_bedding_material_combobox.update_combobox()
        self.cws_bedding_dia_entry.update_entry()
        self.wire_screen_frame.update_frame()
        self.cws_binder_material_combobox.update_combobox()
        self.over_wire_dia_entry.update_entry()
        self.cws_dia_entry.update_entry()
        if self.cable.sheath.material.value != iec.NONE:
            self.ttk_label_under_sheath.grid(column=0, row=13, sticky="W")
            self.clearance_material_combobox.grid(column=1, row=13, sticky="w")
            self.under_sheath_dia_entry.grid(column=5, row=13, sticky="W")
            self.ttk_label_sheath.grid(column=0, row=14, sticky="W")
            self.sheath_frame.grid(column=2, row=14, columnspan=2)
            self.sheath_dia_entry.grid(column=5, row=14, sticky="W")
            self.ttk_label_over_sheath.grid(column=0, row=15, sticky="W")
            self.sheath_bind_material_combobox.grid(column=1, row=15, sticky="W")
            self.over_sheath_dia_entry.grid(column=5, row=15, sticky="W")
        else:
            self.ttk_label_under_sheath.grid_forget()
            self.clearance_material_combobox.grid_forget()
            self.under_sheath_dia_entry.grid_forget()
            self.ttk_label_sheath.grid_forget()
            self.sheath_frame.grid_forget()
            self.sheath_dia_entry.grid_forget()
            self.ttk_label_over_sheath.grid_forget()
            self.sheath_bind_material_combobox.grid_forget()
            self.over_sheath_dia_entry.grid_forget()
        self.clearance_material_combobox.update_combobox()
        self.under_sheath_dia_entry.update_entry()
        self.sheath_frame.update_frame()
        self.sheath_dia_entry.update_entry()
        self.sheath_bind_material_combobox.update_combobox()
        self.over_sheath_dia_entry.update_entry()
        if self.cable.tape.material.value != iec.NONE:
            self.ttk_label_under_tape_screen.grid(column=0, row=16, sticky="W")
            self.under_tape_screen_material_combobox.grid(column=1, row=16, sticky="W")
            self.under_tape_screen_dia_entry.grid(column=5, row=16, sticky="W")
            self.ttk_label_tape.grid(column=0, row=17, sticky="W")
            self.tape_screen_frame.grid(column=2, row=17, columnspan=2)
            self.tape_dia_entry.grid(column=5, row=17, sticky="W")
            self.ttk_label_over_tape_screen.grid(column=0, row=18, sticky="W")
            self.over_tape_screen_material_combobox.grid(column=1, row=18, sticky="W")
            self.over_tape_screen_dia_entry.grid(column=5, row=18, sticky="W")
        else:
            self.ttk_label_under_tape_screen.grid_forget()
            self.under_tape_screen_material_combobox.grid_forget()
            self.under_tape_screen_dia_entry.grid_forget()
            self.ttk_label_tape.grid_forget()
            self.tape_screen_frame.grid_forget()
            self.tape_dia_entry.grid_forget()
            self.ttk_label_over_tape_screen.grid_forget()
            self.over_tape_screen_material_combobox.grid_forget()
            self.over_tape_screen_dia_entry.grid_forget()
        self.under_tape_screen_dia_entry.update_entry()
        self.under_tape_screen_material_combobox.update_combobox()
        self.tape_screen_frame.update_frame()
        self.tape_dia_entry.update_entry()
        self.over_tape_screen_dia_entry.update_entry()
        self.over_tape_screen_material_combobox.update_combobox()
        self.serving_material_combobox.update_combobox()
        self.serving_dia_entry.update_entry()
        self.serving_material_sc_combobox.update_combobox()
        self.serving_dia_sc_entry.update_entry()

    def q_change(self, _event):
        self.event_generate("<<Q_change>>")


class WireScreenFrame(tkinter.Frame):
    """Frame showing wire screen details"""

    def __init__(self, container: tkinter.Frame, cable: Cable, is_cable_auto_design: Callable, **kw):
        self.container = container
        self.cable = cable
        super().__init__(container, **kw)

        self.rowconfigure(0, minsize="0", weight=1, pad="0")
        self.rowconfigure(1, minsize="0", weight=1, pad="0")
        self.rowconfigure(2, minsize="0", weight=1, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="0", weight=1, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="flat")

        # number (Entry box)
        self.cws_no_entry = EntryInt(self, self.cable.wire_screen.number_wires, is_cable_auto_design)
        self.cws_no_entry.grid(column=1, row=1, sticky="W")
        self.cws_no_entry.config(width=10)
        # by
        self.ttk_label_cws_by = ttk.Label(self)
        self.ttk_label_cws_by.grid(column=2, row=1, sticky="EW")
        self.ttk_label_cws_by.config(width=0, anchor="w", text="x", underline=0)
        # wire dia (Entry box)
        self.cws_wire_dia_entry = EntryInt(self, self.cable.wire_screen.wire_size, is_cable_auto_design)
        self.cws_wire_dia_entry.grid(column=3, row=1, sticky="W")
        self.cws_wire_dia_entry.config(width=10)
        # unit
        self.ttk_label_cws_by = ttk.Label(self)
        self.ttk_label_cws_by.grid(column=4, row=1, sticky="E")
        self.ttk_label_cws_by.config(width=0, anchor="e", text="mm", underline=0)

    def update_frame(self):
        self.cws_no_entry.update_entry()
        self.cws_wire_dia_entry.update_entry()

    def q_change(self, _event):
        self.event_generate("<<Q_change>>")


class SheathFrame(tkinter.Frame):
    """Frame showing metal sheath"""

    def __init__(self, container: tkinter.Frame, cable: Cable, is_cable_auto_design: Callable, **kw):
        self.container = container
        self.cable = cable
        super().__init__(container, **kw)

        self.rowconfigure(0, minsize="0", weight=1, pad="0")
        self.rowconfigure(1, minsize="0", weight=1, pad="0")
        self.rowconfigure(2, minsize="0", weight=1, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="0", weight=1, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="flat")

        # thickness label
        self.ttk_label_rt = ttk.Label(self)
        self.ttk_label_rt.grid(column=2, row=1, sticky="EW")
        self.ttk_label_rt.config(width=0, anchor="w", text="thickness", underline=0)
        # thickness (Entry box)
        self.sheath_dia_entry = EntryInt(self, self.cable.sheath.thickness, is_cable_auto_design)
        self.sheath_dia_entry.grid(column=3, row=1, sticky="W")
        self.sheath_dia_entry.config(width=10)
        # unit
        self.ttk_label_u = ttk.Label(self)
        self.ttk_label_u.grid(column=4, row=1, sticky="E")
        self.ttk_label_u.config(width=0, anchor="e", text="mm", underline=0)

    def update_frame(self):
        # self.cws_no_entry.update_entry()
        self.sheath_dia_entry.update_entry()

    def q_change(self, _event):
        self.event_generate("<<Q_change>>")


class TapeScreenFrame(tkinter.Frame):
    """Frame showing tape screen details"""

    def __init__(self, container: tkinter.Frame, cable: Cable, is_cable_auto_design: Callable, **kw):
        self.container = container
        self.cable = cable
        super().__init__(container, **kw)

        self.rowconfigure(0, minsize="0", weight=1, pad="0")
        self.rowconfigure(1, minsize="0", weight=1, pad="0")
        self.rowconfigure(2, minsize="0", weight=1, pad="0")
        self.rowconfigure(3, minsize="0", weight=1, pad="0")
        self.rowconfigure(4, minsize="0", weight=1, pad="0")
        self.rowconfigure(5, minsize="0", weight=1, pad="0")
        self.rowconfigure(6, minsize="0", weight=1, pad="0")
        self.rowconfigure(7, minsize="0", weight=1, pad="0")
        self.columnconfigure(0, minsize="0", weight=1, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        self.config(height="0", width="0", borderwidth="2", relief="flat")

        # number (Entry box)
        self.tape_rt_entry = EntryInt(self, self.cable.tape.tape_thickness, is_cable_auto_design)
        self.tape_rt_entry.grid(column=1, row=1, sticky="W")
        self.tape_rt_entry.config(width=10)
        # by
        self.ttk_label_cws_by = ttk.Label(self)
        self.ttk_label_cws_by.grid(column=2, row=1, sticky="EW")
        self.ttk_label_cws_by.config(width=0, anchor="w", text="x", underline=0)
        # wire dia (Entry box)
        self.tape_width_entry = EntryInt(self, self.cable.tape.tape_width, is_cable_auto_design)
        self.tape_width_entry.grid(column=3, row=1, sticky="W")
        self.tape_width_entry.config(width=10)
        # unit
        self.ttk_label_cws_by = ttk.Label(self)
        self.ttk_label_cws_by.grid(column=4, row=1, sticky="E")
        self.ttk_label_cws_by.config(width=0, anchor="e", text="mm", underline=0)

    def update_frame(self):
        self.tape_rt_entry.update_entry()
        self.tape_width_entry.update_entry()

    def q_change(self, _event):
        self.event_generate("<<Q_change>>")
