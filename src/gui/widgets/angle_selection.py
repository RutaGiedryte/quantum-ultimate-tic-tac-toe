from tkinter import StringVar, Widget, ttk


class AngleSelection(ttk.Frame):
    """Widget for selecting the rotation angle when rotating a qubit."""

    def __init__(self, parent: Widget, textvariable: StringVar, callback, **kw) -> None:
        """Create angle selection widget.

        Args:
            parent: parent widget
            textvariable: variable for the angle
            callback: function to call when submitting the angle
            kw: keyword arguments for `ttk.Frame`
        """

        super().__init__(parent, **kw)

        # create info label
        ttk.Label(
            self,
            text="Insert angle to rotate qubit by",
            padding="0 0 0 5",
        ).grid(row=0, column=0, columnspan=2)

        # entry widget
        self._entry = ttk.Entry(self, textvariable=textvariable)
        self._entry.grid(row=1, column=0)

        # submit widget
        self._button = ttk.Button(self, text="enter")
        self._button.grid(row=1, column=1)
