from tkinter import Tk

from qiskit_ibm_runtime import QiskitRuntimeService

from gui.app import App


def main(service=None):
    root = Tk()
    root.title("Quantum Tic-Tac-Toe")
    root.geometry("700x700")

    # quit with escape
    root.bind("<Escape>", lambda x: root.destroy())

    App(root, ultimate=False, service=service)

    root.mainloop()


if __name__ == "__main__":
    simulate = True
    if simulate:
        main()
    else:
        main(QiskitRuntimeService())
