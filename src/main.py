from tkinter import Tk
from gui.app import App


def main():
    root = Tk()
    root.title("Quantum Tic-Tac-Toe")
    root.geometry("500x500")

    # quit with escape
    root.bind("<Escape>", lambda x: root.destroy())

    App(root, ultimate=False)

    root.mainloop()


if __name__ == "__main__":
    main()
