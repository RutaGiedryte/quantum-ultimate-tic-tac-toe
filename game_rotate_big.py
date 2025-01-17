import math
from enum import Enum
from collections.abc import Callable

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.transpiler import CouplingMap

###############################################################################
# CONSTANTS
###############################################################################
# Separate max angles for single-qubit Y vs. Z rotations:
MAX_ANGLE_Y = math.pi/2       # e.g. up to π/2 for Y rotations
MAX_ANGLE_Z = math.pi/2       # e.g. up to π/2 for Z rotations

MAX_ANGLE_CONTROLLED = math.pi    # Up to π for controlled x

MOVES_BETWEEN_AUTO_COLLAPSE = 10  # universal 10-move timer for auto-collapse

###############################################################################
# FULLY CONNECTED 81-QUBIT COUPLING MAP
###############################################################################
def fully_connected_81_coupling():
    """
    Build a CouplingMap for 81 qubits, fully connected, 
    so we skip 'CircuitTooWideForTarget' issues and routing constraints.
    """
    edges = []
    for i in range(81):
        for j in range(81):
            if i != j:
                edges.append((i, j))
    return CouplingMap(edges)

###############################################################################
# STATE, BOARD, ETC.
###############################################################################
class State(Enum):
    EMPTY = 0
    X = 1
    O = 2
    DRAW = 3

    def __str__(self):
        match self:
            case State.EMPTY: return " "
            case State.X:     return "X"
            case State.O:     return "O"
            case State.DRAW:  return "draw"

class Axis(Enum):
    Y = 0  # single-qubit Y rotation
    X = 1  # controlled X
    Z = 2  # single-qubit Z rotation

def resetBoard():
    """
    theBoard[subBoardID][cellID] = ' ' or 'X' or 'O'
    topBoard[subBoardID] = ' ', 'X', 'O'
    subBoardID, cellID in ['1'..'9']
    """
    theBoard = {}
    for sb in range(1,10):
        sbID = str(sb)
        theBoard[sbID] = {}
        for c in range(1,10):
            theBoard[sbID][str(c)] = ' '
    topBoard = {}
    for sb in range(1,10):
        topBoard[str(sb)] = ' '
    return theBoard, topBoard

def check_subboard_win(theBoard, sbID):
    lines = [
        ('1','2','3'), ('4','5','6'), ('7','8','9'),
        ('1','4','7'), ('2','5','8'), ('3','6','9'),
        ('1','5','9'), ('3','5','7')
    ]
    b = theBoard[sbID]
    for (a,bv,c) in lines:
        if b[a] == b[bv] == b[c] != ' ':
            return b[a]
    return ' '

def check_topboard_win(topBoard):
    lines = [
        ('1','2','3'), ('4','5','6'), ('7','8','9'),
        ('1','4','7'), ('2','5','8'), ('3','6','9'),
        ('1','5','9'), ('3','5','7')
    ]
    for (x,y,z) in lines:
        if topBoard[x] == topBoard[y] == topBoard[z] != ' ':
            return topBoard[x]
    return ' '

def printBoard(theBoard, topBoard, forcedBoards):
    print("\nULTIMATE QUANTUM TIC-TAC-TOE (81 Qubits)\n")
    SUBBOARD_SEP = "||"
    ROW_SEP = "=" * 23
    COL_SEP = "|"

    for subBoardRow in range(3):
        for rowWithin in range(3):
            row_parts = []
            for subBoardCol in range(3):
                sbIndex = 3*subBoardRow + (subBoardCol+1)
                sbID = str(sbIndex)
                start_cell = 3*rowWithin + 1
                sub_line = []
                for offset in range(3):
                    cID = str(start_cell + offset)
                    mark = theBoard[sbID][cID]
                    sub_line.append(mark if mark != ' ' else ' ')
                row_parts.append(COL_SEP.join(sub_line))
            print(f" {SUBBOARD_SEP} ".join(row_parts))
        if subBoardRow < 2:
            print(ROW_SEP)

    print("\nTop Board:")
    for rowBlock in range(3):
        row_str = []
        for colBlock in range(3):
            sbID = str(3*rowBlock + (colBlock+1))
            row_str.append(topBoard[sbID])
        print(" | ".join(row_str))
        if rowBlock<2:
            print(" -+---+-")

    if forcedBoards:
        fb_list = sorted(list(forcedBoards))
        print(f"\nNext move MUST be in sub-board(s): {', '.join(fb_list)}")
    else:
        print("\nNext move can be in ANY sub-board (free choice).")

def subBoardIsFull(theBoard, sbID):
    empties = [c for c,v in theBoard[sbID].items() if v==' ']
    return (len(empties)==0)

def subBoardIsWon(topBoard, sbID):
    return (topBoard[sbID] != ' ')

def boardIsFull(theBoard, topBoard):
    # If every sub-board is won or full => entire board is full
    for sb in range(1,10):
        sbID = str(sb)
        if topBoard[sbID]==' ':
            empties = [c for c,v in theBoard[sbID].items() if v==' ']
            if empties:
                return False
    return True

###############################################################################
# PARTIAL-ONLY COLLAPSE with ENTANGLEMENT LOOKUP
###############################################################################
def partial_collapse(circuit, squaresToMeasure, theBoard, topBoard,
                     squaresActivated, entangledPairs, zBlocked):
    """
    squaresToMeasure are the qubit indices in the sub-board being collapsed,
    plus any specifically entangled qubits (in different sub-boards).
    We measure only these qubits. 
    Then interpret them => 'X'/'O' or remain ' '.

    entangledPairs[q] is a set of qubits entangled with q. 
    We'll unify them into squaresToMeasure if q is in squaresToMeasure.

    Also, once measured, we remove them from zBlocked.
    """
    if not squaresToMeasure:
        print("No squares to collapse.")
        return

    # BFS/DFS to find transitive entanglement
    closure = set(squaresToMeasure)
    queue = list(squaresToMeasure)
    while queue:
        cur = queue.pop()
        for eq in entangledPairs[cur]:
            if eq not in closure:
                closure.add(eq)
                queue.append(eq)

    squaresToMeasure = closure

    print(f"\n--- PARTIAL COLLAPSE of squares: {squaresToMeasure} ---\n")

    # copy circuit for z- and x-basis measure
    qc_z = circuit.copy()
    qc_x = circuit.copy()

    # measure only squaresToMeasure
    for q in squaresToMeasure:
        qc_z.measure(q, q)
        qc_x.h(q)
        qc_x.measure(q, q)

    fc_map = fully_connected_81_coupling()
    simulator = AerSimulator(method='matrix_product_state')

    z_t = transpile(qc_z, simulator, coupling_map=fc_map,
                    routing_method='none', optimization_level=0)
    x_t = transpile(qc_x, simulator, coupling_map=fc_map,
                    routing_method='none', optimization_level=0)

    z_job = simulator.run(z_t, shots=1)
    x_job = simulator.run(x_t, shots=1)

    z_res = z_job.result()
    x_res = x_job.result()

    z_str = list(z_res.get_counts().keys())[0][::-1]
    x_str = list(x_res.get_counts().keys())[0][::-1]

    for q in squaresToMeasure:
        sb_int = q//9 + 1
        c_int  = q%9 + 1
        sbID = str(sb_int)
        cID = str(c_int)
        if theBoard[sbID][cID] != ' ':
            continue

        # z==1 => there is a symbol; z==0 => remain empty
        if z_str[q]=='1':
            # x==1 => 'X', x==0 => 'O'
            if x_str[q]=='1':
                theBoard[sbID][cID] = 'X'
            else:
                theBoard[sbID][cID] = 'O'
        else:
            theBoard[sbID][cID] = ' '

        # remove from squaresActivated
        if q in squaresActivated:
            squaresActivated.remove(q)

        # remove from zBlocked if present
        if q in zBlocked:
            zBlocked.remove(q)

    # reset them in the main circuit
    for q in squaresToMeasure:
        circuit.reset(q)

    # remove entanglement references
    for q in squaresToMeasure:
        for eq in entangledPairs[q]:
            entangledPairs[eq].discard(q)
        entangledPairs[q].clear()

    print("Partial collapse done!\n")
    # check sub-board winners
    for sb in range(1,10):
        sbID = str(sb)
        w = check_subboard_win(theBoard, sbID)
        if w!=' ':
            topBoard[sbID] = w

###############################################################################
# MAIN GAME
###############################################################################
def main():
    theBoard, topBoard = resetBoard()
    circuit = QuantumCircuit(81,81)

    squaresActivated = set()            # squares that are "activated" from |0>, not collapsed yet
    entangledPairs = {q: set() for q in range(81)}  # direct entanglements
    zBlocked = set()                    # track qubits that cannot do z-rotation (controlled x used)

    forcedBoards = set()  
    turn_symbol = 'X'

    # A single universal counter for "moves since last collapse"
    movesSinceLastCollapse = 0

    def auto_collapse_if_10():
        nonlocal movesSinceLastCollapse
        if movesSinceLastCollapse >= MOVES_BETWEEN_AUTO_COLLAPSE:
            # collapse all squares in squaresActivated
            partial_collapse(circuit, set(squaresActivated),
                             theBoard, topBoard,
                             squaresActivated, entangledPairs, zBlocked)
            # then reset the counter
            movesSinceLastCollapse = 0

    while True:
        printBoard(theBoard, topBoard, forcedBoards)
        w = check_topboard_win(topBoard)
        if w in ['X','O']:
            print(f"\nPlayer {w} has won the top board!")
            break
        if boardIsFull(theBoard, topBoard):
            print("\nAll sub-boards are decided or full => It's a tie!")
            break

        print(f"\nIt's {turn_symbol}'s turn. MovesSinceLastCollapse={movesSinceLastCollapse}")

        # check auto collapse if 10 moves since last collapse
        auto_collapse_if_10()

        print("1) y/z rotation, up to pi/2 total angle (1 or 2 squares)")
        print("2) controlled x up to pi (1 control, 1 target)")
        print("3) collapse sub-board")
        print("4) quit")
        choice = input("> ")
        
        if choice=='4':
            print("Quit.")
            break

        elif choice=='3':
            # manual collapse => measure partial
            if forcedBoards:
                pass
            else:
                print("Pick any sub-board. We'll measure squares in that board + entangled ones.")
            sb = input("Which sub-board [1..9]? ")
            toMeasure = set()
            for c in range(1,10):
                q = (int(sb)-1)*9 + (c-1)
                if q in squaresActivated:
                    toMeasure.add(q)

            partial_collapse(circuit, toMeasure,
                             theBoard, topBoard,
                             squaresActivated, entangledPairs, zBlocked)
            print(circuit.draw())
            forcedBoards.clear()

            # RESET movesSinceLastCollapse => 0
            movesSinceLastCollapse = 0

            turn_symbol = 'O' if turn_symbol=='X' else 'X'
            continue

        elif choice=='1':
            # y/z rotation up to pi/2 total angle
            axis_ = input("Rotate around y or z? (y/z) ")
            if axis_ not in ['y','z']:
                print("Invalid axis.")
                continue

            n_squares = input("Rotate how many squares? (1 or 2) ")
            if n_squares not in ['1','2']:
                print("Invalid count.")
                continue
            n_squares = int(n_squares)

            # pick the correct max angle based on axis
            angle_limit = 0.0
            if axis_ == 'y':
                angle_limit = MAX_ANGLE_Y
            else:
                angle_limit = MAX_ANGLE_Z

            angle_left = angle_limit  # we can distribute this across 1 or 2 squares
            squares_done = []

            for _ in range(n_squares):
                while True:
                    sb = input("Which sub-board? ")
                    # if forced, must pick from it unless it's full/won
                    if forcedBoards and sb not in forcedBoards:
                        if subBoardIsFull(theBoard, sb) or subBoardIsWon(topBoard, sb):
                            print("Forced is full/won => free choice now.")
                            break
                        else:
                            print(f"Must pick from forced boards: {forcedBoards}")
                            continue
                    if sb not in [str(i) for i in range(1,10)]:
                        print("Invalid sub-board.")
                        continue
                    break

                # re-ask for a cell until valid (and not blocked if z):
                cell_ok = False
                pos = None
                while not cell_ok:
                    c_ = input("Which cell [1..9]? ")
                    posC = (int(sb)-1)*9 + (int(c_)-1)

                    if axis_=='z' and posC in zBlocked:
                        print(f"Qubit {posC} is blocked from z-rotations. Please choose another cell.")
                        continue
                    else:
                        # good cell
                        pos = posC
                        cell_ok = True

                # re-ask for angle if invalid
                angle_ok = False
                a = 0.0
                while not angle_ok:
                    a_ = float(input(f"Angle in [-{angle_left}, {angle_left}]? "))
                    if abs(a_) > angle_left:
                        print(f"Angle too large, left= {angle_left}. Try again.")
                        continue
                    angle_ok = True
                    a = a_
            
                # apply gate
                if axis_=='y':
                    circuit.ry(a, pos)
                else:
                    circuit.rz(a, pos)
                print(circuit.draw())

                if pos not in squaresActivated:
                    squaresActivated.add(pos)

                angle_left -= abs(a)
                squares_done.append((sb, c_))

            forcedBoards.clear()
            for (sb, c_) in squares_done:
                forcedBoards.add(c_)

            # after a successful move => increment movesSinceLastCollapse
            movesSinceLastCollapse += 1

            turn_symbol = 'O' if turn_symbol=='X' else 'X'
            continue

        elif choice=='2':
            # controlled x up to pi
            while True:
                sbC = input("Control sub-board? ")
                if forcedBoards and sbC not in forcedBoards:
                    if subBoardIsFull(theBoard, sbC) or subBoardIsWon(topBoard, sbC):
                        print("Forced is full/won => free choice now.")
                        break
                    else:
                        print(f"Must pick from forced boards: {forcedBoards}")
                        continue
                if sbC not in [str(i) for i in range(1,10)]:
                    print("Invalid sub-board.")
                    continue
                break

            cC = input("Control cell [1..9]? ")
            posC = (int(sbC)-1)*9 + (int(cC)-1)

            while True:
                sbT = input("Target sub-board? ")
                if forcedBoards and sbT not in forcedBoards:
                    if subBoardIsFull(theBoard, sbT) or subBoardIsWon(topBoard, sbT):
                        print("Forced is full/won => free choice now.")
                        break
                    else:
                        print(f"Must pick from forced boards: {forcedBoards}")
                        continue
                if sbT not in [str(i) for i in range(1,10)]:
                    print("Invalid sub-board.")
                    continue
                break

            cT = input("Target cell [1..9]? ")
            posT = (int(sbT)-1)*9 + (int(cT)-1)

            angle = float(input(f"Angle in [-{MAX_ANGLE_CONTROLLED}, {MAX_ANGLE_CONTROLLED}]? "))
            if abs(angle)>MAX_ANGLE_CONTROLLED:
                print("Angle too big.")
                continue
    
            circuit.crx(angle, posC, posT)
            print(circuit.draw())

            if posC not in squaresActivated:
                squaresActivated.add(posC)
            if posT not in squaresActivated:
                squaresActivated.add(posT)

            forcedBoards.clear()
            forcedBoards.add(cC)
            forcedBoards.add(cT)

            # block z-rotation on these qubits until measured
            zBlocked.add(posC)
            zBlocked.add(posT)

            # after a successful move => increment movesSinceLastCollapse
            movesSinceLastCollapse += 1

            turn_symbol = 'O' if turn_symbol=='X' else 'X'
            continue

        else:
            print("Invalid choice.")
            continue

if __name__=="__main__":
    main()
