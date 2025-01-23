from qiskit_ibm_runtime.fake_provider import FakeSherbrooke
from qiskit_ibm_runtime import QiskitRuntimeService
from backend.quantum_tic_tac_toe import Move
from qiskit_aer import AerSimulator
from backend.parser import create_parser
from cli.qttt_cli import QtttCLI


def main():
    parser = create_parser("qttt-cli")
    args = parser.parse_args()

    service = QiskitRuntimeService() if args.ibm else None

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

    QtttCLI(ultimate, moves, backend).play()


if __name__ == "__main__":
    main()
