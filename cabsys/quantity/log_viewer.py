import tkinter
from tkinter import ttk, filedialog
from cabsys.quantity.log import Log
from typing import Union


class LogViewer(ttk.Frame):

    def __init__(self, parent: Union[tkinter.Frame, tkinter.Toplevel], log: Log, working_dir, file_name,
                 **kw):
        """Create a frame to view the supplied log

        The frame shows the log supplied in three ways: as a tkinter.Tree, a text file, and an XML file. The log frame
        includes a button that when pressed allows the log output to be saved. A file requester is opened to allow
        the user to select the save file location and name. The default save file location and name have to be specified
        by the argument of the function.

        :param parent: frame tkinter parent
        :param log: log to be displayed
        :param working_dir: default directory for any saved log file
        :param file_name: default name of any saved log file
        :param kw: keyword/value to be passed frame super class (Frame or Toplevel)
        """

        super().__init__(parent, **kw)

        self.log = log
        self.working_dir = working_dir
        self.file_name = str(file_name)
        # close open headings, typically due to an exception during calculations
        if len(log.current_heading) > 0:
            log.close_sections('calculation not finished')

        # frame containing log tree
        self.log_frame = ttk.Frame(self)
        self.log_frame.grid(column=1, row=1, sticky='NWES')
        self.log_frame.columnconfigure(1, weight=1)
        self.log_frame.rowconfigure(1, weight=0)
        self.log_frame.rowconfigure(2, weight=1)
        self.log_frame['padding'] = (5, 10)
        self.log_frame['relief'] = tkinter.GROOVE

        # Combobox selecting type of output (tree or text)
        self.log_output_var = tkinter.StringVar()
        self.log_output_var.set('tree')
        self.log_output_combobox = ttk.Combobox(self.log_frame, textvariable=self.log_output_var)
        self.log_output_combobox['values'] = ('text', 'xml', 'tree')
        self.log_output_combobox.state(['readonly'])
        self.log_output_combobox.grid(column=0, row=1)
        self.log_output_combobox.bind('<<ComboboxSelected>>', self.view_tree_text)

        self.save_button = tkinter.Button(self.log_frame, text='save', command=self.save_button_callback)
        self.save_button.grid(column=1, row=1, sticky='W')

        # attribute tree
        self.log_tree = ttk.Treeview(self.log_frame, takefocus=True, selectmode=tkinter.BROWSE)
        self.log_tree['columns'] = ('value', 'unit', 'source')
        self.log_tree.column('value', width=100, anchor=tkinter.CENTER)
        self.log_tree.heading('value', text='value')
        self.log_tree.column('unit', width=50, anchor=tkinter.CENTER)
        self.log_tree.heading('unit', text='unit')
        self.log_tree.column('source', width=350, anchor=tkinter.CENTER)
        self.log_tree.heading('source', text='source')
        # self.log_tree.tag_bind('branch', '<ButtonRelease-1>',
        #                        self.attr_tree_branch_release_callback)
        # self.log_tree.tag_bind('leaf', '<ButtonRelease-1>',
        #                        self.attr_tree_leaf_release_callback)
        self.log_tree.grid(column=0, row=2, columnspan=4, sticky='NWES')
        self.scrollbar_log = ttk.Scrollbar(self.log_frame, orient=tkinter.VERTICAL, command=self.log_tree.yview)
        self.scrollbar_log.grid(column=4, row=2, sticky='NS')
        self.log_tree['yscrollcommand'] = self.scrollbar_log.set

        branch = ''

        # view results in tree view
        if log.required_log_level < 10:
            self.log_tree.insert(branch, 'end', text='install.required_log_level',
                                 values=(log.required_log_level, 'N/A', 'no log output as < 10'))
        else:
            for line in log.result:
                if line[0] == 'heading':
                    idf = self.log_tree.insert(branch, 'end', text=line[1],
                                               values=('-', '-', line[2]), tags='branch')
                    branch = idf
                elif line[0] == 'body':
                    if isinstance(line[2], str):
                        val = line[2]
                    elif line[2] is None:
                        val = 'None'
                    elif isinstance(line[2], str):
                        val = line[2]
                    elif isinstance(line[2], int):
                        val = str(line[2])
                    elif isinstance(line[2], tuple):
                        val = str(line[2])
                    elif isinstance(line[2], float):
                        val = f'{line[2]:^.6g}'
                    else:
                        raise Exception(f'trying to add entry to log but value of type {type(line[2])}')
                    self.log_tree.insert(branch, 'end', text=line[1],
                                         values=(val, line[3], line[4]), tags='branch')
                    # text = text + f'    {line[1]:<15}: {line[2]:>12.5} {line[3]:<10}  {line[4]} \n'
                elif line[0] == 'result':
                    if isinstance(line[2], str):
                        val = line[2]
                    elif isinstance(line[2], int):
                        val = str(line[2])
                    elif isinstance(line[2], tuple):
                        val = str(line[2])
                    elif isinstance(line[2], float):
                        val = f'{line[2]:^.6g}'
                    else:
                        raise Exception(f'trying to add entry to log but value of type {type(line[2])}')
                    self.log_tree.set(branch, 'value', val)
                    self.log_tree.set(branch, 'unit', line[3])
                    self.log_tree.set(branch, 'source', line[4])
                    branch = self.log_tree.parent(branch)
                    # text = text + f'    {line[1]:<15}: {line[2]:>12.5} {line[3]:<10}  {line[4]} \n'
                else:
                    raise Exception('line type in result not recognised')

            # view warnings
            for line in log.warning:
                if line[0] == 'heading':
                    idf = self.log_tree.insert(branch, 'end', text=line[1], tags='branch')
                    branch = idf
                elif line[0] == 'body':
                    if isinstance(line[2], str):
                        val = line[2]
                    else:
                        val = f'{line[2]:^12.5}'
                    self.log_tree.insert(branch, 'end', text=line[1],
                                         values=('-', '-', val), tags='branch')
                    # text = text + f'    {line[1]:<15}: {line[2]:>12.5} {line[3]:<10}  {line[4]} \n'
                elif line[0] == 'result':
                    if isinstance(line[2], str):
                        val = line[2]
                    elif isinstance(line[2], int):
                        val = str(line[2])
                    elif isinstance(line[2], tuple):
                        val = str(line[2])
                    elif isinstance(line[2], float):
                        val = f'{line[2]:^12.5}'
                    else:
                        raise Exception(f'trying to add entry to log but value of type {type(line[2])}')
                    self.log_tree.set(branch, 'source', val)
                    # self.log_tree.set(branch, 'unit', line[3])
                    # self.log_tree.set(branch, 'source', line[4])
                    branch = self.log_tree.parent(branch)
                    # text = text + f'    {line[1]:<15}: {line[2]:>12.5} {line[3]:<10}  {line[4]} \n'
                else:
                    raise Exception('line type in result not recognised')

        # Text xml viewer
        self.log_text_xml = tkinter.Text(self.log_frame, wrap='none')
        self.log_text_xml.insert('1.0', log.text_xml())
        self.log_text_xml['state'] = 'disabled'
        # self.log_text.grid(column=0, row=2, columnspan=4, sticky='NWES')
        self.scrollbar_text_xml_v = ttk.Scrollbar(self.log_frame, orient=tkinter.VERTICAL,
                                                  command=self.log_text_xml.yview)
        self.scrollbar_text_xml_h = ttk.Scrollbar(self.log_frame, orient=tkinter.HORIZONTAL,
                                                  command=self.log_text_xml.xview)
        # self.scrollbar_text_v.grid(column=4, row=2, sticky='NS')
        # self.scrollbar_text_h.grid(column=0, row=3, columnspan=4, sticky='EW')
        self.log_text_xml['yscrollcommand'] = self.scrollbar_text_xml_v.set
        self.log_text_xml['xscrollcommand'] = self.scrollbar_text_xml_h.set

        # Text viewer
        self.log_text = tkinter.Text(self.log_frame, wrap='none')
        if log.required_log_level < 10:
            self.log_text.insert('1.0', 'no text log as install.required_log_level < 10')
        else:
            self.log_text.insert('1.0', log.text())
        self.log_text['state'] = 'disabled'
        # self.log_text.grid(column=0, row=2, columnspan=4, sticky='NWES')
        self.scrollbar_text_v = ttk.Scrollbar(self.log_frame, orient=tkinter.VERTICAL, command=self.log_text.yview)
        self.scrollbar_text_h = ttk.Scrollbar(self.log_frame, orient=tkinter.HORIZONTAL, command=self.log_text.xview)
        # self.scrollbar_text_v.grid(column=4, row=2, sticky='NS')
        # self.scrollbar_text_h.grid(column=0, row=3, columnspan=4, sticky='EW')
        self.log_text['yscrollcommand'] = self.scrollbar_text_v.set
        self.log_text['xscrollcommand'] = self.scrollbar_text_h.set

    def view_tree_text(self, _event):
        if self.log_output_combobox.get() == 'tree':
            self.log_tree.grid(column=0, row=2, columnspan=4, sticky='NWES')
            self.scrollbar_log.grid(column=4, row=2, sticky='NS')
            self.log_text.grid_remove()
            self.scrollbar_text_v.grid_remove()
            self.scrollbar_text_h.grid_remove()
            self.log_text_xml.grid_remove()
            self.scrollbar_text_xml_v.grid_remove()
            self.scrollbar_text_xml_h.grid_remove()
        elif self.log_output_combobox.get() == 'xml':
            self.log_tree.grid_remove()
            self.scrollbar_log.grid_remove()
            self.log_text_xml.grid(column=0, row=2, columnspan=4, sticky='NWES')
            self.scrollbar_text_xml_v.grid(column=4, row=2, sticky='NS')
            self.scrollbar_text_xml_h.grid(column=0, row=3, columnspan=4, sticky='EW')
            self.scrollbar_text_v.grid_remove()
            self.scrollbar_text_h.grid_remove()
            self.log_text.grid_remove()
        else:
            self.log_tree.grid_remove()
            self.scrollbar_log.grid_remove()
            self.log_text.grid(column=0, row=2, columnspan=4, sticky='NWES')
            self.scrollbar_text_v.grid(column=4, row=2, sticky='NS')
            self.scrollbar_text_h.grid(column=0, row=3, columnspan=4, sticky='EW')
            self.log_text_xml.grid_remove()
            self.scrollbar_text_xml_v.grid_remove()
            self.scrollbar_text_xml_h.grid_remove()

    def save_button_callback(self):

        if self.log_output_combobox.get() == 'tree' or self.log_output_combobox.get() == 'xml':
            file_type = ('xml files', '*.xml')
        else:
            file_type = ('txt files', '*.txt')

        save_name: str = filedialog.asksaveasfilename(initialdir=self.working_dir, title='Save file',
                                                      filetypes=(file_type, ('all files', '*.*')),
                                                      initialfile=self.file_name, defaultextension='.inst')
        if save_name is None or save_name == '':
            return
        # make the save directory the new default working directory
        save_dir = save_name.rpartition('/')
        self.working_dir = save_dir[0]
        # add the .xml or txt suffix, if required
        if save_name.partition('.')[1] != '.':
            if file_type == ('xml files', '*.xml'):
                save_name = save_name + '.xml'
            else:
                save_name = save_name + '.txt'
        # get the log as string
        if self.log_output_combobox.get() == 'tree' or self.log_output_combobox.get() == 'xml':
            serial = self.log.text_xml()
        else:
            serial = self.log.text()
        # save selected installation
        with open(save_name, 'w', encoding='utf-8') as save_file:
            save_file.write(serial)


class LogWindow:
    """DataStore Window

        Converts a LogViewer frame into a window. If a parent tkinter window is passed the window will be a child
        window, otherwise a new tkinter root window is used."""

    def __init__(self, log, parent=None):
        # work out if viewer standalone or is tkinter already running
        self.parent = parent
        self.instance = log

        if parent is not None:
            self.top_level = tkinter.Toplevel(parent)
        else:
            self.top_level = tkinter.Tk()

        self.top_level.protocol("WM_DELETE_WINDOW", self.win_close)

        # construct title bar
        try:
            title = f'{log.name} [{type(log)}] - Log viewer'
        except AttributeError:
            title = f'[unnamed] [{type(log)}] - Log viewer'
        self.top_level.title(title)
        self.top_level.columnconfigure(1, weight=1)
        self.top_level.rowconfigure(1, weight=1)
        attr_frame = LogViewer(self.top_level, log)
        attr_frame.grid(column=1, row=1, sticky='NEWS')
        attr_frame.columnconfigure(1, weight=1)
        attr_frame.rowconfigure(1, weight=1)

        self.top_level.grab_set()

    def win_close(self):
        self.top_level.destroy()


def log_show(log, parent=None):
    """Show a Log object

    Displays a tkinter window with the details of the Log object. The attributes of the Log object can
    be modified by the user if required. If a parent tkinter window is passed the window will be a child window,
    otherwise a new tkinter root window is used."""

    lw = LogWindow(log, parent)

    if parent is None:
        lw.top_level.mainloop()
