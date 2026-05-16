import time
from dataclasses import dataclass, field

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from multiprocessing import Queue

MODEL_PATH = "models/face_landmarker.task"


@dataclass
class FaceResult:
    landmarks: list  # list of NormalizedLandmark (x, y, z all in 0-1 range)
    blendshapes: dict[str, float] = field(default_factory=dict)

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

        return FaceResult(landmarks=result.face_landmarks[0], blendshapes=blendshapes)

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
