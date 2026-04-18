import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai')))

from actions import get_rotations, simulate_drop, get_possible_actions

# A simple T-piece
T_PIECE = np.array([
    [1, 1, 1],
    [0, 1, 0]
])

board = np.zeros((20, 10), dtype=int)

def test_get_rotations():
    rotations = get_rotations(T_PIECE)
    assert len(rotations) == 4, f"T-piece should have 4 rotations, got {len(rotations)}"
    print("[X] get_rotations passed")

def test_simulate_drop():
    new_board = simulate_drop(board, T_PIECE, col=0)
    assert new_board is not None, "Should return a board"
    assert np.sum(new_board) == np.sum(T_PIECE), "Piece cells should be placed on board"
    print("[X] simulate_drop passed")

def test_invalid_col():
    # Column 9 with a 3-wide piece should be invalid
    result = simulate_drop(board, T_PIECE, col=9)
    assert result is None, "Should return None for out-of-bounds placement"
    print("[X] invalid column check passed")

def test_get_possible_actions():
    actions = get_possible_actions(T_PIECE, board)
    assert len(actions) > 0, "Should return at least one action"
    for rotated_piece, col, new_board in actions:
        assert new_board is not None
        assert new_board.shape == board.shape
    print(f"[X] get_possible_actions passed — {len(actions)} valid actions found")

if __name__ == "__main__":
    print("\n── Actions Tests ──────────────────────────")
    test_get_rotations()
    test_simulate_drop()
    test_invalid_col()
    test_get_possible_actions()
    print("\n (˶ᵔ ᵕ ᵔ˶) All actions tests passed!")