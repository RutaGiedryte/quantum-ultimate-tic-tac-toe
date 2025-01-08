from qiskit_ibm_runtime import QiskitRuntimeService
from functions import *


def play_game(simulate=True, service=None):
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
            if simulate:
                print("Board collapsing: Simulating")
                collapse(board, move_list, player_list)
            else:
                print("Board collapsing: Running on IBM backend")
                collapse(board, move_list, player_list, True, service)
            print("Board collapsed")

        if check_end_game(board, current_player):
            return

        # Switch player
        current_player = player_o if current_player == player_x else player_x


if __name__ == "__main__":
    simulate = True
    if simulate:
        play_game()
    else:
        play_game(False, QiskitRuntimeService())

