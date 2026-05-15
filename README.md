# Mimic

Real-time facial puppeteering: drive a cartoon avatar with your webcam, streamed to a browser over WebRTC.

## What it does

Open the page, click **Start**, and see yourself transformed into a cartoon character that blinks when you blink, talks when you talk, and tilts when you tilt your head. A small overlay reports end-to-end latency and frame rate in real time.

The project is a small exploration of the real-time digital human synthesis problem: taking a motion signal (here, facial landmarks from a webcam) and synthesizing animated video output frame-by-frame under a strict latency budget.

## Architecture

```
┌─────────┐   ┌─────────┐   ┌──────────────┐   ┌──────────┐   ┌─────────┐   ┌─────────┐
│ Webcam  │──▶│ Capture │──▶│  MediaPipe   │──▶│  Avatar  │──▶│  H.264  │──▶│ Browser │
│         │   │ Process │   │  Inference   │   │ Renderer │   │  Encode │   │ (WebRTC)│
└─────────┘   └─────────┘   └──────────────┘   └──────────┘   └─────────┘   └─────────┘
                                   │                ▲
                                   └─ blendshapes ──┘
```

Stages run in separate processes connected by queues. Each frame carries a capture timestamp so end-to-end latency can be measured at the display.

## Tech stack

| Component                | Choice                                      | Why                                                                   |
|--------------------------|---------------------------------------------|-----------------------------------------------------------------------|
| Media pipeline           | GStreamer (PyGObject)                       | Industry-standard, supports hardware-accelerated encoders             |
| Face landmarks           | MediaPipe Face Landmarker                   | 478 landmarks + 52 ARKit-style blendshapes, designed for real-time    |
| Avatar rendering         | OpenCV + Pillow                             | Lightweight, scriptable, no external rendering stack                  |
| Inter-stage transport    | `asyncio.Queue` / `multiprocessing.Queue`   | Both tried, profiled, and compared                                    |
| Streaming output         | aiortc (WebRTC)                             | Low-latency, browser-native, no plugins needed                        |
| Profiling                | py-spy + `time.perf_counter()` timestamps   | Sampling profiler, no instrumentation overhead                        |

## How facial blendshapes drive the avatar

MediaPipe outputs values from `0.0` to `1.0` for 52 facial expression coefficients (the same ones Apple's ARKit uses for Memoji). The avatar renderer maps a small subset to drawing parameters:

| Blendshape                          | Drives                                  |
|-------------------------------------|------------------------------------------|
| `eyeBlinkLeft`, `eyeBlinkRight`     | Open-eye vs closed-eye drawing           |
| `jawOpen`                           | Vertical mouth opening                   |
| `mouthSmileLeft`, `mouthSmileRight` | Mouth curvature                          |
| `browInnerUp`, `browOuterUpLeft/Right` | Eyebrow Y-offset                      |
| Face yaw/pitch (from landmark math) | Whole-face rotation                      |

## Roadmap (1 week)

This project is timeboxed in preparation for a technical interview. Polish over completeness — better to ship Day 5 confidently than to half-finish Day 6.

- **Day 1** — GStreamer pipeline: webcam → screen, single process
- **Day 2** — MediaPipe Face Landmarker integration; log blendshape values to verify wiring
- **Day 3** — Avatar renderer v1: procedural drawing driven by 4–5 blendshapes
- **Day 4** — Multi-process pipeline, queues between stages, latency instrumentation, py-spy profiling
- **Day 5** — WebRTC output via aiortc; minimal HTML page with start button and latency/FPS overlay
- **Day 6** — Cloud GPU validation: spin up an AWS `g4dn.xlarge`, swap MediaPipe for an ONNX face-landmark model, benchmark CPU vs `onnxruntime-gpu` (CUDA) vs TensorRT
- **Day 7** — README polish, demo screen recording, repository cleanup

## Stretch goals (in priority order)

1. Sprite-based mouth shapes (closed / slightly open / wide open / smile / frown) selected by blendshape values, with linear interpolation between them
2. RabbitMQ producer publishing the blendshape stream to a separate consumer, demonstrating decoupled service architecture
3. ONNX-CPU vs ONNX-CUDA vs TensorRT benchmark with plotted results
4. Head translation/rotation driven by face landmark geometry (full 6-DoF head pose)
5. Adaptive frame-dropping under load (backpressure handling)

## Setup

Tested on Ubuntu 22.04+. Python 3.11+, a webcam, and a modern CPU recommended.

```bash
# System packages
sudo apt install python3-gi python3-gst-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav

# Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Python dependencies
pip install mediapipe opencv-python aiortc numpy pillow

# Profiling (optional)
pip install py-spy

# Run
python -m Mimic.main
```

Then open `http://localhost:8080` in Chrome or Firefox and click **Start**.

## Hardware notes

Developed on AMD Vega integrated graphics (no CUDA available locally). MediaPipe runs well on CPU for development. GPU comparisons performed on AWS `g4dn.xlarge` (NVIDIA T4) on Day 6.

## Profiling targets

End-to-end latency budget: **under 100 ms** from webcam capture to browser display (LAN). Stage budgets:

| Stage          | Target |
|----------------|--------|
| Capture        | < 5 ms |
| MediaPipe (CPU) | < 35 ms |
| Avatar render  | < 10 ms |
| Encode + WebRTC | < 30 ms |

Actual numbers and bottleneck analysis to be added once Day 4 profiling is complete.

## Motivation

Inspired by current work in real-time digital human synthesis (see e.g. [ValkaAI's research blog](https://valka.ai/blog/the-human-digital-frontier)), where the central engineering tension is balancing visual quality, temporal consistency, and end-to-end latency in interactive video generation. This project is a small didactic exercise in the same architectural shape: a motion signal feeding a frame-synthesis stage feeding a low-latency streaming output.

## License

MIT
