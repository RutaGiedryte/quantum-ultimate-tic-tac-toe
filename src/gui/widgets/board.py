from tkinter import Widget, ttk, Canvas
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

        self._callback = callback

        # font
        font = "Roboto"
        font_size = width // 4

        # font colour
        self._x_color = "#CB70FF"
        self._o_color = "#44BC68"
        self._default_color = "#ABABAB"

        self._canvas = Canvas(self, width=width, height=width)
        self._canvas.bind("<Button-1>", lambda event: self._on_click(event))
        self._canvas.grid()

        self._width = width
        self._create_grid()

        # list of enabled cells
        self._enabled = [False for _ in range(9)]

        # list of symbol ids
        self._symbol_ids = [
            self._canvas.create_text(
                self._index_to_pos(i),
                text="",
                fill=self._default_color,
                font=(font, font_size),
            )
            for i in range(9)
        ]

    def enable(self, cells: list[int]) -> None:
        """Enable `cells` of the board.

        Args:
            cells: list of cell indices to enable
        """

        for c in cells:
            self._enabled[c] = True

    def disable(self) -> None:
        """Disable the board."""

        self._enabled = [False for _ in range(9)]

    def reset(self) -> None:
        """Reset the board to its default state.

        Disables all cells, and clears text.
        """

        self._clear_symbols()

    def update_display(self, states: list[State]) -> None:
        """Update symbols to dislpay.

        Sets symbols according to cell states on board.

        Args:
            states: cell states on board
        """

        self._clear_symbols()

        for i in range(9):
            color = self._default_color
            if states[i] == State.X:
                color = self._x_color
            if states[i] == State.O:
                color = self._o_color
            self._canvas.itemconfigure(self._symbol_ids[i], text=states[i], fill=color)

    def touch_cell(self, cell) -> None:
        """Touch cell `cell`.

        Changes the representation of the cell.

        Args:
            cell: cell index to touch
        """
        self._canvas.itemconfigure(self._symbol_ids[cell], text="?")

    def _index_to_pos(self, i: int) -> tuple[float, float]:
        """Calculate cell positon on canvas from cell index.

        Args:
            i: cell index

        Returns:
            coordinates on canvas (x, y)
        """

        x_index = i % 3
        y_index = i // 3

        offset = self._width / 3
        start = offset / 2

        return (start + x_index * offset, start + y_index * offset)

    def _pos_to_index(self, x: int, y: int) -> int:
        """Calculate cell index from position on canvas.

        Args:
            x: x-coordinate
            y: y-coordinate

        Returns:
            cell index at (x, y)
        """
        x_index = int(min(x / self._width * 3, 2))
        y_index = int(min(y / self._width * 3, 2))

        return y_index * 3 + x_index

    def _clear_symbols(self):
        """Set symbols to empty."""

        for symbol in self._symbol_ids:
            self._canvas.itemconfigure(symbol, text="", fill=self._default_color)

    def _create_grid(self) -> None:
        """Create grid lines."""

        first = self._width / 3
        second = first * 2

        line_width = 0.01 * self._width

        # create vertical lines
        self._canvas.create_line(first, 0, first, self._width, width=line_width)
        self._canvas.create_line(second, 0, second, self._width, width=line_width)

        # create horizontal lines
        self._canvas.create_line(0, first, self._width, first, width=line_width)
        self._canvas.create_line(0, second, self._width, second, width=line_width)

    def _on_click(self, event):
        """Callback function for clicking on canvas."""
        index = self._pos_to_index(event.x, event.y)

        # call callback function if clicked cell enabled
        if self._enabled[index]:
            self._callback(index)
