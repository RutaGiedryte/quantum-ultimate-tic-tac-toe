from qiskit_ibm_runtime import QiskitRuntimeService
from backend.functions import *


def play_game(simulate=True, service=None):
    board = ["  "] * 9
    move_types = ["quantum", "classic", "q", "c"]
    player_x = {'classic': 'X', 'quantum': 'x'}
    player_o = {'classic': 'O', 'quantum': 'o'}

    player_list = []
    move_list = []

    current_player = player_x
    other_player = player_o
    while True:
        print_board(board)
        print(f"Player {current_player.get('classic')}'s turn.")

        move_type = ask_move(move_types)
        move_done = False
        # Perform the chosen move
        while not move_done:
            if move_type == "quantum" or move_type == "q":
                if quantum_possible(board, [current_player, other_player]):
                    move_done = quantum_move(board, current_player, other_player, move_list, player_list)
                else:
                    print("No quantum moves possible..")
                    move_type = ask_move(move_types)
            else:
                move_done = classic_move(board, current_player)

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
        other_player = current_player
        current_player = player_o if current_player == player_x else player_x


if __name__ == "__main__":
    simulate = True
    if simulate:
        play_game()
    else:
        play_game(False, QiskitRuntimeService())

