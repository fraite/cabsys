import tkinter
from tkinter import ttk
from typing import Union, Optional



class ResultFrame(tkinter.Frame):
    """Frame to display the results from an installation"""

    def __init__(self, parent: Union[tkinter.Toplevel, tkinter.Tk, tkinter.Frame, tkinter.Tk, tkinter.PanedWindow,
                                     ttk.Notebook],
                 result: str,
                 **kw):
        super().__init__(parent, **kw)

        self.result = result

        self.columnconfigure(0, minsize="0", weight=1, pad="0")
        self.rowconfigure(0, minsize="0", weight=1, pad="0")
        self.config(relief="flat")

        self.result_tb = tkinter.Text(self, state="normal", height=5, width=80, wrap='none')
        self.result_tb.grid(row=0, column=0, sticky="nsew")
        self.result_tb.insert(tkinter.END, result)

        ys = ttk.Scrollbar(self, orient='vertical', command=self.result_tb.yview)
        xs = ttk.Scrollbar(self, orient='horizontal', command=self.result_tb.xview)
        self.result_tb['yscrollcommand'] = ys.set
        self.result_tb['xscrollcommand'] = xs.set
        xs.grid(column=0, row=1, sticky='we')
        ys.grid(column=1, row=0, sticky='ns')

    def add_result(self, result: str):
        self.result_tb.insert(tkinter.END, result)

    def new_result(self, result: Optional[str]):
        if result is None:
            result = ''
        self.result_tb.delete('1.0', tkinter.END)
        self.result_tb.insert(tkinter.END, result)