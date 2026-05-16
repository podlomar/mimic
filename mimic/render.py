import skia
import cv2

from multiprocessing import Queue
from mimic.smiley import Smiley

KEY_BLENDSHAPES = ("jawOpen", "eyeBlinkLeft", "eyeBlinkRight", "mouthSmileLeft", "mouthSmileRight", "browInnerUp")

def render_worker(qin: Queue, qout: Queue) -> None:
    surface = skia.Surface(640, 480)
    smiley = Smiley(center=(320, 240), radius=100)
    print("Render worker started.")
    try:
        while True:
            timestamp, frame, result = qin.get()

            if result is not None:
                smiley.eye_blink_left = result.blendshapes.get("eyeBlinkLeft", 0)
                smiley.eye_blink_right = result.blendshapes.get("eyeBlinkRight", 0)

            with surface as canvas:
                frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                bg = skia.Image.fromarray(frame_rgba, colorType=skia.kRGBA_8888_ColorType)
                canvas.drawImage(bg, 0, 0)

                if result is not None:
                    h, w = surface.height(), surface.width()
                    dot = skia.Paint(AntiAlias=True, Color=skia.Color(0, 255, 0))
                    for lm in result.landmarks:
                        canvas.drawCircle(lm.x * w, lm.y * h, 2, dot)

                smiley.draw(canvas)

            snapshot = surface.makeImageSnapshot()
            rgba = snapshot.toarray()
            bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
            qout.put((timestamp, bgr))
    finally:
        pass
