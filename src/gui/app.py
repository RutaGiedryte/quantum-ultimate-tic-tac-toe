import math
from tkinter import Tk, StringVar, DoubleVar, ttk
from backend.quantum_tic_tac_toe import QuantumTicTacToe, State, Axis, Move
from gui.widgets.angle_selection import AngleSelection
from gui.widgets.board import Board
from gui.widgets.move_selection import MoveSelection
from gui.widgets.number_selection import NumberSelection
from qiskit.providers import BackendV2
from gui.partial_circuits import display_circuit_of_sub_board
from gui.widgets.partial_circuit_selection import PartialCircuitSelection


class App:
    """Main application."""

    def __init__(
        self, root: Tk, ultimate: bool, moves: list[Move], backend: BackendV2
    ) -> None:
        """Create application.

        Args:
            root: root widget
            ultimate: whether to create ultimate version
            moves: list of allowed moves
            backend: backend for running quantum circuit
        """

        self._moves = moves
        self._ultimate = ultimate

        # style
        style = ttk.Style()
        style.configure("TopInfo.TLabel", font=("Roboto", 20))
        style.configure(".", background="#E0E0E0")
        style.configure("TButton", background="#F5F5F5")

        # create game
        self._game = QuantumTicTacToe(backend, math.pi / 2, math.pi, 10, ultimate)
        self._turn = State.X

        # vertical padding for elements
        row_padding = "0 10"

        # row numbers
        partial_circuit_row = 0
        info_row = 1
        board_row = 2
        buttons_row = 3

        button_row_height = 120

        # create main frame
        mainframe = ttk.Frame(root)
        mainframe.grid(row=0, column=0, sticky="NSEW")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(board_row, weight=1)
        mainframe.rowconfigure(buttons_row, minsize=button_row_height)

        # create info label
        self._info_text = StringVar()
        self._info_text.set("It's X's turn")

        info_label = ttk.Label(
            mainframe,
            textvariable=self._info_text,
            padding=row_padding,
            style="TopInfo.TLabel",
        )
        info_label.grid(row=info_row, column=0)

        # create board
        self._board = Board(mainframe, 500, self._click_cell, ultimate)
        self._board.grid(row=board_row, column=0, sticky="NSEW")

        self._n_boards = 9 if ultimate else 1

        # move callbacks
        self._move_callbacks = {
            Move.RX: lambda: self._rotate(Axis.X),
            Move.RY: lambda: self._rotate(Axis.Y),
            Move.RZ: lambda: self._rotate(Axis.Z),
            Move.CRX: lambda: self._rotate_controlled(Axis.X),
            Move.CRY: lambda: self._rotate_controlled(Axis.Y),
            Move.CRZ: lambda: self._rotate_controlled(Axis.Z),
            Move.COLLAPSE: self._collapse,
        }

        # create move type selection widget
        self._move_selection = MoveSelection(
            mainframe,
            {
                move: callback
                for move, callback in self._move_callbacks.items()
                if move in self._moves
            },
            cols=2,
            padding=row_padding,
        )
        self._move_selection.grid(row=buttons_row, column=0, sticky="S")

        # create number of qubits selection widget
        self._number_selection = NumberSelection(
            mainframe, 2, 2, self._select_number_of_qubits, padding=row_padding
        )
        self._number_selection.grid(row=buttons_row, column=0, sticky="S")
        self._number_selection.grid_forget()

        # create angle selection widget
        self._angle = DoubleVar()
        self._angle_selection = AngleSelection(
            mainframe, self._angle, self._set_rotation_angle, padding=row_padding
        )
        self._angle_selection.grid(row=buttons_row, column=0, sticky="S")
        self._angle_selection.grid_forget()

        if ultimate:
            # create partial circuit widget
            self._sub_board = StringVar()
            self._sub_board_selection = PartialCircuitSelection(
                mainframe, self._sub_board, self._partial_circuit, padding=row_padding
            )
            self._sub_board_selection.grid(
                row=partial_circuit_row, column=0, sticky="S"
            )

        # create reset button
        self._reset_button = ttk.Button(
            mainframe,
            text="Play again",
            padding=row_padding,
            width=10,
            command=self._reset,
        )
        self._reset_button.grid(row=buttons_row, column=0, sticky="S")
        self._reset_button.grid_forget()

        # create collapse label
        self._collapse_label = ttk.Label(
            mainframe, text="Choose a board to collapse", padding=row_padding
        )
        self._collapse_label.grid(row=buttons_row, column=0)
        self._collapse_label.grid_forget()

    def _click_cell(self, board: int, cell: int) -> None:
        """Callback function for clicking on cell `cell` of board `board`.

        Args:
            cell: cell index
            board: board index
        """

        collapsed = set()

        self._disable_boards()

        match self._selected_move:
            # simple rotation
            case Move.RX | Move.RY | Move.RZ:
                # set axis
                axis = self._selected_move.get_axis()
                self._remaining_angle -= abs(self._angle.get())

                collapsed = self._game.rotate(
                    board, cell, axis, float(self._angle.get()), self._number_to_rotate
                )
                # display angle selection again if more qubits to rotate
                if self._game.has_moves():
                    self._angle_selection.set_message("Set angle to rotate by")
                    self._angle_selection.enable(self._remaining_angle)
                else:
                    self._angle_selection.grid_forget()
            # controlled rotation
            case Move.CRX | Move.CRY | Move.CRZ:
                # control qubit has been selected - add gate
                if self._game.has_control():
                    c_board, c_cell = self._game.get_control()
                    self._board.entangle(c_board, c_cell, board, cell)
                    axis = self._selected_move.get_axis()
                    collapsed = self._game.rotate_target(
                        board, cell, axis, float(self._angle.get())
                    )
                    self._angle_selection.grid_forget()
                # set control qubit, ask for target qubit
                else:
                    self._game.rotate_control(board, cell)
                    self._angle_selection.set_message("Choose target qubit")
                    self._angle_selection.disable()
                    self._enable_boards()
            case Move.COLLAPSE:
                collapsed = self._game.collapse(board)
                self._collapse_label.grid_forget()

        # Touch cell to update the visuals
        self._board.touch_cell(board, cell, self._game.get_statevector(board, cell))

        # display move selection if no more moves this turn
        if not self._game.has_moves():
            self._show_move_selection()
            self._change_turn()

        #  updated board if collapsed and check for end
        if len(collapsed):
            self._update_boards(collapsed)
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
                self._selected_move = Move.RY
            case Axis.Z:
                self._selected_move = Move.RZ

        # get available boards
        boards = self._game.available_boards(self._selected_move)

        # get max number of qubits that can be rotated
        max_n = 0
        if len(boards) >= 2:
            max_n = 2
        else:
            max_n = min(
                2, self._game.count_avialable_cells(boards[0], self._selected_move)
            )

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
            case Axis.X:
                self._selected_move = Move.CRX
            case Axis.Y:
                self._selected_move = Move.CRY
            case Axis.Z:
                self._selected_move = Move.CRZ

        # set remaining angle
        self._remaining_angle = self._game.max_controlled_angle

        # hide move type widget
        self._move_selection.grid_forget()

        # show angle selection widget
        self._angle_selection.set_message("Set angle to rotate by")
        self._angle_selection.enable(self._remaining_angle)
        self._angle_selection.grid()

    def _collapse(self) -> None:
        """Callback function for clicking collapse move button."""

        self._selected_move = Move.COLLAPSE

        # let player choose board when ultimate
        if self._ultimate:
            self._move_selection.grid_forget()
            self._collapse_label.grid()
            self._enable_boards()
        else:
            self._click_cell(0, 0)

    def _select_number_of_qubits(self, n: int) -> None:
        """Callback function for selecting the number of qubits to rotate.

        Args:
            n: number of qubits to rotate
        """

        self._number_to_rotate = n

        # hide number selection
        self._number_selection.grid_forget()

        max_angle = (
            self._remaining_angle
            if self._number_to_rotate == 1
            else self._remaining_angle - math.pi / 4
        )

        # show angle selection
        self._angle_selection.set_message("Set angle to rotate by")
        self._angle_selection.enable(max_angle)
        self._angle_selection.grid()

    def _set_rotation_angle(self) -> None:
        """Callback function for setting the rotation angle."""

        if self._angle.get() == 0:
            self._angle_selection.set_message("Set angle to rotate by")
            self._disable_boards()
        else:
            message = f"Rotate by {self._angle.get() / math.pi}\u03c0"
            if self._selected_move in [Move.CRX, Move.CRY, Move.CRZ]:
                message += ". Choose control qubit"
            self._angle_selection.set_message(message)
            self._enable_boards()

    def _enable_boards(self) -> None:
        """Enable available boards."""

        # get board to enable
        boards = self._game.available_boards(self._selected_move)
        # enable cells
        for board in boards:
            self._board.enable(
                board, self._game.available_cells(board, self._selected_move)
            )

    def _disable_boards(self) -> None:
        """Disable all boards."""

        for i in range(self._n_boards):
            self._board.disable(i)

    def _update_boards(self, boards: set[int]) -> None:
        """Update `boards`.

        Args:
            boards: set of board indices to update
        """

        for i in boards:
            board_state = self._game.board(i)
            self._board.update_display(i, board_state)

            # check if subboard is finished when ultimate
            if self._ultimate:
                winner = self._game.check_win(i)
                if winner != State.EMPTY:
                    self._board.set_winner(i, winner)

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

        enabled_moves = self._game.available_moves(self._moves)

        self._move_selection.enable(set(enabled_moves))
        self._move_selection.grid()

    def _reset(self) -> None:
        """Reset the game."""

        # reset game
        self._game.reset()

        # reset boards
        for i in range(self._n_boards):
            self._board.reset(i)

        # hide again button
        self._reset_button.grid_forget()

        # set turn
        self._info_text.set("It's X's turn")
        self._turn = State.X

        # show move selection
        self._show_move_selection()

    def _partial_circuit(self) -> None:
        """Callback function for printing partial circuit in the ultimate game."""

        sub_board = self._sub_board.get()

        try:
            sub_board_number = int(sub_board)
            if sub_board_number >= 1 and sub_board_number <= 9:
                display_circuit_of_sub_board(self._game._qc, sub_board_number)
        except ValueError:
            pass

        self._sub_board.set("")
