from enum import Enum
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime.fake_provider.fake_backend import FakeBackendV2
from qiskit_aer import AerSimulator
from collections.abc import Callable
import math

MAX_ANGLE = math.pi / 2
MAX_CONTROLLED_ANGLE = math.pi
MAX_MOVES = 10


class State(Enum):
    """State of a cell on board, or the winner of a game."""

    EMPTY = 0
    X = 1
    O = 2
    DRAW = 3

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


class Axis(Enum):
    """Rotation axis."""

    X = 0
    Y = 1
    Z = 2


def print_board(board: list[State]):
    """Print the board.

    Args:
        board: board to print
    """

    print("\n")
    print(f"  {board[0]} | {board[1]} | {board[2]}")
    print(" ---\u00b9---\u00b2---\u00b3")
    print(f"  {board[3]} | {board[4]} | {board[5]}")
    print(" ---\u2074---\u2075---\u2076")
    print(f"  {board[6]} | {board[7]} | {board[8]}")
    print("    \u2077   \u2078   \u2079")
    print("\n")


def get_int(min: int, max: int, prompt: str, error: str) -> int:
    """Get integer from stdin in range [`min`, `max`].

    Args:
        min: min. value
        max: max. value
        prompt: text to display when asking for input
        error: text to display when invalid input

    Returns:
        integer in range [`min`, `max`]
    """

    while True:
        try:
            val = int(input(prompt))
            if val < min or val > max:
                raise ValueError
            return val
        except ValueError:
            print(error)


def get_float(min: float, max: float, prompt: str, error: str) -> float:
    """Get float from stdin in range [`min`, `max`].

    Args:
        min: min. value
        max: max. value
        prompt: text to display when asking for input
        error: text to display when invalid input

    Returns:
        float in range [`min`, `max`]
    """

    while True:
        try:
            val = float(input(prompt))
            if val < min or val > max:
                raise ValueError
            return val
        except ValueError:
            print(error)


def get_valid_position(board: list[State]) -> int:
    """Get cell index from stdin that has not been taken on `board`.


    Args:
        board: board

    Returns:
        cell index
    """

    while True:
        pos = get_int(
            1,
            9,
            "Enter cell number [1-9]: ",
            "The cell number must be in the range [1,9].",
        )

        # indices start from 0
        pos -= 1

        if board[pos] == State.EMPTY:
            return pos
        else:
            print("This cell already has a value.")


def rotate(board: list[State], qc: QuantumCircuit, axis: Axis) -> None:
    """Move for rotating a qubit around `axis`.


    Args:
        board: board
        qc: quantum circuit
        axis: axis to rotate around
    """

    max_n = min(2, count_empty_cells(board))

    # get number of qubits to rotate
    n = get_int(
        1,
        max_n,
        f"Number of qubits to rotate (max. {max_n}): ",
        f"Number of qubits can be at most {max_n}.",
    )

    remaining_rotation = MAX_ANGLE

    used = set()

    for _ in range(n):
        # get position
        pos = 0
        while True:
            pos = get_valid_position(board)
            if pos in used:
                print("You already rotated this qubit.")
            else:
                break

        # get angle
        angle = get_float(
            -remaining_rotation,
            remaining_rotation,
            f"Enter angle to rotate by (max. {remaining_rotation}): ",
            f"The angle must be between {-remaining_rotation} and {remaining_rotation}.",
        )

        remaining_rotation -= abs(angle)

        # add rotation gate
        match axis:
            case Axis.X:
                qc.rx(angle, pos)
            case Axis.Y:
                qc.ry(angle, pos)
            case Axis.Z:
                qc.rz(angle, pos)

        used.add(pos)


def rotate_controlled(board: list[State], qc: QuantumCircuit, axis: Axis) -> None:
    """Move for controlled rotation.

    Args:
        board: board
        qc: quantum circuit
        axis: axis to rotate around
    """

    # get control and target
    print("Choose control qubit.")
    control = get_valid_position(board)
    print("Choose target qubit.")
    target = 0
    while True:
        target = get_valid_position(board)
        if target == control:
            print("Target cannot be the same as control.")
        else:
            break

    # get angle
    angle = get_float(
        -MAX_CONTROLLED_ANGLE,
        MAX_CONTROLLED_ANGLE,
        f"Enter angle to rotate by (max. {MAX_CONTROLLED_ANGLE}): ",
        f"The angle must be between {-MAX_CONTROLLED_ANGLE} and {MAX_CONTROLLED_ANGLE}.",
    )

    # add controlled rotation gate
    match axis:
        case Axis.X:
            qc.crx(angle, control, target)
        case Axis.Y:
            qc.cry(angle, control, target)
        case Axis.Z:
            qc.crz(angle, control, target)


def collapse(
    board: list[State], qc: QuantumCircuit, backend: AerSimulator | FakeBackendV2
) -> None:
    """Measure the quantum circuit `qc`.

    Update `board` according to the results measured.

    Args:
        board: board to update
        qc: quantum circuit to measure
    """

    qcs = {"exist": qc.copy(), "symbol": qc.copy()}

    # change basis for symbols
    for i in range(9):
        qcs["symbol"].h(i)

    results = {}

    # run circuit
    for key, val in qcs.items():
        val.measure_all()
        transpiled_qc = transpile(val, backend)
        job = backend.run(transpiled_qc, shots=1)
        result = job.result()
        counts = result.get_counts()

        results[key] = list(counts.keys())[0]

    # update board
    for i in range(9):
        # position already taken
        if board[i] != State.EMPTY:
            continue

        # set symbol if measured 1 in z-basis
        if int(results["exist"][8 - i]):
            board[i] = State.X if int(results["symbol"][8 - i]) else State.O

    print("Collapsed board.")


def check_win(board: list[State]) -> State:
    """Check whether someone has won.

    Args:
        board: boards to check

    Returns:
        winner of the game. `State.Draw` iff draw. `State.Empty` iff game has not ended.
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


def count_empty_cells(board: list[State]) -> int:
    return sum([cell == State.EMPTY for cell in board])


class MoveType:
    """Class representing a move type.

    Attributes:
        description: description of the move type
        min_empty: min. number of empty cells required for the move type
        move: function to call when making the move
    """

    def __init__(
        self,
        description: str,
        min_empty: int,
        move: Callable[[list[State], QuantumCircuit], bool],
    ) -> None:
        """Create a move type object.

        Args:
            description: description of the move type
            min_empty: min. number of empty cells required for the move type
            move: function to call when making the move. the function should return whether the board collapsed
        """

        self._description = description
        self._min_empty = min_empty
        self._move = move

    @property
    def description(self) -> str:
        return self._description

    @property
    def min_empty(self) -> int:
        return self._min_empty

    @property
    def move(self) -> Callable[[list[State], QuantumCircuit], bool]:
        return self._move


def main():
    """Game loop."""

    # set backend
    backend = AerSimulator()

    # initialise move types
    move_types = {
        "x": MoveType(
            "rotate around x-axis", 1, lambda b, qc: bool(rotate(b, qc, Axis.X))
        ),
        "z": MoveType(
            "rotate around z-axis", 1, lambda b, qc: bool(rotate(b, qc, Axis.Z))
        ),
        "cy": MoveType(
            "controlled rotation around y-axis",
            2,
            lambda b, qc: bool(rotate_controlled(b, qc, Axis.Y)),
        ),
        "c": MoveType(
            "collapse", 1, lambda b, qc: bool(collapse(b, qc, backend)) or True
        ),
    }

    turn = State.X
    moves = 0
    empty = 9

    board = [State.EMPTY for _ in range(9)]
    qc = QuantumCircuit(9, 9)

    while True:
        print_board(board)
        print(f"It's {turn}'s turn.")

        # create prompt
        prompt = "Select move type: "
        for i, key in enumerate(move_types):
            prompt += f"{move_types[key].description} [{key}]"
            if i < len(move_types) - 1:
                prompt += " | "
        prompt += ": "

        # get move type
        move_type = None

        while True:
            move_type = input(prompt)
            if move_type not in move_types.keys():
                print("Invalid move type!")
            else:
                break

        collapsed = move_types[move_type].move(board, qc)

        moves += 1

        # draw circuit
        if not collapsed:
            print(qc.draw())

        # collapse when MAX_MOVES since last collapse
        if not collapsed and moves == MAX_MOVES:
            collapse(board, qc, backend)
            collapsed = True

        # check win if collapsed
        if collapsed:
            winner = check_win(board)
            # game ended
            if winner != State.EMPTY:
                print_board(board)

                if winner == State.DRAW:
                    print("It's a draw.")
                else:
                    print(f"{winner} has won!")
                break

            # reset circuit
            qc = QuantumCircuit(9, 9)

            # get the number of empty cells
            empty = count_empty_cells(board)

            # remove unavailable moves
            move_types = {
                key: val for key, val in move_types.items() if empty >= val.min_empty
            }

            moves = 0

        turn = State.X if turn == State.O else State.O


if __name__ == "__main__":
    main()
