import Tkinter
import ttk


class DialogBox(Tkinter.Toplevel):
    """
    Generic modal dialog box.
    """

    def __init__(self, parent):
        Tkinter.Toplevel.__init__(self, parent)
        self._parent = parent
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        self.create_body()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def create_body(self):
        """To be implemented by subclasses."""
        pass

    def cancel(self, event=None):
        self._parent.focus_set()
        self.destroy()

    def raise_to_top(self):
        self.lift()
        self.attributes('-topmost',True)
        self.after_idle(self.attributes,'-topmost',False)


class InfoPopup(DialogBox):

    def __init__(self, parent, title, message):
        self._message = message
        DialogBox.__init__(self, parent)
        self.title(title)

    def create_body(self):
        body = Tkinter.Frame(self)
        body.grid()
        label = ttk.Label(body, text=self._message, wraplength=200)
        label.grid(row=0, column=0)
        button = ttk.Button(body, text="OK", command=self.cancel)
        button.grid(row=1, column=0)
        body.pack()


class ErrorPopup(InfoPopup):
    pass


class YesNoPopup(DialogBox):

    def __init__(self, parent, title, message):
        self._message = message
        DialogBox.__init__(self, parent)
        self.title(title)
        self.yes = False

    def create_body(self):
        body = Tkinter.Frame(self)
        body.grid()
        label = ttk.Label(body, text=self._message, wraplength=200)
        label.grid(row=0, column=0, columnspan=2)
        yes_button = ttk.Button(body, text="Yes", command=self.yes_cmd)
        yes_button.grid(row=1, column=0)
        no_button = ttk.Button(body, text="No", command=self.no_cmd)
        no_button.grid(row=1, column=1)
        body.pack()

    def yes_cmd(self):
        self.yes = True
        self.cancel()

    def no_cmd(self):
        self.yes = False
        self.cancel()

    @staticmethod
    def open(parent, title, message):
        p = YesNoPopup(parent, title, message)
        parent.wait_window(p)
        return p.yes
