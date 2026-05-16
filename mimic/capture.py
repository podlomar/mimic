import numpy as np
from collections.abc import Generator

PIPELINE_DESC = (
    "v4l2src device=/dev/video2 ! videoconvert ! "
    "video/x-raw,format=BGR,width=640,height=480,framerate=30/1 ! "
    "appsink name=sink emit-signals=true max-buffers=1 drop=true"
)


def capture_frames() -> Generator[np.ndarray, None, None]:
    # GStreamer imports deferred to avoid GLib/EGL conflict with MediaPipe at import time
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    Gst.init(None)
    pipeline = Gst.parse_launch(PIPELINE_DESC)
    sink = pipeline.get_by_name("sink")
    pipeline.set_state(Gst.State.PLAYING)

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
            yield frame
    finally:
        pipeline.set_state(Gst.State.NULL)
