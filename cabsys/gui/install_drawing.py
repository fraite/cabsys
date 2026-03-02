import math
import tkinter
from tkinter import ttk
from typing import Union, List

import cabsys.iec.iec60287_2_1 as iec60287_2_1
import cabsys.iec.iec60287_1_1 as iec60287_1_1

from cabsys.data_classes.install import Install
from cabsys.data_classes.state import InstallState
from cabsys.quantity.exception import QuantityNoneError
from cabsys.iec.iec60287_2_1 import calc_delta_k_point_4_2_3_2
import cabsys.iec.iec_constants as iec

MAX_CABLE_SET_TABS = 15
DRAWING_GROUND_OFFSET = 50


class InstallDrawingFrame(tkinter.Frame):
    """binder for GuiCollection"""

    def __init__(self, parent: Union[tkinter.Toplevel, tkinter.Tk, tkinter.Frame, tkinter.Tk, tkinter.PanedWindow,
                                     ttk.Notebook],
                 install: Install,
                 install_state: InstallState = None,
                 cond_thetas_list: List[List[float]] = None,
                 amp_list: List[float] = None,
                 **kw):
        self.parent = parent
        self.install = install
        self.install_state = install_state
        # self.install_state = None
        self.cond_thetas_list = cond_thetas_list
        self.amp_list = amp_list
        super().__init__(parent, **kw)

        self.offset_x = None
        self.offset_y = None
        self.drawing_offset_x = 0
        self.drawing_offset_y = 0
        self.drawing_scale = min(self.install.config.drawing_scale.value, 1)
        self.drawing_scale = max(self.drawing_scale, 0)
        self.scale = None

        self.rowconfigure(0, minsize="0", weight=1, pad="5")
        self.columnconfigure(0, minsize='0', weight=1, pad='5')
        self.config(relief=tkinter.GROOVE)

        self.img = None
        self.canvas = tkinter.Canvas(self, background='gray75')
        self.canvas.grid(column=0, row=0, sticky='NSEW')
        self.canvas.bind('<Configure>', self.canvas_configure)
        self.offset_x_scale = tkinter.Scale(self, from_=-400, to=400,
                                            orient=tkinter.HORIZONTAL, showvalue=False,
                                            length=800, command=self.offset_x_callback)
        self.offset_x_scale.grid(column=0, row=1, sticky='EW')
        self.offset_x_scale.set(self.drawing_offset_x)
        self.offset_y_scale = tkinter.Scale(self, from_=0, to=100, orient=tkinter.VERTICAL, showvalue=False,
                                            length=100, command=self.offset_y_callback)
        self.offset_y_scale.grid(column=1, row=0, sticky='NS')
        self.offset_y_scale.set(self.drawing_offset_y)

        self.control_frame = tkinter.Frame(self)
        self.columnconfigure(0, minsize='0', weight=1)
        self.control_frame.grid(column=0, row=2, sticky="EW")
        self.control_frame.columnconfigure(3, minsize="0", weight=1, pad="5")
        self.zoom_label = ttk.Label(self.control_frame, text='Zoom')
        self.zoom_label.grid(column=1, row=1)
        self.scale_scale = tkinter.Scale(self.control_frame, from_=20, to=200, orient=tkinter.HORIZONTAL,
                                         showvalue=False, length=200, command=self.scale_callback)
        self.scale_scale.grid(column=2, row=1, sticky='E')
        self.scale_scale.set(int(self.drawing_scale*100))
        self.dry_zone_lab = ttk.Label(self.control_frame, text=f'Ground {self.install.theta_critical.value} °C '
                                                               f'dried out zone (m²):')
        self.dry_zone_lab.grid(column=3, row=1, sticky='E')
        self.dry_zone_value = ttk.Label(self.control_frame, text='N/A', width=8)
        self.dry_zone_value.grid(column=4, row=1)
        self.ground_thetas_button = tkinter.Button(self.control_frame, width=8,
                                                   text='Plot', command=self.plot_ground_thetas)
        self.ground_thetas_button.grid(column=5, row=1, sticky='E')

    def canvas_configure(self, event):
        # print(event)
        self.draw(event.width, event.height)

    def scale_callback(self, value):
        self.drawing_scale = int(value) / 100
        self.draw()

    def offset_x_callback(self, value):
        self.drawing_offset_x = int(value) / 400
        self.draw()

    def offset_y_callback(self, value):
        self.drawing_offset_y = int(value) / 100
        self.draw()

    def draw(self, width=None, height=None,
             cond_thetas_list: List[List[float]] = None, amp_list: List[float] = None):
        self.dry_zone_lab.config(text=f'Ground {self.install.theta_critical.value} °C dried out zone (m²):')
        self.dry_zone_value.config(text='N/A')

        if cond_thetas_list is not None:
            self.cond_thetas_list = cond_thetas_list
        if amp_list is not None:
            self.amp_list = amp_list
        # self.update()
        # x = self.winfo_rootx()
        # y = self.winfo_rooty()
        if height is None:
            height = self.canvas.winfo_height()
        if width is None:
            width = self.canvas.winfo_width()

        try:
            # min_x, min_y, max_x, max_y = self.install.find_extents()
            # print(self.install.find_extents())
            min_x, min_y, max_x, max_y = self.install.find_extents()
            drawing_width = max_x - min_x
            drawing_height = -min_y
            max_scale = max(drawing_width, drawing_height) / 1000 * 100
            self.scale_scale.config(to=max_scale)
        except QuantityNoneError:
            self.canvas.delete('all')
            self.canvas.create_text(width / 2 - 100, height / 2, text=f'unable to define extent of drawing \n'
                                                                      f'missing cables? \n'
                                                                      f'or problem designing installation?')
            return

        x_scale = self.drawing_scale * width / (max_x - min_x) if max_x != min_x else math.inf
        y_scale = self.drawing_scale * (height - DRAWING_GROUND_OFFSET) / (-min_y)
        self.scale = min(x_scale, y_scale)
        # print(self.scale)
        self.offset_x = int(-self.scale * (min_x + max_x) / 2 + width / 2 +
                            self.scale * (min_x - max_x) / 2 * self.drawing_offset_x)
        self.offset_y = DRAWING_GROUND_OFFSET + int(self.scale * min_y * self.drawing_offset_y)
        # print(height, self.drawing_scale, self.scale, self.offset_x, self.offset_y)

        self.offset_x_scale.config(sliderlength=max(self.offset_x_scale.winfo_width() * (0.8 - 0.8 * self.scale), 20))
        self.offset_y_scale.config(sliderlength=max(self.offset_y_scale.winfo_height() * (0.8 - 0.8 * self.scale), 20))

        self.canvas.delete('all')
        if self.offset_y > 0:
            self.canvas.create_line(0, self.offset_y, width, self.offset_y)
        self.draw_cables()

        if (self.install.rating_type.value == iec.RATING_CONTINUOUS and
                self.amp_list is not None and len(self.amp_list) > 0 and
                self.install.kind.value in [iec.BURIED]):
            self.ground_thetas_button.config(state='normal')
        else:
            # print(self.install_state, self.install.config.memorise.value)
            self.ground_thetas_button.config(state='disabled')

    def create_circle(self, centre_x, centre_y, diameter, outline=None):
        self.canvas.create_oval(self.offset_x + centre_x*self.scale - diameter/2 * self.scale,
                                self.offset_y - centre_y*self.scale - diameter/2 * self.scale,
                                self.offset_x + centre_x*self.scale + diameter/2 * self.scale,
                                self.offset_y - centre_y*self.scale + diameter/2 * self.scale,
                                outline=outline, fill=outline)

    def plot_ground_thetas(self):
        plot_pixel_size = self.install.config.drawing_pixel_size.value
        height = self.winfo_height()
        width = self.winfo_width()
        # TODO: move the ground temperature calculations to IEC60287_support
        wk = []
        for cable_set_k_num in range(len(self.install.cable_sets)):
            wk_cable_sets = []
            for cable_k_num in range(len(self.install.cable_sets[cable_set_k_num].placed_cables)):
                theta_sc = iec60287_1_1.calc_theta_sc(self.install, cable_set_k_num, cable_k_num,
                                                      self.amp_list[cable_set_k_num],
                                                      self.cond_thetas_list[cable_set_k_num][cable_k_num])
                wk_cable = iec60287_2_1.calc_wk(self.install, cable_set_k_num, cable_k_num,
                                                self.cond_thetas_list[cable_set_k_num][cable_k_num],
                                                theta_sc.value,
                                                self.amp_list[cable_set_k_num])
                wk_cable_sets.append(wk_cable.value)
            wk.append(wk_cable_sets)

        if self.install.rating_type.value == iec.RATING_CONTINUOUS:
            self.img = tkinter.PhotoImage(width=int(width), height=int(height))
            image = ''
            dry_zone = 0.0
            dry_zone_pixel_size = (plot_pixel_size / self.scale)**2 / 10**6
            for y_coordinate in range(max(self.offset_y, 0) + plot_pixel_size, height, plot_pixel_size):
                row = '{'
                for x_coordinate in range(0, width, plot_pixel_size):
                    # todo: check that x,y is not inside a cable
                    delta_theta = 0.0
                    for cable_set_k_num, cable_set_k in enumerate(self.install.cable_sets):
                        for cable_k_num in range(len(cable_set_k.placed_cables)):
                            # wk = self.install_state.cable_set_states[cable_set_k_num].placed_cable_states[
                            #     cable_k_num].cable_state.w_k.value
                            delta_theta_k_p = calc_delta_k_point_4_2_3_2(self.install,
                                                                         (x_coordinate - self.offset_x) / self.scale,
                                                                         -(y_coordinate - self.offset_y) / self.scale,
                                                                         cable_set_k_num, cable_k_num,
                                                                         wk[cable_set_k_num][cable_k_num])
                            delta_theta = delta_theta + delta_theta_k_p.value

                    theta = self.install.ambient_theta.value + delta_theta

                    if theta > self.install.theta_critical.value:
                        dry_zone = dry_zone + dry_zone_pixel_size

                    theta_colour = min(max(theta, 0), 80)
                    theta_colour = int(theta_colour / 10) * 10
                    theta_colour = int(theta_colour / 80 * 254)
                    # r, g, b = int(min(delta_theta, int(254 / 4))) * 4, 100, 100
                    r, g, b = (theta_colour, 120 - 40 * (theta > self.install.theta_critical.value),
                               115 - 30 * (theta > self.install.theta_critical.value))
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"

                    # self.canvas.create_rectangle(x_coordinate - plot_pixel_size,
                    #                              y_coordinate- plot_pixel_size,
                    #                              x_coordinate + plot_pixel_size,
                    #                              y_coordinate + plot_pixel_size,
                    #                              fill=hex_color, outline=hex_color)

                    row = row + (' ' + hex_color) * plot_pixel_size
                row = (row + '} ') * plot_pixel_size
                image = image + row
            self.img.put(image)
            self.canvas.create_image(0, max(self.offset_y, 0), image=self.img, anchor=tkinter.NW)
            self.dry_zone_value.config(text=round(dry_zone, 1))
        else:
            raise Exception('trying to plot the ground temperature but the rating type is not continuous')
        self.draw_cables()

    def draw_cables(self):
        for cable_set in self.install.cable_sets:
            for placed_cable in cable_set.placed_cables:
                if cable_set.duct_layout.value in [iec.INDIVIDUAL_AIR_DUCTS, iec.INDIVIDUAL_WATER_DUCT,
                                                   iec.INDIVIDUAL_FILLED_DUCT]:
                    self.create_circle(placed_cable.x.get_value(unit='mm'), placed_cable.y.get_value(unit='mm'),
                                       cable_set.duct_od.value)
                    self.create_circle(placed_cable.x.get_value(unit='mm'), placed_cable.y.get_value(unit='mm'),
                                       cable_set.duct_id.value)
                if cable_set.duct_layout.value in [iec.COMMON_AIR_DUCT, iec.COMMON_WATER_DUCT, iec.COMMON_FILLED_DUCT]:
                    self.create_circle(cable_set.pipe_x.get_value(unit='mm'), cable_set.pipe_y.get_value(unit='mm'),
                                       cable_set.duct_od.value)
                    self.create_circle(cable_set.pipe_x.get_value(unit='mm'), cable_set.pipe_y.get_value(unit='mm'),
                                       cable_set.duct_id.value)
                self.create_circle(placed_cable.x.get_value(unit='mm'), placed_cable.y.get_value(unit='mm'),
                                   placed_cable.cable.calc_outer_diameter(), outline=placed_cable.phase.value)

        height = self.winfo_height()
        width = self.winfo_width()
        if self.scale > 0.2:
            axis_scale = 100
        elif self.scale > 0.06:
            axis_scale = 500
        elif self.scale > 0.02:
            axis_scale = 5000
        elif self.scale > 0.006:
            axis_scale = 10000
        else:
            axis_scale = 50000

        # print(((-self.offset_x) / self.scale), ((width - self.offset_x) / self.scale), self.scale, 100 / self.scale)
        # print(math.ceil((-self.offset_x) / self.scale / axis_scale) * axis_scale,
        #       math.floor((width - self.offset_x) / self.scale / axis_scale) * axis_scale)
        for tick_x in range(math.floor((-self.offset_x) / self.scale / axis_scale) * axis_scale,
                            math.ceil((width - self.offset_x) / self.scale / axis_scale) * axis_scale,
                            axis_scale):
            if ((tick_x / 1000) == int(tick_x / 1000) or self.scale > 0.6 or
                    (self.scale > 0.2 and (tick_x / 500) == int(tick_x / 500))):
                self.canvas.create_line(tick_x * self.scale + self.offset_x, height - DRAWING_GROUND_OFFSET,
                                        tick_x * self.scale + self.offset_x, height - DRAWING_GROUND_OFFSET - 20)
                self.canvas.create_text(tick_x * self.scale + self.offset_x, height - DRAWING_GROUND_OFFSET - 30,
                                        text=str(tick_x / 1000) + " m")
            else:
                self.canvas.create_line(tick_x * self.scale + self.offset_x, height - DRAWING_GROUND_OFFSET,
                                        tick_x * self.scale + self.offset_x, height - DRAWING_GROUND_OFFSET - 10)

        for cable_set in self.install.cable_sets:
            for placed_cable in cable_set.placed_cables:
                tick_x = placed_cable.x.value
                tick_y = placed_cable.y.value
                self.canvas.create_line(tick_x * self.scale + self.offset_x, height - DRAWING_GROUND_OFFSET,
                                        tick_x * self.scale + self.offset_x, height - DRAWING_GROUND_OFFSET - 15,
                                        arrow=tkinter.LAST)
                self.canvas.create_line(0, -tick_y * self.scale + self.offset_y,
                                        15, -tick_y * self.scale + self.offset_y,
                                        arrow=tkinter.LAST)