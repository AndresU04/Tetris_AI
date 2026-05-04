import numpy as np
import random, pygame
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'metrics')))

from agent import TetrisAgent
from metrics_logger import MetricsLogger
from board_state import get_column_heights, get_holes, get_bumpiness, get_aggregate_height

agent = TetrisAgent()
logger = MetricsLogger()

pygame.init()
pygame.font.init()

# ── Layout constants ───────────────────────────────────────────────────────
rows        = 20
columns     = 10
block       = 30
width       = columns * block      # 300
panel_width = 220
height      = rows * block         # 600
bg_color    = (10, 10, 18)

# ── Palette ────────────────────────────────────────────────────────────────
COL_PANEL_BG    = (14, 14, 26)
COL_DIVIDER     = (45, 45, 70)
COL_ACCENT_AI   = (0, 220, 130)
COL_ACCENT_MAN  = (80, 160, 255)
COL_TEXT_DIM    = (120, 120, 160)
COL_TEXT_BRIGHT = (220, 220, 240)
COL_BAR_BG      = (30, 30, 50)
COL_GRID        = (28, 28, 42)

# ── Fonts (set in init_fonts) ──────────────────────────────────────────────
FONT_TITLE = FONT_LABEL = FONT_VALUE = FONT_SMALL = FONT_MONO = None

def init_fonts():
    global FONT_TITLE, FONT_LABEL, FONT_VALUE, FONT_SMALL, FONT_MONO
    FONT_TITLE = pygame.font.SysFont("Consolas", 22, bold=True)
    FONT_LABEL = pygame.font.SysFont("Consolas", 13)
    FONT_VALUE = pygame.font.SysFont("Consolas", 15, bold=True)
    FONT_SMALL = pygame.font.SysFont("Consolas", 12)
    FONT_MONO  = pygame.font.SysFont("Consolas", 14, bold=True)

# ── Global mutable state ───────────────────────────────────────────────────
score  = 0
paused = False
board  = np.zeros((rows, columns))

# ── Pieces ─────────────────────────────────────────────────────────────────
L   = np.array([[0,0,1], [1,1,1]])
J   = np.array([[1,0,0], [1,1,1]])
T   = np.array([[1,1,1], [0,1,0]])
S   = np.array([[0,1,1], [1,1,0]])
Z   = np.array([[1,1,0], [0,1,1]])
Bar = np.array([[1,1,1,1]])
Box = np.array([[1,1], [1,1]])
shapes = [L, T, J, S, Z, Bar, Box]

PIECE_COLORS = [
    (255,  80,  80),
    (255, 160,  40),
    (160,  80, 255),
    ( 60, 220, 100),
    (255,  60, 140),
    ( 60, 200, 255),
    (255, 220,  40),
]

class Tetraminoe:
    def __init__(self):
        idx = random.randint(0, len(shapes) - 1)
        self.shape  = np.rot90(shapes[idx], random.randint(0, 3))
        self.color  = PIECE_COLORS[idx]
        self.row    = 0
        self.column = columns // 3

def get_random_tetraminoe():
    return Tetraminoe()

# ──────────────────────────────────────────────────────────────────────────
# Core game logic
# ──────────────────────────────────────────────────────────────────────────

def draw_grid(surface):
    for i in range(rows + 1):
        pygame.draw.line(surface, COL_GRID, (0, i*block), (width, i*block), 1)
    for j in range(columns + 1):
        pygame.draw.line(surface, COL_GRID, (j*block, 0), (j*block, height), 1)

def get_coordinates(t):
    return [(i + t.row, j + t.column)
            for i, row in enumerate(t.shape)
            for j, cell in enumerate(row) if cell == 1]

def lock_coordinates(coords, t, locked):
    for x, y in coords:
        board[x, y] = 1
        locked[(x, y)] = t.color

def draw_on_board(surface, t, locked):
    for x, y in get_coordinates(t):
        board[x, y] = 1
    for i in range(rows):
        for j in range(columns):
            if (i, j) in locked:
                board[i, j] = 1
                pygame.draw.rect(surface, locked[(i,j)],
                                 pygame.Rect(j*block, i*block, block, block))
            elif board[i, j] == 1:
                pygame.draw.rect(surface, t.color,
                                 pygame.Rect(j*block, i*block, block, block))

def draw_locked_only(surface, locked):
    for (i, j), col in locked.items():
        pygame.draw.rect(surface, col, pygame.Rect(j*block, i*block, block, block))

def falling(t):
    coords = get_coordinates(t)
    for x, y in coords:
        if x == rows - 1:
            return False
        if board[x+1, y] == 1 and (x+1, y) not in coords:
            return False
    return True

def move_tetraminoe(t):
    lv = rv = dv = True
    coords = get_coordinates(t)
    for x, y in coords:
        if y == 0 or (board[x, y-1] == 1 and (x, y-1) not in coords):
            lv = False
        if y == columns-1 or (board[x, y+1] == 1 and (x, y+1) not in coords):
            rv = False
        if x == rows-1 or (board[x+1, y] == 1 and (x+1, y) not in coords):
            dv = False
    return lv, rv, dv

def rotation_valid(t):
    cur   = get_coordinates(t)
    taken = [(i, j) for i in range(rows) for j in range(columns) if board[i,j]==1]
    rot   = np.rot90(t.shape, 1)
    for i, row in enumerate(rot):
        for j, cell in enumerate(row):
            if cell == 1:
                nx, ny = i + t.row, j + t.column
                if (nx, ny) in taken and (nx, ny) not in cur:
                    return False
                if ny > columns-1 or nx > rows-1 or ny < 0 or nx < 0:
                    return False
    return True

# ── BFS-based AI movement planner ─────────────────────────────────────────
#
# State: (row, col, rot_idx)
#   row     – top-left row of the piece bounding box
#   col     – top-left col of the piece bounding box
#   rot_idx – 0-3, index into the piece's unique rotation list
#
# Moves available each step (mirrors what a real player can do):
#   rotate_cw  – rotate piece clockwise by 90°
#   left       – shift piece one column left
#   right      – shift piece one column right
#   drop       – let the piece fall one row (gravity)
#
# The BFS finds the shortest action-sequence to reach every
# (rot_idx, final_col) placement that the agent considers, including
# those that require interleaved moves/rotations through gaps.

def _build_rotations(shape):
    """Return list of unique rotations (numpy arrays) for a piece shape."""
    rots = []
    cur  = shape
    for _ in range(4):
        if not any(np.array_equal(cur, r) for r in rots):
            rots.append(cur)
        cur = np.rot90(cur, 1)
    return rots

def _piece_fits(shape, row, col, snap_board):
    """True if `shape` placed at (row, col) doesn't overlap filled cells or go OOB."""
    ph, pw = shape.shape
    if col < 0 or col + pw > columns:
        return False
    if row < 0 or row + ph > rows:
        return False
    for dr in range(ph):
        for dc in range(pw):
            if shape[dr, dc] == 1 and snap_board[row + dr, col + dc] == 1:
                return False
    return True

def _can_drop_one(shape, row, col, snap_board):
    """True if the piece can move down one more row."""
    return _piece_fits(shape, row + 1, col, snap_board)

def bfs_plan(start_shape, start_col, start_row, snap_board):
    """
    BFS over (row, col, rot_idx) starting from the piece's current position.

    Returns a dict:
        { (rot_idx, final_col): [action, action, ...] }
    mapping every reachable *landed* placement to the shortest action sequence
    that gets there.  Actions are strings: 'rotate', 'left', 'right', 'drop'.

    `snap_board` is a board snapshot (no active piece on it) used for
    collision checks.
    """
    rotations = _build_rotations(start_shape)
    n_rots    = len(rotations)

    # Find rot_idx for the start shape
    start_rot = 0
    for i, r in enumerate(rotations):
        if np.array_equal(r, start_shape):
            start_rot = i
            break

    # BFS
    from collections import deque
    initial = (start_row, start_col, start_rot)
    visited = {initial}
    # queue entries: (row, col, rot_idx, path_so_far)
    queue   = deque()
    queue.append((start_row, start_col, start_rot, []))

    landed  = {}   # (rot_idx, col) -> path

    while queue:
        row, col, rot, path = queue.popleft()
        shape = rotations[rot]

        # Check if this piece has landed (can't drop further)
        if not _can_drop_one(shape, row, col, snap_board):
            key = (rot, col)
            if key not in landed:
                landed[key] = path
            # Don't expand from a landed state — piece is locked
            continue

        # Expand neighbours
        neighbours = []

        # 1. Rotate clockwise
        new_rot = (rot + 1) % n_rots
        new_shape = rotations[new_rot]
        # Try plain rotate; if out of bounds, try wall-kick ±1 col
        for kick in (0, -1, 1, -2, 2):
            new_col = col + kick
            if _piece_fits(new_shape, row, new_col, snap_board):
                neighbours.append((row, new_col, new_rot, path + ['rotate']))
                break

        # 2. Move left
        if _piece_fits(shape, row, col - 1, snap_board):
            neighbours.append((row, col - 1, rot, path + ['left']))

        # 3. Move right
        if _piece_fits(shape, row, col + 1, snap_board):
            neighbours.append((row, col + 1, rot, path + ['right']))

        # 4. Drop one row (gravity step — AI can "use" gravity mid-plan)
        if _can_drop_one(shape, row, col, snap_board):
            neighbours.append((row + 1, col, rot, path + ['drop']))

        for state in neighbours:
            key = state[:3]
            if key not in visited:
                visited.add(key)
                queue.append(state)

    return landed, rotations


def plan_ai_moves(t):
    """
    Ask the agent for the best target placement, then use BFS to find
    the shortest real-player-legal action sequence to reach it —
    including placements inside pockets that need interleaved moves.

    Returns a list of action strings consumed one-per-tick by run_game.
    """
    # Ask agent for best (rotated_shape, target_col)
    target_shape, target_col = agent.get_best_col_and_rotation(board, t.shape)
    if target_shape is None or target_col is None:
        return []

    # Snapshot board without the active piece
    snap = board.copy()
    for x, y in get_coordinates(t):
        snap[x, y] = 0

    landed, rotations = bfs_plan(t.shape, t.column, t.row, snap)

    # Find which rot_idx matches the agent's target shape
    target_rot = None
    for i, r in enumerate(rotations):
        if np.array_equal(r, target_shape):
            target_rot = i
            break

    if target_rot is None:
        return []

    key = (target_rot, target_col)
    if key in landed:
        # Filter out 'drop' actions — gravity handles falling;
        # we only need the steering inputs (rotate/left/right)
        return [a for a in landed[key] if a != 'drop']

    # Fallback: target unreachable via BFS (shouldn't happen often)
    # Try closest reachable column with the right rotation
    best_path  = None
    best_dist  = float('inf')
    for (rot, col), path in landed.items():
        if rot == target_rot:
            dist = abs(col - target_col)
            if dist < best_dist:
                best_dist = dist
                best_path = path
    if best_path is not None:
        return [a for a in best_path if a != 'drop']

    return []

def erase_footprints(t):
    for x, y in get_coordinates(t):
        board[x, y] = 0

def clear_lines(locked):
    global score
    cleared = 0
    cleared_idx = None
    for i in range(rows):
        if np.sum(board[i]) == columns:
            for j in range(columns):
                locked.pop((i, j), None)
                board[i, j] = 0
            cleared += 1
            cleared_idx = i
            score += 1
    if cleared > 0 and cleared_idx is not None:
        new_locked = {}
        for (x, y), color in sorted(locked.items(), reverse=True):
            if x < cleared_idx:
                new_locked[(x + cleared, y)] = color
                board[x, y] = 0
            else:
                new_locked[(x, y)] = color
        locked.clear()
        locked.update(new_locked)

def is_gameover(locked):
    return any(x == 0 for x, y in locked)

# ──────────────────────────────────────────────────────────────────────────
# UI helpers
# ──────────────────────────────────────────────────────────────────────────

def draw_bar(surface, x, y, w, h, value, max_val, color):
    pygame.draw.rect(surface, COL_BAR_BG, pygame.Rect(x, y, w, h), border_radius=3)
    fill = int(w * min(value / max(max_val, 1), 1.0))
    if fill > 0:
        pygame.draw.rect(surface, color, pygame.Rect(x, y, fill, h), border_radius=3)

def draw_column_heights_chart(surface, px, py, chart_w, chart_h):
    heights = get_column_heights(board)
    col_w   = chart_w // columns
    for i, h in enumerate(heights):
        bar_h = int((h / rows) * chart_h)
        shade = int(80 + 160 * h / rows)
        color = (40, shade, 200)
        rx = px + i * col_w
        pygame.draw.rect(surface, COL_BAR_BG,
                         pygame.Rect(rx, py, col_w-1, chart_h), border_radius=2)
        if bar_h > 0:
            pygame.draw.rect(surface, color,
                             pygame.Rect(rx, py + chart_h - bar_h, col_w-1, bar_h),
                             border_radius=2)

def section_header(surface, text, px, y, accent):
    pygame.draw.line(surface, accent, (px, y+8), (px+6, y+8), 3)
    lbl = FONT_LABEL.render(text, True, accent)
    surface.blit(lbl, (px + 10, y))
    return y + 20

def draw_side_panel(surface, next_t, pieces_placed, use_ai, paused, history_lines,
                    ai_fall_speed=0.30, slider_rect_out=None):
    px     = width + 8
    pw     = panel_width - 12
    accent = COL_ACCENT_AI if use_ai else COL_ACCENT_MAN

    pygame.draw.rect(surface, COL_PANEL_BG, pygame.Rect(width, 0, panel_width, height))
    pygame.draw.line(surface, COL_DIVIDER, (width, 0), (width, height), 2)

    y = 10

    # Mode badge
    badge_text = "AI  MODE" if use_ai else "MANUAL"
    badge_surf = FONT_MONO.render(badge_text, True, bg_color)
    bw = badge_surf.get_width() + 16
    pygame.draw.rect(surface, accent, pygame.Rect(px, y, bw, 22), border_radius=4)
    surface.blit(badge_surf, (px + 8, y + 3))
    if paused:
        ps = FONT_LABEL.render("PAUSED", True, (255, 200, 50))
        surface.blit(ps, (px + bw + 8, y + 4))
    y += 30

    # Next piece
    y = section_header(surface, "NEXT PIECE", px, y, accent)
    pb = 17
    for i, row in enumerate(next_t.shape):
        for j, cell in enumerate(row):
            if cell == 1:
                pygame.draw.rect(surface, next_t.color,
                                 pygame.Rect(px + j*pb, y + i*pb, pb-2, pb-2),
                                 border_radius=2)
    y += next_t.shape.shape[0] * pb + 8
    pygame.draw.line(surface, COL_DIVIDER, (width+4, y), (width+panel_width-4, y), 1)
    y += 8

    # Score
    y = section_header(surface, "SCORE", px, y, accent)
    ss = FONT_TITLE.render(str(score), True, COL_TEXT_BRIGHT)
    surface.blit(ss, (px, y))
    y += ss.get_height() + 2
    sub1 = FONT_SMALL.render(f"Pieces placed : {pieces_placed}", True, COL_TEXT_DIM)
    surface.blit(sub1, (px, y));  y += 16
    eff  = score / max(pieces_placed, 1)
    sub2 = FONT_SMALL.render(f"Lines/piece   : {eff:.3f}", True, COL_TEXT_DIM)
    surface.blit(sub2, (px, y));  y += 16
    if not use_ai:
        lvl_s = FONT_SMALL.render(f"Speed level   : {score // 10}", True, (255, 180, 60))
        surface.blit(lvl_s, (px, y));  y += 16
    pygame.draw.line(surface, COL_DIVIDER, (width+4, y), (width+panel_width-4, y), 1)
    y += 8

    # Board metrics
    y = section_header(surface, "BOARD METRICS", px, y, accent)
    agg_h = get_aggregate_height(board)
    holes = get_holes(board)
    bumpy = get_bumpiness(board)

    metrics = [
        ("Agg Height", agg_h, rows * columns, (255, 120,  60)),
        ("Holes",      holes,             50, (255,  60,  80)),
        ("Bumpiness",  bumpy,             60, (255, 200,  40)),
    ]
    bw2 = pw - 4
    for label, val, max_v, color in metrics:
        ls = FONT_SMALL.render(label, True, COL_TEXT_DIM)
        vs = FONT_SMALL.render(str(val), True, COL_TEXT_BRIGHT)
        surface.blit(ls, (px, y))
        surface.blit(vs, (px + bw2 - vs.get_width(), y))
        y += ls.get_height() + 1
        draw_bar(surface, px, y, bw2, 7, val, max_v, color)
        y += 12
    y += 2
    pygame.draw.line(surface, COL_DIVIDER, (width+4, y), (width+panel_width-4, y), 1)
    y += 8

    # Column heights chart
    y = section_header(surface, "COL HEIGHTS", px, y, accent)
    chart_h = 46
    draw_column_heights_chart(surface, px, y, bw2, chart_h)
    y += chart_h + 8
    pygame.draw.line(surface, COL_DIVIDER, (width+4, y), (width+panel_width-4, y), 1)
    y += 8

    # Lines-cleared sparkline
    y = section_header(surface, "LINES HISTORY", px, y, accent)
    spark_h = 32
    spark_w = bw2
    pygame.draw.rect(surface, COL_BAR_BG, pygame.Rect(px, y, spark_w, spark_h), border_radius=3)
    if history_lines:
        slot_w = spark_w / max(len(history_lines), 1)
        for i, v in enumerate(history_lines):
            bh  = int((v / 4) * spark_h) if v > 0 else 2
            bh  = min(bh, spark_h)
            col = (60, 220, 120) if v > 0 else (50, 50, 80)
            rx  = int(px + i * slot_w)
            pygame.draw.rect(surface, col,
                             pygame.Rect(rx+1, y + spark_h - bh,
                                         max(int(slot_w)-1, 1), bh),
                             border_radius=1)
    y += spark_h + 8
    pygame.draw.line(surface, COL_DIVIDER, (width+4, y), (width+panel_width-4, y), 1)
    y += 8

    # ── AI Speed Slider (AI mode only) ────────────────────────────────────
    slider_rect = pygame.Rect(0, 0, 0, 0)
    if use_ai:
        y = section_header(surface, "AI SPEED", px, y, accent)
        # Speed range: fall_speed 0.05 (fast) to 0.60 (slow)
        # Slider value maps left=slow, right=fast
        SPEED_MIN, SPEED_MAX = 0.05, 0.60
        slider_w = bw2
        slider_h = 8
        slider_rect = pygame.Rect(px, y + 4, slider_w, slider_h)
        # Draw track
        pygame.draw.rect(surface, COL_BAR_BG, slider_rect, border_radius=4)
        # Fraction: 0=slowest(right-most?), invert so right=fast
        frac = 1.0 - (ai_fall_speed - SPEED_MIN) / (SPEED_MAX - SPEED_MIN)
        frac = max(0.0, min(1.0, frac))
        # Filled portion
        fill_w = int(slider_w * frac)
        if fill_w > 0:
            pygame.draw.rect(surface, accent,
                             pygame.Rect(px, y + 4, fill_w, slider_h), border_radius=4)
        # Thumb
        thumb_x = px + fill_w
        pygame.draw.circle(surface, COL_TEXT_BRIGHT, (thumb_x, y + 4 + slider_h // 2), 7)
        pygame.draw.circle(surface, accent,          (thumb_x, y + 4 + slider_h // 2), 5)
        # Labels
        slow_s = FONT_SMALL.render("SLOW", True, COL_TEXT_DIM)
        fast_s = FONT_SMALL.render("FAST", True, COL_TEXT_DIM)
        surface.blit(slow_s, (px, y + 16))
        surface.blit(fast_s, (px + slider_w - fast_s.get_width(), y + 16))
        # Current speed label
        fps_val = int(1.0 / max(ai_fall_speed, 0.01))
        spd_s = FONT_SMALL.render(f"{fps_val} rows/s", True, COL_TEXT_BRIGHT)
        surface.blit(spd_s, (px + slider_w // 2 - spd_s.get_width() // 2, y + 16))
        y += 32
        pygame.draw.line(surface, COL_DIVIDER, (width+4, y), (width+panel_width-4, y), 1)
        y += 8

    # Write slider rect back if container provided
    if slider_rect_out is not None:
        slider_rect_out.append(slider_rect)

    # Stop / Start buttons
    btn_w2, btn_h2 = bw2, 26
    stop_col  = (160, 35, 35) if not paused else (70, 20, 20)
    start_col = (30, 140, 60) if paused     else (18, 70, 35)

    stop_rect  = pygame.Rect(px, y, btn_w2, btn_h2)
    pygame.draw.rect(surface, stop_col, stop_rect, border_radius=5)
    sl = FONT_LABEL.render("STOP", True, (255,255,255))
    surface.blit(sl, (stop_rect.centerx - sl.get_width()//2,
                       stop_rect.centery - sl.get_height()//2))
    y += btn_h2 + 5

    start_rect = pygame.Rect(px, y, btn_w2, btn_h2)
    pygame.draw.rect(surface, start_col, start_rect, border_radius=5)
    stl = FONT_LABEL.render("START", True, (255,255,255))
    surface.blit(stl, (start_rect.centerx - stl.get_width()//2,
                        start_rect.centery - stl.get_height()//2))
    y += btn_h2 + 5

    # End Game button
    end_rect = pygame.Rect(px, y, btn_w2, btn_h2)
    pygame.draw.rect(surface, (80, 40, 10), end_rect, border_radius=5)
    pygame.draw.rect(surface, (160, 80, 20), end_rect, 1, border_radius=5)
    etl = FONT_LABEL.render("END GAME", True, (255, 200, 100))
    surface.blit(etl, (end_rect.centerx - etl.get_width()//2,
                        end_rect.centery - etl.get_height()//2))

    return stop_rect, start_rect, end_rect, slider_rect

# ──────────────────────────────────────────────────────────────────────────
# Start screen
# ──────────────────────────────────────────────────────────────────────────

def draw_start_screen(surface, hovered):
    surface.fill(bg_color)
    sw = width + panel_width
    sh = height

    # Decorative blocks
    rng = random.Random(42)
    for _ in range(45):
        rx = rng.randint(0, sw)
        ry = rng.randint(0, sh)
        rs = rng.randint(8, 24)
        rc = (rng.randint(15,60), rng.randint(15,60), rng.randint(30,90))
        pygame.draw.rect(surface, rc, pygame.Rect(rx, ry, rs, rs), border_radius=2)

    cx = sw // 2

    # Title
    t1 = FONT_TITLE.render("T  E  T  R  I  S", True, (220, 220, 240))
    surface.blit(t1, (cx - t1.get_width()//2, 90))
    sub = FONT_LABEL.render("Heuristic AI  ·  Dellacherie weights", True, COL_TEXT_DIM)
    surface.blit(sub, (cx - sub.get_width()//2, 122))

    pygame.draw.line(surface, COL_DIVIDER, (cx-160, 152), (cx+160, 152), 1)

    prompt = FONT_VALUE.render("SELECT  MODE", True, COL_TEXT_BRIGHT)
    surface.blit(prompt, (cx - prompt.get_width()//2, 168))

    btn_w, btn_h = 210, 52

    # AI button
    ai_rect = pygame.Rect(cx - btn_w//2, 208, btn_w, btn_h)
    ai_col  = COL_ACCENT_AI if hovered == 0 else (0, 130, 78)
    pygame.draw.rect(surface, ai_col, ai_rect, border_radius=9)
    if hovered == 0:
        pygame.draw.rect(surface, (255,255,255), ai_rect, 2, border_radius=9)
    ai_lbl = FONT_VALUE.render("WATCH  AI  PLAY", True, (10,10,18))
    surface.blit(ai_lbl, (ai_rect.centerx - ai_lbl.get_width()//2,
                           ai_rect.centery - ai_lbl.get_height()//2))
    ai_desc = FONT_SMALL.render("Dellacherie heuristic agent", True, COL_TEXT_DIM)
    surface.blit(ai_desc, (cx - ai_desc.get_width()//2, 268))

    # Manual button
    man_rect = pygame.Rect(cx - btn_w//2, 298, btn_w, btn_h)
    man_col  = COL_ACCENT_MAN if hovered == 1 else (40, 95, 170)
    pygame.draw.rect(surface, man_col, man_rect, border_radius=9)
    if hovered == 1:
        pygame.draw.rect(surface, (255,255,255), man_rect, 2, border_radius=9)
    man_lbl = FONT_VALUE.render("PLAY  YOURSELF", True, (10,10,18))
    surface.blit(man_lbl, (man_rect.centerx - man_lbl.get_width()//2,
                            man_rect.centery - man_lbl.get_height()//2))
    man_desc = FONT_SMALL.render("Arrow keys  ·  Space to hard-drop", True, COL_TEXT_DIM)
    surface.blit(man_desc, (cx - man_desc.get_width()//2, 358))

    pygame.draw.line(surface, COL_DIVIDER, (cx-160, 382), (cx+160, 382), 1)

    # Key legend
    keys = [("← →", "Move left / right"),
            ("↑",   "Rotate"),
            ("↓",   "Soft drop"),
            ("Spc", "Hard drop")]
    ky = 394
    for k, desc in keys:
        ks = FONT_SMALL.render(k, True, COL_ACCENT_MAN)
        ds = FONT_SMALL.render(f"  {desc}", True, COL_TEXT_DIM)
        tw = ks.get_width() + ds.get_width()
        surface.blit(ks, (cx - tw//2, ky))
        surface.blit(ds, (cx - tw//2 + ks.get_width(), ky))
        ky += 17

    return ai_rect, man_rect

def show_start_screen(surface):
    clock   = pygame.time.Clock()
    hovered = None
    while True:
        mx, my = pygame.mouse.get_pos()
        ai_rect, man_rect = draw_start_screen(surface, hovered)
        hovered = (0 if ai_rect.collidepoint(mx, my)
                   else 1 if man_rect.collidepoint(mx, my) else None)
        ai_rect, man_rect = draw_start_screen(surface, hovered)
        pygame.display.flip()
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ai_rect.collidepoint(event.pos):
                    return True
                if man_rect.collidepoint(event.pos):
                    return False

# ──────────────────────────────────────────────────────────────────────────
# Game-over screen
# ──────────────────────────────────────────────────────────────────────────

def show_gameover_screen(surface, final_score, pieces_placed, use_ai):
    clock   = pygame.time.Clock()
    sw      = width + panel_width
    cx      = sw // 2
    btn_w   = 150
    btn_h   = 44
    retry_rect = pygame.Rect(cx - btn_w - 8, 355, btn_w, btn_h)
    menu_rect  = pygame.Rect(cx + 8,         355, btn_w, btn_h)
    accent     = COL_ACCENT_AI if use_ai else COL_ACCENT_MAN

    while True:
        mx, my  = pygame.mouse.get_pos()
        hovered = (0 if retry_rect.collidepoint(mx, my)
                   else 1 if menu_rect.collidepoint(mx, my) else None)

        overlay = pygame.Surface((sw, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(cx - 175, 155, 350, 275)
        pygame.draw.rect(surface, (18, 18, 32), panel, border_radius=12)
        pygame.draw.rect(surface, COL_DIVIDER,  panel, 2, border_radius=12)

        go = FONT_TITLE.render("GAME  OVER", True, (255, 60, 60))
        surface.blit(go, (cx - go.get_width()//2, 175))

        sc = FONT_VALUE.render(f"Lines cleared : {final_score}", True, accent)
        surface.blit(sc, (cx - sc.get_width()//2, 224))
        pp = FONT_LABEL.render(f"Pieces placed : {pieces_placed}", True, COL_TEXT_DIM)
        surface.blit(pp, (cx - pp.get_width()//2, 250))
        ef = FONT_LABEL.render(
            f"Efficiency    : {final_score/max(pieces_placed,1):.3f} lines/pc",
            True, COL_TEXT_DIM)
        surface.blit(ef, (cx - ef.get_width()//2, 272))

        pygame.draw.line(surface, COL_DIVIDER, (cx-140, 310), (cx+140, 310), 1)

        rc = (0, 170, 85) if hovered == 0 else (0, 100, 50)
        pygame.draw.rect(surface, rc, retry_rect, border_radius=7)
        rs = FONT_VALUE.render("RETRY", True, (255,255,255))
        surface.blit(rs, (retry_rect.centerx - rs.get_width()//2,
                           retry_rect.centery - rs.get_height()//2))

        mc = (65, 90, 200) if hovered == 1 else (35, 50, 120)
        pygame.draw.rect(surface, mc, menu_rect, border_radius=7)
        ms = FONT_VALUE.render("MENU", True, (255,255,255))
        surface.blit(ms, (menu_rect.centerx - ms.get_width()//2,
                           menu_rect.centery - ms.get_height()//2))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if retry_rect.collidepoint(event.pos):
                    return "retry"
                if menu_rect.collidepoint(event.pos):
                    return "menu"

# ──────────────────────────────────────────────────────────────────────────
# Game loop
# ──────────────────────────────────────────────────────────────────────────

def run_game(screen, use_ai):
    global board, score, paused

    board[:] = 0
    score    = 0
    paused   = False

    locked        = {}
    pieces_placed = 0
    history_lines = []

    logger.start_game()

    tetraminoe      = get_random_tetraminoe()
    next_tetraminoe = get_random_tetraminoe()

    # AI step queue: list of 'rotate'/'left'/'right' executed one per timer tick.
    # 'drop' steps are stripped — gravity handles falling independently.
    # After every gravity drop we re-plan from the new row so the BFS path
    # stays valid even as the piece descends into tighter spaces.
    ai_queue      = plan_ai_moves(tetraminoe) if use_ai else []
    # ai_move_speed is recalculated each frame to stay proportional to fall_speed
    # so the AI always has enough steering steps per gravity tick.
    ai_move_speed = 0.055
    ai_move_time  = 0.0

    clock      = pygame.time.Clock()
    # AI fall speed: controlled by slider. Manual: starts at 0.40, speeds up over time.
    AI_SPEED_MIN, AI_SPEED_MAX = 0.05, 0.60
    ai_fall_speed  = 0.30   # mutable for AI slider
    fall_speed     = 0.40 if not use_ai else ai_fall_speed
    fall_time      = 0.0

    # Slider drag state
    dragging_slider = False
    stop_rect  = start_rect = end_rect = slider_rect = pygame.Rect(0, 0, 0, 0)

    # Manual mode: speed up every 10 lines cleared
    manual_speed_level = 0

    while True:
        dt = clock.tick(60)
        mx, my = pygame.mouse.get_pos()

        # ── Events ────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if stop_rect.collidepoint(event.pos):
                    paused = True
                elif start_rect.collidepoint(event.pos):
                    paused = False
                    fall_time    = 0.0
                    ai_move_time = 0.0
                elif end_rect.collidepoint(event.pos):
                    logger.end_game()
                    return "menu"
                elif use_ai and slider_rect.width > 0 and slider_rect.collidepoint(event.pos):
                    dragging_slider = True

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging_slider = False

            if event.type == pygame.MOUSEMOTION and dragging_slider and use_ai:
                rel = (mx - slider_rect.x) / max(slider_rect.width, 1)
                rel = max(0.0, min(1.0, rel))
                # rel=0 → slowest, rel=1 → fastest
                ai_fall_speed = AI_SPEED_MAX - rel * (AI_SPEED_MAX - AI_SPEED_MIN)
                fall_speed = ai_fall_speed

            if event.type == pygame.KEYDOWN and not use_ai and not paused:
                lv, rv, dv = move_tetraminoe(tetraminoe)
                if event.key == pygame.K_LEFT and lv:
                    erase_footprints(tetraminoe)
                    tetraminoe.column -= 1
                elif event.key == pygame.K_RIGHT and rv:
                    erase_footprints(tetraminoe)
                    tetraminoe.column += 1
                elif event.key == pygame.K_DOWN and dv:
                    erase_footprints(tetraminoe)
                    tetraminoe.row += 1
                elif event.key == pygame.K_UP and rotation_valid(tetraminoe):
                    erase_footprints(tetraminoe)
                    tetraminoe.shape = np.rot90(tetraminoe.shape, 1)
                elif event.key == pygame.K_SPACE:
                    erase_footprints(tetraminoe)
                    while falling(tetraminoe):
                        tetraminoe.row += 1

        if not paused:
            elapsed = dt / 1000.0

            # ── Scale AI steering speed to match fall speed ───────────
            # Target 4 steering steps per gravity tick so the AI can
            # always finish repositioning before the piece lands,
            # regardless of how fast the slider is set.
            if use_ai:
                ai_move_speed = max(fall_speed / 4.0, 1.0 / 60.0)

            # ── AI steering (one action per ai_move_speed seconds) ────
            if use_ai and ai_queue:
                ai_move_time += elapsed
                if ai_move_time >= ai_move_speed:
                    ai_move_time = 0.0
                    step = ai_queue.pop(0)
                    erase_footprints(tetraminoe)

                    if step == 'rotate':
                        if rotation_valid(tetraminoe):
                            tetraminoe.shape = np.rot90(tetraminoe.shape, 1)
                            # Wall-kick: clamp if rotation pushed piece OOB
                            pw = tetraminoe.shape.shape[1]
                            if tetraminoe.column + pw > columns:
                                tetraminoe.column = columns - pw
                            if tetraminoe.column < 0:
                                tetraminoe.column = 0

                    elif step == 'left':
                        lv, _, _ = move_tetraminoe(tetraminoe)
                        if lv:
                            tetraminoe.column -= 1

                    elif step == 'right':
                        _, rv, _ = move_tetraminoe(tetraminoe)
                        if rv:
                            tetraminoe.column += 1

            # ── Gravity ───────────────────────────────────────────────
            fall_time += elapsed
            if fall_time >= fall_speed:
                fall_time = 0.0

                if falling(tetraminoe):
                    erase_footprints(tetraminoe)
                    tetraminoe.row += 1
                    # Re-plan from the new row so BFS paths into pockets
                    # remain valid as the board state changes — this is
                    # intentional and matches the original behaviour.
                    # Crucially we do NOT reset ai_move_time here so that
                    # accumulated steering time carries over and steps fire
                    # immediately at high speeds.
                    if use_ai:
                        ai_queue = plan_ai_moves(tetraminoe)
                else:
                    # Lock piece
                    coords = get_coordinates(tetraminoe)
                    lock_coordinates(coords, tetraminoe, locked)

                    tetraminoe      = next_tetraminoe
                    next_tetraminoe = get_random_tetraminoe()

                    lines_before = score
                    clear_lines(locked)
                    lines_just = score - lines_before

                    history_lines.append(lines_just)
                    if len(history_lines) > 20:
                        history_lines.pop(0)

                    # Re-plan only when a new piece spawns
                    ai_queue     = plan_ai_moves(tetraminoe) if use_ai else []
                    ai_move_time = 0.0

                    pieces_placed += 1
                    logger.log_step(lines_cleared=lines_just, score=score)

                    # ── Manual mode: speed up every 10 lines ──────────
                    if not use_ai:
                        new_level = score // 10
                        if new_level > manual_speed_level:
                            manual_speed_level = new_level
                            # Speed up by 0.03s per level, floor at 0.08s
                            fall_speed = max(0.08, 0.40 - manual_speed_level * 0.03)

        # ── Draw ──────────────────────────────────────────────────────
        screen.fill(bg_color)
        if paused:
            draw_locked_only(screen, locked)
        else:
            draw_on_board(screen, tetraminoe, locked)
        draw_grid(screen)

        stop_rect, start_rect, end_rect, slider_rect = draw_side_panel(
            screen, next_tetraminoe, pieces_placed,
            use_ai, paused, history_lines,
            ai_fall_speed=ai_fall_speed)

        pygame.display.flip()

        # ── Game over ─────────────────────────────────────────────────
        if not paused and is_gameover(locked):
            logger.end_game()
            logger.print_summary()
            return show_gameover_screen(screen, score, pieces_placed, use_ai)

# ──────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────

def main():
    init_fonts()
    screen = pygame.display.set_mode((width + panel_width, height))
    pygame.display.set_caption("Tetris  ·  AI Edition")

    while True:
        use_ai = show_start_screen(screen)
        result = "retry"
        while result == "retry":
            result = run_game(screen, use_ai)
        # result == "menu" -> back to start screen

main()
