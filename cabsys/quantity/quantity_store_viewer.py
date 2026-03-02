import tkinter
from tkinter import ttk
from tkinter.messagebox import showwarning
from idlelib.tooltip import Hovertip
from typing import Dict, Union, List, Any
import cabsys.quantity.quantity_constants as qc
from cabsys.quantity.quantity_store import QFloat, QBool, QInt, QStr, QuantityBase

try:
    from typing import GenericMeta   # python 3.6
except ImportError:
    # in 3.7, Generic Meta doesn't exist but we don't need it
    class GenericMeta(type):
        pass
import typing
from cabsys.quantity.quantity_store import QuantityStore
import winsound


class QuantFrame(tkinter.Frame):

    def __init__(self, parent: Union[tkinter.Toplevel, tkinter.Tk, tkinter.Frame, tkinter.Tk, tkinter.PanedWindow],
                 instance: QuantityStore,
                 edit_name: bool = True, show_name: bool = True,
                 is_auto_design: bool = False,
                 end_attr_name: List[str] = None, end_options: List[Dict[str, object]] = None,
                 **kw) -> None:
        """Fills a ttk_Frame that contains a representation of a DataStore object

        A frame that shows all the attributes of the given instance object. Where the attributes are quantities, the
        unit, source and description are also shown as well as the value. Where the attributes are simple Python classes
        such as Float, Strings or Integers, the value will be shown. These values can be changed by the user.

        Where an attribute is another DataStore or List, a tree view shows all these attributes. By selecting the
        DataStore or List item in the TreeView the attributes for the item in the TreeView will be shown.

        If a end_attr_name is given, the tree widget will not show the object given by name and the object will be
        shown as an attribute instead. The available options are defined in the end_options, with the key being the
        option names, and the object being the objects relating to the name.

        The name attribute can be used by other objects to identify an object and in these cases changing the name of
        the object can cause problems. By resetting edit_name or show_name to false, this allows the name either to be
        shown but not allowed to be edited, or not show the name attribute at all.

        :param parent:  tkinter widget parent that the data_store_ttk_frame is to be inserted into
        :param instance: DataStore object that is to be shown
        :param edit_name: allow 'name' attribute to be edited
        :param show_name: allow 'name' attribute to be shown
        :param is_auto_design: if true the DataStore object will update its design after an attribute is changed
        :param end_attr_name: a list of attribute names that stop the viewer from showing sub attributes
        :param end_options: the options to show an end attribute
        """

        super().__init__(parent, **kw)
        self.instance = instance
        self.edit_name = edit_name
        self.show_name = show_name
        self.is_auto_design = is_auto_design
        if end_attr_name is None:
            self.end_attr_name = []
        else:
            self.end_attr_name = end_attr_name
        if end_options is None:
            self.end_class_options = []
        else:
            self.end_class_options = end_options

        # these contain the attributes chosen in the tree, and the object it belongs to
        self.chosen_instance_in_tree = self.instance
        self.chosen_attr = None
        self.chosen_attr_iid = None
        self.chosen_attr_type = None
        self.old_value_before_edit = ''
        self.old_value_type_before_edit = None

        self.combobox_key_pressed = False

        self.attr_fixed = tkinter.IntVar()

        self.paned_window = ttk.PanedWindow(self, orient=tkinter.HORIZONTAL)
        self.paned_window.grid(column=1, row=1, sticky='NWES')
        self.paned_window.columnconfigure(1, weight=1)
        self.paned_window.rowconfigure(1, weight=1)

        # frame containing navigation tree and list of attributes
        self.navigator_frame = ttk.Frame(self.paned_window)
        self.navigator_frame.grid(column=1, row=1, sticky='NWES')
        self.navigator_frame.columnconfigure(1, weight=1)
        self.navigator_frame.rowconfigure(1, weight=1)
        self.navigator_frame['padding'] = (5, 10)
        self.navigator_frame['relief'] = tkinter.GROOVE
        self.paned_window.add(self.navigator_frame)

        # navigation tree
        self.nav_tree = ttk.Treeview(self.navigator_frame, takefocus=True, selectmode=tkinter.BROWSE)

        self.nav_tree.tag_bind('branch', '<ButtonRelease-1>',
                               self.attr_tree_branch_release_callback)
        # self.attr_tree.tag_bind('leaf', '<ButtonRelease-1>',
        #                         self.attr_tree_leaf_release_callback)
        self.nav_tree.grid(column=0, row=1, columnspan=4, sticky='NWES')
        self.scrollbar_navigator = ttk.Scrollbar(self.navigator_frame, orient=tkinter.VERTICAL,
                                                 command=self.nav_tree.yview)
        self.scrollbar_navigator.grid(column=4, row=1, sticky='NS')
        self.nav_tree['yscrollcommand'] = self.scrollbar_navigator.set

        # attr frame
        self.attr_canvas = tkinter.Canvas(self.paned_window)
        self.attr_canvas.grid(column=2, row=1, sticky='NS')
        self.attr_canvas.columnconfigure(1, weight=1)
        self.paned_window.add(self.attr_canvas, weight=1)

        self.scrollbar_attr = ttk.Scrollbar(self, orient=tkinter.VERTICAL, command=self.attr_canvas.yview)
        self.scrollbar_attr.grid(column=3, row=1, sticky='NS')
        self.attr_canvas['yscrollcommand'] = self.scrollbar_attr.set
        self.attr_frame = ttk.Frame(self.attr_canvas)
        self.canvas_attr_window = self.attr_canvas.create_window((0, 0), window=self.attr_frame, anchor='nw')
        self.attr_canvas.bind('<Configure>', self.frame_width)
        self.attr_frame.bind('<Configure>', self.frame_func)
        # self.attr_frame.grid(column=2, row=1, sticky='NWES')
        # self.attr_frame.columnconfigure(1, weight=1)
        # self.attr_frame.rowconfigure(1, weight=1)
        # self.attr_frame['padding'] = (5, 10)
        # self.attr_frame['relief'] = tkinter.GROOVE
        ttk.Label(self.attr_frame, text='attribute name').grid(column=0, row=0)
        self.attr_frame.grid_columnconfigure(0, minsize=150)
        ttk.Label(self.attr_frame, text='attribute value').grid(column=1, row=0)
        self.attr_frame.grid_columnconfigure(1, minsize=350)
        ttk.Label(self.attr_frame, text='unit').grid(column=3, row=0)
        self.attr_frame.grid_columnconfigure(3, minsize=60)
        ttk.Label(self.attr_frame, text='source').grid(column=4, row=0)
        self.attr_frame.columnconfigure(4, minsize=150, weight=1)
        # ttk.Label(self.attr_frame, text='description of attribute').grid(column=5, row=0)
        # self.attr_frame.columnconfigure(5, minsize=300)

        self.attr_source_combobox_list: Dict[str, ttk.Combobox] = dict()
        self.attr_value_combobox_list: Dict[str, ttk.Combobox] = dict()
        self.attr_labels: [ttk.Label] = []
        self.attr_type_combobox_s: [ttk.Combobox] = []
        self.attr_unit_labels: [ttk.Label] = []
        # self.attr_desc_labels: [ttk.Label] = []

        self.update_viewer()

    def frame_width(self, event):
        canvas_width = event.width
        self.attr_canvas.itemconfig(self.canvas_attr_window, width=canvas_width-6)
        # self.attr_frame.config(width=canvas_width-4)

    def update_viewer(self) -> None:

        # these contain the attributes chosen in the tree, and the object it belongs to
        self.chosen_instance_in_tree = self.instance
        self.chosen_attr = None
        self.chosen_attr_iid = None
        self.chosen_attr_type = None
        self.old_value_before_edit = ''
        self.old_value_type_before_edit = None

        self.nav_tree_rebuild()

        self.combobox_key_pressed = False

        self.attr_frame_build(self.chosen_instance_in_tree)

    def frame_func(self, _event):
        self.attr_canvas.configure(scrollregion=self.attr_canvas.bbox('all'), width=self.attr_frame.winfo_width())

    def attr_frame_empty(self):
        for attr_label in self.attr_labels:
            attr_label.destroy()
        self.attr_labels = []
        for k, attr_combobox in self.attr_value_combobox_list.items():
            attr_combobox.destroy()
        self.attr_value_combobox_list = {}
        for attr_type_combobox in self.attr_type_combobox_s:
            attr_type_combobox.destroy()
        self.attr_type_combobox_s = []
        for k, attr_source_combobox in self.attr_source_combobox_list.items():
            attr_source_combobox.destroy()
        self.attr_source_combobox_list = {}
        for attr_unit_label in self.attr_unit_labels:
            attr_unit_label.destroy()
        self.attr_unit_labels = []
        # for attr_desc_label in self.attr_desc_labels:
        #     attr_desc_label.destroy()
        # self.attr_desc_labels = []

    def attr_frame_build(self, selected_quantity_store: QuantityStore):
        self.attr_frame_empty()
        row = 0
        for item_key, item_val in vars(selected_quantity_store).items():

            attr_value, attr_unit, attr_description, \
                attr_source, attr_options = self.get_attr_details(item_key, selected_quantity_store)

            if attr_value is None:
                continue
            else:
                # attribute label
                attr_label = ttk.Label(self.attr_frame, text=item_key)
                attr_label.grid(column=0, row=row + 1)
                self.attr_labels.append(attr_label)

                # self.attribute source combobox
                attr_source_combobox = ttk.Combobox(self.attr_frame)
                attr_source_combobox.set(attr_source)
                attr_source_combobox.config(state=tkinter.DISABLED, width=30)
                attr_source_combobox['values'] = (qc.ATTR_USER_SET, '<None>')
                # show this box, but disable
                attr_source_combobox.grid(column=4, row=row + 1, sticky='EW')
                # attr_user_combobox.bind('<<ComboboxSelected>>', self.attr_fixed_checkbox_button1_callback)
                self.attr_source_combobox_list[item_key] = attr_source_combobox

                # attribute value Combobox widget
                if isinstance(item_val, QuantityBase):
                    attr_combobox = QuantityCombobox(self.attr_frame, item_val)
                else:
                    attr_combobox = ttk.Combobox(self.attr_frame)
                attr_combobox.config(state=tkinter.NORMAL)

                if attr_value == '<None>':
                    attr_combobox.set('<None>')
                else:
                    if type(attr_value) == bool:
                        if attr_value:
                            attr_combobox.set('True')
                        else:
                            attr_combobox.set('False')
                    else:
                        attr_combobox.set(attr_value)
                if type(attr_value) == bool:
                    attr_combobox['values'] = ['True', 'False', '<None>']
                else:
                    attr_combobox['values'] = attr_options

                attr_combobox.grid(column=1, row=row + 1, sticky='EW')
                attr_combobox.bind('<Button-1>', lambda
                                   event, arg1=item_key, arg2=attr_combobox:
                                   self.attr_combobox_button1_callback(event, arg1, arg2)
                                   )
                attr_combobox.bind('<ButtonRelease-1>', lambda
                                   event, arg1=item_key, arg2=attr_combobox:
                                   self.attr_combobox_buttonrelease1_callback(event, arg1, arg2)
                                   )
                attr_combobox.bind('<<ComboboxSelected>>', lambda
                                   event, arg1=item_key, arg2=attr_combobox, arg3=attr_source_combobox:
                                   self.attr_combobox_changed_callback2(event, arg1, arg2, arg3)
                                   )
                attr_combobox.bind('<Return>', lambda
                                   event, arg1=item_key, arg2=attr_combobox, arg3=attr_source_combobox:
                                   self.attr_combobox_changed_callback2(event, arg1, arg2, arg3)
                                   )
                attr_combobox.bind('<FocusOut>', lambda
                                   event, arg1=item_key, arg2=attr_combobox, arg3=attr_source_combobox:
                                   self.attr_combobox_focus_lost(event, arg1, arg2, arg3)
                                   )
                attr_combobox.bind('<Key>', self.combobox_key)
                if attr_description is not None and attr_description != '' and attr_description != '-':
                    Hovertip(attr_combobox, attr_description)
                self.attr_value_combobox_list[item_key] = attr_combobox

                # unit of measure
                attr_unit_label = ttk.Label(self.attr_frame, text=attr_unit)
                attr_unit_label.grid(column=3, row=row + 1)
                self.attr_unit_labels.append(attr_unit_label)
                # description
                # attr_desc_label = ttk.Label(self.attr_frame, text=attr_description)
                # attr_desc_label.grid(column=5, row=row + 1)
                # self.attr_desc_labels.append(attr_desc_label)

                row = row + 1

    def attr_frame_update(self, selected_quantity_store: QuantityStore):
        """Update the attribute frame

        Note that this only updates the existing attributes displayed in the frame. New attributes are not added to the
        frame and attributes that do not exist are not deleted.

        :param selected_quantity_store:
        :return:
        """
        row = 0
        for item_key, item_val in vars(selected_quantity_store).items():

            attr_value, attr_unit, attr_description, \
                attr_source, attr_options = self.get_attr_details(item_key, selected_quantity_store)

            if attr_value is not None:
                # self.attribute fixed checkbox
                attr_source_combobox = self.attr_source_combobox_list[item_key]
                attr_source_combobox.set(attr_source)
                attr_source_combobox.config(state=tkinter.DISABLED)
                attr_source_combobox['values'] = (qc.ATTR_USER_SET, '<None>')

                # attribute value Combobox widget
                attr_combobox = self.attr_value_combobox_list[item_key]
                if item_key == 'name' and not self.edit_name:
                    attr_combobox.config(state=tkinter.DISABLED)
                else:
                    attr_combobox.config(state=tkinter.NORMAL)
                if attr_value == '<None>':
                    attr_combobox.set('<None>')
                else:
                    if type(attr_value) == bool:
                        if attr_value:
                            attr_combobox.set('True')
                        else:
                            attr_combobox.set('False')
                    else:
                        attr_combobox.set(attr_value)
                if type(attr_value) == bool:
                    attr_combobox['values'] = ['True', 'False', '<None>']
                else:
                    attr_combobox['values'] = attr_options

                row = row + 1

    def get_attr_details(self, attr_name, quantity_store: QuantityStore) -> (Any, Any, Any, Any, Any):
        """Extracts details from an attribute in a quantity_store

        If:
            * attribute name starts with '_', or is 'name' and self.shown_name is false, then returns None.
            * attribute is a List then returns None.
            * attribute is a QuantityStore and the QuantityStore has a name attribute, then the att_value returned is
              the QuantityStore.name, the options are those defined in self.end_class_options and all other values
              returned are '-'
        otherwise
            * the quantities value, unit, description, source and options are returned

        :param attr_name: attribute name
        :param quantity_store: the quantity_store object holding the attribute
        :return: attr_value, attr_unit, attr_description, attr_source, attr_options
        """

        if attr_name.startswith('_'):
            return None, None, None, None, None
        if attr_name == 'name' and not self.show_name:
            return None, None, None, None, None

        item_val = getattr(quantity_store, attr_name)

        if isinstance(item_val, Dict):
            return None, None, None, None, None

        if isinstance(item_val, List):
            return None, None, None, None, None

        if isinstance(item_val, QuantityStore):
            attr_value = getattr(item_val, 'name', None)
            attr_unit = attr_description = attr_source = '-'
            if attr_value is not None:
                index = self.end_attr_name.index(attr_name)
                attr_options = list(self.end_class_options[index].keys())
                attr_options.append('<None>')
                return attr_value, attr_unit, attr_description, attr_source, attr_options
            else:
                return None, None, None, None, None

        attr_value = quantity_store.get_value(attr_name)
        if attr_value is None:
            attr_value = '<None>'

        if attr_name in self.end_attr_name:
            index = self.end_attr_name.index(attr_name)
            attr_options = list(self.end_class_options[index].keys())
            attr_options.append('<None>')
        else:
            data_store_options = quantity_store.get_options(attr_name, default='-')
            if data_store_options is None:
                attr_options = '<None>'
            else:
                attr_options = list(data_store_options)
                attr_options.append('<None>')

        data_store_source = quantity_store.get_source(attr_name, default='-')
        if data_store_source is None:
            attr_source = '<None>'
        else:
            attr_source = data_store_source

        data_store_unit = quantity_store.get_unit(attr_name, default='-')
        if data_store_unit is None:
            attr_unit = '<None>'
        else:
            attr_unit = data_store_unit

        data_store_description = quantity_store.get_description(attr_name, default='-')
        if data_store_description is None:
            attr_description = '<None>'
        else:
            attr_description = data_store_description

        return attr_value, attr_unit, attr_description, attr_source, attr_options

    def nav_tree_rebuild(self):
        """rebuilds the navigation tree

        Deletes the existing navigation tree and replaces it with QuantityStore in self.instance. The selected item will
        be the self.instance at the root of the tree.

        :return:
        """
        ds_item = self.instance
        idd_list = []
        self.nav_tree_update_branch_add(ds_item, type(ds_item).__name__, '', idd_list)
        self.nav_tree_update_branch_delete('', idd_list)
        # set focus and selection to first item in navigation tree
        self.nav_tree.focus(idd_list[0])
        self.nav_tree.selection_set(idd_list[0])

    def nav_tree_update_branch_add(self, branch, branch_name: str, idd: str, idd_list: list):
        if branch_name.startswith('_'):
            return
        if branch_name in self.end_attr_name:
            return
        if isinstance(branch, QuantityStore) or isinstance(branch, list) or isinstance(branch, dict):
            if isinstance(branch, QuantityStore) or isinstance(branch, dict):
                parent_idd = idd
                if idd == '':
                    idd = branch_name
                else:
                    idd = f'{parent_idd},{branch_name}'
                idd_list.append(idd)
                if not self.nav_tree.exists(idd):
                    self.nav_tree.insert(parent_idd, 'end', idd, text=branch_name, tags='branch')
            if isinstance(branch, QuantityStore):
                for k, v in vars(branch).items():
                    self.nav_tree_update_branch_add(v, k, idd, idd_list)
            elif isinstance(branch, dict):
                for k, v in branch.items():
                    self.nav_tree_update_branch_add(v, k, idd, idd_list)
            else:
                for i, list_item in enumerate(branch):
                    list_item_name = f'{branch_name}[{str(i)}]'
                    self.nav_tree_update_branch_add(list_item, list_item_name, idd, idd_list)

    def nav_tree_update_branch_delete(self, tree_item, idd_list: list):
        tree_item_children = self.nav_tree.get_children(tree_item)
        for index in range(len(tree_item_children)):
            tree_item_child = tree_item_children[index]
            if tree_item_child not in idd_list:
                self.nav_tree.delete(tree_item_child)
            else:
                self.nav_tree_update_branch_delete(tree_item_child, idd_list)

    def fill_attr_entry_widgets_branch(self, chosen_attr_idd: str):
        """Update the attribute entry widgets with the new chosen attribute for an attribute branch.

        Puts the entry widgets (attribute Combobox, attribute type Combobox and fixed Checkbox with the details from
        the new attribute chosen in the attribute tree."""

        self.chosen_attr_iid = chosen_attr_idd

        # find chosen attribute and chosen instance using chosen attribute list
        chosen_attr_list = chosen_attr_idd.split(',')
        chosen_attr_instance = self.instance
        while len(chosen_attr_list) > 1:
            del chosen_attr_list[0]
            if isinstance(chosen_attr_instance, QuantityStore):
                if '[' in chosen_attr_list[0]:
                    list_name = chosen_attr_list[0].split('[')[0]
                    item_no = chosen_attr_list[0].split('[')[1][:-1]
                    chosen_attr_instance_child = vars(chosen_attr_instance)[list_name][int(item_no)]
                else:
                    chosen_attr_instance_child = vars(chosen_attr_instance)[chosen_attr_list[0]]
            elif isinstance(chosen_attr_instance, dict):
                if '[' in chosen_attr_list[0]:
                    list_name = chosen_attr_list[0].split('[')[0]
                    item_no = chosen_attr_list[0].split('[')[1][:-1]
                    chosen_attr_instance_child = chosen_attr_instance[list_name][int(item_no)]
                else:
                    chosen_attr_instance_child = chosen_attr_instance[chosen_attr_list[0]]
            elif isinstance(chosen_attr_instance, list) or isinstance(chosen_attr_instance, tuple):
                raise Exception('should not get a list or tuple')
                # chosen_attr_instance_child = chosen_attr_instance[int(chosen_attr_list[0])]
            else:
                raise Exception(f'Got {type(chosen_attr_instance).__name__}, only dict or DataStore object allowed')
                # chosen_attr_instance_child = chosen_attr_instance[chosen_attr_list[0]]
            chosen_attr_instance = chosen_attr_instance_child
            # del chosen_attr_list[0]
        self.chosen_instance_in_tree = chosen_attr_instance
        self.chosen_attr = chosen_attr_list[0]
        if isinstance(chosen_attr_instance, QuantityStore):
            self.attr_frame_build(chosen_attr_instance)
        else:
            self.attr_frame_empty()

    def change_chosen_attr_value2(self, attr_name: str, new_value: str) -> str:

        # try:
        #     annotation = self.chosen_instance_in_tree.__annotations__[attr_name]
        # except KeyError:
        #     raise Exception(f'no type annotation for {attr_name} found')

        old_value = getattr(self.chosen_instance_in_tree, attr_name)

        if (isinstance(old_value, QFloat) or isinstance(old_value, QBool) or isinstance(old_value, QInt) or
                isinstance(old_value, QStr)):
            old_value_value = old_value.value
            try:
                if new_value == '<None>':
                    old_value.value = None
                    old_value.source = None
                else:
                    if isinstance(old_value, QFloat):
                        old_value.set_value(float(new_value), source=qc.ATTR_USER_SET)
                    elif isinstance(old_value, QBool):
                        if new_value == 'False':
                            old_value.set_value(False, source=qc.ATTR_USER_SET)
                        else:
                            old_value.set_value(True, source=qc.ATTR_USER_SET)
                    elif isinstance(old_value, QInt):
                        old_value.set_value(int(new_value), source=qc.ATTR_USER_SET)
                    elif isinstance(old_value, QStr):
                        old_value.set_value(str(new_value), source=qc.ATTR_USER_SET)
                    else:
                        raise Exception(f'type{type(old_value)} not implemented')
            except ValueError:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                # print(f'decode error Expected {new_value} but got {annotation}')
                # selected_attr_name = item_iid.split(',')[-1]
                tkinter.messagebox.showerror('ValueError', f'Unable to assign {new_value} to {attr_name}.' +
                                             f'\n Got {type(new_value)} type')
                if old_value_value is None:
                    new_value = '<None>'
                else:
                    new_value = old_value_value
            return new_value

        elif new_value == '<None>':
            setattr(self.chosen_instance_in_tree, attr_name, None)
            if attr_name in self.end_attr_name:
                setattr(self.chosen_instance_in_tree, '_'+attr_name+'_source', None)
            return new_value

        elif attr_name in self.end_attr_name:
            index = self.end_attr_name.index(attr_name)
            new_object_dict = self.end_class_options[index]
            new_object = new_object_dict[new_value]
            setattr(self.chosen_instance_in_tree, attr_name, new_object)
            setattr(self.chosen_instance_in_tree, '_' + attr_name + '_source', qc.ATTR_USER_SET)
            return new_value

        else:
            try:
                annotation = self.chosen_instance_in_tree.__annotations__[attr_name]
            except KeyError:
                raise Exception(f'no type annotation for {attr_name} found')
            try:

                if attr_name in self.end_attr_name:
                    index = self.end_attr_name.index(attr_name)
                    new_object_dict = self.end_class_options[index]
                    new_object = new_object_dict[new_value]
                    setattr(self.chosen_instance_in_tree, attr_name, new_object)
                    setattr(self.chosen_instance_in_tree, '_'+attr_name+'_source', qc.ATTR_USER_SET)
                elif annotation == typing.Optional[int] or annotation == int:
                    setattr(self.chosen_instance_in_tree, attr_name, int(new_value))
                elif annotation == typing.Optional[str] or annotation == str:
                    setattr(self.chosen_instance_in_tree, attr_name, str(new_value))
                elif annotation == typing.Optional[float] or annotation == float:
                    setattr(self.chosen_instance_in_tree, attr_name, float(new_value))
                # TODO: remove bool annotation
                elif annotation == typing.Optional[bool] or annotation == bool or annotation == QBool:
                    if new_value == 'True':
                        setattr(self.chosen_instance_in_tree, attr_name, True)
                    elif new_value == 'False':
                        setattr(self.chosen_instance_in_tree, attr_name, False)
                    else:
                        raise ValueError(f'could not convert {new_value} to bool for attribute {attr_name}')
                else:
                    raise ValueError(f'unable to recognise {attr_name} type in annotation')
            except ValueError:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                # print(f'decode error Expected {new_value} but got {annotation}')
                # selected_attr_name = item_iid.split(',')[-1]
                tkinter.messagebox.showerror('ValueError', f'Unable to assign {new_value} to {attr_name}.' +
                                             f'\n Expected {annotation} but got {type(new_value)}')
                if old_value is None:
                    new_value = '<None>'
                else:
                    new_value = str(old_value)

            # if new_value == '<None>':
            #     self.chosen_instance_in_tree.set_source(attr_name, None)
            # else:
            #    self.chosen_instance_in_tree.set_source(attr_name, dc.ATTR_USER_CABSYS_SET)
            return new_value

    def attr_tree_branch_release_callback(self, _event):
        # self.clear_attr_entry()
        self.fill_attr_entry_widgets_branch(self.nav_tree.focus())

    def attr_combobox_button1_callback(self, _event, attr_name: str, attr_combobox: ttk.Combobox):
        pass

    def attr_combobox_buttonrelease1_callback(self, _event, attr_name: str, attr_combobox: ttk.Combobox):
        attr_value = getattr(self.chosen_instance_in_tree, attr_name)
        if attr_value is None or isinstance(attr_value, bool):
            attr_combobox.selection_range(0, tkinter.END)

    def combobox_key(self, _event):
        self.combobox_key_pressed = True

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

        combobox.selection_range(0, tkinter.END)
        self.event_generate("<<Q_change>>", when="tail")

    def attr_combobox_focus_lost(self, event, attr_name: str, combobox: ttk.Combobox,
                                 fixed_combobox: ttk.Combobox):
        if self.combobox_key_pressed:
            self.attr_combobox_changed_callback2(event, attr_name, combobox, fixed_combobox)


class _DataStoreWindow:
    """DataStore Window

    used by data_store_show function
    """

    def __init__(self, instance, parent=None,
                 edit_name: bool = True, show_name: bool = True, is_auto_design: bool = True,
                 end_attr_name: List[str] = None, end_class_options: List[str] = None):
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
        attr_frame = QuantFrame(self.top_level, instance=instance,
                                edit_name=edit_name, show_name=show_name, is_auto_design=is_auto_design,
                                end_attr_name=end_attr_name, end_options=end_class_options)
        attr_frame.grid(column=1, row=1, sticky='NEWS')
        attr_frame.columnconfigure(1, weight=1)
        attr_frame.rowconfigure(1, weight=1)
        # DataStoreViewer(attr_frame, instance, cable_options, curve_options, edit_name, show_name, is_auto_design)
        self.top_level.grab_set()

    def win_close(self):
        self.top_level.destroy()


def data_store_show(instance, parent=None,
                    edit_name: bool = True, show_name: bool = True, is_auto_design: bool = False):
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
    """

    dsw = _DataStoreWindow(instance, parent, edit_name, show_name, is_auto_design)

    if parent is None:
        dsw.top_level.mainloop()


# TODO: expand this to use in overveiw widgets
class QuantityCombobox(ttk.Combobox):
    """Combobox for values tied to a string quantity"""

    def __init__(self, container, quantity: QuantityBase, **kw):
        super().__init__(container, style='TCombobox', **kw)
        self.container = container
        self.quantity = quantity

    def get_quantity(self) -> QuantityBase:
        return self.quantity
