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
        pass

    def cancel(self, event=None):
        self._parent.focus_set()
        self.destroy()


class InfoPopup(DialogBox):

    def __init__(self, parent, title, message):
        self._message = message
        DialogBox.__init__(self, parent)
        self.title(title)

    def create_body(self):
        body = Tkinter.Frame()
        label = ttk.Label(body, text=self._message)
        button = ttk.Button(body, text="OK", command=self.cancel)
        body.pack()

