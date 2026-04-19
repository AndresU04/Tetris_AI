from board_state import (
    get_aggregate_height, 
    get_holes,
    get_bumpiness,
    get_complete_lines
)

# Dellacherie weights for the hurestics
WEIGHT_AGGREGATE_HEIGHT = -0.510066
WEIGHT_HOLES = -0.35663
WEIGHT_BUMPINESS = -0.184483
WEIGHT_COMPLETE_LINES = 0.760666

def score_board(board):
    """Scores a board state using the given heuristic weights.
    Higher score = better board."""

    aggregate_height = get_aggregate_height(board)
    holes = get_holes(board)
    bumpiness = get_bumpiness(board)
    complete_lines = get_complete_lines(board)

    score = (
        WEIGHT_AGGREGATE_HEIGHT * aggregate_height +
        WEIGHT_HOLES * holes +
        WEIGHT_BUMPINESS * bumpiness +
        WEIGHT_COMPLETE_LINES * complete_lines
    )

    return score