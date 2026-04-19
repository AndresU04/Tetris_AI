import numpy as np
import sys
import os

# Path for heuristic.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai')))

from heuristic import score_board

# Empty board
empty_board = np.zeros((20, 10), dtype=int)

# Bad boards = tall and full of holes
bad_board = np.zeros((20, 10), dtype=int)
bad_board[15, 0] = 1  # tall column
bad_board[17, 0] = 1  # hole in col 0
bad_board[16, 1] = 1
bad_board[18, 1] = 1  # hole in col 1

# Good board = one complete line flat
good_board = np.zeros((20, 10), dtype=int)
good_board[19, :] = 1 # complete bottom row, flat surface

def test_empty_board():
    score = score_board(empty_board)
    assert score == 0.0, f"Empty board should score 0.0, got {score}"
    print(f"[X] empty board score = {score}")

def test_bad_board_score_lower():
    bad_score = score_board(bad_board)
    empty_score = score_board(empty_board)
    assert bad_score < empty_score, "Bad board should score lower than the empty board"
    print(f"[X] bad board score = {bad_score:.4f} < empty score = {empty_score}")

def test_good_board_score_higher():
    good_score = score_board(good_board)
    bad_score = score_board(bad_board)
    assert good_score > bad_score, "Good board should score higher than the bad board"
    print(f"[X] good board score = {good_score:.4f} > bad board score = {bad_score:.4f}")

if __name__ == "__main__":
    print("\n── Heuristic Tests ──────────────────────────")
    test_empty_board()
    test_bad_board_score_lower()
    test_good_board_score_higher()
    print("\n(˶ᵔ ᵕ ᵔ˶) All heuristic tests passed!")