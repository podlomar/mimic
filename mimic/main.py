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
    
    while True:
        timestamp, frame = output_queue.get()
        print(f"Timestamp: {timestamp:.2f} seconds")
        cv2.imshow("Webcam", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    capture_process.terminate()
    capture_process.join()

    inference_process.terminate()
    inference_process.join()

    render_process.terminate()
    render_process.join()

    cv2.destroyAllWindows()
