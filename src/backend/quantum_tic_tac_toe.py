import random

from qiskit import QuantumCircuit, generate_preset_pass_manager
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.transpiler import CouplingMap
from qiskit.providers import BackendV2
from qiskit_ibm_runtime import SamplerV2
from backend.math import rotate_vec
from backend.enums import State, Move, Axis


def fully_connected_81_coupling():
    """
    Build a CouplingMap for 81 qubits, fully connected,
    so we skip 'CircuitTooWideForTarget' issues and routing constraints.
    """

    edges = []
    for i in range(81):
        for j in range(81):
            if i != j:
                edges.append((i, j))

    return CouplingMap(edges)


def get_fair_bitstring(counts, threshold, total) -> str:
    """
    Remove the noise from a job result without losing the quantum aspects.

    :param counts: The result to process
    :param threshold: The noise level threshold, values under this threshold are discarded
    :param total: The total amount of shots
    :return: Returns a bitstring as if the circuit was run 1 time without noise.
    """
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
    """
    Run a given quantum circuit on the provided backend with the proper amount of shots.

    :param qc:  the quantum circuit to run
    :param backend: the backend to run on
    :param shots:  the amount of shots
    :return: returns the counts variable form the job result.
    """
    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
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
        self._n_boards = 9 if ultimate else 1

        self._backend = backend

        if self._backend.name == "aer_simulator_matrix_product_state":
            self._qc = QuantumCircuit(self._n_bits, self._n_bits)
        else:
            self._qc = QuantumCircuit(self._n_bits)

        self._max_angle = max_angle
        self._max_controlled_angle = max_controlled_angle
        self._max_turns = max_turns

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
        self._boards = [[State.EMPTY for _ in range(9)] for _ in range(self._n_boards)]
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
        # cells to measure
        self._active_cells = [set() for _ in range(self._n_boards)]
        # entangled boards. board_id: set of entangled boards
        self._entangled_boards = {i: set() for i in range(self._n_boards)}
        # available boards
        self._available_boards = {i for i in range(self._n_boards)}
        # state vectors
        self._state_vectors = [
            [[0, 0, 1] for _ in range(9)] for _ in range(self._n_boards)
        ]

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

        # filter out boards that cannot be used with current move
        return list(
            {i for i in self._available_boards if self.count_avialable_cells(i, move)}
        )

    def available_cells(self, board: int, move: Move) -> list[int]:
        """Get the indices of available cells on board `board` for `move`.

        Args:
            board: board index
            move: move to check

        Returns:
            list of available cells on board `board`
        """

        allowed = [State.EMPTY]
        # allow entangled cells if move is not z-rotation
        if move != Move.RZ:
            allowed.append(State.ENTANGLED)

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
            i: board index. -1 if getting big board state

        Returns:
            board at index `i`
        """

        if i == -1:
            return self._board_wins

        return self._boards[i]

    def collapse(self, board: int | None = None) -> set[int]:
        """Collapse `board`.

        Args:
            board: board index. None if collapsing all boards

        Returns:
            set of collapsed board indices
        """

        qcs = {"exist": self._qc.copy(), "symbol": self._qc.copy()}

        if board is None:
            boards = {i for i in range(self._n_boards)}
        else:
            # get boards to collapse
            boards = set()
            to_check = [board]
            while len(to_check):
                b = to_check.pop()

                if b in boards:
                    continue
                boards.add(b)

                for entangled_board in self._entangled_boards[b]:
                    to_check.append(entangled_board)
                self._entangled_boards[b].clear()

        results = {}

        cmap = fully_connected_81_coupling()

        if self._backend.name != "aer_simulator_matrix_product_state":
            for i in range(qcs['symbol'].num_qubits):
                qcs['symbol'].h(i)
            for b, cells in enumerate(self._active_cells):
                if b not in boards:
                    continue
                cells.clear()
        else:
            # measure only active cells
            for b, cells in enumerate(self._active_cells):
                if b not in boards:
                    continue
                for c in cells:
                    index = b * 9 + c
                    qcs["exist"].measure(index, index)
                    qcs["symbol"].h(index)
                    qcs["symbol"].measure(index, index)
                cells.clear()

        # run circuit
        for key, val in qcs.items():
            if self._backend.name == "aer_simulator_matrix_product_state":
                pm = generate_preset_pass_manager(backend=self._backend, optimization_level=3, coupling_map=cmap)
                isa_circuit = pm.run(val)
                sampler = SamplerV2(mode=self._backend)
                job = sampler.run([isa_circuit], shots=1)
                result = job.result()
                try:
                    counts = getattr(result[0].data, val.cregs[0].name, None).get_counts()  # type: ignore
                except AttributeError:
                    raise SystemError("Empty or invalid result..")  # What after this?

                # There is only one shot...?
                most_populated_string = max(counts, key=counts.get)
                # print(most_populated_string)
                results[key] = most_populated_string
            else:
                # Maybe optimize that we only run the x-basis for the qubits that are 1 in the z-basis?
                result_string = ""
                dag = circuit_to_dag(val)
                seperated = dag.separable_circuits(remove_idle_qubits=True)
                for i in range(len(seperated)):
                    qc = dag_to_circuit(seperated[i])
                    qc.measure_active()
                    if qc.num_qubits <= 0:
                        result_string += str(0)
                        continue
                    # We can change the amount of shots if we want...
                    counts = run_circuit(qc=qc, backend=self._backend, shots=2 ** (qc.num_qubits + 3))
                    bitstring = get_fair_bitstring(counts, 0.05, 2 ** (qc.num_qubits + 3))
                    result_string += str(bitstring)
                results[key] = result_string

        # update board
        for i in range(self._n_bits):
            board = i // 9

            if board not in boards:
                continue

            cell = i % 9

            # reset state vector
            self._state_vectors[board][cell] = [0, 0, 1]

            # position already taken
            if self._boards[board][cell] in [State.X, State.O]:
                continue

            # unmark cell as entangled
            if self._boards[board][cell] == State.ENTANGLED:
                self._boards[board][cell] = State.EMPTY

            # set symbol if measured 1 in z-basis
            if self._backend.name == "aer_simulator_matrix_product_state":
                if int(results["exist"][self._n_bits - 1 - i]):
                    self._boards[board][cell] = (
                        State.X if int(results["symbol"][self._n_bits - 1 - i]) else State.O
                    )
            else:
                if int(results["exist"][i]):
                    self._boards[board][cell] = (
                        State.X if int(results["symbol"][i]) else State.O
                    )

            # reset measured qubit
            self._qc.reset(i)

        # reset whole circuit if collapsed whole board
        if board is None:
            if self._backend.name == "aer_simulator_matrix_product_state":
                self._qc = QuantumCircuit(self._n_bits, self._n_bits)
            else:
                self._qc = QuantumCircuit(self._n_bits)

        self._touched = [set() for _ in self._boards]

        # update big board
        for i, b in enumerate(self._boards):
            self._board_wins[i] = self._check_win(b)

        self._turns = -1
        self._increase_turns()

        return boards

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

    def rotate(
        self, board: int, cell: int, axis: Axis, angle: float, n: int
    ) -> set[int]:
        """Add rotation gate to the circuit.

        If it has been `max_moves` since the last collapse, the board collapses.

        Args:
            board: board index
            cell: cell index
            axis: axis to rotate around
            angle: angle to rotate by
            n: number of qubits that are rotated this turn

        Returns:
            set of collapsed board indices
        """

        assert board < len(self._boards), "Invalid board index"
        assert cell < 9, "Invalid cell index"
        assert abs(angle) <= self._max_angle, "Angle too large"
        assert n > 0, "Number of qubits must be at least 1"
        assert self._boards[board][cell] not in [State.X, State.O], (
            "Cannot rotate non-empty cell"
        )
        if axis == Axis.Z:
            assert self._boards[board][cell] != State.ENTANGLED, (
                "Cannot z-rotate entangled cell"
            )

        qubit = board * 9 + cell
        match axis:
            case Axis.X:
                self._qc.rx(angle, qubit)
            case Axis.Y:
                self._qc.ry(angle, qubit)
            case Axis.Z:
                self._qc.rz(angle, qubit)

        self._touch_cell(board, cell)

        if self._moves_left_in_turn == 0:
            self._moves_left_in_turn = n

        self._moves_left_in_turn -= 1

        # rotate state vector
        self._state_vectors[board][cell] = rotate_vec(
            self._state_vectors[board][cell], angle, axis
        )

        if self._moves_left_in_turn == 0:
            return self._increase_turns()
        return set()

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

        self._boards[board][cell] = State.ENTANGLED

        self._moves_left_in_turn = 1

        self._touch_cell(board, cell)

    def rotate_target(
        self,
        board: int,
        cell: int,
        axis: Axis,
        angle: float,
    ) -> set[int]:
        """Add controlled rotation gate to the circuit.

        The control qubit has to be set (`rotate_control`) before calling this function. If it has been `max_moves` since the last collapse, the board collapses.

        Args:
            board: target board index
            cell: target cell index
            axis: axis to rotate around
            angle: angle to rotate by

        Returns:
            set of collapsed board indices
        """

        assert self._c_board != -1 and self._c_cell != -1, (
            "Control qubit has not been selected"
        )
        assert angle <= self._max_controlled_angle, "Angle too large"
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

        # add to entangled boards
        self._entangled_boards[board].add(self._c_board)
        self._entangled_boards[self._c_board].add(board)

        # reset control qubit index
        self._c_board = -1
        self._c_cell = -1

        self._moves_left_in_turn = 0

        # mark cell as entangled
        self._boards[board][cell] = State.ENTANGLED

        self._touch_cell(board, cell)

        # rotate state vector
        self._state_vectors[board][cell] = rotate_vec(
            self._state_vectors[board][cell], angle, axis
        )

        return self._increase_turns()

    def get_statevector(self, board, cell) -> list[int]:
        """Get the state vector of `cell` on `board`.

        Args:
            board: board index
            cell: cell index

        Returns:
            state vector
        """

        if self._boards[board][cell] == State.ENTANGLED:
            return [0, 0, 0]

        return self._state_vectors[board][cell]

    def circuit_string(self):
        """Get string representation of the circuit."""

        return self._qc.draw()

    def _touch_cell(self, board: int, cell: int) -> None:
        """Add cell to list of active cells.

        Removes the board from the list of available boards if there is more than one board available.

        Args:
            board: board index
            cell: cell index
        """

        self._active_cells[board].add(cell)
        self._touched[board].add(cell)
        if len(self._available_boards) != 1:
            self._available_boards.remove(board)

    def _increase_turns(self) -> set[int]:
        """Increase the number of moves.

        Collapses the board when the number of move has reached `max_moves`.
        Sets available boards based on touched cells.

        Returns:
            set of collapsed board indices
        """

        self._turns += 1

        # collapse boards if reached max turns
        collapsed = set()
        if self._turns == self._max_turns:
            collapsed = self.collapse()

        # get available boards
        self._available_boards = {
            cell
            for touched in self._touched
            for cell in touched
            if cell == 0 or self._ultimate
        }

        # filter out finished boards
        finished = {
            i for i, state in enumerate(self._board_wins) if state != State.EMPTY
        }

        self._available_boards = self._available_boards.difference(finished)

        # enable all unfinished boards if no boards available
        if len(self._available_boards) == 0:
            self._available_boards = {i for i in range(self._n_boards)}.difference(
                finished
            )

        self._touched = [set() for _ in self._boards]

        return collapsed

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
