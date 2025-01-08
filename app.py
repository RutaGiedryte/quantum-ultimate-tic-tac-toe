from tkinter import *
from tkinter import ttk
from enum import Enum

class MoveType(Enum):
    CLASSICAL = 0
    QUANTUM = 1

    def __str__(self) -> str:
        """Get string representation of the move type."""

        match self:
            case MoveType.CLASSICAL:
                return "classical"
            case MoveType.QUANTUM:
                return "quantum"


class TicTacToe:
    def __init__(self, root: Tk) -> None:
        """Create GUI widgets."""

        # window title
        root.title("Quantum Tic-Tac-Toe")

        # create main frame
        mainframe = ttk.Frame(root)
        mainframe.grid(row=0, column=0)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        # create info label
        self._info_text = StringVar()

        info_label = ttk.Label(mainframe, textvariable=self._info_text)
        info_label.grid(row=0, column=0)

        # create board frame
        boardframe = ttk.Frame(mainframe, padding="0 25")
        boardframe.grid(row=1, column=0)

        # create cells
        cellframes = [ttk.Frame(boardframe, width=100, height=100) for i in range(9)]
        for i in range(9):
            cellframes[i].grid(row=i//3, column=i%3)
            cellframes[i].columnconfigure(0, weight=1)
            cellframes[i].rowconfigure(0, weight=1)
            cellframes[i].grid_propagate(0)

        self._cell_buttons = [ttk.Button(cellframes[i], command=lambda i=i: self._click_cell(i), state="disabled") for i in range(9)]
        for cell_button in self._cell_buttons:
            cell_button.grid(row=0, column=0, sticky=(N, W, S, E))

        # create move type frame
        self._move_type_frame = ttk.Frame(mainframe)
        self._move_type_frame.grid(row=2, column=0, sticky=S)

        # create move type buttons
        self._classical_button = ttk.Button(self._move_type_frame, text="Classical", command=lambda: self._click_move_type(MoveType.CLASSICAL))
        self._classical_button.grid(row=0, column=0)

        self._quantum_button = ttk.Button(self._move_type_frame, text="Quantum", command=lambda: self._click_move_type(MoveType.QUANTUM))
        self._quantum_button.grid(row=0, column=2)

        # create reset button
        self._reset_button = ttk.Button(mainframe, text="Play again")
        self._reset_button.grid(row=3, column=0)
        self._reset_button.grid_forget()

        # quit with escape
        root.bind("<Escape>", lambda x: root.destroy())

    def _reset_widgets(self) -> None:
        """Reset widgets to their default state."""

        # reset cell buttons
        for cell_button in self._cell_buttons:
            cell_button["state"] = "disabled"
            cell_button["text"] = ""

        # reset move type buttons
        self._classical_button["state"] = "normal"
        self._quantum_button["state"] = "normal"

        # hide reset button
        self._reset_button.grid_forget()
        # display move type frame
        self._move_type_frame.grid()

    def _click_cell(self, i: int) -> None:
        """Callback function for clicking on cell `i`

        Args:
            i: cell index 
        """

        print(f"Clicked cell {i}")
        #Todo: cell click logic

    def _click_move_type(self, type: MoveType) -> None:
        """Callback function for clicking on move type button.
        
        Args:
            type: move type
        """

        print(f"Chose {type} move")
        #Todo: move type click logic

from time import sleep
def main():
    root = Tk()
    root.geometry("500x500")
    ttt = TicTacToe(root)
    root.mainloop()

if __name__ == "__main__":
    main()
