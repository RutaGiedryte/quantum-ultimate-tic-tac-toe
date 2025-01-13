from enum import Enum
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime.fake_provider import FakeAlmadenV2
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

    # get number of qubits to rotate
    n = get_int(
        1, 2, "Number of qubits to rotate [1-2]: ", "Number of qubits can be at most 2."
    )

    remaining_rotation = MAX_ANGLE

    for _ in range(n):
        # get position
        pos = get_valid_position(board)

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


def collapse(board: list[State], qc: QuantumCircuit) -> None:
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

    backend = FakeAlmadenV2()

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
        # position already taeken
        if board[i] != State.EMPTY:
            continue

        # set symbol if measured 1 in z-basis
        if int(results["exist"][8 - i]):
            board[i] = State.X if int(results["symbol"][8 - i]) else State.O

    # reset qubits
    qc.reset(range(9))

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


def main():
    """Game loop."""

    move_types = {"x", "z", "cy", "c"}

    turn = State.X
    moves = 0

    board = [State.EMPTY for _ in range(9)]
    qc = QuantumCircuit(9, 9)

    while True:
        print_board(board)
        print(f"It's {turn}'s turn.")

        # get move type
        move_type = None
        while True:
            move_type = input(
                "Select move type: rotate around x-axis [x] | rotate around z-axis [z] | controlled rotation around y-axis [cy] | collapse [c]: "
            )
            if move_type not in move_types:
                print("Invalid move type!")

            break

        collapsed = False

        match move_type:
            case "x":
                rotate(board, qc, Axis.X)
            case "z":
                rotate(board, qc, Axis.Z)
            case "cy":
                rotate_controlled(board, qc, Axis.Y)
            case "c":
                collapse(board, qc)
                collapsed = True
                moves = -1

        moves += 1

        # draw circuit
        print(qc.draw())

        # collapse when MAX_MOVES since last collapse
        if moves == MAX_MOVES:
            collapse(board, qc)
            collapsed = True
            moves = 0

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

        turn = State.X if turn == State.O else State.O


if __name__ == "__main__":
    main()
