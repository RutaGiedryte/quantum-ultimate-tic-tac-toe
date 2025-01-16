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
        self._text = StringVar()
        ttk.Label(
            self,
            textvariable=self._text,
            padding="0 0 0 5",
        ).grid(row=0, column=0, columnspan=2)

        # entry widget
        self._angle = textvariable
        self._entry = ttk.Entry(self, textvariable=self._angle)
        self._entry.grid(row=1, column=0)

        # submit widget
        self._button = ttk.Button(self, text="enter", command=callback)
        self._button.grid(row=1, column=1)

        self._callback = callback

    def set_message(self, message: str) -> None:
        """Set prompt message.

        Args:
            message: prompt message
        """

        self._text.set(message)

    def disable(self) -> None:
        """Disable the button and enrty."""

        self._entry["state"] = "disabled"
        self._button["state"] = "disabled"

    def enable(self) -> None:
        """Enable the button and entry.

        Clears the angle entry box. Focuses on angle entry box.
        """
        self._angle.set("")
        self._entry["state"] = "normal"
        self._button["state"] = "normal"
        self._entry.focus()
