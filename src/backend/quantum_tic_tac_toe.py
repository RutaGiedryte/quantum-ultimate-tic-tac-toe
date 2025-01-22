import random

from enum import Enum
from typing import Any

from qiskit import QuantumCircuit, generate_preset_pass_manager
from qiskit.providers import BackendV2
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit_ibm_runtime import SamplerV2

import warnings  # Qiskit using deprecated internal stuff for dag_to_circuit...
warnings.filterwarnings("ignore", category=DeprecationWarning)


class Axis(Enum):
    """Rotation axis."""

    X = 0
    Y = 1
    Z = 2


class Move(Enum):
    """Possible moves."""

    RX = "x", "x-rotation", 1
    RY = "y", "y-rotation", 1
    RZ = "z", "z-rotation", 1
    CRX = "cx", "controlled x-rotation", 2
    CRY = "cy", "controlled y-rotation", 2
    CRZ = "cz", "controlled z-rotation", 2
    COLLAPSE = "c", "collapse", 1

    def __init__(self, key: str, description: str, min_empty: int) -> None:
        """Construct move.

        Args:
            key: short identifier for the move
            description: move description
            min_empty: min. number of empty cells required for the movec
        """

        self._key = key
        self._description = description
        self._min_empty = min_empty

    @property
    def key(self):
        return self._key

    @property
    def description(self):
        return self._description

    @property
    def min_empty(self):
        return self._min_empty

    def get_axis(self) -> Axis:
        """Get the rotation axis of the move.

        Returns:
            rotation axis iff rotation move

        Raises:
            ValueError: if not a rotation move
        """

        match self:
            case Move.RX | Move.CRX:
                return Axis.X
            case Move.RY | Move.CRY:
                return Axis.Y
            case Move.RZ | Move.CRZ:
                return Axis.Z
            case Move.COLLAPSE:
                raise ValueError

    def __eq__(self, other: Any) -> bool:
        """Check equality based on `key`."""

        if type(self) is not type(other):
            return False

        return self._key == other._key

    def __hash__(self) -> int:
        return hash(self._key)


class State(Enum):
    """State of a cell on board, or the winner of a game."""

    EMPTY = 0
    X = 1
    O = 2
    DRAW = 3
    Z_BLOCKED = 4

    def __str__(self) -> str:
        match self:
            case State.EMPTY:
                return " "
            case State.X:
                return "X"
            case State.O:
                return "O"
            case State.DRAW:
                return "draw"
            case State.Z_BLOCKED:
                return "z"


def get_fair_bitstring(counts, threshold, total) -> str:
    probabilities = {state: count / total for state, count in counts.items()}
    try:
        filtered_probabilities = {state: prob for state, prob in probabilities.items() if prob >= threshold}
        if not filtered_probabilities:
            raise ValueError("All states were filtered out.")
    except ValueError:
        filtered_probabilities = {max(counts, key=counts.get): 1}
    total_prob = sum(filtered_probabilities.values())
    normalized_probabilities = {state: prob / total_prob for state, prob in filtered_probabilities.items()}
    states, probs = zip(*normalized_probabilities.items())
    chosen_state = random.choices(states, weights=probs, k=1)[0]
    return chosen_state


def run_circuit(qc, backend, shots) -> dict:
    qc.measure_all()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=0)
    isa_circuit = pm.run(qc)
    sampler = SamplerV2(mode=backend)
    job = sampler.run([isa_circuit], shots=shots)
    result = job.result()
    try:
        counts = getattr(result[0].data, qc.cregs[0].name, None).get_counts()
    except AttributeError:
        raise SystemError("Empty or invalid result..")  # Handle this?
    return counts


class QuantumTicTacToe:
    """Class representing quantum tic-tac-toe game."""

    def __init__(
        self,
        backend: BackendV2,
        max_angle: float,
        max_controlled_angle: float,
        max_turns: int,
        ultimate: bool,
    ):
        """Create the game.

        Args:
            backend: backend used for running the quantum circuit
            max_angle: max. angle for rotation move
            max_controlled_angle: max. angle for controlled rotation move
            max_turns: max. number of turns between collapses
            ultimate: whether to create ultimate version
        """

        self._ultimate = ultimate
        self._n_bits = 81 if ultimate else 9

        self._qc = QuantumCircuit(self._n_bits)

        self._backend = backend
        self._max_angle = max_angle
        self._max_controlled_angle = max_controlled_angle
        self._max_moves = max_turns

        self.reset()

    @property
    def max_angle(self) -> float:
        return self._max_angle

    @property
    def max_controlled_angle(self) -> float:
        return self._max_controlled_angle

    def reset(self) -> None:
        """Reset game."""

        # initialise boards
        n_boards = 9 if self._ultimate else 1
        self._boards = [[State.EMPTY for _ in range(9)] for _ in range(n_boards)]
        # number of turns since last collapse
        self._turns = 0
        # control qubit position
        self._c_board = -1
        self._c_cell = -1
        # a turn can have multiple moves (e.g., rotation with 2 qubits)
        self._moves_left_in_turn = 0
        # qubits that have been touched in current turn
        self._touched = [set() for _ in self._boards]
        # board wins
        self._board_wins = [State.EMPTY for _ in range(9)]

    def has_control(self) -> bool:
        """Check if control qubit has been set.

        Returns:
            true iff control qubit has been set
        """

        return self._c_board != -1

    def get_control(self) -> tuple[int, int]:
        """Get control qubit board and cell index.

        Returns:
            (board index, cell index)
        """
        return self._c_board, self._c_cell

    def has_moves(self) -> bool:
        """Check if there are moves left in a multi-move turn.

        Returns:
            true iff there are moves left
        """
        return self._moves_left_in_turn != 0

    def available_boards(self, move: Move) -> list[int]:
        """Get a list of indices of boards that can be used with `move`.

        Args:
            move: move to check

        Returns:
            list of board indices that can be used with `move`
        """

        if self.count_avialable_cells(0, move) == 0:
            return []

        return [0]

    def available_cells(self, board: int, move: Move) -> list[int]:
        """Get the indices of available cells on board `board` for `move`.

        Args:
            board: board index
            move: move to check

        Returns:
            list of available cells on board `board`
        """

        allowed = [State.EMPTY]
        # allow z_blocked cells if move is not z-rotation
        if move != Move.RZ:
            allowed.append(State.Z_BLOCKED)

        return [
            i
            for i, state in enumerate(self._boards[board])
            if state in allowed and i not in self._touched[board]
        ]

    def available_moves(self, moves: list[Move]) -> list[Move]:
        """Filter available moves from a list of moves.

        Args:
            moves: list of moves to filter

        Returns
            available moves
        """

        allowed = []

        for move in moves:
            available_boards = self.available_boards(move)
            n_empty = sum(
                [self.count_avialable_cells(board, move) for board in available_boards]
            )

            if n_empty >= move.min_empty:
                allowed.append(move)

        return allowed

    def count_avialable_cells(self, board: int, move: Move) -> int:
        """Get the number of available cells on board `board` for `move`.

        Args:
            board: board index
            move: move to check

        Returns:
            number of empty cells on board `board` for `move`
        """

        return len(self.available_cells(board, move))

    def board(self, i: int) -> list[State]:
        """Get the board at index `i`.

        Args:
            i: board index

        Returns:
            board at index `i`
        """

        return self._boards[i]

    def collapse(self) -> bool:
        """Collapse the board.

        Returns:
            whether the board collapsed
        """

        qcs = {"exist": self._qc.copy(), "symbol": self._qc.copy()}

        # change basis for symbols
        for i in range(9):
            qcs["symbol"].h(i)

        results = {}

        # run circuit
        for key, val in qcs.items():
            if self._backend.name == "aer_simulator":
                # Does optimization give more errors / remove quantum aspects?
                counts = run_circuit(val, self._backend, 1)
                results[key] = list(counts.keys())[0]
            else:
                result_string = ""
                dag = circuit_to_dag(val)
                seperated = dag.separable_circuits(remove_idle_qubits=True)
                for i in seperated:
                    qc = dag_to_circuit(i)
                    if qc.num_qubits <= 0:
                        result_string += str(0)
                        continue
                    # What does changing the optimization_level do?
                    counts = run_circuit(qc=qc, backend=self._backend, shots=2 ** (qc.num_qubits + 3))
                    # Make sure to change the three here as well...
                    bitstring = get_fair_bitstring(counts, 0.05, 2 ** (qc.num_qubits + 3))
                    result_string += str(bitstring)
                results[key] = result_string

        # update board
        for i in range(self._n_bits):
            board = i // 9
            cell = i % 9

            # position already taken
            if self._boards[board][cell] in [State.X, State.O]:
                continue

            # unblock z-rotation
            if self._boards[board][cell] == State.Z_BLOCKED:
                self._boards[board][cell] = State.EMPTY

            # set symbol if measured 1 in z-basis
            if int(results["exist"][self._n_bits - 1 - i]):
                self._boards[board][cell] = (
                    State.X if int(results["symbol"][self._n_bits - 1 - i]) else State.O
                )

        # reset cirquit
        self._qc = QuantumCircuit(self._n_bits)

        self._turns = 0
        self._touched = [set() for _ in self._boards]

        # update big board
        for i, board in enumerate(self._boards):
            self._board_wins[i] = self._check_win(board)

        return True

    def check_win(self, board: int | None = None) -> State:
        """Check whether someone has won.

        Args:
            board: board index to check. None if checking big board

        Returns:
            winner of board `board`. `State.DRAW` iff draw. `State.EMPTY` iff board has not ended
        """
        # check big board if no board selected
        if board is None:
            if self._ultimate:
                return self._check_win(self._board_wins)
            return self._board_wins[0]
        return self._board_wins[board]

    def rotate(self, board: int, cell: int, axis: Axis, angle: float, n: int) -> bool:
        """Add rotation gate to the circuit.

        If it has been `max_moves` since the last collapse, the board collapses.

        Args:
            board: board index
            cell: cell index
            axis: axis to rotate around
            angle: angle to rotate by
            n: number of qubits that are rotated this turn

        Returns:
            whether the board collapsed
        """

        assert board < len(self._boards), "Invalid board index"
        assert cell < 9, "Invalid cell index"
        assert abs(angle) <= self._max_angle, "Angle too large"
        assert n > 0, "Number of qubits must be at least 1"
        assert self._boards[board][cell] not in [State.X, State.O], (
            "Cannot rotate non-empty cell"
        )
        if axis == Axis.Z:
            assert self._boards[board][cell] != State.Z_BLOCKED, (
                "Cannot z-rotate z-blocked cell"
            )

        qubit = board * 9 + cell
        match axis:
            case Axis.X:
                self._qc.rx(angle, qubit)
            case Axis.Y:
                self._qc.ry(angle, qubit)
            case Axis.Z:
                self._qc.rz(angle, qubit)

        self._touched[board].add(cell)

        if self._moves_left_in_turn == 0:
            self._moves_left_in_turn = n

        self._moves_left_in_turn -= 1

        if self._moves_left_in_turn == 0:
            return self._increase_turns()
        return False

    def rotate_control(self, board: int, cell: int) -> None:
        """Set control qubit.

        Args:
            board: board index
            cell: cell index
        """

        assert board < len(self._boards), "Invalid board index"
        assert cell < 9, "Invalid cell index"
        assert self._boards[board][cell] not in [State.X, State.O], "Cell is not empty"

        self._c_board = board
        self._c_cell = cell

        self._boards[board][cell] = State.Z_BLOCKED

        self._moves_left_in_turn = 1
        self._touched[board].add(cell)

    def rotate_target(
        self,
        board: int,
        cell: int,
        axis: Axis,
        angle: float,
    ) -> bool:
        """Add controlled rotation gate to the circuit.

        The control qubit has to be set (`rotate_control`) before calling this function. If it has been `max_moves` since the last collapse, the board collapses.

        Args:
            board: target board index
            cell: target cell index
            axis: axis to rotate around
            angle: angle to rotate by

        Returns:
            whether the board collapsed
        """

        assert self._c_board != -1 and self._c_cell != -1, (
            "Control qubit has not been selected"
        )
        assert angle < self._max_controlled_angle, "Angle too large"
        assert self._boards[board][cell] not in [State.X, State.O], "Cell is not empty"

        c_qubit = self._c_board * 9 + self._c_cell
        t_qubit = board * 9 + cell

        match axis:
            case Axis.X:
                self._qc.crx(angle, c_qubit, t_qubit)
            case Axis.Y:
                self._qc.cry(angle, c_qubit, t_qubit)
            case Axis.Z:
                self._qc.crz(angle, c_qubit, t_qubit)

        # reset control qubit index
        self._c_board = -1
        self._c_cell = -1

        self._moves_left_in_turn = 0

        # block z-rotation
        self._boards[board][cell] = State.Z_BLOCKED

        return self._increase_turns()

    def circuit_string(self):
        """Get string representation of the circuit."""

        return self._qc.draw()

    def _increase_turns(self) -> bool:
        """Increase the number of moves.

        Collapses the board when the number of move has reached `max_moves`.

        Returns:
            whether the board collapsed
        """
        self._turns += 1
        self._touched = [set() for _ in self._boards]

        if self._turns == self._max_moves:
            self.collapse()
            return True

        return False

    def _check_win(self, board: list[State]) -> State:
        """Check whether someone has won a board.

        Args:
            board: board to check

        Returns:
            winner of the game. `State.DRAW` iff draw. `State.EMPTY` iff game has not ended.
        """
        winner = State.EMPTY

        full = True

        combinations = [
            # horisontal
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            # vertrical
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            # diagonal
            (0, 4, 8),
            (2, 4, 6),
        ]

        for comb in combinations:
            row = (board[comb[0]], board[comb[1]], board[comb[2]])

            # check if all full
            full = full and all(state != State.EMPTY for state in row)

            current_winner = State.EMPTY

            if row == (State.X, State.X, State.X):
                current_winner = State.X
            elif row == (State.O, State.O, State.O):
                current_winner = State.O

            if current_winner != State.EMPTY:
                if winner == State.EMPTY:
                    winner = current_winner
                elif winner != current_winner:
                    return State.DRAW

        if winner == State.EMPTY:
            return State.DRAW if full else State.EMPTY
        return winner
