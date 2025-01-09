from tkinter import Tk, StringVar, S, ttk
from enum import Enum
from gui.board import Board


class MoveType(Enum):
    CLASSICAL = 0
    QUANTUM = 1

    def __str__(self) -> str:
        """Get string representation of the move type."""

        match self:
            case MoveType.CLASSICAL:
                return "classical"
            case MoveType.QUANTUM:
                return "quantum"


class App:
    """Main application."""

    def __init__(self, root: Tk, ultimate: bool, width: int = 300) -> None:
        """Create application.

        Args:
            root: root widget
            ultimate: whether to create ultimate version
            width: width of the board
        """

        # create main frame
        mainframe = ttk.Frame(root)
        mainframe.grid(row=0, column=0)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # create board frame
        boardframe = ttk.Frame(mainframe)
        boardframe.grid(row=1, column=0)

        board_width = width // 3 if ultimate else width
        n_boards = 9 if ultimate else 1

        # create boards
        self._boards = [
            Board(boardframe, board_width, lambda c, b=i: self._click_cell(b, c))
            for i in range(n_boards)
        ]
        for i in range(n_boards):
            self._boards[i].grid(row=i // 3, column=i % 3)

        # create info label
        self._info_text = StringVar()

        info_label = ttk.Label(mainframe, textvariable=self._info_text)
        info_label.grid(row=0, column=0)

        # create board frame
        boardframe = ttk.Frame(mainframe, padding="0 25")
        boardframe.grid(row=1, column=0)

        # create move type frame
        self._move_type_frame = ttk.Frame(mainframe)
        self._move_type_frame.grid(row=2, column=0, sticky=S)

        # create move type buttons
        self._classical_button = ttk.Button(
            self._move_type_frame,
            text="Classical",
            command=lambda: self._click_move_type(MoveType.CLASSICAL),
        )
        self._classical_button.grid(row=0, column=0)

        self._quantum_button = ttk.Button(
            self._move_type_frame,
            text="Quantum",
            command=lambda: self._click_move_type(MoveType.QUANTUM),
        )
        self._quantum_button.grid(row=0, column=2)

        # create reset button
        self._reset_button = ttk.Button(mainframe, text="Play again")
        self._reset_button.grid(row=3, column=0)
        self._reset_button.grid_forget()

    def _reset_widgets(self) -> None:
        """Reset widgets to their default state."""

        # reset boards
        for board in self._boards:
            board.reset()

        # reset move type buttons
        self._classical_button["state"] = "normal"
        self._quantum_button["state"] = "normal"

        # hide reset button
        self._reset_button.grid_forget()
        # display move type frame
        self._move_type_frame.grid_forget()

    def _click_cell(self, board: int, cell: int) -> None:
        """Callback function for clicking on cell `cell` of board `board`.

        Args:
            cell: cell index
            board: board index
        """

        print(f"Clicked cell {cell} of board {board}")
        # Todo: move to `Board` class?
        # Todo: cell click logic

    def _click_move_type(self, type: MoveType) -> None:
        """Callback function for clicking on move type button.

        Args:
            type: move type
        """

        print(f"Chose {type} move")
        # Todo: move type click logic
