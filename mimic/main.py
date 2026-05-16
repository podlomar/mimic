import cv2
import numpy as np
import skia

from mimic.capture import capture_frames
from mimic.inference import FaceLandmarker, KEY_BLENDSHAPES
from mimic.smiley import Smiley


def render(frame: np.ndarray, surface: skia.Surface, smiley: Smiley, result) -> np.ndarray:
    h, w = frame.shape[:2]

    with surface as canvas:
        # Background: webcam frame (BGR → RGBA for Skia)
        frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        bg = skia.Image.fromarray(frame_rgba, colorType=skia.kRGBA_8888_ColorType)
        canvas.drawImage(bg, 0, 0)

        if result is not None:
            # Landmarks — 1 px green dots
            dot = skia.Paint(AntiAlias=True, Color=skia.Color(0, 255, 0))
            for lm in result.landmarks:
                canvas.drawCircle(lm.x * w, lm.y * h, 1, dot)

            smiley.draw(canvas)

    # Skia surface → BGR numpy
    snapshot = surface.makeImageSnapshot()
    rgba = snapshot.toarray()
    return cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)


def run() -> None:
    landmarker = FaceLandmarker()
    smiley = Smiley(center=(320, 240), radius=100)
    surface = skia.Surface(640, 480)
    try:
        for frame in capture_frames():
            result = landmarker.process(frame)

            if result is not None:
                values = "  ".join(
                    f"{name}={result.blendshapes.get(name, 0):.2f}"
                    for name in KEY_BLENDSHAPES
                )
                print(values, end="\r", flush=True)

            output = render(frame, surface, smiley, result)
            cv2.imshow("mimic", output)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        landmarker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
