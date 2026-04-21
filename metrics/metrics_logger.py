import json
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt


class MetricsLogger:
    """
    Tracks and saves performance metrics for each game the AI plays.
    """

    def __init__(self, log_dir="metrics/logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.games = []
        self.current_game = None

    # ── Game lifecycle ────────────────────────────────────────────────────────

    def start_game(self):
        """Call this when a new game starts."""
        self.current_game = {
            "game_number": len(self.games) + 1,
            "timestamp": datetime.datetime.now().isoformat(),
            "lines_cleared": 0,
            "score": 0,
            "pieces_placed": 0,
            "duration_seconds": 0,
            "start_time": datetime.datetime.now()
        }

    def end_game(self):
        """Call this when a game ends."""
        if self.current_game is None:
            return

        # Calculate duration
        end_time = datetime.datetime.now()
        duration = (end_time - self.current_game["start_time"]).total_seconds()
        self.current_game["duration_seconds"] = round(duration, 2)

        # Remove non-serializable start_time before saving
        game_record = {k: v for k, v in self.current_game.items() if k != "start_time"}
        self.games.append(game_record)
        self._save_to_file(game_record)
        self.current_game = None

    # ── In-game updates ───────────────────────────────────────────────────────

    def log_step(self, lines_cleared=0, score=0):
        """Call this after every piece is placed."""
        if self.current_game is None:
            return
        self.current_game["lines_cleared"] += lines_cleared
        self.current_game["score"] = score
        self.current_game["pieces_placed"] += 1

    # ── Saving ────────────────────────────────────────────────────────────────

    def _save_to_file(self, game_record):
        """Saves a single game record to a JSON file."""
        filename = f"game_{game_record['game_number']:04d}.json"
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, "w") as f:
            json.dump(game_record, f, indent=2)

    # ── Plotting ──────────────────────────────────────────────────────────────

    def plot_performance(self):
        """Plots lines cleared and score over all recorded games."""
        if not self.games:
            print("No games recorded yet.")
            return

        game_numbers = [g["game_number"] for g in self.games]
        lines = [g["lines_cleared"] for g in self.games]
        scores = [g["score"] for g in self.games]
        pieces = [g["pieces_placed"] for g in self.games]

        fig, axes = plt.subplots(3, 1, figsize=(10, 8))
        fig.suptitle("Tetris AI Performance", fontsize=14, fontweight="bold")

        axes[0].plot(game_numbers, lines, color="dodgerblue", marker="o")
        axes[0].set_ylabel("Lines Cleared")
        axes[0].set_title("Lines Cleared per Game")
        axes[0].grid(True)

        axes[1].plot(game_numbers, scores, color="green", marker="o")
        axes[1].set_ylabel("Score")
        axes[1].set_title("Score per Game")
        axes[1].grid(True)

        axes[2].plot(game_numbers, pieces, color="orange", marker="o")
        axes[2].set_ylabel("Pieces Placed")
        axes[2].set_title("Pieces Placed per Game")
        axes[2].grid(True)

        plt.xlabel("Game Number")
        plt.tight_layout()
        plt.savefig(os.path.join(self.log_dir, "performance.png"))
        plt.show()
        print(f"[X] Plot saved to {self.log_dir}/performance.png")

    # ── Summary ───────────────────────────────────────────────────────────────

    def print_summary(self):
        """Prints a summary of all recorded games."""
        if not self.games:
            print("No games recorded yet.")
            return

        lines = [g["lines_cleared"] for g in self.games]
        scores = [g["score"] for g in self.games]
        pieces = [g["pieces_placed"] for g in self.games]

        print("\n── AI Performance Summary ──────────────────")
        print(f"  Total games played : {len(self.games)}")
        print(f"  Avg lines cleared  : {np.mean(lines):.2f}")
        print(f"  Best lines cleared : {max(lines)}")
        print(f"  Avg score          : {np.mean(scores):.2f}")
        print(f"  Best score         : {max(scores)}")
        print(f"  Avg pieces placed  : {np.mean(pieces):.2f}")
        print("────────────────────────────────────────────\n")