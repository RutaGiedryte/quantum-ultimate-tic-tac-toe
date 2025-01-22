from tkinter import StringVar, Widget, ttk, DoubleVar
import math


class AngleSelection(ttk.Frame):
    """Widget for selecting the rotation angle when rotating a qubit."""

    def __init__(self, parent: Widget, angle_var: DoubleVar, callback, **kw) -> None:
        """Create angle selection widget.

        Args:
            parent: parent widget
            angle_var: variable for the angle
            callback: function to call when changing the angle
            kw: keyword arguments for `ttk.Frame`
        """

        super().__init__(parent, **kw)

        self._angle_var = angle_var

        # values from -pi with pi with pi/4 step
        self._allowed_values = [math.pi * (i / 4) if i else 0 for i in range(-4, 5)]

        # create info label
        self._text = StringVar()
        ttk.Label(
            self,
            textvariable=self._text,
            padding="0 0 0 5",
        ).grid(row=0, column=0)

        # create slider

        self._slider = ttk.Scale(
            self, length=300, command=self._change_angle, variable=angle_var
        )
        self._slider.grid(row=1, column=0)

        self._callback = callback

    def set_message(self, message: str) -> None:
        """Set prompt message.

        Args:
            message: prompt message
        """

        self._text.set(message)

    def disable(self) -> None:
        """Disable the angle slider."""

        self._slider.configure(state="disabled")

    def enable(self, max: float) -> None:
        """Enable the angle slider.

        Sets the maximum value, and sets the current value to 0.

        Args:
            max: max. angle
        """
        self._slider.configure(from_=-max, to=max, state="normal")
        self._angle_var.set(0)

    def _change_angle(self, angle) -> None:
        """Callback function for changing the angle on the slider.

        Args:
            angle: new angle
        """

        angle = float(angle)

        # round to allowed value
        if angle not in self._allowed_values:
            closest = min(self._allowed_values, key=lambda val: abs(val - angle))
            self._slider.set(closest)

        self._callback()
