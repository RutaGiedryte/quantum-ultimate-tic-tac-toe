from tkinter import Widget, ttk


class MoveInfo:
    """Class represeting a move type.
    
    Attributes:
        key: move type key
        text: text for displaying the move type
        min_empty: min. number of empty cells required for the move
        callback: function to call when selecting the move type
    """

    def __init__(self, key: str, text: str, min_empty: int, callback) -> None:
        """Create move info.
        
        Args:
            key: move type key
            text: text for displaying the mmove type
            min_empty: min. number of empty cells required for the move
            callback: function to call when selecting the move type
        """

        self._key = key
        self._text = text
        self._min_empty = min_empty
        self._callback = callback

    @property
    def key(self) -> str:
        return self._key

    @property
    def text(self) -> str:
        return self._text

    @property
    def min_empty(self) -> int:
        return self._min_empty

    @property
    def callback(self):
        return self._callback


class MoveSelection(ttk.Frame):
    """Widget for selecting the move type."""

    def __init__(self, parent: Widget, moves: list[MoveInfo], cols: int, **kw) -> None:
        """Create move selection widget.
        
        Args:
            parent: parent widget
            moves: list of possible moves
            cols: number of columns to use for displaying the buttons
            kw: keyword arguments for `ttk.Frame`
        """

        super().__init__(parent, **kw)

        # create info label
        ttk.Label(self, text="Select move", padding="0 0 0 5").grid(
            row=0, column=0, columnspan=cols
        )

        # button width in number of chars
        width = max([len(move.text) for move in moves])

        # create buttons
        self._buttons = {
            info.key: ttk.Button(
                self, text=info.text, command=info.callback, width=width
            )
            for info in moves
        }

        # set positions
        for i, key in enumerate(self._buttons):
            row = i // cols + 1
            col = i % cols
            self._buttons[key].grid(row=row, column=col)
