import tkinter
from tkinter import ttk
from idlelib.tooltip import Hovertip
from typing import Union
from collections.abc import Callable

import cabsys.quantity.quantity_constants as dc
import cabsys.quantity.quantity_store as quant_store

# TODO: move overview_widgets from gui package to quantity package and rename to quantity_widgets


class EntryInt(ttk.Entry):
    """EntryBox widget tied to a Quantity instance"""

    def __init__(self, container: tkinter.Widget, quantity: quant_store.QuantityBase, is_auto_design: Callable,
                 *args, **kw):
        """EntryBox widget tied to a Quantity instance

        The EntryBox widget is not fully bound to the Quantity instance. If the Quantity instance changes value the
        EntryInt needs to be updated by calling the update_entry method. If the value of the EntryInt widget is changed
        the Quantity instance will be automatically updated.

        where the is_auto_design callable returns False, empty EntryBox widgets will cause the quantity value to be set
        to None and the EntryBox widget will show "<None>" in grey.

        where the is_auto_design callable returns True, empty EntryBox widgets will cause the quantity value to be set
        to the default calculated value and the EntryBox widget will show the default calculated value in grey.

        note: Style is defined in project_viewer

        :param container: the container holding the EntryInt widget
        :param quantity: the quantity instance the widget is tied to
        :param is_auto_design: callable that returns if the quantity is calculated by an auto_design function
        :param args: arguments to be passed to the Entry ttk widget
        :param kw: keywords to be passed to the Entry ttk widget
        """

        super().__init__(container, *args, style='Placeholder.TEntry', **kw)
        self.container = container
        self.quantity = quantity
        self.auto_design = is_auto_design
        self.default_on_entry: bool = False

        self.string_var = tkinter.StringVar()
        value = self.quantity.value
        if value is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(value)

        self.config(state="normal")
        self.config(textvariable=self.string_var)

        # grey out the entry box if required - note also set in self.update_entry()
        if self.auto_design():
            if self.quantity.source in dc.ATTR_FIXED_INPUTS:
                self['style'] = 'TEntry'
            else:
                self['style'] = 'Placeholder.TEntry'
        else:
            if value is None:
                self['style'] = 'Placeholder.TEntry'
            else:
                self['style'] = 'TEntry'

        self.bind('<Return>', lambda
                  event: self._return_callback(event)
                  )
        self.bind('<FocusOut>', lambda
                  event: self._focus_out_callback(event)
                  )
        self.bind('<FocusIn>', lambda
                  event: self._clear_entry_box(event)
                  )

        Hovertip(self, self.quantity.description)

    def update_entry(self, quantity: quant_store.QuantityBase = None) -> None:
        """Update the entry box with the value of the quantity assigned to the entry box

        Puts the value of the quantity assigned in the entry box into the entry box and sets the style to:
        * greyed out if not a user selected value (for auto design objects)
        * greyed out if value is None for non-auto design objects

        The assigned quantity object can be changed if required.

        :param quantity: re-assign the entry box to a new quantity given
        :return: None
        """
        # entry box is being re-assigned to a new quantity if required
        if quantity is not None:
            self.quantity = quantity
        # put the value of the quantity into the box
        value = self.quantity.value
        if value is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(value)
        # grey out the entry box if required - note also set in self.__init()
        if self.auto_design():
            if self.quantity.source in dc.ATTR_FIXED_INPUTS:
                self['style'] = 'TEntry'
            else:
                self['style'] = 'Placeholder.TEntry'
        else:
            if value is None:
                self['style'] = 'Placeholder.TEntry'
            else:
                self['style'] = 'TEntry'

    def _clear_entry_box(self, _event):
        if self.auto_design():
            if self.quantity.source not in dc.ATTR_FIXED_INPUTS:
                self.string_var.set('')
                self.default_on_entry = True
            else:
                self.default_on_entry = False
            self['style'] = 'TEntry'
        else:
            # if self.string_var.get() == '<None>':
            if self.quantity.value is None:
                self.string_var.set('')
                self['style'] = 'TEntry'

    def _return_callback(self, _event):
        # self.update_quantity(event)
        self.container.focus_set()
        # if self.quantity.source not in dc.ATTR_FIXED_INPUTS:
        #     self.string_var.set('')
        # self['style'] = 'TEntry'

    def _focus_out_callback(self, _event) -> None:
        old_value = self.quantity.value
        if self.auto_design():
            try:
                if self.string_var.get() == '':
                    if self.default_on_entry:
                        if old_value is None:
                            self.string_var.set('<None>')
                        else:
                            self.string_var.set(old_value)
                    else:
                        self.quantity.source = None
                        self.container.event_generate("<<Q_change>>")
                    self['style'] = 'Placeholder.TEntry'
                else:
                    if isinstance(self.quantity, quant_store.QInt):
                        q_value = int(self.string_var.get())
                    elif isinstance(self.quantity, quant_store.QFloat):
                        q_value = float(self.string_var.get())
                    elif isinstance(self.quantity, quant_store.QStr):
                        q_value = self.string_var.get()
                    else:
                        raise Exception(f'unexpected quantity for entry widget {type(quant_store)}')
                    self.quantity.set_value(q_value, source=dc.ATTR_USER_SET)
                    self.container.event_generate("<<Q_change>>")

            except ValueError:
                if old_value is None:
                    self.string_var.set('<None>')
                else:
                    self.string_var.set(old_value)
                if self.default_on_entry:
                    self['style'] = 'Placeholder.TEntry'

        else:
            if self.string_var.get() == '':
                self.quantity.set_value(None)
                self.string_var.set('<None>')
                self['style'] = 'Placeholder.TEntry'
            else:
                if isinstance(self.quantity, quant_store.QInt):
                    q_value = int(self.string_var.get())
                elif isinstance(self.quantity, quant_store.QFloat):
                    q_value = float(self.string_var.get())
                elif isinstance(self.quantity, quant_store.QStr):
                    q_value = self.string_var.get()
                else:
                    raise Exception(f'unexpected quantity for entry widget {type(quant_store)}')
                self.quantity.set_value(q_value, source=dc.ATTR_USER_SET)
                self['style'] = 'TEntry'
            self.container.event_generate("<<Q_change>>")

    def get_quantity(self) -> quant_store.QuantityBase:
        return self.quantity


class ComboboxString(ttk.Combobox):
    """Combobox for values tied to a string quantity"""

    def __init__(self, container, quantity: Union[quant_store.QStr, quant_store.QFloat], is_auto_design: Callable,
                 **kw):
        super().__init__(container, style='Placeholder.TCombobox', **kw)
        self.container = container
        self.quantity = quantity
        self.auto_design = is_auto_design
        if self.quantity.options is None:
            options = []
        else:
            options = list(self.quantity.options)
        options.append('<default>')

        self.config(values=options)

        self.string_var = tkinter.StringVar()
        value = self.quantity.value
        if value is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(value)

        self.config(textvariable=self.string_var)

        # set colour of combobox - note also set in self.update_combobox()
        if self.auto_design():
            if self.quantity.source in dc.ATTR_FIXED_INPUTS:
                self['style'] = 'TCombobox'
            else:
                self['style'] = 'Placeholder.TCombobox'
        else:
            if value is None:
                self['style'] = 'Placeholder.TCombobox'
            else:
                self['style'] = 'TCombobox'

        self.bind('<<ComboboxSelected>>', lambda
                  event: self.update_quantity(event)
                  )

        Hovertip(self, self.quantity.description)

    def update_combobox(self, quantity: Union[quant_store.QStr, quant_store.QFloat] = None):
        if quantity is not None:
            self.quantity = quantity

        value = self.quantity.value
        if value is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(value)

        # set colour of combobox - note also set in self.__init__()
        if self.auto_design():
            if self.quantity.source in dc.ATTR_FIXED_INPUTS:
                self['style'] = 'TCombobox'
            else:
                self['style'] = 'Placeholder.TCombobox'
        else:
            if value is None:
                self['style'] = 'Placeholder.TCombobox'
            else:
                self['style'] = 'TCombobox'

    def update_quantity(self, _event):
        old_value = self.quantity.value
        try:
            if self.string_var.get() == '<default>':
                self.quantity.set_value(None, source=None)
            else:
                str_value = str(self.string_var.get())
                self.quantity.set_value(str_value, source=dc.ATTR_USER_SET)
            if self.quantity.value is None:
                value = ''
            else:
                value = self.quantity.get_value()
            self.string_var.set(value)
            self.container.event_generate("<<Q_change>>", when="tail")
        except ValueError:
            self.string_var.set(old_value)
            # self.ambient_temp_var1.set(self.install.auto_ambient_theta.value)

    def get_quantity(self) -> quant_store.QuantityBase:
        return self.quantity


class ComboboxBool(ttk.Combobox):
    """Combobox for values tied to a bool quantity"""

    def __init__(self, container: tkinter.Frame, quantity: quant_store.QBool, is_auto_design: Callable, **kw):
        super().__init__(container, style='Placeholder.TCombobox', **kw)
        self.config(state="readonly")
        self.container = container
        self.quantity: quant_store.QBool = quantity
        self.auto_design = is_auto_design

        self.config(values=('True', 'False', '<default>'))

        self.string_var = tkinter.StringVar()
        value = self.quantity.value
        if value is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(str(value))

        # set colour of combobox - note also set in self.__init__()
        if self.auto_design():
            if self.quantity.source in dc.ATTR_FIXED_INPUTS:
                self['style'] = 'TCombobox'
            else:
                self['style'] = 'Placeholder.TCombobox'
        else:
            if value is None:
                self['style'] = 'Placeholder.TCombobox'
            else:
                self['style'] = 'TCombobox'

        self.config(textvariable=self.string_var, state='readonly')

        self.bind('<<ComboboxSelected>>', lambda
                  event: self.update_quantity(event)
                  )

        Hovertip(self, self.quantity.description)

    def update_combobox(self, quantity: quant_store.QBool = None):
        if quantity is not None:
            self.quantity = quantity

        value = self.quantity.value
        if value is None:
            self.string_var.set('<None>')
        elif value:
            self.string_var.set('True')
        else:
            self.string_var.set('False')

        # set colour of widget - see also self.__init__()
        if self.auto_design():
            if self.quantity.source in dc.ATTR_FIXED_INPUTS:
                self['style'] = 'TCombobox'
            else:
                self['style'] = 'Placeholder.TCombobox'
        else:
            if value is None:
                self['style'] = 'Placeholder.TCombobox'
            else:
                self['style'] = 'TCombobox'

    def update_quantity(self, _event):
        old_value = self.quantity.get_value()
        try:
            if self.string_var.get() == '<default>':
                self.quantity.set_value(None, source=None)
            elif self.string_var.get() == 'False':
                self.quantity.set_value(False, source=dc.ATTR_USER_SET)
            else:
                self.quantity.set_value(True, source=dc.ATTR_USER_SET)
            self.string_var.set(str(self.quantity.get_value()))
            self.container.event_generate("<<Q_change>>", when="tail")
        except ValueError:
            self.string_var.set(str(old_value))
            # self.ambient_temp_var1.set(self.install.auto_ambient_theta.value)

    def get_quantity(self) -> quant_store.QuantityBase:
        return self.quantity


class CheckbuttonBool(ttk.Checkbutton):
    """Checkbutton for values tied to a bool quantity"""

    def __init__(self, container: tkinter.Frame, quantity: quant_store.QBool, is_auto_design: Callable, **kw):

        super().__init__(container, onvalue='True', offvalue='False', command=self.update_quantity,
                         style='Placeholder.TCheckbutton', **kw)

        self.string_var = tkinter.StringVar()
        self.quantity: quant_store.QBool = quantity
        self.text = self.cget('text')
        value = self.quantity.value
        if value is None:
            self.string_var.set('<None>')
        else:
            self.string_var.set(str(value))

        self.container = container
        self.auto_design = is_auto_design

        # set colour of Checkbutton - note also set in self.__init__()
        if self.auto_design():
            if self.quantity.source in dc.ATTR_FIXED_INPUTS:
                self['style'] = 'TCheckbutton'
                if self.text != '':
                    self.config(text=f'{self.text}')
            else:
                self['style'] = 'Placeholder.TCheckbutton'
                if self.text != '':
                    self.config(text=f'{self.text}*')
        else:
            if value is None:
                self['style'] = 'Placeholder.TCheckbutton'
                if self.text != '':
                    self.config(text=f'{self.text}*')
            else:
                self['style'] = 'TCheckbutton'
                if self.text != '':
                    self.config(text=f'{self.text}')

        self.config(variable=self.string_var)

        if is_auto_design():
            self.bind('<Button-2>', lambda
                      event: self.set_quantity_auto_calc(event)
                      )

        if is_auto_design():
            Hovertip(self, self.quantity.description + '\n(* = default value, use middle mouse button for default)')
        else:
            Hovertip(self, self.quantity.description)

    def update_checkbutton(self, quantity: quant_store.QBool = None):
        if quantity is not None:
            self.quantity = quantity

        value = self.quantity.value
        if value is None:
            self.string_var.set('<None>')
        elif value:
            self.string_var.set('True')
        else:
            self.string_var.set('False')

        # set colour of widget - see also self.__init__()
        if self.auto_design():
            if self.quantity.source in dc.ATTR_FIXED_INPUTS:
                self['style'] = 'TCheckbutton'
                if self.text != '':
                    self.config(text=f'{self.text}')
            else:
                self['style'] = 'Placeholder.TCheckbutton'
                if self.text != '':
                    self.config(text=f'{self.text}*')
        else:
            if value is None:
                self['style'] = 'Placeholder.TCheckbutton'
                if self.text != '':
                    self.config(text=f'{self.text}*')
            else:
                self['style'] = 'TCheckbutton'
                if self.text != '':
                    self.config(text=f'{self.text}')

    def update_quantity(self):
        if self.string_var.get() == 'False':
            self.quantity.set_value(False, source=dc.ATTR_USER_SET)
        elif self.string_var.get() == 'True':
            self.quantity.set_value(True, source=dc.ATTR_USER_SET)
        else:
            self.quantity.set_value(None)
        self.container.event_generate("<<Q_change>>", when="tail")

    def set_quantity_auto_calc(self, _event):

        if self.auto_design():
            self.quantity.set_value(None, source=None)

        self.container.event_generate("<<Q_change>>", when="tail")

    def get_quantity(self) -> quant_store.QuantityBase:
        return self.quantity
