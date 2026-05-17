from dataclasses import dataclass

import numpy as np
from collections.abc import Generator
from multiprocessing import Process, Queue

PIPELINE_DESC = (
    "v4l2src device=/dev/video2 ! videoconvert ! "
    "video/x-raw,format=BGR,width=640,height=480,framerate=30/1 ! "
    "appsink name=sink emit-signals=true max-buffers=1 drop=true"
)

@dataclass
class VideoFrame:
    timestamp: float
    data: np.ndarray
    fps: float

def capture_frames() -> Generator[tuple[float, np.ndarray], None, None]:
    # GStreamer imports deferred to avoid GLib/EGL conflict with MediaPipe at import time
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    Gst.init(None)
    pipeline = Gst.parse_launch(PIPELINE_DESC)
    sink = pipeline.get_by_name("sink")
    pipeline.set_state(Gst.State.PLAYING)

    last_timestamp = 0.0

    try:
        while True:
            sample = sink.emit("pull-sample")
            if sample is None:
                break

            buf = sample.get_buffer()
            caps = sample.get_caps()
            structure = caps.get_structure(0)
            width = structure.get_int("width").value
            height = structure.get_int("height").value
            success, map_info = buf.map(Gst.MapFlags.READ)
            if not success:
                continue
            frame = np.frombuffer(map_info.data, dtype=np.uint8).reshape((height, width, 3)).copy()
            buf.unmap(map_info)
            
            timestamp = buf.pts / Gst.SECOND
            fps = 1.0 / (timestamp - last_timestamp) if last_timestamp > 0 else 0.0
            last_timestamp = timestamp
            yield VideoFrame(timestamp=timestamp, data=frame, fps=fps)
    finally:
        pipeline.set_state(Gst.State.NULL)

def capture_worker(q: Queue) -> None:
    for video_frame in capture_frames():
        print(f"Captured frame at {video_frame.timestamp:.2f} seconds, FPS: {video_frame.fps:.1f}")
        q.put(video_frame)
