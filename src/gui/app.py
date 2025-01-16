import math
from tkinter import N, Tk, StringVar, ttk
from backend.quantum_tic_tac_toe import QuantumTicTacToe, State
from gui.widgets.angle_selection import AngleSelection
from gui.widgets.board import Board
from backend.quantum_tic_tac_toe import Axis
from gui.widgets.move_selection import Move, MoveInfo, MoveSelection
from gui.widgets.number_selection import NumberSelection
from qiskit_aer import AerSimulator


class App:
    """Main application."""

    def __init__(self, root: Tk, ultimate: bool, width: int = 500) -> None:
        """Create application.

        Args:
            root: root widget
            ultimate: whether to create ultimate version
            width: width of the board
        """

        # style
        style = ttk.Style()
        style.configure("TopInfo.TLabel", font=("Roboto", 20))

        # create game
        self._game = QuantumTicTacToe(
            AerSimulator(), math.pi / 2, math.pi, 10, ultimate
        )
        self._turn = State.X

        # vertical padding for elements
        row_padding = "0 10"

        # row numbers
        info_row = 0
        board_row = 1
        buttons_row = 2

        # create main frame
        mainframe = ttk.Frame(root)
        mainframe.grid(row=0, column=0, sticky=N)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # create info label
        self._info_text = StringVar()
        self._info_text.set("It's X's turn")

        info_label = ttk.Label(
            mainframe,
            textvariable=self._info_text,
            padding=row_padding,
            style="TopInfo.TLabel",
        )
        info_label.grid(row=info_row, column=0, sticky=N)

        # create board
        self._board = Board(mainframe, width, self._click_cell, ultimate)
        self._board.grid(row=board_row, column=0, sticky=N)

        self._n_boards = 9 if ultimate else 1

        # moves
        self._moves = {
            Move.RX: MoveInfo("x-rotation", 1, lambda: self._rotate(Axis.X)),
            Move.RZ: MoveInfo("z-rotation", 1, lambda: self._rotate(Axis.Z)),
            Move.CRY: MoveInfo(
                "controlled y-rotation",
                2,
                lambda: self._rotate_controlled(Axis.Y),
            ),
            Move.COLLAPSE: MoveInfo("collapse", 1, self._collapse),
        }

        # create move type selection widget
        self._move_selection = MoveSelection(
            mainframe, self._moves, 2, padding=row_padding
        )
        self._move_selection.grid(row=buttons_row, column=0, sticky=N)

        # create number of qubits selection widget
        self._number_selection = NumberSelection(
            mainframe, 2, 2, self._select_number_of_qubits, padding=row_padding
        )
        self._number_selection.grid(row=buttons_row, column=0, sticky=N)
        self._number_selection.grid_forget()

        # create angle selection widget
        self._angle = StringVar()
        self._angle_selection = AngleSelection(
            mainframe, self._angle, self._set_rotation_angle, padding=row_padding
        )
        self._angle_selection.grid(row=buttons_row, column=0, sticky=N)
        self._angle_selection.grid_forget()

        # create reset button
        self._reset_button = ttk.Button(
            mainframe,
            text="Play again",
            padding=row_padding,
            width=10,
            command=self._reset,
        )
        self._reset_button.grid(row=buttons_row, column=0, sticky=N)
        self._reset_button.grid_forget()

    def _click_cell(self, board: int, cell: int) -> None:
        """Callback function for clicking on cell `cell` of board `board`.

        Args:
            cell: cell index
            board: board index
        """

        collapsed = False

        self._board.touch_cell(board, cell)

        self._disable_boards()

        match self._selected_move:
            # simple rotation
            case Move.RX | Move.RZ:
                axis = Axis.X if self._selected_move == Move.RX else Axis.Z
                collapsed = self._game.rotate(
                    board, cell, axis, float(self._angle.get()), self._number_to_rotate
                )
                # display angle selection again if more qubits to rotate
                if self._game.has_moves():
                    self._angle_selection.set_message(
                        f"Enter angle to rotate by {self._remaining_angle}"
                    )
                    self._angle_selection.enable()
                else:
                    self._angle_selection.grid_forget()
            # controlled rotation
            case Move.CRY:
                # control qubit has been selected - add gate
                if self._game.has_control():
                    collapsed = self._game.rotate_target(
                        board, cell, Axis.Y, float(self._angle.get())
                    )
                    self._angle_selection.grid_forget()
                # set control qubit, ask for target qubit
                else:
                    self._game.rotate_control(board, cell)
                    self._angle_selection.set_message("Choose target qubit")
                    self._enable_boards()

        # display move selection if no more moves this turn
        if not self._game.has_moves():
            self._show_move_selection()
            self._change_turn()

        #  updated board if collapsed and check for end
        if collapsed:
            self._update_boards()
            self._check_end()

    def _rotate(self, axis: Axis) -> None:
        """Callback function for clicking rotate move button.

        Args:
            axis: axis to rotate around
        """

        # set current move as rotation
        match axis:
            case Axis.X:
                self._selected_move = Move.RX
            case Axis.Y:
                raise ValueError("Cannot rotate around Y-axis")
            case Axis.Z:
                self._selected_move = Move.RZ

        # get available boards
        boards = self._game.available_boards()

        # get max number of qubits that can be rotated
        max_n = 0
        if len(boards) >= 2:
            max_n = 2
        else:
            max_n = min(2, self._game.count_empty_cells(boards[0]))

        # set remaining angle
        self._remaining_angle = self._game.max_angle

        # set max number of quibts
        self._number_selection.set_max(max_n)

        # hide move type widget
        self._move_selection.grid_forget()

        # show qubit number selection widget
        self._number_selection.grid()

    def _rotate_controlled(self, axis: Axis) -> None:
        """Callback function for clicking controlled rotation move button.

        Args:
            axis: axis to rotate around
        """

        # set current move
        match axis:
            case Axis.Y:
                self._selected_move = Move.CRY
            case _:
                raise ValueError("Can only make controlled Y-rotation")

        # set remaining angle
        self._remaining_angle = self._game.max_controlled_angle

        # hide move type widget
        self._move_selection.grid_forget()

        # show angle selection widget
        self._angle_selection.set_message(
            f"Enter angle to rotate by (max. {self._remaining_angle})"
        )
        self._angle_selection.enable()
        self._angle_selection.grid()

    def _collapse(self) -> None:
        """Callback function for clicking collapse move button."""

        # collapse and update boards
        self._game.collapse()
        self._update_boards()

        # disable boards
        self._disable_boards()

        end = self._check_end()

        if not end:
            self._change_turn()
            self._show_move_selection()

    def _select_number_of_qubits(self, n: int) -> None:
        """Callback function for selecting the number of qubits to rotate.

        Args:
            n: number of qubits to rotate
        """

        self._number_to_rotate = n

        # hide number selection
        self._number_selection.grid_forget()

        # show angle selection
        self._angle_selection.set_message(
            f"Enter angle to rotate by (max. {self._remaining_angle})"
        )
        self._angle_selection.enable()
        self._angle_selection.grid()

    def _set_rotation_angle(self) -> None:
        """Callback function for setting the rotation angle."""

        # check if valid angle
        angle = 0
        try:
            angle = float(self._angle.get())
            if angle > self._remaining_angle:
                raise ValueError
        except ValueError:
            self._angle_selection.set_message(
                f"The angle must be between {-self._remaining_angle} and {self._remaining_angle}"
            )
            return

        self._remaining_angle -= abs(angle)

        # disable angle button
        self._angle_selection.disable()

        if self._selected_move == Move.CRY:
            self._angle_selection.set_message("Choose control qubit")

        # enable board
        self._enable_boards()

    def _enable_boards(self) -> None:
        """Enable available boards."""

        # get board to enable
        boards = self._game.available_boards()
        # enable cells
        for board in boards:
            self._board.enable(board, self._game.available_cells(board))

    def _disable_boards(self) -> None:
        """Disable all boards."""

        for i in range(self._n_boards):
            self._board.disable(i)

    def _update_boards(self) -> None:
        """Update all boards."""

        for i in range(self._n_boards):
            board_state = self._game.board(i)
            self._board.update_display(i, board_state)

    def _change_turn(self) -> None:
        """Change turn."""

        self._turn = State.X if self._turn == State.O else State.O
        self._info_text.set(f"It's {self._turn}'s turn")

    def _check_end(self) -> bool:
        """Check if game ended.

        Displays winner information and play again button if ended.

        Returns:
            whether the game ended
        """

        winner = self._game.check_win()

        if winner == State.EMPTY:
            return False

        if winner == State.DRAW:
            self._info_text.set("It's a draw")
        else:
            self._info_text.set(f"{winner} has won!")

        # hide move selection
        self._move_selection.grid_forget()

        # display reset button
        self._reset_button.grid()

        return True

    def _show_move_selection(self) -> None:
        """Show move selection widget.

        Only enables possible moves.
        """

        available_boards = self._game.available_boards()
        n_empty = sum([self._game.count_empty_cells(i) for i in available_boards])

        enabled_moves = set()

        for move, info in self._moves.items():
            if n_empty >= info.min_empty:
                enabled_moves.add(move)

        self._move_selection.enable(enabled_moves)
        self._move_selection.grid()

    def _reset(self) -> None:
        """Reset the game."""

        # reset game
        self._game.reset()

        # reset board
        self._board.reset()

        # hide again button
        self._reset_button.grid_forget()

        # set turn
        self._info_text.set("It's X's turn")
        self._turn = State.X

        # show move selection
        self._show_move_selection()
