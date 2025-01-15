from tkinter import Tk, StringVar, ttk
from gui.widgets.angle_selection import AngleSelection
from gui.widgets.board import Board
from backend.game import Axis
from gui.widgets.move_selection import MoveInfo, MoveSelection
from gui.widgets.number_selection import NumberSelection


class App:
    """Main application."""

    def __init__(self, root: Tk, ultimate: bool, width: int = 500) -> None:
        """Create application.

        Args:
            root: root widget
            ultimate: whether to create ultimate version
            width: width of the board
        """

        # vertical padding for elements
        row_padding = "0 10"

        # row numbers
        info_row = 0
        board_row = 1
        buttons_row = 2

        # create main frame
        mainframe = ttk.Frame(root)
        mainframe.grid(row=0, column=0)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # create info label
        self._info_text = StringVar()
        self._info_text.set("It's X's turn")

        info_label = ttk.Label(
            mainframe, textvariable=self._info_text, padding=row_padding
        )
        info_label.grid(row=info_row, column=0)

        # create board frame
        boardframe = ttk.Frame(mainframe, padding=row_padding)
        boardframe.grid(row=board_row, column=0)

        board_width = width // 3 if ultimate else width
        n_boards = 9 if ultimate else 1

        # create boards
        self._boards = [
            Board(boardframe, board_width, lambda c, b=i: self._click_cell(b, c))
            for i in range(n_boards)
        ]
        for i in range(n_boards):
            self._boards[i].grid(row=i // 3, column=i % 3)

        # moves
        self._moves = [
            MoveInfo("x", "x-rotation", 1, lambda: self._rotate(Axis.X)),
            MoveInfo("z", "z-rotation", 1, lambda: self._rotate(Axis.Z)),
            MoveInfo(
                "cy",
                "controlled y-rotation",
                2,
                lambda: self._rotate_controlled(Axis.Y),
            ),
            MoveInfo("c", "collapse", 1, self._collapse),
        ]

        # create move type selection widget
        self._move_selection = MoveSelection(
            mainframe, self._moves, 2, padding=row_padding
        )
        self._move_selection.grid(row=buttons_row, column=0)

        # create number of qubits selection widget
        self._number_selection = NumberSelection(
            mainframe, 2, 2, self._select_number_of_qubits, padding=row_padding
        )
        self._number_selection.grid(row=buttons_row, column=0)
        self._number_selection.grid_forget()

        # create angle selection widget
        self._angle = StringVar()
        self._angle_selection = AngleSelection(
            mainframe, self._angle, self._set_rotation_angle, padding=row_padding
        )
        self._angle_selection.grid(row=buttons_row, column=0)
        self._angle_selection.grid_forget()

        # create reset button
        self._reset_button = ttk.Button(
            mainframe, text="Play again", padding=row_padding, width=10
        )
        self._reset_button.grid(row=buttons_row, column=0)
        self._reset_button.grid_forget()

    def _reset_widgets(self) -> None:
        """Reset widgets to their default state."""

        print("Reset game")

    def _click_cell(self, board: int, cell: int) -> None:
        """Callback function for clicking on cell `cell` of board `board`.

        Args:
            cell: cell index
            board: board index
        """

        print(f"Clicked cell {cell} of board {board}")

    def _rotate(self, axis: Axis) -> None:
        """Callback function for clicking rotate move button.

        Args:
            axis: axis to rotate around
        """

        print(f"Rotate around {axis}-axis")

    def _rotate_controlled(self, axis: Axis) -> None:
        """Callback function for clicking controlled rotation move button.

        Args:
            axis: axis to rotate around
        """

        print(f"Controlled rotation around {axis}-axis")

    def _collapse(self) -> None:
        """Callback function for clicking collapse move button."""

        print("Collapse")

    def _select_number_of_qubits(self, n: int) -> None:
        """Callback function for selecting the number of qubits to rotate.

        Args:
            n: number of qubits to rotate
        """

        print(f"Rotating {n} qubits")

    def _set_rotation_angle(self) -> None:
        """Callback function for setting the rotation angle."""

        print(f"Rotate by {self._angle.get()}")
