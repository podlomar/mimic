import cv2
from mimic.capture import capture_frames
from mimic.inference import FaceLandmarker, KEY_BLENDSHAPES


def run() -> None:
    landmarker = FaceLandmarker()
    try:
        for frame in capture_frames():
            result = landmarker.process(frame)
            if result is not None:
                h, w = frame.shape[:2]
                for lm in result.landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 1, (0, 255, 0), -1)

                values = "  ".join(
                    f"{name}={result.blendshapes.get(name, 0):.2f}"
                    for name in KEY_BLENDSHAPES
                )
                print(values, end="\r", flush=True)

            cv2.imshow("mimic", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        landmarker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
