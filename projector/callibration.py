"""
calibrate.py — Camera / projector calibration script
=====================================================
Run this once each time the physical setup changes (camera or projector moves).
Produces calibration.npy which vision_thread.py loads automatically.

Usage:
    python calibrate.py

What it does:
    1. Projects 4 reference dots onto the surface via a fullscreen Pygame window
    2. Opens a second window showing the live camera feed
    3. You click each dot in the camera feed in the order they're numbered
    4. OpenCV computes the homography matrix and saves it to calibration.npy

Tips:
    - Use a plain flat surface (table, floor, wall)
    - Make sure the room isn't too bright — dots need to be visible to the camera
    - Click the centre of each dot as accurately as you can
    - If the result feels off, just re-run the script
"""

import cv2
import numpy as np
import pygame
import sys

# ── Config ────────────────────────────────────────────────────────────────────
# These are the pixel positions of the 4 reference dots ON THE PROJECTOR OUTPUT.
# They're set as fractions of the window so they work at any resolution.
# Arranged as: top-left, top-right, bottom-right, bottom-left (clockwise).
_PROJ_W = 1280
_PROJ_H = 720
_MARGIN = 100  # how far in from the edge each dot sits

PROJECTOR_POINTS = np.float32([
    [_MARGIN,          _MARGIN],           # top-left
    [_PROJ_W - _MARGIN, _MARGIN],          # top-right
    [_PROJ_W - _MARGIN, _PROJ_H - _MARGIN],# bottom-right
    [_MARGIN,          _PROJ_H - _MARGIN], # bottom-left
])

_DOT_RADIUS = 12
_DOT_COLOR  = (255, 255, 255)
_LABEL_COLOR = (255, 220, 0)
_ORDER_LABELS = ["1: top-left", "2: top-right", "3: bottom-right", "4: bottom-left"]


# ── Step 1: Project reference dots ───────────────────────────────────────────
def render_projection(screen: pygame.Surface, font: pygame.font.Font, tick: int) -> None:
    """
    Draw the current state of the projection based on how many points
    have been clicked so far. Called every frame from the main loop.

    States per dot:
      - not yet reached  : dim grey, not highlighted
      - current target   : bright white, pulsing ring around it
      - already clicked  : green, static
    """
    screen.fill((0, 0, 0))
    n_clicked = len(clicked_points)

    for i, (x, y) in enumerate(PROJECTOR_POINTS):
        ix, iy = int(x), int(y)

        if i < n_clicked:
            # Already clicked — show green confirmation
            color = (0, 220, 80)
            pygame.draw.circle(screen, color, (ix, iy), _DOT_RADIUS)
            pygame.draw.circle(screen, color, (ix, iy), _DOT_RADIUS + 6, 2)

        elif i == n_clicked:
            # Current target — bright white with pulsing ring
            pulse = abs((tick % 60) - 30) / 30  # 0→1→0 over 60 frames
            ring_r = int(_DOT_RADIUS + 8 + pulse * 10)
            ring_alpha = int(180 + pulse * 75)
            color = (255, 255, 255)
            pygame.draw.circle(screen, color, (ix, iy), _DOT_RADIUS)
            pygame.draw.circle(screen, (ring_alpha, ring_alpha, ring_alpha),
                               (ix, iy), ring_r, 2)

        else:
            # Not yet reached — dim
            color = (80, 80, 80)
            pygame.draw.circle(screen, color, (ix, iy), _DOT_RADIUS)

        # Label
        label = font.render(_ORDER_LABELS[i], True,
                            (0, 220, 80) if i < n_clicked else
                            (255, 220, 0) if i == n_clicked else
                            (80, 80, 80))
        offset_x = 20 if x < _PROJ_W / 2 else -label.get_width() - 20
        offset_y = 20 if y < _PROJ_H / 2 else -label.get_height() - 20
        screen.blit(label, (ix + offset_x, iy + offset_y))

    # Status line at bottom
    if n_clicked < 4:
        msg = f"Click dot {n_clicked + 1} in the camera window: {_ORDER_LABELS[n_clicked]}"
    else:
        msg = "All 4 points captured — computing calibration..."
    status = font.render(msg, True, (180, 180, 180))
    screen.blit(status, (20, _PROJ_H - 40))
    pygame.display.flip()


# ── Step 2: Collect clicked points from camera feed ──────────────────────────
clicked_points: list[tuple[int, int]] = []

def _on_mouse_click(event, x, y, flags, param) -> None:
    if event == cv2.EVENT_LBUTTONDOWN and len(clicked_points) < 4:
        clicked_points.append((x, y))
        print(f"  Point {len(clicked_points)} captured: ({x}, {y})")


def collect_camera_points(
    cap: cv2.VideoCapture,
    screen: pygame.Surface,
    font_pygame: pygame.font.Font,
    clock: pygame.time.Clock,
) -> np.ndarray:
    """
    Show live camera feed in an OpenCV window while simultaneously updating
    the projection window to reflect which dots have been confirmed.
    User clicks the 4 projected dots in the camera feed in numbered order.
    Returns the 4 clicked points as a numpy array.
    """
    cv_window = "Calibration — click each dot in order (1→2→3→4)"
    cv2.namedWindow(cv_window)
    cv2.setMouseCallback(cv_window, _on_mouse_click)

    cv_font = cv2.FONT_HERSHEY_SIMPLEX
    print("\nCamera feed open. Click each projected dot in numbered order.")
    print("Order: top-left → top-right → bottom-right → bottom-left\n")

    tick = 0
    while len(clicked_points) < 4:
        # ── Pygame events (keeps projection window alive + responsive) ────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Calibration cancelled.")
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                print("Calibration cancelled.")
                sys.exit()

        # ── Update projection window ──────────────────────────────────────────
        render_projection(screen, font_pygame, tick)
        tick += 1

        # ── Update camera window ──────────────────────────────────────────────
        ok, frame = cap.read()
        if not ok:
            continue

        display = frame.copy()
        for i, (px, py) in enumerate(clicked_points):
            cv2.circle(display, (px, py), 8, (0, 255, 0), -1)
            cv2.putText(display, str(i + 1), (px + 10, py - 10),
                        cv_font, 0.7, (0, 255, 0), 2)

        remaining = len(clicked_points)
        if remaining < 4:
            prompt = f"Click dot {remaining + 1}: {_ORDER_LABELS[remaining]}"
            cv2.putText(display, prompt, (20, 40), cv_font, 0.8, (0, 200, 255), 2)

        cv2.imshow(cv_window, display)
        cv2.waitKey(1)
        clock.tick(60)

    # Flash projection green briefly to confirm all done
    for _ in range(90):
        screen.fill((0, 40, 0))
        msg = pygame.font.SysFont("monospace", 36).render(
            "Calibration captured — computing...", True, (0, 255, 100)
        )
        screen.blit(msg, ((_PROJ_W - msg.get_width()) // 2, _PROJ_H // 2 - 20))
        pygame.display.flip()
        clock.tick(60)
        for event in pygame.event.get():
            pass  # drain events during flash

    cv2.destroyAllWindows()
    return np.float32(clicked_points)


# ── Step 3: Compute and save homography ──────────────────────────────────────
def compute_and_save(camera_pts: np.ndarray) -> None:
    H, status = cv2.findHomography(camera_pts, PROJECTOR_POINTS)

    if H is None:
        print("\nERROR: Could not compute homography. Points may be collinear.")
        print("Re-run the script and click more carefully.")
        sys.exit(1)

    inliers = int(status.sum()) if status is not None else "unknown"
    print(f"\nHomography computed ({inliers}/4 inliers).")

    np.save("calibration.npy", H)
    print("Saved to calibration.npy — vision_thread.py will load this automatically.\n")
    print("Matrix:")
    print(np.array2string(H, precision=4, suppress_small=True))


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=== Calibration script ===")
    print(f"Projector resolution assumed: {_PROJ_W}x{_PROJ_H}")
    print(f"Reference dot margin: {_MARGIN}px from each edge\n")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        sys.exit(1)

    pygame.init()
    screen = pygame.display.set_mode((_PROJ_W, _PROJ_H), pygame.FULLSCREEN)
    pygame.display.set_caption("Calibration")
    font = pygame.font.SysFont("monospace", 22)
    clock = pygame.time.Clock()

    print("Projection window open. Switch to the camera window to click the dots.")
    camera_pts = collect_camera_points(cap, screen, font, clock)

    cap.release()
    pygame.quit()

    print("\nAll 4 points captured:")
    for i, (x, y) in enumerate(camera_pts):
        print(f"  {_ORDER_LABELS[i]}: camera ({int(x)}, {int(y)}) "
              f"→ projector ({int(PROJECTOR_POINTS[i][0])}, {int(PROJECTOR_POINTS[i][1])})")

    compute_and_save(camera_pts)
    print("Calibration complete. You can now run main.py.")


if __name__ == "__main__":
    main()
EOF