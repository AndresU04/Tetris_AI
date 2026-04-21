import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'metrics')))

from metrics_logger import MetricsLogger

def test_single_game():
    logger = MetricsLogger(log_dir="metrics/logs/test")
    logger.start_game()
    logger.log_step(lines_cleared=1, score=100)
    logger.log_step(lines_cleared=0, score=100)
    logger.log_step(lines_cleared=2, score=300)
    logger.end_game()

    assert len(logger.games) == 1
    game = logger.games[0]
    assert game["lines_cleared"] == 3
    assert game["score"] == 300
    assert game["pieces_placed"] == 3
    assert game["duration_seconds"] >= 0
    print("[X] single game tracking passed")

def test_multiple_games():
    logger = MetricsLogger(log_dir="metrics/logs/test")
    for i in range(5):
        logger.start_game()
        logger.log_step(lines_cleared=i, score=i * 100)
        logger.end_game()

    assert len(logger.games) == 5
    print(f"[X] multiple games tracking passed — {len(logger.games)} games recorded")

def test_json_saved():
    logger = MetricsLogger(log_dir="metrics/logs/test")
    logger.start_game()
    logger.log_step(lines_cleared=4, score=800)
    logger.end_game()

    filepath = "metrics/logs/test/game_0001.json"
    assert os.path.exists(filepath), "JSON file should be saved"
    with open(filepath) as f:
        data = json.load(f)
    assert data["lines_cleared"] == 4
    print("[X] JSON save passed")

def test_summary():
    logger = MetricsLogger(log_dir="metrics/logs/test")
    for i in range(3):
        logger.start_game()
        logger.log_step(lines_cleared=i+1, score=(i+1)*100)
        logger.end_game()
    logger.print_summary()
    print("[X] print_summary passed")

if __name__ == "__main__":
    print("\n── Metrics Logger Tests ──────────────────────────")
    test_single_game()
    test_multiple_games()
    test_json_saved()
    test_summary()
    print("\n(˶ᵔ ᵕ ᵔ˶) All metrics logger tests passed!")