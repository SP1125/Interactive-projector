import cv2
import mediapipe as mp
import numpy as np
import queue
import threading

from events import EventType, GameEvent
from queue_bus import event_queue

# ── MediaPipe setup ───────────────────────────────────────────────────────────
_mp_hands = mp.solutions.hands
_PINCH_THRESHOLD = 0.05  # normalised distance between index tip and thumb tip

# ── Calibration ───────────────────────────────────────────────────────────────
# CV team: place your calibration.npy file in the project root.
# It should be the homography matrix produced by your calibration script
# (the output of cv2.findHomography). Do not recompute it here.
try:
    _H = np.load("calibration.npy")
except FileNotFoundError:
    # No calibration file found — coords will be passed through unchanged.
    # This is fine for mouse-injection testing but will cause parallax in production.
    _H = None
    print("[vision_thread] WARNING: calibration.npy not found — running without transform.")


def _camera_to_projector(x: int, y: int) -> tuple[int, int]:
    """
    Apply homography transform to convert raw camera pixel coords
    into projector surface coords. This is what eliminates parallax.
    If no calibration matrix is loaded, returns coords unchanged.
    """
    if _H is None:
        return x, y
    pt = np.float32([[[x, y]]])
    transformed = cv2.perspectiveTransform(pt, _H)
    return int(transformed[0][0][0]), int(transformed[0][0][1])


# ── Helpers ───────────────────────────────────────────────────────────────────
def _pinch_distance(hand_landmarks) -> float:
    """Euclidean distance between index fingertip and thumb tip (normalised 0-1)."""
    index = hand_landmarks.landmark[_mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb = hand_landmarks.landmark[_mp_hands.HandLandmark.THUMB_TIP]
    return ((index.x - thumb.x) ** 2 + (index.y - thumb.y) ** 2) ** 0.5


def _landmark_to_screen(landmark, frame_w: int, frame_h: int) -> tuple[int, int]:
    """Convert normalised MediaPipe coords (0-1) to pixel coords."""
    return int(landmark.x * frame_w), int(landmark.y * frame_h)


def _post(event: GameEvent) -> None:
    """Drop event onto the queue. Silently discards if queue is full."""
    try:
        event_queue.put_nowait(event)
    except queue.Full:
        pass


# ── Main vision loop ──────────────────────────────────────────────────────────
def run_vision(running_flag: threading.Event) -> None:
    """
    Main vision loop. Run this on a daemon thread.
    `running_flag` is a threading.Event — when cleared, this function returns.

    Latency mitigations applied here:
      - model_complexity=0: uses the lite MediaPipe model (faster, negligible accuracy loss)
      - CAP_PROP_BUFFERSIZE=1: always reads the latest camera frame, not a queued one
      - 640x480 resolution: sufficient for hand tracking, much faster than 1080p
    """
    cap = cv2.VideoCapture(0)

    # Request low-latency camera settings
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)      # don't buffer stale frames
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    pinching = False  # tracks whether we're mid-pinch

    with _mp_hands.Hands(
        model_complexity=0,           # lite model — big latency win
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    ) as hands:
        while running_flag.is_set():
            ok, frame = cap.read()
            if not ok:
                continue

            # MediaPipe expects RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if not results.multi_hand_landmarks:
                # Hand left frame mid-pinch — treat as release
                if pinching:
                    pinching = False
                    _post(GameEvent(EventType.RELEASE, {}))
                continue

            hand = results.multi_hand_landmarks[0]
            dist = _pinch_distance(hand)

            # Raw camera coords → projector coords via homography
            raw_x, raw_y = _landmark_to_screen(
                hand.landmark[_mp_hands.HandLandmark.INDEX_FINGER_TIP],
                frame_w, frame_h
            )
            x, y = _camera_to_projector(raw_x, raw_y)
            payload = {"x": x, "y": y}

            if dist < _PINCH_THRESHOLD:
                if not pinching:
                    pinching = True
                    _post(GameEvent(EventType.TAP, payload))
                else:
                    _post(GameEvent(EventType.DRAG, payload))
            else:
                if pinching:
                    pinching = False
                    _post(GameEvent(EventType.RELEASE, payload))

    cap.release()