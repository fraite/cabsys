import tkinter
# from tkinter import ttk
import os

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# from matplotlib.backend_bases import key_press_handler
# from matplotlib.figure import Figure
# from matplotlib.widgets import CheckButtons
import matplotlib.pyplot as plt

# import numpy as np

from cabsys.data_classes.current_curve import CurrentCurve


class CurrentGraphFrame(tkinter.Frame):

    def __init__(self, parent):
        tkinter.Frame.__init__(self, parent)

        # button1 = ttk.Button(self, text="Back to Home",
        #                     command=lambda: controller.show_frame(StartPage))
        # button1.pack()

        # self.fig = Figure(figsize=(5, 5), dpi=100)
        # self.sub_plot = self.fig.add_subplot(111)
        # self.sub_plot.plot([1, 2, 3, 4, 5, 6, 7, 8], [5, 6, 1, 3, 8, 9, 3, 5])

        self.fig, self.ax = plt.subplots()
        # self.ax2 = self.ax.twinx()
        # l0, = self.ax.plot([1, 2, 3, 4, 5, 6, 7, 8], [5, 6, 1, 3, 8, 9, 3, 5])

        self.working_dir = os.getcwd()
        self.transient_result = None

        canvas = FigureCanvasTkAgg(self.fig, self)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

        frame = tkinter.Frame(self)
        frame.pack(pady=10, padx=10)

    def update_graph(self, current_curve: CurrentCurve):

        self.ax.clear()
        # self.ax2.clear()
        times = []
        currents = []
        current_point = None
        if current_curve is not None and len(current_curve.points) > 0:
            for time_point_result in current_curve.points:
                time_point = time_point_result.time.get_value(unit='s')
                if current_point is not None:
                    times.append(time_point - 0.001)
                    currents.append(current_point)
                current_point = time_point_result.current.get_value(unit='A')
                times.append(time_point)
                currents.append(current_point)
            # add point to end of transient
            if current_curve.cyclic.value and current_curve.cycle_time.value is not None:
                times.append(current_curve.cycle_time.get_value(unit='s'))
                currents.append(current_curve.points[-1].current.get_value(unit="A"))
            else:
                last_time = current_curve.points[-1].time.get_value(unit='s')
                start_time = current_curve.points[0].time.get_value(unit='s')
                end_time = last_time + (last_time - start_time) * 0.1 + 60.0
                times.append(end_time)
                currents.append(current_curve.points[-1].current.get_value(unit="A"))

            self.ax.plot(times, currents, label=f'current')
            self.ax.set_ylim(ymin=0)
            self.ax.set(xlabel='time (s)', ylabel='current (A)', title=f'Current Curve: {current_curve.name}')
            # self.ax2.set(ylabel='current (A)')
            self.ax.legend()
            # self.ax2.legend()

        plt.draw()
