import tkinter
from tkinter import filedialog
# from tkinter import ttk
import os

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# from matplotlib.backend_bases import key_press_handler
# from matplotlib.figure import Figure
# from matplotlib.widgets import CheckButtons
import matplotlib.pyplot as plt

# import numpy as np


class GraphFrame(tkinter.Frame):

    def __init__(self, parent):
        tkinter.Frame.__init__(self, parent)

        # button1 = ttk.Button(self, text="Back to Home",
        #                     command=lambda: controller.show_frame(StartPage))
        # button1.pack()

        # self.fig = Figure(figsize=(5, 5), dpi=100)
        # self.sub_plot = self.fig.add_subplot(111)
        # self.sub_plot.plot([1, 2, 3, 4, 5, 6, 7, 8], [5, 6, 1, 3, 8, 9, 3, 5])

        self.fig, self.ax = plt.subplots()
        self.ax2 = self.ax.twinx()
        # l0, = self.ax.plot([1, 2, 3, 4, 5, 6, 7, 8], [5, 6, 1, 3, 8, 9, 3, 5])

        self.working_dir = os.getcwd()
        self.transient_result = None

        canvas = FigureCanvasTkAgg(self.fig, self)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

        frame = tkinter.Frame(self)
        frame.pack(pady=10, padx=10)

        label = tkinter.Label(frame, text="Graph Page!")
        label.pack(pady=10, padx=10, side=tkinter.TOP)

        button = tkinter.Button(frame, text='Export', command=self.export_graph)
        button.pack(side=tkinter.TOP)

    def update_graph(self, transient_result):

        self.transient_result = transient_result

        self.ax.clear()
        self.ax2.clear()
        time = []
        thetas = []
        currents = []
        if transient_result is not None:
            theta_c = [[[] for _cable_thetas in cable_set_thetas] for cable_set_thetas in transient_result[0][1]]
            theta_sc = [[[] for _cable_thetas in cable_set_thetas] for cable_set_thetas in transient_result[0][1]]
            theta_cs = [[[] for _cable_thetas in cable_set_thetas] for cable_set_thetas in transient_result[0][1]]
            currents_cs = [[] for _cable_set in transient_result[0][2]]
            for time_point_result in transient_result:
                time.append(time_point_result[0])
                thetas.append(time_point_result[1])
                currents.append(time_point_result[2])
            for thetas_time_point in thetas:
                for cable_set_i, cable_set_thetas in enumerate(thetas_time_point):
                    for cable_i, cable_thetas in enumerate(cable_set_thetas):
                        theta_c[cable_set_i][cable_i].append(cable_thetas[0])
                        theta_sc[cable_set_i][cable_i].append(cable_thetas[1])
                        theta_cs[cable_set_i][cable_i].append(cable_thetas[2])
            for currents_time_point in currents:
                for cable_set_i, cable_set_currents in enumerate(currents_time_point):
                    currents_cs[cable_set_i].append(cable_set_currents)

            for cable_set_i, cable_set_thetas in enumerate(transient_result[0][1]):
                self.ax2.plot(time, currents_cs[cable_set_i], label=f'Current {cable_set_i}')
                for cable_i, cable_thetas in enumerate(cable_set_thetas):
                    self.ax.plot(time, theta_c[cable_set_i][cable_i], label=f'theta_c {cable_set_i}, {cable_i}')
                    self.ax.plot(time, theta_sc[cable_set_i][cable_i], label=f'theta_sc {cable_set_i}, {cable_i}')
                    self.ax.plot(time, theta_cs[cable_set_i][cable_i], label=f'theta_cs {cable_set_i}, {cable_i}')

            self.ax.set(xlabel='time (s)', ylabel='temperature (°C)', title='Transient Temperatures')
            self.ax2.set(ylabel='current (A)')
            self.ax.legend()
            self.ax2.legend()

        plt.draw()

    def export_graph(self):

        if self.transient_result is None:
            return

        save_install = 'transient'
        save_name: str = filedialog.asksaveasfilename(initialdir=self.working_dir, title='Save file',
                                                      filetypes=(('csv files', "*.csv"), ('all files', '*.*')),
                                                      initialfile=save_install, defaultextension='.inst')
        if save_name is None or save_name == '':
            return

        # make the save directory the new default working directory
        save_dir = save_name.rpartition('/')
        self.working_dir = save_dir[0]
        # add the .inst suffix, if required
        if save_name.partition('.')[1] != '.':
            save_name = save_name + '.csv'
        # save selected install
        # serial = canning.dumps_install(save_install, name=save_install.name)
        serial = ''

        # generate headers
        time_point_result = self.transient_result[0]
        time = 'time'
        thetas = time_point_result[1]
        currents = time_point_result[2]

        serial = f'{serial}"{time}"'

        for i_cable_set, _cable_set_current in enumerate(currents):
            serial = f'{serial}, "current ({i_cable_set})"'

        for i_cable_set, cable_set_thetas in enumerate(thetas):
            for i_cable, _cable_theta in enumerate(cable_set_thetas):
                serial = f'{serial}, "theta_c ({i_cable_set}, {i_cable})"'
                serial = f'{serial}, "theta_sc ({i_cable_set}, {i_cable})"'
                serial = f'{serial}, "theta_cs ({i_cable_set}, {i_cable})"'

        serial = f'{serial}\n'

        # generate results
        for time_point_result in self.transient_result:
            time = time_point_result[0]
            thetas = time_point_result[1]
            currents = time_point_result[2]

            serial = f'{serial}{time}'

            for cable_set_current in currents:
                serial = f'{serial}, {cable_set_current}'

            for cable_set_thetas in thetas:
                for cable_theta in cable_set_thetas:
                    serial = f'{serial}, {cable_theta[0]}'
                    serial = f'{serial}, {cable_theta[1]}'
                    serial = f'{serial}, {cable_theta[2]}'

            serial = f'{serial}\n'

        with open(save_name, 'w', encoding='utf-8') as save_file:
            save_file.write(serial)
