from tkinter import Widget, ttk
from backend.quantum_tic_tac_toe import Move
from collections.abc import Callable


class MoveSelection(ttk.Frame):
    """Widget for selecting the move type."""

    def __init__(
        self, parent: Widget, moves: dict[Move, Callable[[], None]], cols: int, **kw
    ) -> None:
        """Create move selection widget.

        Args:
            parent: parent widget
            moves: dictionary of possible moves and their callback functions (Move: Callback)
            cols: number of columns to use for displaying the buttons
            kw: keyword arguments for `ttk.Frame`
        """

        super().__init__(parent, **kw)

        # create info label
        ttk.Label(self, text="Select move", padding="0 0 0 5").grid(
            row=0, column=0, columnspan=cols
        )

        # button width in number of chars
        width = max([len(move.description) for move in moves.keys()])

        # create buttons
        self._buttons = {
            move: ttk.Button(self, text=move.description, command=callback, width=width)
            for move, callback in moves.items()
        }

        # set positions
        for i, key in enumerate(self._buttons):
            row = i // cols + 1
            col = i % cols
            self._buttons[key].grid(row=row, column=col)

    def enable(self, moves: set[Move]) -> None:
        """Enable move buttons.

        Args:
            moves: moves to enable
        """

        for move, button in self._buttons.items():
            if move in moves:
                button["state"] = "normal"
            else:
                button["state"] = "disabled"
