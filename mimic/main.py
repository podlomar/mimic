import cv2
from mimic.capture import capture_frames


def run() -> None:
    for frame in capture_frames():
        cv2.imshow("mimic", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
