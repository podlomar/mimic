import time
import cv2
from mimic.render import render_worker
from mimic.capture import capture_worker
from mimic.inference import inference_worker

from multiprocessing import Process, Queue

if __name__ == "__main__":
    frames_queue = Queue()
    face_queue = Queue()
    output_queue = Queue()

    capture_process = Process(target=capture_worker, args=(frames_queue,))
    inference_process = Process(target=inference_worker, args=(frames_queue, face_queue))
    render_process = Process(target=render_worker, args=(face_queue, output_queue))

    capture_process.start()
    inference_process.start()
    render_process.start()

    font = cv2.FONT_HERSHEY_SIMPLEX
    displayed_stats = ["FPS: --", "Inference: -- ms", "Render: -- ms"]
    samples = []
    last_update = time.monotonic()

    while True:
        video_frame = output_queue.get()

        samples.append((video_frame.fps, video_frame.inference_phase, video_frame.render_phase))
        now = time.monotonic()
        if now - last_update >= 0.5:
            n = len(samples)
            avg_fps = sum(s[0] for s in samples) / n
            avg_inf = sum(s[1] for s in samples) / n
            avg_rnd = sum(s[2] for s in samples) / n
            displayed_stats = [
                f"FPS: {avg_fps:.1f}",
                f"Inference: {avg_inf:.0f} ms",
                f"Render: {avg_rnd:.0f} ms",
            ]
            samples.clear()
            last_update = now

        y = 30
        for text in displayed_stats:
            cv2.putText(video_frame.data, text, (10, y), font, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(video_frame.data, text, (10, y), font, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            y += 25

        cv2.imshow("Webcam", video_frame.data)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    capture_process.terminate()
    capture_process.join()

    inference_process.terminate()
    inference_process.join()

    render_process.terminate()
    render_process.join()

    cv2.destroyAllWindows()
