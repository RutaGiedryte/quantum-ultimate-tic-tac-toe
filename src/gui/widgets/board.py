from tkinter import Widget, ttk
from collections.abc import Callable


class Board(ttk.Frame):
    """Widget represeting the board."""

    def __init__(
        self, parent: Widget, width: int, callback: Callable[[int], None], **kw
    ) -> None:
        """Create board widget.

        Args:
            parent: parent widget
            width: board width
            callback: callback function for clicking on a cell
            kw: keyword arguments for `ttk.Frame`
        """

        super().__init__(parent, **kw)

        cell_width = width // 3

        # create cells
        cellframes = [
            ttk.Frame(self, width=cell_width, height=cell_width) for i in range(9)
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
