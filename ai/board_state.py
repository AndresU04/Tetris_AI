import numpy as np

def get_column_heights(board):
    """Returns the heights of each column"""
    heights = []
    for col in range(board.shape[1]):
        column = board[:, col]
        filled = np.where(column == 1)[0]
        if len(filled) == 0:
            heights.append(0)
        else:
            heights.append(board.shape[0] - filled[0])
    return heights

def get_aggregate_height(board):
    """Sum of all column heights"""
    return sum(get_column_heights(board))

def get_holes(board):
    """Returns the number of cells with at least one filled cell 
    above the them."""
    holes = 0
    for col in range(board.shape[1]):
        column = board[:, col]
        filled = np.where(column == 1)[0]
        if len(filled) == 0:
            continue
        top = filled[0]
        holes += np.sum(column[top: ] == 0)
    return holes

def get_bumpiness(board):
    """The sum of absolute height diffrences 
    between adjacent columns"""
    heights = get_column_heights(board)
    bumpiness = 0
    for i in range(len(heights) - 1):
        bumpiness += abs(heights[i] - heights[i+1])
    return bumpiness

def get_complete_lines(board):
    """Number of lines that are completely filled"""
    return int(np.sum(np.all(board == 1, axis = 1)))

def get_board_props(board):
    """Returns all four heuristic features as a dict"""
    return{
        "aggregate_height": get_aggregate_height(board),
        "holes": get_holes(board),
        "bumpiness": get_bumpiness(board),
        "complete_lines": get_complete_lines(board)
    }



