# vision_thread.py

import os
import queue
import time
import traceback
import urllib.request

import cv2
import numpy as np

from mediapipe.tasks.python.vision import hand_landmarker
from mediapipe.tasks.python.vision.core import image as mp_image
from mediapipe.tasks.python.vision.core import vision_task_running_mode as running_mode
from mediapipe.tasks.python.core import base_options

from queue_bus import event_queue
from events import GameEvent, EventType

# ── Model ─────────────────────────────────────────────────────────────────────
MODEL_PATH = "hand_landmarker.task"
MODEL_URLS = [
    "https://storage.googleapis.com/mediapipe-assets/hand_landmarker.task",
    "https://storage.googleapis.com/mediapipe-tasks/hand_landmarker.task",
    "https://storage.googleapis.com/mediapipe-tasks/models/hand_landmarker.task",
]

# ── Tap detection config ──────────────────────────────────────────────────────
TAP_HOLD_TIME  = 0.5    # seconds finger must stay still before TAP fires
TAP_COOLDOWN   = 0.30   # minimum seconds between taps
MOVE_THRESHOLD = 0.03   # max normalised movement still counted as "still"

# ── Output paths ──────────────────────────────────────────────────────────────
OUTPUT_DIR        = "outputs"
OUTPUT_VIDEO_PATH = os.path.join(OUTPUT_DIR, "hand_landmarks_output.avi")
SAMPLE_IMAGE_PATH = os.path.join(OUTPUT_DIR, "hand_landmarks_sample.png")


def ensure_model(path=MODEL_PATH):
    if os.path.exists(path):
        return path
    for url in MODEL_URLS:
        try:
            print(f"Downloading model from {url}...")
            urllib.request.urlretrieve(url, path)
            print("Model downloaded to", path)
            return path
        except Exception:
            print(f"Failed to download from {url}")
    raise RuntimeError(
        "Failed to download MediaPipe hand landmarker model.\n"
        "Please place hand_landmarker.task next to this file."
    )

def _post(event: GameEvent) -> None:
    """Post to queue — silently drop if full, never block the vision thread."""
    try:
        event_queue.put_nowait(event)
        print(f"[VISION] posted {event.type} payload={event.payload}")
    except queue.Full:
        pass


def process_landmarks(hand_landmarks, frame_width: int, frame_height: int,
                      state: dict) -> None:
    """
    Called once per frame when hands are detected.
    Converts normalised landmark coords → pixel coords, then fires events.
    """
    for landmarks in hand_landmarks:
        index_tip = landmarks[8]
        index_pip = landmarks[6]

        x = int(index_tip.x * frame_width)
        y = int(index_tip.y * frame_height)

        pointing = index_tip.y < index_pip.y

        last_x = index_tip.x if state["last_x"] is None else state["last_x"]
        last_y = index_tip.y if state["last_y"] is None else state["last_y"]
        movement = abs(index_tip.x - last_x) + abs(index_tip.y - last_y)

        now = time.time()

        if pointing:
            if movement >= MOVE_THRESHOLD:
                state["tap_start_time"] = None
                _post(GameEvent(EventType.DRAG, {"x": x, "y": y}))
            else:
                if state["tap_start_time"] is None:
                    state["tap_start_time"] = now

                hold     = now - state["tap_start_time"]
                last_tap = state["last_tap_time"]

                if hold >= TAP_HOLD_TIME and (now - last_tap) > TAP_COOLDOWN:
                    state["last_tap_time"]  = now
                    state["tap_start_time"] = None
                    _post(GameEvent(EventType.TAP, {"x": x, "y": y}))
        else:
            if state["tap_start_time"] is not None or state["was_pointing"]:
                _post(GameEvent(EventType.RELEASE, {"x": x, "y": y}))
            state["tap_start_time"] = None

        state["was_pointing"] = pointing
        state["last_x"]       = index_tip.x
        state["last_y"]       = index_tip.y

        print(f"[VISION] finger=({x},{y}) pointing={pointing} move={movement:.4f}")

def main():
    model_file = ensure_model()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    base_opts = base_options.BaseOptions(model_asset_path=model_file)
    options   = hand_landmarker.HandLandmarkerOptions(
        base_options=base_opts,
        running_mode=running_mode.VisionTaskRunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    state = {
        "tap_start_time": None,
        "last_tap_time":  0,
        "last_x":         None,
        "last_y":         None,
        "was_pointing":   False,
    }

    with hand_landmarker.HandLandmarker.create_from_options(options) as landmarker:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            print("Cannot open camera")
            return

        frame_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        writer = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, 20.0, (frame_width, frame_height))
        if not writer.isOpened():
            print("Warning: video writer could not be opened.")

        saved_sample = False

        try:
            while True:
                cap.grab()
                ret, frame = cap.retrieve()
                if not ret:
                    print("Failed to grab frame")
                    break

                frame = cv2.flip(frame, -1)  # mirror image for more intuitive interaction   

                rgb          = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_img       = mp_image.Image(mp_image.ImageFormat.SRGB, rgb)
                timestamp_ms = int(time.time() * 1000)
                result       = landmarker.detect_for_video(mp_img, timestamp_ms)

                if result.hand_landmarks:
                    try:
                        process_landmarks(result.hand_landmarks, frame_width, frame_height, state)
                    except Exception:
                        traceback.print_exc()

                    if not saved_sample:
                        cv2.imwrite(SAMPLE_IMAGE_PATH, frame)
                        print("Saved sample image to", SAMPLE_IMAGE_PATH)
                        saved_sample = True
                else:
                    if state["was_pointing"] or state["tap_start_time"]:
                        _post(GameEvent(EventType.RELEASE, {}))
                    state["tap_start_time"] = None
                    state["was_pointing"]   = False

                #if writer.isOpened():
                    #writer.write(frame)
        
        finally:
            cap.release()
            if writer.isOpened():
                writer.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()