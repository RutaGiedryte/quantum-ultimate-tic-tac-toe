from tkinter import Widget, ttk


class NumberSelection(ttk.Frame):
    """Widget for selecting the number of qubits to rotate."""

    def __init__(self, parent: Widget, max_n: int, cols: int, callback, **kw) -> None:
        """Create number selection widget.

        Args:
            parent: parent widget
            max_n: max number of qubits that can be rotated in one move
            cols: number of columns to use for displaying the buttons
            callback: function to call when selecting the number of qubits. the function should take the number of qubits as an argument.
            kw: keyword arguments for `ttk.Frame`
        """

        super().__init__(parent, **kw)

        # create info label
        ttk.Label(
            self,
            text="Choose number of qubits to rotate",
            padding="0 0 0 5",
        ).grid(row=0, column=0, columnspan=2)

        # create number of qubits buttons
        self._qubit_number_buttons = [
            ttk.Button(
                self,
                text=n + 1,
                command=lambda n=n + 1: callback(n),
            )
            for n in range(max_n)
        ]

        for i, button in enumerate(self._qubit_number_buttons):
            row = i // cols + 1
            col = i % cols
            button.grid(row=row, column=col)
