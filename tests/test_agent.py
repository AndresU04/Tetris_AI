import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai')))

from agent import TetrisAgent

agent = TetrisAgent()

# T-piece
T_PIECE = np.array([
    [1, 1, 1],
    [0, 1, 0]
])

# Empty board
empty_board = np.zeros((20, 10), dtype=int)

# Almost complete line — agent should fill it
smart_board = np.zeros((20, 10), dtype=int)
smart_board[19, :9] = 1  # bottom row missing only last cell

# I-piece (vertical) to fill the gap
I_PIECE = np.array([
    [1],
    [1],
    [1],
    [1]
])

def test_returns_action():
    action = agent.pick_best_action(empty_board, T_PIECE)
    assert action is not None, "Should return an action"
    rotated_piece, col, resulting_board = action
    assert resulting_board.shape == empty_board.shape
    print(f"[X] pick_best_action returned action at col={col}")

def test_returns_col_and_rotation():
    rotated_piece, col = agent.get_best_col_and_rotation(empty_board, T_PIECE)
    assert rotated_piece is not None
    assert col is not None
    assert 0 <= col <= 9
    print(f"[X] get_best_col_and_rotation returned col={col}")

def test_agent_is_smart():
    """Agent should prefer completing a line over anything else."""
    action = agent.pick_best_action(smart_board, I_PIECE)
    assert action is not None
    _, col, resulting_board = action
    complete_lines = int(np.sum(np.all(resulting_board == 1, axis=1)))
    assert complete_lines >= 1, "Agent should complete at least 1 line"
    print(f"[X] agent cleared {complete_lines} line(s) — it's smart!")

def test_no_actions():
    """A completely filled board should return None."""
    full_board = np.ones((20, 10), dtype=int)
    action = agent.pick_best_action(full_board, T_PIECE)
    assert action is None, "Should return None on a full board"
    print("[X] no actions on full board handled correctly")

if __name__ == "__main__":
    print("\n── Agent Tests ──────────────────────────")
    test_returns_action()
    test_returns_col_and_rotation()
    test_agent_is_smart()
    test_no_actions()
    print("\n(˶ᵔ ᵕ ᵔ˶) All agent tests passed!")