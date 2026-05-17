import time
from mimic.capture import get_timestamp
import skia
import cv2

from multiprocessing import Queue
from mimic.smiley import Smiley

KEY_BLENDSHAPES = ("jawOpen", "eyeBlinkLeft", "eyeBlinkRight", "mouthSmileLeft", "mouthSmileRight", "browInnerUp")

def render_worker(qin: Queue, qout: Queue) -> None:
    surface = skia.Surface(1280, 720)
    smiley = Smiley(cx=320, cy=240)
    print("Render worker started.")
    try:
        while True:
            video_frame = qin.get()

            if video_frame.face is not None:
                smiley.eye_blink_left = video_frame.face.blendshapes.get("eyeBlinkLeft", 0)
                smiley.eye_blink_right = video_frame.face.blendshapes.get("eyeBlinkRight", 0)
                smiley.tilt = video_frame.face.tilt
                smiley.scale = video_frame.face.scale
                smiley.cx = video_frame.face.nose_x
                smiley.cy = video_frame.face.nose_y

            with surface as canvas:
                frame_rgba = cv2.cvtColor(video_frame.data, cv2.COLOR_BGR2RGBA)
                bg = skia.Image.fromarray(frame_rgba, colorType=skia.kRGBA_8888_ColorType)
                canvas.drawImage(bg, 0, 0)

                if video_frame.face is not None:
                    h, w = surface.height(), surface.width()
                    dot = skia.Paint(AntiAlias=True, Color=skia.Color(0, 255, 0))
                    for lm in video_frame.face.landmarks:
                        canvas.drawCircle(lm.x * w, lm.y * h, 2, dot)

                smiley.draw(canvas)

            snapshot = surface.makeImageSnapshot()
            rgba = snapshot.toarray()
            bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
            timestamp = get_timestamp()
            video_frame.render_phase = timestamp - video_frame.captured_stamp - video_frame.inference_phase
            video_frame.data = bgr
            qout.put(video_frame)
    finally:
        pass
