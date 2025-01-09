import math
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def print_board(board):
    print("\n")
    print(f"  {board[0]} | {board[1]} | {board[2]}")
    print(" ----\u00b9----\u00b2----\u00b3")
    print(f"  {board[3]} | {board[4]} | {board[5]}")
    print(" ----\u2074----\u2075----\u2076")
    print(f"  {board[6]} | {board[7]} | {board[8]}")
    print("     \u2077    \u2078    \u2079")
    print("\n")


def check_win(board, player):
    win_combinations = [
        (0, 1, 2),  # top row
        (3, 4, 5),  # middle row
        (6, 7, 8),  # bottom row
        (0, 3, 6),  # left column
        (1, 4, 7),  # middle column
        (2, 5, 8),  # right column
        (0, 4, 8),  # diagonal (top-left to bottom-right)
        (2, 4, 6)   # diagonal (top-right to bottom-left)
    ]

    for combo in win_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] == player.get('classic') + " ":
            return True
    return False


def check_draw(board):
    return (all(space != "  " for space in board)
            and all(space == 'X ' or space == 'O ' for space in board))


def check_full(board):
    return all(cell.strip() != "" for cell in board)


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


def get_valid_position(board):
    while True:
        try:
            move = int(input("Enter a position (1-9): "))
            if move < 1 or move > 9:
                raise ValueError
            if board[move - 1] == "  ":
                return move - 1
            else:
                print("That position is already taken. Try again.")
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 9.")


def get_valid_quantum_position(board, current_player, other_player):
    found = place_1 = place_2 = False
    while not found:
        try:
            found = True
            place_1 = int(input("Enter the first position (1-9): "))
            place_2 = int(input("Enter the second position (1-9): "))
            if place_1 < 1 or place_1 > 9 or place_2 < 1 or place_2 > 9 or place_1 == place_2:
                raise ValueError
            for i in [place_1 - 1, place_2 - 1]:
                if (board[i] == current_player.get('classic') + " "
                        or board[i] == other_player.get('classic') + " "
                        or board[i] == current_player.get('quantum') + other_player.get('quantum')
                        or board[i] == other_player.get('quantum') + current_player.get('quantum')
                        or board[i] == current_player.get('quantum') + ' '):
                    print(f'Position {i + 1} is already taken. Try again.')
                    found = False
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 9.")
    return place_1, place_2


def quantum_possible(board, players):
    # Make sure players[0] is the current player
    # A spot is full if:
    #   - Own quantum mark
    #   - Both quantum mark /2 ways
    #   - Any classic mark /2 ways
    possible_moves = 0
    for i in board:
        if (i != players[0].get('quantum') + " "
                and i != players[0].get('quantum') + players[1].get('quantum')
                and i != players[1].get('quantum') + players[0].get('quantum')
                and i != players[0].get('classic') + " "
                and i != players[1].get('classic') + " "):
            possible_moves += 1

    return True if possible_moves >= 2 else False


def quantum_move(board, current_player, other_player, move_list, player_list):
    print("You chose a QUANTUM move.")
    position = get_valid_quantum_position(board, current_player, other_player)
    if board[position[0] - 1] == other_player.get('quantum') + " ":
        board[position[0] - 1] = other_player.get('quantum') + current_player.get('quantum')
    else:
        board[position[0] - 1] = current_player.get('quantum') + " "
    if board[position[1] - 1] == other_player.get('quantum') + " ":
        board[position[1] - 1] = other_player.get('quantum') + current_player.get('quantum')
    else:
        board[position[1] - 1] = current_player.get('quantum') + " "

    player_list.append(current_player)
    move_list.append((position[0], position[1]))
    return True


def classic_move(board, current_player):
    print("You chose a CLASSIC move.")
    position = get_valid_position(board)
    board[position] = current_player.get('classic') + " "
    return True


def check_end_game(board, current_player):
    if check_win(board, current_player):
        print_board(board)
        print(f"Player {current_player.get('classic')} wins!")
        return True
    if check_draw(board):
        print_board(board)
        print("It's a draw!")
        return True
    return False


def collapse(board, move_list, player_list, quantum=False, service=None):
    print_board(board)
    amplitudes = combine_and_normalize(move_list)

    # 1) Verify 'vec' has length 2^n for some integer n
    length = len(amplitudes)
    n_qubits = int(math.log2(length))
    if 2 ** n_qubits != length:
        raise ValueError("State vector length must be a power of 2.")

    # 2) Create the circuit with n qubits and n classical bits
    qc = QuantumCircuit(n_qubits, n_qubits)

    # 3) Initialize the qubits to the custom state vector
    qc.initialize(amplitudes, range(n_qubits))

    # 4) Measure all qubits into all classical bits
    qc.measure(range(n_qubits), range(n_qubits))

    # 5) Transpile and run
    if quantum:
        backend = service.least_busy(simulator=False, operational=True)
    else:
        backend = AerSimulator()

    transpiled_qc = transpile(qc, backend)
    job = backend.run(transpiled_qc, shots=1)
    result = job.result()
    counts = result.get_counts()

    bitstring = list(counts.keys())[0]
    for i in range(len(move_list)):
        place_1 = move_list[i][int(bitstring[i])]
        board[place_1 - 1] = player_list[i].get('classic') + " "

    for i in range(9):
        if board[i] != "X " and board[i] != "O ":
            board[i] = "  "

    move_list.clear()
    player_list.clear()


def ask_move(move_types):
    # Ask the user which type of move they'd like to make
    move_type = ""
    while move_type not in move_types:
        move_type = input("Which type of move? (quantum/classic): ").strip().lower()
        if move_type not in move_types:
            print("Invalid choice. Please choose 'quantum (q)' or 'classic (c)'.")

    return move_type
