# drawing.py

import cv2
import numpy as np
import math


# ── Colour palette (BGR for OpenCV) ──────────────────────────────────────────
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
CYAN        = (255, 229, 0)    # #00E5FF in BGR
DARK_OCEAN  = (30,  20,  5)    # very dark teal
P1_RED      = (68,  23, 255)   # #FF1744
P2_BLUE     = (255, 121, 41)   # #2979FF
ORANGE      = (0,   101, 230)  # #E65100
AMBER       = (0,   171, 255)  # #FFAB00
MISS_BLUE   = (255, 216, 128)  # #80D8FF
DARK_NAVY   = (40,  21,  4)
MID_OCEAN   = (37,  20,  4)


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_text_centred(img, text, cx, cy, font_scale, color, thickness=1, font=cv2.FONT_HERSHEY_DUPLEX):
    (w, h), _ = cv2.getTextSize(text, font, font_scale, thickness)
    cv2.putText(img, text, (int(cx - w / 2), int(cy + h / 2)), font, font_scale, color, thickness, cv2.LINE_AA)


def draw_text(img, text, x, y, font_scale, color, thickness=1, font=cv2.FONT_HERSHEY_DUPLEX):
    cv2.putText(img, text, (int(x), int(y)), font, font_scale, color, thickness, cv2.LINE_AA)


def draw_glow_rect(img, x1, y1, x2, y2, color, border_thickness=2, glow_radius=10, glow_alpha=0.3):
    """Draw a rectangle with a soft glow border."""
    overlay = img.copy()
    for r in range(glow_radius, 0, -2):
        alpha = glow_alpha * (1 - r / glow_radius)
        cv2.rectangle(overlay, (x1 - r, y1 - r), (x2 + r, y2 + r), color, 1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    cv2.rectangle(img, (x1, y1), (x2, y2), color, border_thickness)


def draw_glow_circle(img, cx, cy, radius, color, thickness=-1, glow_radius=12, glow_alpha=0.25):
    overlay = img.copy()
    for r in range(glow_radius, 0, -3):
        alpha = glow_alpha * (1 - r / glow_radius)
        cv2.circle(overlay, (cx, cy), radius + r, color, 1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    cv2.circle(img, (cx, cy), radius, color, thickness)


def draw_ocean_background(img, t: float):
    """Full-screen animated ocean. t = 0..1 animation phase."""
    h, w = img.shape[:2]

    # Deep gradient: top dark sky → bottom abyss
    for y in range(h):
        frac = y / h
        if frac < 0.35:
            sky_t = frac / 0.35
            color = lerp_color((2, 8, 10), (4, 21, 30), sky_t)
        else:
            ocean_t = (frac - 0.35) / 0.65
            color = lerp_color((4, 21, 30), (2, 12, 18), ocean_t)
        img[y, :] = color

    # Stars (top 35% of screen)
    rng = np.random.RandomState(42)
    for i in range(40):
        sx = int(rng.random() * w)
        sy = int(rng.random() * h * 0.35)
        brightness = int(60 + 120 * abs(math.sin(t * 2 * math.pi * (0.4 + i * 0.07) + i)))
        r = max(1, int(rng.random() * 2))
        cv2.circle(img, (sx, sy), r, (brightness, brightness, brightness), -1)

    # Horizon glow line
    horizon_y = int(h * 0.42)
    for dx in range(w):
        alpha = math.sin(dx / w * math.pi)  # fade in/out
        intensity = int(80 * alpha)
        if 0 <= horizon_y < h:
            b, g, r_val = img[horizon_y, dx]
            img[horizon_y, dx] = (
                min(255, b + intensity),
                min(255, g + intensity),
                min(255, r_val + 40),
            )

    # Animated wave bands
    wave_configs = [
        (0.44, (48, 30, 4),  14, 1.1, 0.0),
        (0.48, (46, 28, 5),  11, 1.6, 0.4),
        (0.52, (44, 24, 4),   9, 2.0, 0.9),
        (0.57, (40, 20, 3),   7, 1.4, 1.5),
        (0.62, (32, 14, 2),   5, 1.8, 2.1),
        (0.68, (24, 10, 2),   4, 1.2, 1.8),
        (0.78, (16,  8, 1),   3, 1.5, 0.3),
    ]
    for y_frac, color, amp, freq, off in wave_configs:
        base_y = h * y_frac
        pts = []
        for x in range(0, w, 3):
            y = int(base_y + amp * math.sin(x / w * 2 * math.pi * freq + t * 2 * math.pi + off))
            pts.append([x, y])
        pts += [[w, h], [0, h]]
        poly = np.array(pts, dtype=np.int32)
        cv2.fillPoly(img, [poly], color)

    # Cyan shimmer lines on waves
    for i in range(4):
        y_frac = 0.45 + i * 0.055
        base_y = h * y_frac
        phase = t * 2 * math.pi + i * 0.8
        prev = None
        for x in range(0, w, 4):
            y = int(base_y + 3 * math.sin(x / w * math.pi * 3 + phase))
            if prev:
                alpha = 0.06 + 0.03 * abs(math.sin(phase + i))
                overlay = img.copy()
                cv2.line(overlay, prev, (x, y), CYAN, 1)
                cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
            prev = (x, y)

    # Distant ship silhouette on horizon
    ship_x = int(w * 0.60)
    ship_y = horizon_y - 18
    ship_color = (26, 14, 8)
    hull_pts = np.array([
        [ship_x, ship_y + 18],
        [ship_x + int(w*0.03), ship_y + 8],
        [ship_x + int(w*0.18), ship_y + 8],
        [ship_x + int(w*0.21), ship_y + 18],
    ], dtype=np.int32)
    cv2.fillPoly(img, [hull_pts], ship_color)
    # Bridge
    cv2.rectangle(img,
        (ship_x + int(w*0.07), ship_y - 2),
        (ship_x + int(w*0.12), ship_y + 8),
        ship_color, -1)
    # Tower
    cv2.rectangle(img,
        (ship_x + int(w*0.09), ship_y - 14),
        (ship_x + int(w*0.11), ship_y - 2),
        ship_color, -1)

    # Sweeping searchlight from distant ship
    beam_angle = math.sin(t * 2 * math.pi * 0.3) * 0.18
    bx = ship_x + int(w * 0.10)
    by = ship_y - 10
    beam_len = int(h * 0.35)
    end_x = int(bx + beam_len * math.sin(beam_angle))
    end_y = int(by - beam_len * math.cos(beam_angle))
    overlay = img.copy()
    # Draw a thin triangle for the beam
    spread = int(beam_len * 0.15)
    tri_pts = np.array([
        [bx, by],
        [end_x - spread, end_y],
        [end_x + spread, end_y],
    ], dtype=np.int32)
    cv2.fillPoly(overlay, [tri_pts], (20, 20, 20))
    cv2.addWeighted(overlay, 0.07, img, 0.93, 0, img)


def draw_ocean_tile(img, x, y, w, h, grid_row, grid_col):
    """Draw a single ocean tile with depth shading and wave shimmer."""
    depth_t = grid_row / 9.0
    base = lerp_color((63, 42, 10), (26, 14, 2), depth_t)
    cv2.rectangle(img, (x, y), (x + w, y + h), base, -1)

    phase = grid_col * 0.7 + grid_row * 0.4
    shimmer_y = y + int(h * (0.3 + 0.25 * math.sin(phase)))
    shimmer_alpha = 0.07 + 0.05 * abs(math.sin(phase * 1.3))

    overlay = img.copy()
    cv2.line(overlay, (x, shimmer_y), (x + w, shimmer_y), CYAN, 1)
    cv2.addWeighted(overlay, shimmer_alpha, img, 1 - shimmer_alpha, 0, img)

    # Specular dot
    spec_x = x + int(w * ((math.sin(phase * 3.7) * 0.5 + 0.5) * 0.6 + 0.2))
    spec_y = y + int(h * ((math.cos(phase * 2.3) * 0.5 + 0.5) * 0.4 + 0.1))
    cv2.circle(img, (spec_x, spec_y), 1, (200, 220, 130), -1)

    # Cyan border
    cv2.rectangle(img, (x, y), (x + w - 1, y + h - 1), CYAN, 1)


def draw_hit_tile(img, x, y, w, h):
    """Orange fire tile."""
    cv2.rectangle(img, (x, y), (x + w, y + h), ORANGE, -1)
    # Flame: bright centre fading out
    cx, cy = x + w // 2, y + h // 2
    cv2.circle(img, (cx, cy + h // 6), h // 4, AMBER, -1)
    cv2.circle(img, (cx, cy - h // 8), h // 5, WHITE, -1)
    # Border
    cv2.rectangle(img, (x, y), (x + w - 1, y + h - 1), AMBER, 1)


def draw_miss_tile(img, x, y, w, h):
    """Dark tile with a cyan X cross."""
    cv2.rectangle(img, (x, y), (x + w, y + h), (30, 20, 16), -1)
    pad = max(2, w // 5)
    cv2.line(img, (x + pad, y + pad), (x + w - pad, y + h - pad), MISS_BLUE, 2, cv2.LINE_AA)
    cv2.line(img, (x + w - pad, y + pad), (x + pad, y + h - pad), MISS_BLUE, 2, cv2.LINE_AA)
    cv2.rectangle(img, (x, y), (x + w - 1, y + h - 1), (60, 40, 30), 1)


def draw_sunk_tile(img, x, y, w, h, player_color, ship_size, tile_index, is_horizontal, grid_row, grid_col):
    """Player-coloured tile with ship segment and fire overlay."""
    # Base colour: player colour tinted
    overlay_color = tuple(int(c * 0.85) for c in player_color)
    cv2.rectangle(img, (x, y), (x + w, y + h), overlay_color, -1)

    # Hull segment
    hull_color = (26, 26, 26)
    deck_color = (42, 42, 42)
    is_bow   = tile_index == 0
    is_stern = tile_index == ship_size - 1

    deck_top = y + h // 4
    hull_bot = y + int(h * 0.82)

    # Draw rotated if vertical
    if not is_horizontal:
        # For vertical ships swap the drawing axes
        _draw_hull_v(img, x, y, w, h, is_bow, is_stern, deck_color, hull_color, ship_size, tile_index)
    else:
        _draw_hull_h(img, x, y, w, h, is_bow, is_stern, deck_color, hull_color, ship_size, tile_index)

    # Accent stripe
    acc = tuple(min(255, int(c * 1.4)) for c in player_color)
    cv2.rectangle(img, (x, y + int(h * 0.68)), (x + w, y + int(h * 0.74)), acc, -1)

    # Fire overlay — simple flame shapes
    rng = np.random.RandomState(grid_row * 10 + grid_col)
    fx = x + int(w * (0.2 + rng.random() * 0.6))
    _draw_flame(img, fx, y + int(h * 0.85), w // 4, h // 2)
    _draw_flame(img, x + w - fx + x, y + int(h * 0.80), w // 5, h // 3)

    # Border
    cv2.rectangle(img, (x, y), (x + w - 1, y + h - 1), tuple(min(255, c + 60) for c in player_color), 1)


def _draw_hull_h(img, x, y, w, h, is_bow, is_stern, deck_color, hull_color, ship_size, tile_index):
    deck_top = y + h // 4
    deck_bot = y + int(h * 0.72)
    hull_bot = y + int(h * 0.82)

    if is_bow and is_stern:
        pts = np.array([[x + w//8, deck_top], [x + 7*w//8, deck_top],
                        [x + w - 2, deck_bot], [x + 2, deck_bot]], np.int32)
        cv2.fillPoly(img, [pts], hull_color)
    elif is_bow:
        pts = np.array([[x, deck_top], [x + w, deck_top],
                        [x + w, hull_bot], [x + w//10, hull_bot],
                        [x, deck_bot]], np.int32)
        cv2.fillPoly(img, [pts], hull_color)
    elif is_stern:
        pts = np.array([[x, deck_top], [x + w, deck_top],
                        [x + w, deck_bot], [x + 9*w//10, hull_bot],
                        [x, hull_bot]], np.int32)
        cv2.fillPoly(img, [pts], hull_color)
    else:
        cv2.rectangle(img, (x, deck_top), (x + w, hull_bot), hull_color, -1)

    # Ship-specific detail
    mid_y = y + h // 3
    if ship_size >= 4 and tile_index == 1:
        cv2.rectangle(img, (x + w//8, y + h//8), (x + 7*w//8, deck_top), deck_color, -1)
    if ship_size == 3 and tile_index == 1:
        cv2.rectangle(img, (x + w//6, y + h//10), (x + 5*w//6, deck_top), deck_color, -1)
    if ship_size == 2 and is_bow:
        cv2.rectangle(img, (x + w//5, y + h//6), (x + 3*w//4, deck_top), deck_color, -1)


def _draw_hull_v(img, x, y, w, h, is_bow, is_stern, deck_color, hull_color, ship_size, tile_index):
    # Vertical ship — treat w/h roles swapped
    left  = x + w // 4
    right = x + int(w * 0.76)
    top   = y
    bot   = y + h

    if is_bow and is_stern:
        pts = np.array([[left, top + h//8], [right, top + h//8],
                        [right, bot - h//8], [left, bot - h//8]], np.int32)
        cv2.fillPoly(img, [pts], hull_color)
    elif is_bow:
        pts = np.array([[left + w//10, top], [right - w//10, top],
                        [right, top + h//2], [right, bot],
                        [left, bot], [left, top + h//2]], np.int32)
        cv2.fillPoly(img, [pts], hull_color)
    elif is_stern:
        pts = np.array([[left, top], [right, top],
                        [right, bot - h//2], [right - w//10, bot],
                        [left + w//10, bot], [left, bot - h//2]], np.int32)
        cv2.fillPoly(img, [pts], hull_color)
    else:
        cv2.rectangle(img, (left, top), (right, bot), hull_color, -1)


def _draw_flame(img, cx, base_y, fw, fh):
    """Draw a teardrop flame shape."""
    pts = []
    steps = 16
    for i in range(steps + 1):
        angle = math.pi * i / steps
        px = cx + int(fw * math.sin(angle))
        py = base_y - int(fh * (1 - math.cos(angle)) / 2)
        pts.append([px, py])
    pts = np.array(pts, dtype=np.int32)
    cv2.fillPoly(img, [pts], AMBER)
    # Bright inner core
    cv2.circle(img, (cx, base_y - fh // 3), max(1, fw // 3), WHITE, -1)


def draw_ship_icon(img, x, y, icon_w, icon_h, ship_size: int, sunk: bool = False, sunk_color=None):
    """
    Draw a top-down ship icon at (x,y) sized icon_w × icon_h.
    Each ship size has a unique silhouette.
    """
    color     = sunk_color if (sunk and sunk_color) else (85, 78, 69)   # #455A64 BGR-ish
    deck_col  = (100, 90, 78)
    accent    = CYAN if not sunk else (min(255, color[0]+60), min(255, color[1]+60), min(255, color[2]+60))

    hull_top = y + icon_h // 4
    hull_bot = y + int(icon_h * 0.76)

    # Hull body (all sizes share the same outer hull)
    pts = np.array([
        [x + icon_w // 12, hull_top],
        [x + 11 * icon_w // 12, hull_top],
        [x + icon_w - 2, hull_bot],
        [x + 2, hull_bot],
    ], np.int32)
    cv2.fillPoly(img, [pts], color)

    # Unique superstructures per size
    if ship_size == 5:  # Carrier — flat runway stripe + island
        cv2.rectangle(img,
            (x + icon_w//12, y + int(icon_h*0.43)),
            (x + 11*icon_w//12, y + int(icon_h*0.57)),
            deck_col, -1)
        cv2.rectangle(img,
            (x + int(icon_w*0.62), y + int(icon_h*0.12)),
            (x + int(icon_w*0.82), hull_top),
            deck_col, -1)
        cv2.line(img, (x + int(icon_w*0.70), y + int(icon_h*0.12)),
                      (x + int(icon_w*0.70), y + int(icon_h*0.02)), accent, 1)

    elif ship_size == 4:  # Battleship — centre bridge + two gun turrets
        cv2.rectangle(img,
            (x + icon_w//3, y + int(icon_h*0.12)),
            (x + 2*icon_w//3, hull_top),
            deck_col, -1)
        cv2.line(img, (x + icon_w//2, y + int(icon_h*0.12)),
                      (x + icon_w//2, y), accent, 1)
        # Front gun
        cv2.rectangle(img, (x + icon_w//12, hull_top), (x + icon_w//4, y + int(icon_h*0.48)), deck_col, -1)
        cv2.line(img, (x + icon_w//8, hull_top), (x, y + int(icon_h*0.42)), deck_col, 2)
        # Rear gun
        cv2.rectangle(img, (x + 3*icon_w//4, hull_top), (x + 11*icon_w//12, y + int(icon_h*0.48)), deck_col, -1)
        cv2.line(img, (x + 7*icon_w//8, hull_top), (x + icon_w, y + int(icon_h*0.42)), deck_col, 2)

    elif ship_size == 3:  # Destroyer — sleek bridge offset forward
        cv2.rectangle(img,
            (x + icon_w//5, y + int(icon_h*0.14)),
            (x + icon_w//2, hull_top),
            deck_col, -1)
        # Mast with crossbar
        cv2.line(img, (x + icon_w//3, y + int(icon_h*0.14)),
                      (x + icon_w//3, y), deck_col, 1)
        cv2.line(img, (x + icon_w//5, y + int(icon_h*0.06)),
                      (x + icon_w//2, y + int(icon_h*0.06)), deck_col, 1)
        # Torpedo tubes rear
        cv2.rectangle(img,
            (x + int(icon_w*0.60), y + int(icon_h*0.38)),
            (x + int(icon_w*0.88), y + int(icon_h*0.58)),
            deck_col, -1)

    elif ship_size == 2:  # Patrol — small rounded wheelhouse
        cv2.rectangle(img,
            (x + icon_w//5, y + int(icon_h*0.18)),
            (x + 3*icon_w//5, hull_top),
            deck_col, -1)
        cv2.line(img, (x + icon_w//3, y + int(icon_h*0.18)),
                      (x + icon_w//3, y + int(icon_h*0.04)), deck_col, 1)

    # Accent stripe along waterline
    cv2.rectangle(img,
        (x + icon_w//12, y + int(icon_h*0.68)),
        (x + 11*icon_w//12, y + int(icon_h*0.74)),
        accent, -1)

    # If sunk, add fire overlay
    if sunk:
        for fx_frac in [0.25, 0.55, 0.80]:
            fx = x + int(icon_w * fx_frac)
            _draw_flame(img, fx, y + int(icon_h * 0.72), icon_w // 10, icon_h // 3)