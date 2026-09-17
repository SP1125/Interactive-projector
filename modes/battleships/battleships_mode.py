# modes/battleships/battleships_mode.py

import math
import time

import cv2
import numpy as np
import pygame

from input_state import InputState
from modes.base import GameMode
from events import EventType, GameEvent

from .game_board import GameBoard, ShipGenerator, GRID_ROWS, GRID_COLS
from .drawing import (
    draw_ocean_background,
    draw_ocean_tile,
    draw_hit_tile,
    draw_miss_tile,
    draw_sunk_tile,
    draw_ship_icon,
    draw_glow_rect,
    draw_glow_circle,
    draw_text_centred,
    draw_text,
    CYAN, WHITE, P1_RED, P2_BLUE, AMBER, ORANGE, MISS_BLUE,
)

# ── Layout constants ──────────────────────────────────────────────────────────
CELL      = 52          # px per grid cell
GRID_W    = CELL * GRID_COLS
GRID_H    = CELL * GRID_ROWS
MARGIN_X  = 40          # left margin before grid
MARGIN_Y  = 120         # top margin (leaves room for HUD)

# Icon panel (right of grid)
ICON_PANEL_X  = MARGIN_X + GRID_W + 24
ICON_PANEL_W  = 180
ICON_H        = 36

# Player colours (BGR for OpenCV)
P1_COLOR = P1_RED
P2_COLOR = P2_BLUE


def _cv2_surface(frame: np.ndarray) -> pygame.Surface:
    """Convert a BGR OpenCV frame to a pygame Surface."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # pygame expects (width, height, 3) with axes swapped
    return pygame.surfarray.make_surface(rgb.swapaxes(0, 1))


class BattleshipsMode(GameMode):

    def __init__(self) -> None:
        self.board = GameBoard()
        ShipGenerator.place_ships(self.board)

        self.current_player = 1
        self.p1_score       = 0
        self.p2_score       = 0

        self.flash_cells: dict[tuple, float] = {}  # (r,c) → timestamp

        self.cursor_x    = 0
        self.cursor_y    = 0
        self.finger_down = False

        self._anim_t     = 0.0   # animation phase, wraps 0→1
        self._bg_cache = None
        self._last_anim_t = -1.0

        # Canvas dimensions — set on first render from surface size
        self._W = 1280
        self._H = 720



    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event: GameEvent) -> None:
        x = event.payload.get("x", 0)
        y = event.payload.get("y", 0)

        if event.type == EventType.DRAG:
            self.cursor_x = x
            self.cursor_y = y

        elif event.type == EventType.TAP:
            self.cursor_x    = x
            self.cursor_y    = y
            self.finger_down = True
            self._handle_tap(x, y)

        elif event.type == EventType.RELEASE:
            self.finger_down = False

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, input_state: InputState) -> None:
        now = time.time()
        self._anim_t = (now % 4.0) / 4.0   # 4-second loop

        expired = [cell for cell, t in self.flash_cells.items() if now - t > 0.4]
        for cell in expired:
            del self.flash_cells[cell]

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface, input_state: InputState) -> None:
        self._W, self._H = surface.get_size()

        # Build a fresh BGR canvas
        frame = np.zeros((self._H, self._W, 3), dtype=np.uint8)

        draw_ocean_background(frame, self._anim_t)
        self._draw_hud(frame)
        self._draw_grid(frame)
        self._draw_ship_panel(frame)
        self._draw_cursor(frame)

        surface.blit(_cv2_surface(frame), (0, 0))



    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(self, img: np.ndarray) -> None:
        W = self._W

        # Title
        draw_text_centred(img, "BATTLESHIPS", W // 2, 36,
                          font_scale=1.1, color=CYAN, thickness=2)

        # Player 1 panel (left)
        self._draw_player_badge(img, 1, 30, 60)

        # Player 2 panel (right)
        self._draw_player_badge(img, 2, W - 230, 60)

        # Whose turn indicator
        turn_color = P1_COLOR if self.current_player == 1 else P2_COLOR
        label = f"PLAYER {self.current_player}'S TURN"
        draw_text_centred(img, label, W // 2, 72,
                          font_scale=0.55, color=turn_color, thickness=1)

        # Divider line
        cv2.line(img, (0, 95), (W, 95), tuple(int(c * 0.4) for c in CYAN), 1)

    def _draw_player_badge(self, img: np.ndarray, player: int, x: int, y: int) -> None:
        color  = P1_COLOR if player == 1 else P2_COLOR
        score  = self.p1_score if player == 1 else self.p2_score
        ships  = sum(1 for s in self.board.ships.values()
                     if not s.is_sunk and (s.sunk_by_player != (2 if player == 1 else 1)))
        label  = f"P{player}  SCORE: {score}  SHIPS LEFT: {self.board.remaining_ships}"

        draw_glow_rect(img, x, y - 18, x + 220, y + 14, color,
                       border_thickness=1, glow_radius=6, glow_alpha=0.2)
        draw_text(img, label, x + 8, y + 6, font_scale=0.45, color=color, thickness=1)

    # ── Grid ──────────────────────────────────────────────────────────────────

    def _draw_grid(self, img: np.ndarray) -> None:
        now = time.time()

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = MARGIN_X + c * CELL
                y = MARGIN_Y + r * CELL

                flashing  = (r, c) in self.flash_cells
                revealed  = self.board.revealed[r][c]
                cell_val  = self.board.board[r][c]

                if flashing:
                    # White flash on recent reveal
                    cv2.rectangle(img, (x, y), (x + CELL, y + CELL), WHITE, -1)
                    cv2.rectangle(img, (x, y), (x + CELL - 1, y + CELL - 1), CYAN, 1)

                elif not revealed:
                    draw_ocean_tile(img, x, y, CELL, CELL, r, c)

                elif cell_val == 0:
                    draw_miss_tile(img, x, y, CELL, CELL)

                else:
                    ship = self.board.ships.get(cell_val)
                    if ship and ship.is_sunk:
                        player_color = P1_COLOR if ship.sunk_by_player == 1 else P2_COLOR
                        tile_index = ship.cells.index((r, c))
                        draw_sunk_tile(img, x, y, CELL, CELL,
                                       player_color, ship.size,
                                       tile_index, ship.horizontal, r, c)
                    else:
                        draw_hit_tile(img, x, y, CELL, CELL)

        # Grid border glow
        gx1 = MARGIN_X - 2
        gy1 = MARGIN_Y - 2
        gx2 = MARGIN_X + GRID_W + 2
        gy2 = MARGIN_Y + GRID_H + 2
        player_color = P1_COLOR if self.current_player == 1 else P2_COLOR
        draw_glow_rect(img, gx1, gy1, gx2, gy2, player_color,
                       border_thickness=2, glow_radius=14, glow_alpha=0.18)

        # Hovered cell highlight
        hc = (self.cursor_x - MARGIN_X) // CELL
        hr = (self.cursor_y - MARGIN_Y) // CELL
        if 0 <= hr < GRID_ROWS and 0 <= hc < GRID_COLS:
            hx = MARGIN_X + hc * CELL
            hy = MARGIN_Y + hr * CELL
            overlay = img.copy()
            cv2.rectangle(overlay, (hx, hy), (hx + CELL, hy + CELL), CYAN, -1)
            cv2.addWeighted(overlay, 0.15, img, 0.85, 0, img)
            cv2.rectangle(img, (hx, hy), (hx + CELL - 1, hy + CELL - 1), CYAN, 1)

    # ── Ship icon panel ───────────────────────────────────────────────────────

    def _draw_ship_panel(self, img: np.ndarray) -> None:
        px = ICON_PANEL_X
        py = MARGIN_Y

        draw_text(img, "FLEET", px, py - 10,
                  font_scale=0.45, color=CYAN, thickness=1)

        unique_sizes = []
        seen = set()
        for ship in self.board.ships.values():
            if ship.size not in seen:
                seen.add(ship.size)
                unique_sizes.append(ship)
        unique_sizes.sort(key=lambda s: -s.size)

        for i, ship in enumerate(unique_sizes):
            iy  = py + i * (ICON_H + 8)
            iw  = max(40, ship.size * 20)

            sunk_color = P1_COLOR if ship.sunk_by_player == 1 else P2_COLOR
            draw_ship_icon(img, px, iy, iw, ICON_H - 4,
                           ship.size, ship.is_sunk,
                           sunk_color if ship.is_sunk else None)

            label = f"x{sum(1 for s in self.board.ships.values() if s.size == ship.size)}"
            draw_text(img, label, px + iw + 6, iy + ICON_H // 2 + 4,
                      font_scale=0.38, color=CYAN if not ship.is_sunk else AMBER)

    # ── Cursor ────────────────────────────────────────────────────────────────

    def _draw_cursor(self, img: np.ndarray) -> None:
        color = P1_COLOR if self.current_player == 1 else P2_COLOR
        draw_glow_circle(img, self.cursor_x, self.cursor_y, 8,
                         color, thickness=-1, glow_radius=16, glow_alpha=0.3)
        # Crosshair lines
        cv2.line(img, (self.cursor_x - 14, self.cursor_y),
                      (self.cursor_x - 9,  self.cursor_y), color, 1, cv2.LINE_AA)
        cv2.line(img, (self.cursor_x + 9,  self.cursor_y),
                      (self.cursor_x + 14, self.cursor_y), color, 1, cv2.LINE_AA)
        cv2.line(img, (self.cursor_x, self.cursor_y - 14),
                      (self.cursor_x, self.cursor_y - 9),  color, 1, cv2.LINE_AA)
        cv2.line(img, (self.cursor_x, self.cursor_y + 9),
                      (self.cursor_x, self.cursor_y + 14), color, 1, cv2.LINE_AA)

    # ── Tap logic ─────────────────────────────────────────────────────────────

    def _handle_tap(self, x: int, y: int) -> None:
        col = (x - MARGIN_X) // CELL
        row = (y - MARGIN_Y) // CELL
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            self._reveal(row, col)

    def _reveal(self, row: int, col: int) -> None:
        if self.board.revealed[row][col]:
            return

        self.board.revealed[row][col] = True
        self.flash_cells[(row, col)]  = time.time()

        ship_id  = self.board.board[row][col]

        if ship_id == 0:
            # Miss — switch player
            self.current_player = 2 if self.current_player == 1 else 1
            return

        ship = self.board.ships[ship_id]
        ship.hits_remaining -= 1

        if ship.is_sunk:
            ship.sunk_by_player = self.current_player
            if self.current_player == 1:
                self.p1_score += 1
            else:
                self.p2_score += 1
            # Reveal and flash entire ship
            for (r, c) in ship.cells:
                self.board.revealed[r][c] = True
                self.flash_cells[(r, c)]  = time.time()

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset_board(self) -> None:
        self.board = GameBoard()
        ShipGenerator.place_ships(self.board)
        self.current_player = 1
        self.flash_cells    = {}

    def _get_background(self, frame):
    # only redraw background every 3rd frame
        if self._frame_count % 3 == 0:
            self._bg_cache = np.zeros((self._H, self._W, 3), dtype=np.uint8)
            draw_ocean_background(self._bg_cache, self._anim_t)
        frame[:] = self._bg_cache