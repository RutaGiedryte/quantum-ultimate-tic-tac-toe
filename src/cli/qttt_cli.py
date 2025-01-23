import math
from backend.quantum_tic_tac_toe import Axis, QuantumTicTacToe, State, Move
from qiskit.providers import BackendV2
from cli.input import get_int, get_float, get_int_from_list


class QtttCLI:
    """CLI version of Quantum Tic-Tac-Toe."""

    def __init__(self, ultimate: bool, moves: list[Move], backend: BackendV2):
        """Create the game.

        Args:
            ultimate: whether to create the ultimate version
            moves: list of allowed moves
            backend: backend to use for running the circuit
        """

        # initialise move types
        self._move_callbacks = {
            Move.RX: lambda: self._rotate(Axis.X),
            Move.RY: lambda: self._rotate(Axis.Y),
            Move.RZ: lambda: self._rotate(Axis.Z),
            Move.CRX: lambda: self._rotate_controlled(Axis.X),
            Move.CRY: lambda: self._rotate_controlled(Axis.Y),
            Move.CRZ: lambda: self._rotate_controlled(Axis.Z),
            Move.COLLAPSE: self._collapse,
        }

        self._game = QuantumTicTacToe(backend, math.pi / 2, math.pi, 10, ultimate)
        self._moves = moves
        self._ultimate = ultimate

    def play(self):
        """Play one game."""

        turn = State.X
        self._game.reset()

        while True:
            if self._ultimate:
                print()
                self._print_board(-1)

            print()
            self._print_board()
            print()

            print(f"It's {turn}'s turn.")

            available_moves = {
                move.key: move for move in self._game.available_moves(self._moves)
            }

            # create prompt
            prompt = "Select move type: "
            for i, key in enumerate(available_moves):
                prompt += f"{available_moves[key].description} [{key}]"
                if i < len(available_moves) - 1:
                    prompt += " | "
            prompt += ": "

            # get move type
            move_str = None

            while True:
                move_str = input(prompt)
                if move_str not in available_moves.keys():
                    print("Invalid move type!")
                else:
                    break

            collapsed = self._move_callbacks[available_moves[move_str]]()

            # draw circuit
            if not collapsed:
                print()
                print(self._game.circuit_string())

            # check win if collapsed
            if collapsed:
                print("\nBoard collapsed\n")
                winner = self._game.check_win(0)
                # game ended
                if winner != State.EMPTY:
                    self._print_board(-1 if self._ultimate else 0)
                    print()

                    if winner == State.DRAW:
                        print("It's a draw.")
                    else:
                        print(f"{winner} has won!")
                    break

            turn = State.X if turn == State.O else State.O

    def _rotate(self, axis: Axis) -> bool:
        """Move for rotating a qubit around `axis`.

        Args:
            axis: axis to rotate around

        Returns:
            whether the board collapsed
        """

        match axis:
            case Axis.X:
                move = Move.RX
            case Axis.Y:
                move = Move.RY
            case Axis.Z:
                move = Move.RZ

        max_n = min(2, self._game.count_avialable_cells(0, move))

        # get number of qubits to rotate
        n = get_int(
            1,
            max_n,
            f"Number of qubits to rotate (max. {max_n}): ",
            f"Number of qubits can be at most {max_n}.",
        )

        remaining_rotation = self._game.max_angle

        used = set()

        collapsed = set()

        for _ in range(n):
            # get board index
            board = self._get_valid_board_index(move) if self._ultimate else 0

            # get position
            pos = self._get_valid_position(board, move)

            # get angle
            angle = get_float(
                -remaining_rotation,
                remaining_rotation,
                f"Enter angle to rotate by (max. {remaining_rotation}): ",
                f"The angle must be between {-remaining_rotation} and {remaining_rotation}.",
            )

            remaining_rotation -= abs(angle)

            # add rotation gate
            collapsed.update(self._game.rotate(0, pos, axis, angle, n))

            used.add(pos)

        return len(collapsed) != 0

    def _rotate_controlled(self, axis: Axis) -> bool:
        """Move for controlled rotation.

        Args:
            axis: axis to rotate around

        Returns:
            whether the board collapsed
        """

        move = None
        match axis:
            case Axis.X:
                move = Move.CRX
            case Axis.Y:
                move = Move.CRY
            case Axis.Z:
                move = Move.CRZ

        # get control qubit index
        print("Choose control qubit.")
        board = self._get_valid_board_index(move) if self._ultimate else 0
        control = self._get_valid_position(board, move)

        # set control qubit
        self._game.rotate_control(0, control)

        # get target qubit index
        print("Choose target qubit.")
        board = self._get_valid_board_index(move) if self._ultimate else 0
        target = self._get_valid_position(board, move)

        # get angle
        angle = get_float(
            -self._game.max_controlled_angle,
            self._game.max_controlled_angle,
            f"Enter angle to rotate by (max. {self._game.max_controlled_angle}): ",
            f"The angle must be between {-self._game.max_controlled_angle} and {self._game.max_controlled_angle}.",
        )

        # set target qubit
        return len(self._game.rotate_target(board, target, axis, angle)) != 0

    def _collapse(self) -> bool:
        """Move for collapsing board.

        Returns:
            whether the board collapsed
        """

        board = self._get_valid_board_index(Move.COLLAPSE) if self._ultimate else 0
        return len(self._game.collapse(board)) != 0

    def _get_valid_board_index(self, move: Move) -> int:
        """Get board index from stding that is allowed for `move`

        Args:
            move: move

        Returns:
            board index
        """

        available = self._game.available_boards(move)

        available_from_one = [i + 1 for i in available]

        return (
            get_int_from_list(
                available_from_one,
                f"Enter board number {available_from_one}: ",
                f"Board number must be in {available_from_one}",
            )
            - 1
        )

    def _get_valid_position(self, board: int, move: Move) -> int:
        """Get cell index for `board` from stdin that is allowed for `move`.

        Args:
            board: board index
            move: move

        Returns:
            cell index
        """

        available = self._game.available_cells(board, move)

        # list with 1-based indexing
        available_from_one = [i + 1 for i in available]

        return (
            get_int_from_list(
                available_from_one,
                f"Enter cell number {available_from_one}: ",
                f"Cell number must be in {available_from_one}",
            )
            - 1
        )

    def _print_board(self, board: int | None = None):
        """Print the board.

        Args:
            board: board index. `None` if printing whole board. `-1` if printing big board for ultimate
        """

        # print 9 boards if ultimate and board index not given
        big = self._ultimate and board is None

        # for row of boards
        for i in range(3 if big else 1):
            # for row in board
            for j in range(3):
                self._print_row(i * 3 + j, board)
                self._print_row_separator(j, big)

            if big and i < 2:
                self._print_big_board_separator()

    def _print_row(self, row: int, board: int | None):
        """Print board row.

        Args:
            row: row to print
            board: board index to print. `None` if printing all subboards
        """

        vertical = "\u2502"
        double_vertical = "\u2551"

        # row in board
        cell_row = row % 3

        # print all boards if no index given
        if board is None:
            board_row = row // 3
            board_indices = (
                [3 * board_row, 1 + 3 * board_row, 2 + 3 * board_row]
                if self._ultimate
                else [3 * board_row]
            )
        else:
            board_indices = [board]

        # list of board rows to print
        rows = [
            self._game.board(i)[3 * cell_row : 3 + 3 * cell_row] for i in board_indices
        ]

        # for each row
        for i in range(len(rows)):
            values = rows[i]
            print("  ", end="")

            # for cell in row
            for j in range(3):
                # print cell value
                print(f" {values[j]} ", end="")
                # print vertical bar
                if j < 2:
                    print(vertical, end="")

            # print double vertical bar between boards
            if i < len(rows) - 1:
                print(f"   {double_vertical}", end="")

        print()

    def _print_row_separator(self, row: int, big: bool) -> None:
        """Print board row separator.

        Args:
            row: row number
            big: whether printing big board
        """

        numbers = [
            "\u00b9",
            "\u00b2",
            "\u00b3",
            "\u2074",
            "\u2075",
            "\u2076",
            "\u2077",
            "\u2078",
            "\u2079",
        ]
        horizontal = "\u2500" * 3 if (row + 1) % 3 else " " * 3

        double_vertical = "\u2551"

        cell_row = row % 3

        # for each board
        for i in range(3 if big else 1):
            print("  ", end="")  # cell

            # for each cell
            for j in range(3):
                # print horizontal bar
                print(horizontal, end="")
                # print number
                print(numbers[3 * cell_row + j], end="")

            # print double vertical between subboards
            if big and i < 2:
                print(f"  {double_vertical}", end="")

        print()

    def _print_big_board_separator(self) -> None:
        """Print horizontal separator for ultimate board."""

        line = "\u2550" * 16
        cross = "\u256c"

        # for each board
        for i in range(3):
            # print line
            print(line, end="")

            # print cross
            if i < 2:
                print(cross, end="")

        print()
