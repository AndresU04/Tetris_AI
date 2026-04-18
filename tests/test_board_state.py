import numpy as np
import sys
import os

# Make sure Python can find your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai')))

from board_state import get_column_heights, get_holes, get_bumpiness, get_complete_lines

# ── Shared test board ──────────────────────────────────────────────────────────
# 20 rows x 10 cols  (0 = empty, 1 = filled)
# We'll build a simple, predictable board by hand.

board = np.zeros((20, 10), dtype=int)

# Fill bottom row completely (1 complete line)
board[19, :] = 1

# Add a small stack in column 0 (rows 17-19) and column 1 (row 19 only)
board[17, 0] = 1
board[18, 0] = 1
# This creates a "hole" at row 19 col 0? No — col 0 rows 17-19 are all filled.
# Let's punch a hole: leave row 18 col 1 empty but fill above and below
board[17, 1] = 1   # filled
# board[18, 1] = 0  # empty  ← this is the hole (already 0 by default)
board[19, 1] = 1   # filled (bottom row already set)

# ── Tests ──────────────────────────────────────────────────────────────────────

def test_get_heights():
    heights = get_column_heights(board)
    assert len(heights) == 10, "Should return one height per column"
    # Col 0: filled at rows 17,18,19 → height = 3
    assert heights[0] == 3, f"Col 0 height should be 3, got {heights[0]}"
    # Col 1: filled at rows 17 and 19, hole at 18 → height = 3 (top filled cell)
    assert heights[1] == 3, f"Col 1 height should be 3, got {heights[1]}"
    # Cols 2-9: only bottom row filled → height = 1
    assert heights[2] == 1, f"Col 2 height should be 1, got {heights[2]}"
    print("[X] get_heights passed")

def test_get_holes():
    holes = get_holes(board)
    # Col 1: has 1 hole (row 18 is empty, row 17 above it is filled)
    assert holes == 1, f"Expected 1 hole, got {holes}"
    print("[x] get_holes passed")

def test_get_bumpiness():
    bumpiness = get_bumpiness(board)
    heights = get_column_heights(board)
    # Manually compute expected bumpiness
    expected = sum(abs(heights[i] - heights[i+1]) for i in range(9))
    assert bumpiness == expected, f"Expected {expected}, got {bumpiness}"
    print("[x] get_bumpiness passed")

def test_get_complete_lines():
    lines = get_complete_lines(board)
    # Only row 19 is completely filled
    assert lines == 1, f"Expected 1 complete line, got {lines}"
    print("[X] get_complete_lines passed")

# ── Run all ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n── Board State Tests ──────────────────────────")
    print("Test board (bottom 5 rows):")
    print(board[15:, :])
    print()
    test_get_heights()
    test_get_holes()
    test_get_bumpiness()
    test_get_complete_lines()
    print("\n (˶ᵔ ᵕ ᵔ˶) All board_state tests passed!")