import numpy as np
from actions import get_possible_actions
from heuristic import score_board

class TetrisAgent:
    """A heuristic based Tetris agent that picks the best move 
    by scoring every possible board state using Dellacherie weights."""

    def pick_best_action(self, board, piece):
        """Given a current baord and piece, it returns the best
        (rotated_piece, col, resulting_board) tuple"""

        possible_actions = get_possible_actions(piece, board)

        if not possible_actions:
            return None
        
        best_action = None
        best_score = float('-inf')

        for action in possible_actions:
            rotated_piece, col, resulting_board = action
            score = score_board(resulting_board)

            if score > best_score:
                best_score = score
                best_action = action

        return best_action
    
    def get_best_col_and_rotation(self, board, piece):
        """Convenient function return just (rotated_piece, col)
        so the game can execute the move."""

        action = self.pick_best_action(board, piece)

        if action is None:
            return None, None
        
        rotated_piece, col, _ = action
        return rotated_piece, col
    