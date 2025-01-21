from tkinter import Widget, ttk, Canvas
from collections.abc import Callable
from PIL import Image, ImageTk
from qiskit.visualization import plot_bloch_vector
from qiskit.quantum_info import DensityMatrix
import matplotlib.pyplot as plt

from backend.quantum_tic_tac_toe import State, get_theta_and_phi
from os import getcwd, path


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
        self._n_boards = 9 if ultimate else 1

        self._board_width = width / 3 if ultimate else width

        # font
        self._font = "Roboto"
        self._font_size = int(self._board_width / 4)

        # font colour
        self._x_color = "#CB70FF"
        self._o_color = "#44BC68"
        self._default_color = "#ABABAB"

        self._canvas = Canvas(self, width=width, height=width)
        self._canvas.bind("<Button-1>", lambda event: self._on_click(event))
        self._canvas.grid()

        self._width = width

        self._grid_line_ids = []

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
        self._enabled = [[False for _ in range(9)] for _ in range(self._n_boards)]

        # list of entanglement lines
        self._entanglement_ids = []

        # Load the standard images
        self._default_bloch = self.import_img(width, "Bloch_-1.png")
        self._cross_img = self.import_img(width, "X.png")
        self._circle_img = self.import_img(width, "O.png")

        # Insert the default bloch images and save their ids
        self._symbol_ids = [
            [
                self._canvas.create_image(
                    self._index_to_pos(b, c), anchor="center", image=self._default_bloch
                )
                for c in range(9)
            ]
            for b in range(self._n_boards)
        ]

        # Save references to the images so they don't get garbage collected
        self._image_refs = [
            [self._default_bloch for c in range(9)] for b in range(self._n_boards)
        ]

        # lower the tag so the images don't get in the way of clicking on the canvas
        for list in self._symbol_ids:
            for id in list:
                self._canvas.tag_lower(id)

        self.bind("<Configure>", self._on_resize)

    def import_img(self, width: int, name: str):
        """Imports the desired image

        Args:
            width: width and height of the board
            name: name of the image to be imported
        """

        try:
            img_path = path.join(getcwd(), "src", "Images", name)
            return ImageTk.PhotoImage(
                Image.open(img_path).resize(
                    (width // 3, width // 3), Image.Resampling.LANCZOS
                )
            )
        except FileNotFoundError:
            print(f"Image not found at {img_path}. Please check the path.")
            return

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

        self._entanglement_ids.append(
            self._canvas.create_line(
                cx,
                cy,
                tx,
                ty,
                width=width,
                fill=color,
                arrowshape=arrow_shape,
                arrow="last",
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

    def disable(self, board: int) -> None:
        """Disable `board`.

        Args:
            board: board index
        """

        self._enabled[board] = [False for _ in range(9)]

    def reset(self) -> None:
        """Reset the board to its default state.

        Clears cell symbols. Deletes entanglement lines.
        """

        # reset symbols to default bloch
        for symbols in self._symbol_ids:
            for symbol in symbols:
                self._canvas.itemconfigure(symbol, image=self._default_bloch)

        # delete lines
        self._canvas.delete(*self._entanglement_ids)
        self._entanglement_ids = []

    def update_display(self, board: int, states: list[State]) -> None:
        """Update symbols to display on `board`.

        Sets symbols according to cell states on board.

        Args:
            board: board index
            states: cell states on board
        """

        self.reset()

        for i in range(9):
            if states[i] == State.X:
                tk_img = self._cross_img
            elif states[i] == State.O:
                tk_img = self._circle_img
            else:
                tk_img = self._default_bloch
            self._image_refs[board][i] = tk_img
            self._canvas.itemconfigure(
                self._symbol_ids[board][i], image=self._image_refs[board][i]
            )

    def touch_cell(self, board: int, cell: int, reduced_state: DensityMatrix) -> None:
        """Touch `cell` on `board`.

        Changes the representation of the cell.

        Args:
            board: board index
            cell: cell index
        """

        try:
            img_path = path.join(getcwd(), "src", "Images", f"Bloch_{cell}.png")
            theta, phi = get_theta_and_phi(reduced_state)

            plot_bloch_vector([1, theta, phi], coord_type="spherical").savefig(
                path.join(img_path), transparent=True
            )
            plt.close()

            img = Image.open(img_path).resize(
                (int(self._board_width // 3), int(self._board_width / 3)),
                Image.Resampling.LANCZOS,
            )

            tk_img = ImageTk.PhotoImage(img)

        except FileNotFoundError:
            print(f"Image not found at {img_path}. Please check the path.")
            return

        self._image_refs[board][cell] = tk_img
        self._canvas.itemconfigure(
            self._symbol_ids[board][cell], image=self._image_refs[board][cell]
        )

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

        # scale entanglement line width
        for id in self._entanglement_ids:
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
