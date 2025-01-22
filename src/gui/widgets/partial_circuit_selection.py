from tkinter import StringVar, Widget, ttk

class Partial_Circuit_Selection(ttk.Frame):
    """Widget for selecting the partial circuit to display."""

    def __init__(self, parent: Widget, textvariable: StringVar, callback, **kw) -> None:
        """Create angle selection widget.

        Args:
            parent: parent widget
            textvariable: variable for the sub-board
            callback: function to call when submitting the sub-board
            kw: keyword arguments for `ttk.Frame`
        """

        super().__init__(parent, **kw)

        # entry widget
        self._sub_board = textvariable
        self._entry = ttk.Entry(self, textvariable=self._sub_board, width=10)
        self._entry.grid(row=0, column=0)

        # spacing widget
        space = ttk.Label(self, text="", width=1)
        space.grid(row=0, column=1)

        # submit widget
        self._button = ttk.Button(self, text="show partial circuit", command=callback, width=20)
        self._button.grid(row=0, column=2)

        self._callback = callback
