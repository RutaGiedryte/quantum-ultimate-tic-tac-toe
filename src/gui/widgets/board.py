from tkinter import Widget, ttk
from collections.abc import Callable

from backend.quantum_tic_tac_toe import State


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
            ttk.Button(
                cellframes[i],
                command=lambda i=i: callback(i),
                state="disabled",
                style="Cell.TButton",
            )
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

        Disables all buttons, and clears text.
        """

        for button in self._cell_buttons:
            button["state"] = "disabled"
            button["text"] = ""
            button["style"] = "Cell.TButton"

    def update_display(self, states: list[State]) -> None:
        """Update symbols to dislpay.

        Sets symbols according to cell states on board.

        Args:
            states: cell states on board
        """

        for i in range(9):
            self._cell_buttons[i]["text"] = states[i]
            if states[i] == State.X:
                self._cell_buttons[i]["style"] = "X.Cell.TButton"
            if states[i] == State.O:
                self._cell_buttons[i]["style"] = "O.Cell.TButton"

    def touch_cell(self, cell):
        """Touch cell `cell`.

        Changes the representation of the cell.

        Args:
            cell: cell index to touch
        """
        self._cell_buttons[cell]["text"] = "?"
