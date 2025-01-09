from tkinter import Widget, ttk
from collections.abc import Callable


class Board:
    """Widget represeting the board."""

    def __init__(
        self, parent: Widget, width: int, callback: Callable[[int], None]
    ) -> None:
        """Create board widget.

        Args:
            parent: parent widget
            width: board width
            callback: callback function for clicking on cell
        """

        # create board frame
        self._boardframe = ttk.Frame(parent, padding=5)

        cell_width = width // 3

        # create cells
        cellframes = [
            ttk.Frame(self._boardframe, width=cell_width, height=cell_width)
            for i in range(9)
        ]
        for i in range(9):
            cellframes[i].grid(row=i // 3, column=i % 3)
            cellframes[i].columnconfigure(0, weight=1)
            cellframes[i].rowconfigure(0, weight=1)
            cellframes[i].grid_propagate(False)

        self._cell_buttons = [
            ttk.Button(cellframes[i], command=lambda i=i: callback(i), state="disabled")
            for i in range(9)
        ]
        for cell_button in self._cell_buttons:
            cell_button.grid(row=0, column=0, sticky="NWSE")

    def grid(self, row: int, column: int) -> None:
        """Position the board in the parent widget.

        Args:
            row: row in grid
            column: column in grid
        """

        self._boardframe.grid(row=row, column=column)

    def enable(self, cells: list[int]) -> None:
        """Enable `cells` of the board.

        Args:
            cells: list of cell indices to enable
        """

        for c in cells:
            self._cell_buttons[c]["state"] = "normal"

    def disable(self) -> None:
        """Disable the board."""

        for button in self._cell_buttons:
            button["state"] = "disabled"

    def reset(self) -> None:
        """Reset the board to its default state.

        Disable all buttons, and clears text.
        """

        for button in self._cell_buttons:
            button["state"] = "disabled"
            button["text"] = ""
