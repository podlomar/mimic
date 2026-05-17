import math
import time
from dataclasses import dataclass, field

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from multiprocessing import Queue

MODEL_PATH = "models/face_landmarker.task"

def head_tilt(landmarks) -> float:
    """Returns head roll in degrees. Positive = tilted right."""
    left  = landmarks[33]   # left eye outer corner
    right = landmarks[263]  # right eye outer corner
    dx = right.x - left.x
    dy = right.y - left.y
    return math.degrees(math.atan2(dy, dx))

def face_scale(landmarks, w: int, h: int) -> float:
    top    = landmarks[10]   # forehead
    bottom = landmarks[152]  # chin
    dx = (bottom.x - top.x) * w
    dy = (bottom.y - top.y) * h
    return math.hypot(dx, dy) / 120


@dataclass
class FaceResult:
    landmarks: list
    blendshapes: dict[str, float]
    tilt: float
    scale: float
    nose_x: int
    nose_y: int

class FaceLandmarker:
    def __init__(self, model_path: str = MODEL_PATH):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            output_face_blendshapes=True,
            num_faces=1,
        )
        self._detector = vision.FaceLandmarker.create_from_options(options)
        self._start = time.monotonic()

    def process(self, frame: np.ndarray, timestamp: float) -> FaceResult | None:
        """Process a BGR frame; returns landmarks + blendshapes or None if no face found."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(timestamp * 1000)
        result = self._detector.detect_for_video(mp_image, timestamp_ms)

        if not result.face_landmarks:
            return None

        blendshapes: dict[str, float] = {}
        if result.face_blendshapes:
            for category in result.face_blendshapes[0]:
                blendshapes[category.category_name] = category.score

        h, w = frame.shape[:2]
        lms = result.face_landmarks[0]
        tilt = head_tilt(lms)
        scale = face_scale(lms, w, h)
        nose_x = int(lms[168].x * w)
        nose_y = int(lms[168].y * h)
        return FaceResult(landmarks=lms, blendshapes=blendshapes, tilt=tilt, scale=scale, nose_x=nose_x, nose_y=nose_y)

    def close(self) -> None:
        self._detector.close()

def inference_worker(qin: Queue, qout: Queue) -> None:
    landmarker = FaceLandmarker()
    print("Inference worker started.")
    try:
        while True:
            timestamp, frame = qin.get()
            result = landmarker.process(frame, timestamp)
            qout.put((timestamp, frame, result))
    finally:
        landmarker.close()
