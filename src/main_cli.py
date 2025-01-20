import math
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke
from qiskit_ibm_runtime import QiskitRuntimeService
from backend.quantum_tic_tac_toe import Axis, QuantumTicTacToe, State, Move
from qiskit_aer import AerSimulator
from backend.parser import create_parser


def print_board(board: list[State]):
    """Print the board.

    Args:
        board: board to print
    """

    assert len(board) == 9, "Not a valid board"

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


def get_valid_position(game: QuantumTicTacToe, board: int, move: Move) -> int:
    """Get cell index for `board` from stdin that is allowed for `move`.

    Args:
        game: game object
        board: board index
        move: move

    Returns:
        cell index
    """

    available = game.available_cells(board, move)

    # list with 1-based indexing
    available_from_one = [i + 1 for i in available]

    while True:
        pos = get_int(
            1,
            9,
            f"Enter cell number {available_from_one}: ",
            f"The cell number must be in {available_from_one}.",
        )

        # indices start from 0
        pos -= 1

        if pos in available:
            return pos
        else:
            print("You cannot use this cell.")


def rotate(game: QuantumTicTacToe, axis: Axis) -> bool:
    """Move for rotating a qubit around `axis`.

    Args:
        game: game object
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

    max_n = min(2, game.count_avialable_cells(0, move))

    # get number of qubits to rotate
    n = get_int(
        1,
        max_n,
        f"Number of qubits to rotate (max. {max_n}): ",
        f"Number of qubits can be at most {max_n}.",
    )

    remaining_rotation = game.max_angle

    used = set()

    collapsed = set()

    for _ in range(n):
        # get position
        pos = get_valid_position(game, 0, move)

        # get angle
        angle = get_float(
            -remaining_rotation,
            remaining_rotation,
            f"Enter angle to rotate by (max. {remaining_rotation}): ",
            f"The angle must be between {-remaining_rotation} and {remaining_rotation}.",
        )

        remaining_rotation -= abs(angle)

        # add rotation gate
        collapsed.update(game.rotate(0, pos, axis, angle, n))

        used.add(pos)

    return len(collapsed) != 0


def rotate_controlled(game: QuantumTicTacToe, axis: Axis) -> bool:
    """Move for controlled rotation.

    Args:
        game: game object
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
    control = get_valid_position(game, 0, move)

    # set control qubit
    game.rotate_control(0, control)

    # get target qubit index
    print("Choose target qubit.")
    target = get_valid_position(game, 0, move)

    # get angle
    angle = get_float(
        -game.max_controlled_angle,
        game.max_controlled_angle,
        f"Enter angle to rotate by (max. {game.max_controlled_angle}): ",
        f"The angle must be between {-game.max_controlled_angle} and {game.max_controlled_angle}.",
    )

    # set target qubit
    return len(game.rotate_target(0, target, axis, angle)) != 0


def qttt_cli(ultimate: bool, moves: list[Move], backend):
    """Game loop.

    Args:
        ultimate: whether to create ultimate version
        moves: list of allowed moves
        backend: backend used for running the quantum circuit
    """

    # initialise move types
    move_callbacks = {
        Move.RX: lambda game: rotate(game, Axis.X),
        Move.RY: lambda game: rotate(game, Axis.Y),
        Move.RZ: lambda game: rotate(game, Axis.Z),
        Move.CRX: lambda game: rotate_controlled(game, Axis.X),
        Move.CRY: lambda game: rotate_controlled(game, Axis.Y),
        Move.CRZ: lambda game: rotate_controlled(game, Axis.Z),
        Move.COLLAPSE: lambda game: game.collapse(),
    }

    turn = State.X

    game = QuantumTicTacToe(backend, math.pi / 2, math.pi, 10, ultimate)

    while True:
        print_board(game.board(0))
        print(f"It's {turn}'s turn.")

        available_moves = {move.key: move for move in game.available_moves(moves)}

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

        collapsed = move_callbacks[available_moves[move_str]](game)

        # draw circuit
        if not collapsed:
            print(game.circuit_string())

        # check win if collapsed
        if collapsed:
            print("Board collapsed")
            winner = game.check_win(0)
            # game ended
            if winner != State.EMPTY:
                print_board(game.board(0))

                if winner == State.DRAW:
                    print("It's a draw.")
                else:
                    print(f"{winner} has won!")
                break

        turn = State.X if turn == State.O else State.O


def main():
    parser = create_parser("qttt-cli")
    args = parser.parse_args()

    service = None if args.simulate else QiskitRuntimeService()

    moves = [Move.RY, Move.RZ, Move.CRX, Move.COLLAPSE]

    ultimate = args.ultimate

    # set backend
    if service:
        backend = service.least_busy(
            simulator=False, operational=True, min_num_qubits=81 if ultimate else 9
        )
    else:
        # backend = FakeSherbrooke()
        backend = AerSimulator()  # use non-noisy simulation

    qttt_cli(ultimate, moves, backend)


if __name__ == "__main__":
    main()
