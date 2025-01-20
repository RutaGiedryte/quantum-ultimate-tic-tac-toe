from tkinter import Widget, ttk, Canvas
from collections.abc import Callable

from backend.quantum_tic_tac_toe import State


class Board(ttk.Frame):
    """Widget represeting the board."""

    def __init__(
        self,
        parent: Widget,
        width: int,
        callback: Callable[[int, int], None],
        ultimate: bool,
        **kw,
    ) -> None:
        """Create board widget.

        Args:
            parent: parent widget
            width: board width
            callback: callback function for clicking on a cell
            ultimate: whether to create the ultimate version
            kw: keyword arguments for `ttk.Frame`
        """

        super().__init__(parent, **kw)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._callback = callback
        self._ultimate = ultimate

        self._board_width = width / 3 if ultimate else width

        n_boards = 9 if ultimate else 1

        # font
        self._font = "Roboto"
        self._font_size = int(self._board_width / 4)
        self._win_font_size = int(self._board_width)

        # bg colours
        self._cell_disabled_color = "#E0E0E0"
        self._cell_enabled_color = "#FFFFFF"

        # font colour
        self._x_color = "#CB70FF"
        self._o_color = "#44BC68"
        self._draw_color = "#FFB300"
        self._default_color = "#ABABAB"

        self._canvas = Canvas(self, width=width, height=width, highlightthickness=0)
        self._canvas.bind("<Button-1>", lambda event: self._on_click(event))
        self._canvas.grid()

        self._width = width

        self._grid_line_ids = []

        # cell backgrounds
        self._cell_bg_ids = [[] for _ in range(n_boards)]
        offset = self._board_width / 3 / 2

        for b, cells in enumerate(self._cell_bg_ids):
            for c in range(9):
                x_centre, y_centre = self._index_to_pos(b, c)
                id = self._canvas.create_rectangle(
                    x_centre - offset,
                    y_centre - offset,
                    x_centre + offset,
                    y_centre + offset,
                    fill=self._cell_disabled_color,
                    width=0,
                )
                cells.append(id)

        # create grid lines
        self._create_grid(width, 0, 0)
        # create sub-board grid lines if ultimate
        if ultimate:
            for i in range(3):
                for j in range(3):
                    self._create_grid(
                        self._board_width, i * self._board_width, j * self._board_width
                    )

        # list of enabled cells
        self._enabled = [[False for _ in range(9)] for _ in range(n_boards)]

        # list of entanglement lines, indexed by control qubit board index
        self._entanglement_ids = [[] for _ in range(n_boards)]

        # list of symbol ids
        self._symbol_ids = [
            [
                self._canvas.create_text(
                    self._index_to_pos(b, c),
                    text="",
                    fill=self._default_color,
                    font=(self._font, self._font_size),
                )
                for c in range(9)
            ]
            for b in range(9 if ultimate else 1)
        ]

        self._win_symbol_ids = [
            self._canvas.create_text(
                self._index_to_pos(b, 4),
                text="",
                fill=self._draw_color,
                font=(self._font, self._win_font_size),
            )
            for b in range(n_boards)
        ]

        self.bind("<Configure>", self._on_resize)

    def entangle(self, c_board: int, c_cell: int, t_board: int, t_cell: int) -> None:
        """Create arrow from control to target.

        Args:
            c_board: control board index
            c_cell: control cell index
            t_board: target board index
            t_cell: target cell index
        """

        cx, cy = self._index_to_pos(c_board, c_cell)
        tx, ty = self._index_to_pos(t_board, t_cell)

        width = 4
        color = "#FFA35C"
        arrow_shape = (20, 20, 5)

        self._entanglement_ids[c_board].append(
            self._canvas.create_line(
                cx,
                cy,
                tx,
                ty,
                width=width,
                fill=color,
                arrowshape=arrow_shape,
                arrow="both",
            )
        )

    def enable(self, board: int, cells: list[int]) -> None:
        """Enable `cells` of `board`.

        Args:
            board: board index
            cells: list of cell indices to enable
        """

        for c in cells:
            self._enabled[board][c] = True
            self._canvas.itemconfigure(
                self._cell_bg_ids[board][c], fill=self._cell_enabled_color
            )

    def disable(self, board: int) -> None:
        """Disable `board`.

        Args:
            board: board index
        """

        self._enabled[board] = [False for _ in range(9)]

        for id in self._cell_bg_ids[board]:
            self._canvas.itemconfigure(id, fill=self._cell_disabled_color)

    def reset(self, board) -> None:
        """Reset the `board` to its default state.

        Clears cell symbols. Deletes entanglement lines.

        Args:
            board: board index
        """

        # clear symbols
        for id in self._symbol_ids[board]:
            self._canvas.itemconfigure(id, text="", fill=self._default_color)

        # delete lines
        self._canvas.delete(*self._entanglement_ids[board])
        self._entanglement_ids[board].clear()

        # clear win symbol
        self._canvas.itemconfigure(
            self._win_symbol_ids[board], text="", fill=self._draw_color
        )

    def update_display(self, board: int, states: list[State]) -> None:
        """Update symbols to display on `board`.

        Sets symbols according to cell states on board.

        Args:
            board: board index
            states: cell states on board
        """

        self.reset(board)

        for i in range(9):
            color = self._default_color
            if states[i] == State.X:
                color = self._x_color
            if states[i] == State.O:
                color = self._o_color
            self._canvas.itemconfigure(
                self._symbol_ids[board][i], text=states[i], fill=color
            )

    def set_winner(self, board: int, winner: State) -> None:
        """Set subboard winner.

        Displays a symbol over the subboard based on the winner.

        Args:
            board: board index
            winner: subboard winner
        """

        id = self._win_symbol_ids[board]

        match winner:
            case State.X:
                self._canvas.itemconfigure(id, text="X", fill=self._x_color)
            case State.O:
                self._canvas.itemconfigure(id, text="O", fill=self._o_color)
            case State.DRAW:
                self._canvas.itemconfigure(id, text="?")

    def touch_cell(self, board: int, cell: int) -> None:
        """Touch `cell` on `board`.

        Changes the representation of the cell.

        Args:
            board: board index
            cell: cell index
        """
        self._canvas.itemconfigure(self._symbol_ids[board][cell], text="?")

    def _index_to_pos(self, board: int, cell: int) -> tuple[float, float]:
        """Calculate cell positon on canvas from board and cell index.

        Args:
            board: board index
            cell: cell index

        Returns:
            coordinates on canvas (x, y)
        """

        board_x_index = board % 3
        board_y_index = board // 3

        board_offset = self._width / 3

        cell_x_index = cell % 3
        cell_y_index = cell // 3

        cell_offset = self._board_width / 3
        cell_start = cell_offset / 2

        x = board_x_index * board_offset + cell_start + cell_x_index * cell_offset
        y = board_y_index * board_offset + cell_start + cell_y_index * cell_offset

        return (x, y)

    def _pos_to_index(self, x: float, y: float) -> tuple[int, int]:
        """Calculate board and cell index from position on canvas.

        Args:
            x: x-coordinate
            y: y-coordinate

        Returns:
            (board index, cell index) at (x, y)
        """

        board_x_index = 0
        board_y_index = 0

        if self._ultimate:
            board_x_index = int(min(x / self._width * 3, 2))
            board_y_index = int(min(y / self._width * 3, 2))

        board_index = board_y_index * 3 + board_x_index

        board_offset = self._width / 3

        x -= board_x_index * board_offset
        y -= board_y_index * board_offset

        cell_x_index = int(min(x / self._board_width * 3, 2))
        cell_y_index = int(min(y / self._board_width * 3, 2))

        cell_index = cell_y_index * 3 + cell_x_index

        return board_index, cell_index

    def _create_grid(self, width, x, y) -> None:
        """Create grid lines.

        Args:
            width: grid width
            x: upper left corner x-coordinate
            y: upper left corner y-coordinate
        """

        x1 = width / 3 + x
        x2 = width / 3 * 2 + x

        y1 = width / 3 + y
        y2 = width / 3 * 2 + y

        line_width = 0.01 * width

        # create vertical lines
        self._grid_line_ids.append(
            self._canvas.create_line(x1, y, x1, y + width, width=line_width)
        )
        self._grid_line_ids.append(
            self._canvas.create_line(x2, y, x2, y + width, width=line_width)
        )

        # create horizontal lines
        self._grid_line_ids.append(
            self._canvas.create_line(x, y1, x + width, y1, width=line_width)
        )
        self._grid_line_ids.append(
            self._canvas.create_line(x, y2, x + width, y2, width=line_width)
        )

    def _on_click(self, event):
        """Callback function for clicking on canvas."""
        board, cell = self._pos_to_index(event.x, event.y)

        # call callback function if clicked cell enabled
        if self._enabled[board][cell]:
            self._callback(board, cell)

    def _on_resize(self, event):
        """Callback function for resizing window."""

        width = min(event.width, event.height)

        # change canvas size
        self._canvas.config(width=width, height=width)

        # calculate scale
        scale = width / self._width

        # update width variables
        self._width = width
        self._board_width = width / 3 if self._ultimate else width

        # scale all objects on canvas
        self._canvas.scale("all", 0, 0, scale, scale)

        # scale symbols
        self._font_size = int(self._board_width / 4)
        font = (self._font, self._font_size)

        for symbols in self._symbol_ids:
            for id in symbols:
                self._canvas.itemconfigure(id, font=font)

        # scale win symbols
        self._win_font_size = int(self._board_width)
        font = (self._font, self._win_font_size)

        for id in self._win_symbol_ids:
            self._canvas.itemconfigure(id, font=font)

        # scale entanglement line width
        for list in self._entanglement_ids:
            for id in list:
                width = float(self._canvas.itemcget(id, "width")) * scale
                arrow_shape = self._canvas.itemcget(id, "arrowshape").split()

                arrow_shape = (
                    scale * float(arrow_shape[0]),
                    scale * float(arrow_shape[1]),
                    scale * float(arrow_shape[2]),
                )

                self._canvas.itemconfigure(id, width=width, arrowshape=arrow_shape)

        # scale grid line width
        for id in self._grid_line_ids:
            width = float(self._canvas.itemcget(id, "width")) * scale
            self._canvas.itemconfigure(id, width=width)
