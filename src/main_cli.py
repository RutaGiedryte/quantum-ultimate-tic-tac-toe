from qiskit_aer import AerSimulator
from collections.abc import Callable
import math

from backend.quantum_tic_tac_toe import Axis, QuantumTicTacToe, State


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


def get_valid_position(board: list[State]) -> int:
    """Get cell index from stdin that has not been taken on `board`.

    Args:
        board: board

    Returns:
        cell index
    """

    assert len(board) == 9, "Not a valid board"

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


def rotate(game: QuantumTicTacToe, axis: Axis) -> bool:
    """Move for rotating a qubit around `axis`.

    Args:
        game: game object
        axis: axis to rotate around

    Returns:
        whether the board collapsed
    """

    max_n = min(2, game.count_empty_cells(0))

    # get number of qubits to rotate
    n = get_int(
        1,
        max_n,
        f"Number of qubits to rotate (max. {max_n}): ",
        f"Number of qubits can be at most {max_n}.",
    )

    remaining_rotation = game.max_angle

    used = set()

    collapsed = False

    for _ in range(n):
        # get position
        pos = 0
        while True:
            pos = get_valid_position(game.board(0))
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
        collapsed = collapsed or game.rotate(0, pos, axis, angle, n)

        used.add(pos)

    return collapsed


def rotate_controlled(game: QuantumTicTacToe, axis: Axis) -> bool:
    """Move for controlled rotation.

    Args:
        game: game object
        axis: axis to rotate around

    Returns:
        whether the board collapsed
    """

    # get control and target
    print("Choose control qubit.")
    control = get_valid_position(game.board(0))
    print("Choose target qubit.")
    target = 0
    while True:
        target = get_valid_position(game.board(0))
        if target == control:
            print("Target cannot be the same as control.")
        else:
            break

    # get angle
    angle = get_float(
        -game.max_controlled_angle,
        game.max_controlled_angle,
        f"Enter angle to rotate by (max. {game.max_controlled_angle}): ",
        f"The angle must be between {-game.max_controlled_angle} and {game.max_controlled_angle}.",
    )

    # add controlled rotation gate
    game.rotate_control(0, control)
    return game.rotate_target(0, target, axis, angle)


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
        move: Callable[[QuantumTicTacToe], bool],
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
    def move(self) -> Callable[[QuantumTicTacToe], bool]:
        return self._move


def qtt_cli(ultimate: bool):
    """Game loop.

    Args:
        ultimate: whether to create ultimate version
    """

    # set backend
    backend = AerSimulator()

    # initialise move types
    move_types = {
        "x": MoveType("rotate around x-axis", 1, lambda game: rotate(game, Axis.X)),
        "z": MoveType("rotate around z-axis", 1, lambda game: rotate(game, Axis.Z)),
        "cy": MoveType(
            "controlled rotation around y-axis",
            2,
            lambda game: rotate_controlled(game, Axis.Y),
        ),
        "c": MoveType("collapse", 1, lambda game: game.collapse()),
    }

    turn = State.X
    empty = 9

    game = QuantumTicTacToe(backend, math.pi / 2, math.pi, 10, ultimate)

    while True:
        print_board(game.board(0))
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

        collapsed = move_types[move_type].move(game)

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

            # get the number of empty cells
            empty = game.count_empty_cells(0)

            # remove unavailable moves
            move_types = {
                key: val for key, val in move_types.items() if empty >= val.min_empty
            }

        turn = State.X if turn == State.O else State.O


def main():
    qtt_cli(False)


if __name__ == "__main__":
    main()
