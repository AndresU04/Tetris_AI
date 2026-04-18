import numpy as np

def get_rotations(piece): 
    """Returns all unique roations of a given piece"""

    rotations = []
    current = piece
    for _ in range(4):
        # Converts it to a tuple to check for duplicates
        if not any(np.array_equal(current, r) for r in rotations):
            rotations.append(current)
        current = np.rot90(current)
    return rotations

def simulate_drop(board, piece, col):
    """Simulates dropping a piece at a given collum.
    Returns the new board state or None if the placment is invalid"""

    piece_height, piece_width = piece.shape

    # Check if the piece fits horizontally
    if col + piece_width > board.shape[1]:
        return None
    
    # Find the lowest row the piece can drop to 
    drop_row = 0
    for row in range(board.shape[0] - piece_height + 1):
        if np.any(board[row: row + piece_height, col: col + piece_width] + piece > 1):
            break
        drop_row = row
    
    # Place the piece on a copy of the board
    new_board = board.copy()
    new_board[drop_row: drop_row + piece_height, col: col + piece_width] += piece

    return new_board

def get_possible_actions(piece, board):
    """Returns a list of as (rotated_piece, col, resulting_board) tuples
    for every valid placement of the piece on the board."""

    actions = []
    rotations = get_rotations(piece)

    for rotated_piece in rotations:
        piece_width = rotated_piece.shape[1]
        for col in range(board.shape[1] - piece_width + 1):
            new_board = simulate_drop(board, rotated_piece, col)
            if new_board is not None:
                actions.append((rotated_piece, col, new_board))

    return actions


    