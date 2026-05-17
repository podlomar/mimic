from dataclasses import dataclass
import time

import numpy as np
from collections.abc import Generator
from multiprocessing import Process, Queue

PIPELINE_DESC = (
    "v4l2src device=/dev/video2 ! "
    "image/jpeg,width=1280,height=720,framerate=30/1 ! "
    "jpegdec ! videoconvert ! "
    "video/x-raw,format=BGR ! "
    "appsink name=sink emit-signals=true max-buffers=1 drop=true"
)

def get_timestamp() -> int:
    return int(round(time.monotonic() * 1000))

@dataclass
class FaceResult:
    landmarks: list
    blendshapes: dict[str, float]
    tilt: float
    scale: float
    nose_x: int
    nose_y: int

@dataclass
class SceneFrame:
    captured_stamp: int
    inference_phase: int | None
    render_phase: int | None
    data: np.ndarray
    width: int
    height: int
    fps: float
    face: FaceResult | None

def capture_frames() -> Generator[tuple[float, np.ndarray], None, None]:
    # GStreamer imports deferred to avoid GLib/EGL conflict with MediaPipe at import time
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    Gst.init(None)
    pipeline = Gst.parse_launch(PIPELINE_DESC)
    sink = pipeline.get_by_name("sink")
    pipeline.set_state(Gst.State.PLAYING)

    start_time = get_timestamp()
    last_timestamp = 0

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
            
            timestamp = get_timestamp()
            fps = 1000.0 / (timestamp - last_timestamp) if last_timestamp > 0 else 0
            last_timestamp = timestamp
            yield SceneFrame(
                captured_stamp=timestamp,
                inference_phase=None,
                render_phase=None,
                data=frame,
                width=width,
                height=height,
                fps=fps,
                face=None,
            )
    finally:
        pipeline.set_state(Gst.State.NULL)

def capture_worker(q: Queue) -> None:
    for video_frame in capture_frames():
        q.put(video_frame)
