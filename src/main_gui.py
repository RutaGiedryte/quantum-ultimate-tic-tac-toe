from tkinter import Tk
from gui.app import App
from backend.quantum_tic_tac_toe import Move
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke
from qiskit_ibm_runtime import QiskitRuntimeService
from backend.parser import create_parser


def main():
    parser = create_parser("qttt")
    args = parser.parse_args()

    root = Tk()
    root.title("Quantum Tic-Tac-Toe")
    root.geometry("700x700")
    root.minsize(500, 500)

    # quit with escape
    root.bind("<Escape>", lambda x: root.destroy())

    service = QiskitRuntimeService() if args.ibm else None

    moves = [Move.RY, Move.RZ, Move.CRX, Move.COLLAPSE]

    ultimate = args.ultimate

    if service:
        backend = service.least_busy(
            simulator=False, operational=True, min_num_qubits=81 if ultimate else 9
        )
    else:
        backend = FakeSherbrooke()
        # backend = AerSimulator(method="matrix_product_state")  # use non-noisy simulator

    App(root, ultimate=ultimate, moves=moves, backend=backend)

    root.mainloop()


if __name__ == "__main__":
    main()
