"""
calibrate.py — Camera / projector calibration via surface taps
==============================================================
Run this once each time the physical setup changes (camera or projector moves).
Produces calibration.npy which vision_thread.py loads automatically.

Usage:
    python calibrate.py

What it does:
    1. Projects 4 reference dots onto the surface one at a time
    2. User taps each dot directly on the surface with their finger
    3. Camera detects the fingertip position via MediaPipe
    4. OpenCV computes the homography matrix and saves calibration.npy

No laptop interaction needed — the whole process happens on the surface.
"""

import cv2
import mediapipe as mp
import numpy as np
import pygame
import sys
import time

# ── Config ────────────────────────────────────────────────────────────────────
_PROJ_W = 1280
_PROJ_H = 720
_MARGIN = 100

PROJECTOR_POINTS = np.float32([
    [_MARGIN,           _MARGIN],            # top-left
    [_PROJ_W - _MARGIN, _MARGIN],            # top-right
    [_PROJ_W - _MARGIN, _PROJ_H - _MARGIN],  # bottom-right
    [_MARGIN,           _PROJ_H - _MARGIN],  # bottom-left
])

_ORDER_LABELS = ["1: top-left", "2: top-right", "3: bottom-right", "4: bottom-left"]
_DOT_RADIUS = 16
_PINCH_THRESHOLD = 0.05
_TAP_COOLDOWN = 1.2   # seconds to wait after a tap before accepting the next one
                       # prevents a single tap registering multiple times

# ── MediaPipe ─────────────────────────────────────────────────────────────────
_mp_hands = mp.solutions.hands


def _pinch_distance(hand_landmarks) -> float:
    index = hand_landmarks.landmark[_mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb = hand_landmarks.landmark[_mp_hands.HandLandmark.THUMB_TIP]
    return ((index.x - thumb.x) ** 2 + (index.y - thumb.y) ** 2) ** 0.5


def _fingertip_px(hand_landmarks, frame_w: int, frame_h: int) -> tuple[int, int]:
    tip = hand_landmarks.landmark[_mp_hands.HandLandmark.INDEX_FINGER_TIP]
    return int(tip.x * frame_w), int(tip.y * frame_h)


# ── Projection rendering ──────────────────────────────────────────────────────
def render_projection(
    screen: pygame.Surface,
    font: pygame.font.Font,
    tick: int,
    n_confirmed: int,
    waiting_for_release: bool,
) -> None:
    """Redraw the projection surface showing current calibration state."""
    screen.fill((0, 0, 0))

    for i, (x, y) in enumerate(PROJECTOR_POINTS):
        ix, iy = int(x), int(y)

        if i < n_confirmed:
            # Confirmed — green
            pygame.draw.circle(screen, (0, 220, 80), (ix, iy), _DOT_RADIUS)
            pygame.draw.circle(screen, (0, 220, 80), (ix, iy), _DOT_RADIUS + 6, 2)

        elif i == n_confirmed:
            # Current target — white, pulsing ring
            pulse = abs((tick % 60) - 30) / 30
            ring_r = int(_DOT_RADIUS + 8 + pulse * 10)
            brightness = int(180 + pulse * 75)
            pygame.draw.circle(screen, (255, 255, 255), (ix, iy), _DOT_RADIUS)
            pygame.draw.circle(
                screen, (brightness, brightness, brightness), (ix, iy), ring_r, 2
            )
        else:
            # Not yet reached — dim
            pygame.draw.circle(screen, (60, 60, 60), (ix, iy), _DOT_RADIUS)

        label_color = (
            (0, 220, 80)   if i < n_confirmed  else
            (255, 220, 0)  if i == n_confirmed  else
            (60, 60, 60)
        )
        label = font.render(_ORDER_LABELS[i], True, label_color)
        offset_x = 24 if x < _PROJ_W / 2 else -label.get_width() - 24
        offset_y = 24 if y < _PROJ_H / 2 else -label.get_height() - 24
        screen.blit(label, (ix + offset_x, iy + offset_y))

    # Status line
    if n_confirmed < 4:
        if waiting_for_release:
            msg = "Tap registered — lift your finger"
        else:
            msg = f"Tap dot {n_confirmed + 1}: {_ORDER_LABELS[n_confirmed]}"
    else:
        msg = "All 4 taps captured — computing calibration..."

    status = font.render(msg, True, (180, 180, 180))
    screen.blit(status, ((_PROJ_W - status.get_width()) // 2, _PROJ_H - 44))
    pygame.display.flip()


# ── Main calibration loop ─────────────────────────────────────────────────────
def run_calibration() -> None:
    # Camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        sys.exit(1)

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Pygame projection window
    pygame.init()
    screen = pygame.display.set_mode((_PROJ_W, _PROJ_H), pygame.FULLSCREEN)
    pygame.display.set_caption("Calibration")
    font = pygame.font.SysFont("monospace", 24)
    clock = pygame.time.Clock()

    camera_points: list[tuple[int, int]] = []
    was_pinching = False
    waiting_for_release = False  # true between tap registered and finger lifted
    last_tap_time = 0.0
    tick = 0

    print("Calibration started. Tap each projected dot in order.")

    with _mp_hands.Hands(
        model_complexity=0,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    ) as hands:

        while len(camera_points) < 4:
            # ── Pygame events ─────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Calibration cancelled.")
                    cap.release()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    print("Calibration cancelled.")
                    cap.release()
                    pygame.quit()
                    sys.exit()

            # ── Camera frame ──────────────────────────────────────────────────
            ok, frame = cap.read()
            if not ok:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            now = time.time()
            pinching = False

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                dist = _pinch_distance(hand)
                pinching = dist < _PINCH_THRESHOLD

                if pinching and not was_pinching:
                    # Fresh pinch — check cooldown then record
                    if not waiting_for_release and (now - last_tap_time) > _TAP_COOLDOWN:
                        x, y = _fingertip_px(hand, frame_w, frame_h)
                        camera_points.append((x, y))
                        last_tap_time = now
                        waiting_for_release = True
                        n = len(camera_points)
                        print(f"  Dot {n} tapped: camera coords ({x}, {y})")

                if not pinching:
                    waiting_for_release = False  # finger lifted, ready for next tap

            was_pinching = pinching

            # ── Render projection ─────────────────────────────────────────────
            render_projection(screen, font, tick, len(camera_points), waiting_for_release)
            tick += 1
            clock.tick(60)

    # ── All 4 tapped — flash confirmation ─────────────────────────────────────
    confirm_font = pygame.font.SysFont("monospace", 36)
    for _ in range(120):
        screen.fill((0, 30, 0))
        msg = confirm_font.render("Calibration captured!", True, (0, 255, 100))
        screen.blit(msg, ((_PROJ_W - msg.get_width()) // 2, _PROJ_H // 2 - 20))
        pygame.display.flip()
        clock.tick(60)
        for event in pygame.event.get():
            pass

    cap.release()
    pygame.quit()

    # ── Compute and save homography ───────────────────────────────────────────
    cam_pts = np.float32(camera_points)

    print("\nAll 4 points captured:")
    for i, (cx, cy) in enumerate(camera_points):
        px, py = PROJECTOR_POINTS[i]
        print(f"  {_ORDER_LABELS[i]}: camera ({cx}, {cy}) → projector ({int(px)}, {int(py)})")

    H, status = cv2.findHomography(cam_pts, PROJECTOR_POINTS)

    if H is None:
        print("\nERROR: Could not compute homography. Try again and tap more carefully.")
        sys.exit(1)

    np.save("calibration.npy", H)
    print(f"\nSaved calibration.npy — {int(status.sum())}/4 inliers.")
    print("Run main.py to start the game.")


if __name__ == "__main__":
    run_calibration()