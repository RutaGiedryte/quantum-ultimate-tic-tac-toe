import math
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from functions import *


def collapse(board, move_list, player_list):
    print_board(board)
    vec = combine_and_normalize(move_list)
    shots = 1
    # 1) Verify 'vec' has length 2^n for some integer n
    length = len(vec)
    n_qubits = int(math.log2(length))
    if 2 ** n_qubits != length:
        raise ValueError("State vector length must be a power of 2.")

    # 2) Create the circuit with n qubits and n classical bits
    qc = QuantumCircuit(n_qubits, n_qubits)

    # 3) Initialize the qubits to the custom state vector
    qc.initialize(vec, range(n_qubits))

    # 4) Measure all qubits into all classical bits
    qc.measure(range(n_qubits), range(n_qubits))

    # 5) Transpile and run
    simulator = AerSimulator()
    transpiled_qc = transpile(qc, simulator)
    job = simulator.run(transpiled_qc, shots=shots)
    result = job.result()
    counts = result.get_counts()

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
            quantum_move(board,
                         current_player, player_o if current_player == player_x else player_x,
                         move_list,
                         player_list)
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
    play_game()
