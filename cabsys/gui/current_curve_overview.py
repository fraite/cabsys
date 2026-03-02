import tkinter
from tkinter import ttk
from collections.abc import Callable
from typing import List, Union

from cabsys.gui.overview_widgets import EntryInt, ComboboxBool, ComboboxString

from cabsys.data_classes.auto_current_curve import AutoCurrentCurve
from cabsys.data_classes.current_curve import CurrentCurve, TransientCurrentPoint
from cabsys.gui.current_graph import CurrentGraphFrame


class CurrentCurveOverviewFrame(tkinter.Frame):
    """binder for GuiCollection"""

    def __init__(self, current_curve: CurrentCurve, **kw):
        self.current_curve = current_curve
        if isinstance(current_curve, AutoCurrentCurve):
            current_curve.auto_design()
        super().__init__(**kw)

        self.rowconfigure(0, minsize="0", weight=0, pad="0")
        self.rowconfigure(1, minsize="0", weight=1, pad="0")
        # self.rowconfigure(2, minsize="0", weight=0, pad="0")
        self.columnconfigure(0, minsize="0", weight=0, pad="0")
        self.columnconfigure(1, minsize="0", weight=1, pad="0")
        # self.config(height="0")
        # self.config(width="0")
        self.config(relief="flat")

        # common frame
        self.common_frame = CommonFrame(self, self.current_curve, self.is_current_curve_auto_design)
        self.common_frame.grid(column=0, row=0)
        self.common_frame.grid(sticky="EW")
        self.common_frame.bind('<<Q_change>>', self.q_change)

        # graph frame
        self.graph_frame = CurrentGraphFrame(self)
        self.graph_frame.grid(column=1, row=0, rowspan=2)
        self.graph_frame.grid(sticky='NSEW')

        # frame holding points and scrollbar
        self.points_scroll = ttk.Frame(self)
        self.points_scroll.grid(column=0, row=1, sticky="NSEW")
        self.points_scroll.rowconfigure(0, minsize="0", weight=1, pad="0")
        self.points_scroll.columnconfigure(0, minsize="0", weight=1, pad="0")
        self.points_scroll.columnconfigure(1, minsize="0", weight=0, pad="0")
        # self.points_scroll.rowconfigure(1, minsize="0", weight=0, pad="0")
        self.points_scroll.config(relief=tkinter.GROOVE)

        self.points_canvas = tkinter.Canvas(self.points_scroll)
        self.points_canvas.grid(column=0, row=0, sticky='NS')
        self.scrollbar = ttk.Scrollbar(self.points_scroll, orient=tkinter.VERTICAL, command=self.points_canvas.yview)
        self.scrollbar.grid(column=1, row=0, sticky='NS')
        self.points_canvas['yscrollcommand'] = self.scrollbar.set

        # Create a frame inside the canvas which will be scrolled with it.
        # points frame
        self.points_frame = PointsFrame(self.points_canvas, self.current_curve)
        self.points_canvas.create_window((0, 0), window=self.points_frame, anchor='nw')
        self.points_frame.bind('<Configure>', self.frame_func)
        self.points_frame.grid_columnconfigure(0, minsize=150)
        self.points_frame.bind('<<Q_change>>', self.q_change)

    def is_current_curve_auto_design(self):
        if isinstance(self.current_curve, AutoCurrentCurve):
            return self.current_curve.is_auto_design()
        else:
            return None

    def update_frame(self):
        self.common_frame.update_frame()
        self.points_frame.update_frame()
        self.graph_frame.update_graph(self.current_curve)

    def frame_func(self, _event):
        self.points_canvas.configure(scrollregion=self.points_canvas.bbox('all'), width=self.points_frame.winfo_width())

    def q_change(self, _event):
        if isinstance(self.current_curve, AutoCurrentCurve):
            self.current_curve.auto_design_no_exceptions()
        self.update_frame()
        self.event_generate("<<Q_change>>", when="tail")


class CommonFrame(tkinter.Frame):
    """Frame showing common installation parameters"""

    def __init__(self, container: tkinter.Frame, current_curve: CurrentCurve,
                 is_current_curve_auto_design: Callable, **kw):
        self.container = container
        self.current_curve = current_curve
        super().__init__(container, **kw)

        if isinstance(current_curve, AutoCurrentCurve):
            auto_design: Callable = current_curve.is_auto_design
        else:
            auto_design: Callable = lambda: None
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
        self.config(height="0", width="0", borderwidth="2", relief=tkinter.GROOVE)

        if isinstance(self.current_curve, AutoCurrentCurve):
            # Combobox kind
            self.ttk_label_kind = ttk.Label(self)
            self.ttk_label_kind.grid(column=0, row=1, sticky="w")
            self.ttk_label_kind.config(width=0, anchor="e", text="current curve kind", underline=0)
            # kind of current curve (Combobox)
            self.kind_combobox = ComboboxString(self, self.current_curve.auto_kind, is_current_curve_auto_design)
            self.kind_combobox.grid(column=1)
            self.kind_combobox.grid(row=1)
            self.kind_combobox.grid(sticky="W")
            self.kind_combobox.config(width=20, state="readonly")

            # number of points
            self.ttk_label_number_points = ttk.Label(self)
            self.ttk_label_number_points.grid(column=0, row=2, sticky="W")
            self.ttk_label_number_points.config(width=0, anchor="e", text="number of points", underline=0)
            # diameter (Entry box)
            self.number_points_entry = EntryInt(self, self.current_curve.auto_number_points, auto_design)
            self.number_points_entry.grid(column=1, row=2, sticky="W")
            self.number_points_entry.config(width=10)

        else:
            # number of points
            self.ttk_label_number_points = ttk.Label(self)
            self.ttk_label_number_points.grid(column=0, row=2, sticky="W")
            self.ttk_label_number_points.config(width=0, anchor="e", text="number of points", underline=0)
            # diameter (Entry box)
            self.number_points_str = tkinter.StringVar()
            self.number_points_str.set(str(len(self.current_curve.points)))
            self.number_points_entry2 = ttk.Entry(self, textvariable=self.number_points_str)
            self.number_points_entry2.grid(column=1, row=2, sticky="W")
            self.number_points_entry2.config(width=10)
            self.number_points_entry2.bind('<Return>', lambda
                                           event: self._number_points_callback(event)
                                          )
            self.number_points_entry2.bind('<FocusOut>', lambda
                                           event: self._number_points_callback(event)
                                          )

        # Combobox Auto Comment
        self.ttk_label_6 = ttk.Label(self)
        self.ttk_label_6.grid(column=0, row=3, sticky="W")
        self.ttk_label_6.config(width=0, anchor="e", text="Auto_Comment", underline=-1)
        # ComboBox
        self.combobox_comment = EntryInt(self, self.current_curve.auto_comment, is_current_curve_auto_design)
        self.combobox_comment.grid(column=1, row=3, sticky="W")
        self.combobox_comment.config(width=40)

        # emergency
        self.ttk_label_emergency = ttk.Label(self)
        self.ttk_label_emergency.grid(column=0, row=4, sticky="w")
        self.ttk_label_emergency.config(width=0, anchor="e", text="emergency", underline=0)
        # new_widget(Combobox)
        self.emergency_combobox = ComboboxBool(self, self.current_curve.emergency, is_current_curve_auto_design)
        self.emergency_combobox.grid(column=1, columnspan=3)
        self.emergency_combobox.grid(row=4)
        self.emergency_combobox.grid(sticky="W")
        self.emergency_combobox.config(width=10, state="readonly")

        # cyclic
        self.ttk_label_cyclic = ttk.Label(self)
        self.ttk_label_cyclic.grid(column=0, row=5, sticky="w")
        self.ttk_label_cyclic.config(width=0, anchor="e", text="cyclic", underline=0)
        # new_widget(Combobox)
        self.cyclic_combobox = ComboboxBool(self, self.current_curve.cyclic, is_current_curve_auto_design)
        self.cyclic_combobox.grid(column=1, columnspan=3)
        self.cyclic_combobox.grid(row=5)
        self.cyclic_combobox.grid(sticky="W")
        self.cyclic_combobox.config(width=10, state="readonly")

        # cyclic time
        self.ttk_label_cyclic_time = ttk.Label(self)
        self.ttk_label_cyclic_time.grid(column=0, row=6, sticky="W")
        self.ttk_label_cyclic_time.config(width=0, anchor="e", text="cyclic_time", underline=0)
        # cyclic_time (Entry box)
        self.cyclic_time_entry = EntryInt(self, self.current_curve.cycle_time, auto_design)
        self.cyclic_time_entry.grid(column=1, row=6, sticky="W")
        self.cyclic_time_entry.config(width=10)
        # unit
        self.ttk_label_u = ttk.Label(self)
        self.ttk_label_u.grid(column=4, row=6, sticky="E")
        self.ttk_label_u.config(width=0, anchor="e", text="s", underline=0)

        # normalise
        self.ttk_label_normalise = ttk.Label(self)
        self.ttk_label_normalise.grid(column=0, row=7, sticky="w")
        self.ttk_label_normalise.config(width=0, anchor="e", text="normalise", underline=0)
        # new_widget(Combobox)
        self.normalise_combobox = ComboboxBool(self, self.current_curve.normalise_curve, is_current_curve_auto_design)
        self.normalise_combobox.grid(column=1, columnspan=3)
        self.normalise_combobox.grid(row=7)
        self.normalise_combobox.grid(sticky="W")
        self.normalise_combobox.config(width=10, state="readonly")

    def update_frame(self):
        if isinstance(self.current_curve, AutoCurrentCurve):
            self.kind_combobox.update_combobox()
            self.number_points_entry.update_entry()
        self.combobox_comment.update_entry()
        self.emergency_combobox.update_combobox()
        self.cyclic_combobox.update_combobox()
        self.cyclic_time_entry.update_entry()
        self.normalise_combobox.update_combobox()

    def _number_points_callback(self, _event):
        try:
            new_number_points = int(self.number_points_str.get())
        except ValueError:
            new_number_points = len(self.current_curve.points)
        while new_number_points > len(self.current_curve.points):
            point = TransientCurrentPoint()
            point.time.set_value(value=self.current_curve.points[-1].time.value,
                                 unit=self.current_curve.points[-1].time.unit,
                                 source=self.current_curve.points[-1].time.source)
            point.current.set_value(value=self.current_curve.points[-1].current.value,
                                    unit=self.current_curve.points[-1].current.unit,
                                    source=self.current_curve.points[-1].current.source)
            self.current_curve.points.append(point)
        while new_number_points < len(self.current_curve.points):
            self.current_curve.points.pop()

        self.number_points_str.set(str(new_number_points))

        self.event_generate("<<Q_change>>")


class PointsFrame(tkinter.Frame):
    """Frame showing common installation parameters"""

    def __init__(self, container: Union[tkinter.Frame, tkinter.Canvas], current_curve: CurrentCurve, **kw):
        self.container = container
        self.current_curve = current_curve
        super().__init__(container, **kw)

        if isinstance(current_curve, AutoCurrentCurve):
            self.auto_design: Callable = current_curve.is_auto_design
        else:
            self.auto_design: Callable = lambda: None
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
        self.config(height="0", width="0", borderwidth="2", relief=tkinter.GROOVE)

        # cyclic time
        ttk_label_time = ttk.Label(self)
        ttk_label_time.grid(column=1, row=0, sticky="W")
        ttk_label_time.config(width=0, anchor="e", text=f"time (s)", underline=0)
        # current
        self.ttk_label_u = ttk.Label(self)
        self.ttk_label_u.grid(column=2, row=0, sticky="E")
        self.ttk_label_u.config(width=0, anchor="e", text="current (A)", underline=0)

        self.time_entry: List[(ttk.Label, EntryInt, EntryInt)] = []
        self.update_frame()

    def update_frame(self):
        for cyclic_entry in self.time_entry:
            cyclic_entry[0].destroy()
            cyclic_entry[1].destroy()
            cyclic_entry[2].destroy()
        self.time_entry = []
        row = 0
        for point in self.current_curve.points:
            # cyclic time
            ttk_label_cyclic_time = ttk.Label(self)
            ttk_label_cyclic_time.grid(column=0, row=row + 1, sticky="W")
            ttk_label_cyclic_time.config(width=0, anchor="e", text=f"point {row}", underline=0)
            # cyclic_time (Entry box)
            cyclic_time_entry = EntryInt(self, point.time, self.auto_design)
            cyclic_time_entry.grid(column=1, row=row + 1, sticky="W")
            cyclic_time_entry.config(width=10)
            # cyclic_current (Entry box)
            cyclic_current_entry = EntryInt(self, point.current, self.auto_design)
            cyclic_current_entry.grid(column=2, row=row + 1, sticky="W")
            cyclic_current_entry.config(width=10)
            #
            self.time_entry.append((ttk_label_cyclic_time, cyclic_time_entry, cyclic_current_entry))
            row = row + 1
