# Quantum (Ultimate) Tic-Tac-Toe

Quantum tic-tac-toe is a quantum version of the classical game — tic-tac-toe. In this quantum version, each cell is represented by a qubit. All cells start in the $\ket{0}$ state. Every turn, players can rotate a qubit around an axis of their choice. The players can also choose to measure the state of the board.

Two copies of the quantum circuit are measured: one in z-basis, and one in x-basis. Measuring in z-basis determines whether the symbol exists: it exists if we measure 1. Measuring in x-basis determines what symbol it is: 'O' if it is 1, and 'X' if it is 0. Once a symbol is measured to exist, the corresponding qubit can no longer be rotated.

The board is automatically measured after ten turns since the last measurement.

## Moves

There are three types of moves:
- Rotate 1-2 qubits around y- or z-axis. The maximum angle of $\pi / 2$ is divided among the number of qubits the player chose to rotate.
- Perform a controlled x-rotation. The maximum angle for this move is $\pi$. After this move, the chosen qubits cannot be rotated around z-axis until the qubits have been measured.
- Measure the board.

## Ultimate Version

In the ultimate version, there are nine sub-boards. The goal is to win three sub-boards in a row horizontally, vertically, or diagonally.

A player is only allowed to make a move in the sub-boards that correspond to the qubits that were rotated in the previous turn. E.g., if the previous player rotated the top-left qubit in a sub-board, the current player has to play in the top-left sub-board. If a player chooses to rotate two qubits, they cannot both be in the same sub-board, unless there is only one sub-board available.

If the sub-board that a player has to play in is finished, the player can choose from any unfinished sub-board. The player can also choose from any unfinished sub-board after a measurement.

# Installation

Install the program with the following command:
```bash
pip install .
```

# Running the Program

Run the program with the following command:
```bash
qttt [-u] [-i]
```

Use the `-u` flag to run the ultimate version. 

You can use the `-i` flag to run it on an IBM quantum computer, instead of simulating locally. Running on the quantum computer introduces noise.

You can also run a terminal version of the game:
```bash
qttt-cli [-u] [-i]
```
