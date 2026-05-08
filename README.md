# Tetris AI Code Layout

This project is organized into separate folders so that the game logic, AI logic, metrics, and tests are easier to understand.

## `ai/`

The `ai` folder contains the main artificial intelligence logic for the Tetris agent. This is where the program decides where the current piece should be placed.

### `actions.py`

This file generates possible placements for the current Tetris piece. It checks different rotations and columns, simulates where the piece would land, and returns valid board states that the AI can evaluate.

### `agent.py`

This file is the AI decision maker. It looks at all possible placements, uses the heuristic score to compare them, and chooses the best rotation and column for the current piece.

### `heuristic.py`

This file scores a board state using weighted board features. It gives penalties for bad features like high stacks, holes, and bumpiness, and gives rewards for completed lines.

### `board_state.py`

This file calculates the board features used by the heuristic. It measures aggregate height, holes, bumpiness, and complete lines.

## `game/`

The `game` folder contains the main Tetris game logic and visual interface.

### `tetris_ai.py`

This is the main game file. It runs the Pygame window, controls the game loop, renders the board, handles piece movement, updates the board, and connects the game to the AI agent. It also supports AI/manual play behavior and shows live game information.

## `metrics/`

The `metrics` folder contains code for tracking gameplay information. It records useful values such as score, cleared lines, board height, holes, bumpiness, and other performance metrics. These metrics help evaluate how well the AI is playing.

## `tests/`

The `tests` folder contains test files used to check that different parts of the project work correctly. These tests can help verify the AI logic, board calculations, and game behavior.

## `requirements.txt`

This file lists the Python libraries needed to run the project. The main libraries are NumPy and Pygame. Users can install them by running:

```bash
pip install -r requirements.txt