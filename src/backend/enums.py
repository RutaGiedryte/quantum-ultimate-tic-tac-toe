from enum import Enum
from typing import Any


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
    ENTANGLED = 4

    def __str__(self) -> str:
        match self:
            case State.EMPTY:
                return " "
            case State.X:
                return "X"
            case State.O:
                return "O"
            case State.DRAW:
                return "?"
            case State.ENTANGLED:
                return "e"
