import math
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService
from functions import *


def combine_and_normalize(tuples_list):
    n = len(tuples_list)
    if n == 0:
        return []

    result = []
    # Loop over all binary patterns from 0 to 2^n - 1
    for i in range(2 ** n):
        # Extract bits from left (most significant) to right (least significant)
        bits = [(i >> (n - 1 - j)) & 1 for j in range(n)]

        # Collect the chosen elements from each tuple
        chosen = []
        for j, bit in enumerate(bits):
            chosen.append(tuples_list[j][bit])

        # If there are duplicates, append 0; otherwise 1
        if len(chosen) != len(set(chosen)):
            result.append(0)
        else:
            result.append(1)

    # Normalize the resulting list (as a vector)
    norm = math.sqrt(sum(x * x for x in result))
    if norm == 0:
        # If norm is zero, all elements are zero; return as is.
        return result
    else:
        return [x / norm for x in result]


def collapse(board, move_list, player_list):
    print_board(board)
    amplitudes = combine_and_normalize(move_list)

    # 1) Verify 'vec' has length 2^n for some integer n
    length = len(amplitudes)
    n_qubits = int(math.log2(length))
    if 2 ** n_qubits != length:
        raise ValueError("State vector length must be a power of 2.")

    # 2) Create the circuit with n qubits and n classical bits
    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.initialize(amplitudes, range(n_qubits))
    qc.measure(range(n_qubits), range(n_qubits))

    # 3) Run the circuit on a quantum backend
    backend = service.least_busy(simulator=False, operational=True)

    # 4) Transpile for the backend
    transpiled_qc = transpile(qc, backend=backend)

    # 5) Run the transpiled circuit on the backend (shots=1)
    job = backend.run(transpiled_qc, shots=1)
    job_result = job.result()

    # 6) Get results and collapse board
    counts = job_result.get_counts()
    bitstring = list(counts.keys())[0]
    # print(bitstring)
    for i in range(len(move_list)):
        place_1 = move_list[i][int(bitstring[i])]
        board[place_1 - 1] = player_list[i].get('classic') + " "

    for i in range(9):
        if board[i] != "X " and board[i] != "O ":
            board[i] = "  "

    move_list.clear()
    player_list.clear()


def play_game():
    board = ["  "] * 9
    move_types = ["quantum", "classic", "q", "c"]
    player_x = {'classic': 'X', 'quantum': 'x'}
    player_o = {'classic': 'O', 'quantum': 'o'}

    player_list = []
    move_list = []

    current_player = player_x
    while True:
        print_board(board)
        print(f"Player {current_player.get('classic')}'s turn.")

        # Ask the user which type of move they'd like to make
        move_type = ""
        while move_type not in move_types:
            move_type = input("Which type of move? (quantum/classic): ").strip().lower()
            if move_type not in move_types:
                print("Invalid choice. Please choose 'quantum (q)' or 'classic (c)'.")

        # Perform the chosen move
        if move_type == "quantum" or move_type == "q":
            quantum_move(board, current_player, player_o if current_player == player_x else player_x, move_list, player_list)
        else:
            classic_move(board, current_player)

        if check_end_game(board, current_player):
            return
        # Check for a win or a draw
        if check_full(board):
            collapse(board, move_list, player_list)
            print("Board collapsed")

        if check_end_game(board, current_player):
            return

        # Switch player
        current_player = player_o if current_player == player_x else player_x


if __name__ == "__main__":
    # Load saved credentials
    service = QiskitRuntimeService()

    play_game()
