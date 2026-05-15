# Mimic — Implementation Plan

A working plan document. Refer to `README.md` for project description and architecture; this file is the build schedule.

**Timebox:** 7 days. **Target audience:** technical interviewers at a real-time video synthesis company. **Optimization target:** depth + a clean demo, not feature count.

---

## Day 0 — Pre-flight (do this before Day 1)

Before the timer starts, get the boring stuff out of the way so Day 1 is pure progress.

- [ ] Decide on a final project name and check GitHub + PyPI availability
- [ ] Create a private GitHub repository (flip to public on Day 7)
- [ ] Verify webcam works: `ffplay /dev/video0` should show your face
- [ ] Verify Python 3.11+ is available: `python3 --version`
- [ ] Confirm CPU model: `lscpu | grep "Model name"` — note clock speed, core count
- [ ] Read the [MediaPipe Face Landmarker docs](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python) (10 min) — specifically the section on blendshapes
- [ ] Skim the [aiortc README](https://github.com/aiortc/aiortc) (5 min) — server-side WebRTC mental model
- [ ] Create an AWS account if you don't have one, and check that you can launch a `g4dn.xlarge` in your region (usually requires a vCPU quota increase — request it now, approval can take 24h)

**Definition of done:** repo exists, webcam works, AWS quota ready.

---

## Day 1 — GStreamer pipeline foundation (~2h)

**Goal:** Webcam frames flowing through a Python-controlled GStreamer pipeline to a display window. Single process, no ML, no avatar.

### Tasks

- [ ] Install system dependencies:
  ```bash
  sudo apt install python3-gi python3-gst-1.0 \
      gstreamer1.0-tools \
      gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
      gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
      gstreamer1.0-libav
  ```
- [ ] Set up Python venv and install minimal deps:
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install opencv-python numpy
  ```
- [ ] Create project structure:
  ```
  mimic/
    __init__.py
    main.py
    capture.py        # GStreamer pipeline
  pyproject.toml
  README.md
  plan.md
  .gitignore
  ```
- [ ] Write `capture.py`: a GStreamer pipeline `v4l2src ! videoconvert ! appsink` that yields numpy BGR frames via a generator function
- [ ] Write `main.py`: consume frames from `capture.py`, display with `cv2.imshow()`
- [ ] Verify: `python -m mimic.main` shows your webcam in a window at 30 FPS

### Gotchas

- GStreamer error messages are cryptic; set `GST_DEBUG=3` env var if pipeline doesn't start
- `appsink` needs `emit-signals=true` and `max-buffers=1 drop=true` to avoid latency buildup
- If `cv2.imshow` won't open, you're probably missing Qt: `sudo apt install libxcb-xinerama0`

### Definition of done

Webcam window opens, smooth video, no warnings in console.

---

## Day 2 — MediaPipe integration (~2h)

**Goal:** Each captured frame produces a set of blendshape values. Verify wiring by watching values change as you make faces.

### Tasks

- [ ] `pip install mediapipe`
- [ ] Download the Face Landmarker model (`face_landmarker.task`) into `models/` — link in MediaPipe docs
- [ ] Create `mimic/inference.py`: a `FaceLandmarker` wrapper class with a `process(frame) -> BlendshapeResult` method
- [ ] In `main.py`, run each captured frame through inference; overlay the 478 landmarks as small dots using `cv2.circle()`
- [ ] Print a few key blendshape values to console: `jawOpen`, `eyeBlinkLeft`, `mouthSmileLeft`
- [ ] Smoke test: open your mouth → `jawOpen` rises toward 1.0; blink → `eyeBlinkLeft` spikes briefly

### Gotchas

- MediaPipe expects RGB, OpenCV gives BGR — `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)` first
- The Face Landmarker has `running_mode=LIVE_STREAM` (async callback) vs `VIDEO` (synchronous) — start with `VIDEO`, it's simpler and you'll multi-process on Day 4 anyway
- Blendshape names use camelCase, not snake_case

### Definition of done

Landmarks overlaid on your face in real time; console prints reasonable blendshape values that respond to expressions.

---

## Day 3 — Avatar renderer v1 (~3h, weekend slot)

**Goal:** Replace the webcam frame with a procedurally drawn cartoon face that responds to your blendshapes.

### Tasks

- [ ] Create `mimic/renderer.py` with a `render(blendshapes) -> np.ndarray` function returning a 640x480 BGR image
- [ ] Implement the cartoon as 5 layers, drawn each frame with OpenCV primitives:
  1. **Face base** — filled ellipse, fixed color
  2. **Left eye** — if `eyeBlinkLeft > 0.5` draw a horizontal line, else draw a filled circle with a smaller circle inside (iris)
  3. **Right eye** — same with `eyeBlinkRight`
  4. **Mouth** — ellipse with height proportional to `jawOpen`, and curve influenced by `(mouthSmileLeft + mouthSmileRight) / 2`
  5. **Eyebrows** — two short lines, Y position modulated by `browInnerUp`
- [ ] In `main.py`, switch the display from raw webcam to rendered avatar
- [ ] Tune the blendshape-to-pixel mappings until the avatar feels responsive — this takes some iteration

### Definition of done

You can blink, smile, frown, raise eyebrows, open your mouth, and the avatar mirrors each one within a noticeable but acceptable lag. **Take a 10-second screen recording at this point — Day 3's demo is what proves the project is real.**

### Notes for the interview

This is the day to start a `NOTES.md` (or just a section here) capturing decisions for later articulation:

- *Why procedural drawing rather than sprites?* — speed of iteration, no asset pipeline needed for v1
- *Why threshold-based eye blinking rather than smooth interpolation?* — discrete state was simpler to debug; smooth interpolation could come later
- *Which blendshapes did you skip and why?* — there are 52; you're using ~7. The unused ones aren't expressive enough to be worth the rendering complexity yet

---

## Day 4 — Multi-process pipeline + profiling (~3h, weekend slot)

**Goal:** Split capture, inference, and rendering into separate processes connected by queues. Measure latency. Identify the bottleneck.

This is the most important day for the interview.

### Tasks

- [ ] Refactor `main.py` into three workers, each in its own `multiprocessing.Process`:
  - `capture_worker(out_queue)` — pulls frames from GStreamer, timestamps each one, pushes `(timestamp, frame)`
  - `inference_worker(in_queue, out_queue)` — pulls frames, runs MediaPipe, pushes `(timestamp, blendshapes)`
  - `render_worker(in_queue, out_queue)` — pulls blendshapes, renders avatar, pushes `(timestamp, avatar_frame)`
- [ ] Display loop in the main process reads from the final queue and shows frames with a latency overlay (`now - timestamp`)
- [ ] Use `multiprocessing.Queue` with `maxsize=2` between stages to enforce backpressure rather than memory growth
- [ ] Install `py-spy` and capture a flame graph during 30 seconds of operation:
  ```bash
  py-spy record -o profile.svg --pid $(pgrep -f mimic.main)
  ```
- [ ] Add per-stage timing: record `t_enter`, `t_exit` in each worker, log p50 / p95 every second
- [ ] Now repeat the same exercise with `asyncio.Queue` inside a single process running three coroutines — compare the two approaches
- [ ] Write findings into `NOTES.md`: latencies measured, where time is spent, which architecture wins and why

### What to look for

The bottleneck is almost certainly MediaPipe on CPU at this point — likely 25–40 ms per frame depending on your CPU. The interesting question is what *else* is going on: queue contention, frame drops, GIL effects when using asyncio vs the multiprocessing isolation.

### Definition of done

You have a flame graph, a latency-per-stage table, and a written paragraph explaining what the bottleneck is and what you'd do to fix it. The flame graph goes in the repo (`docs/profile.svg`).

---

## Day 5 — WebRTC streaming (~2h)

**Goal:** Browser opens a page, clicks Start, sees the avatar streamed live.

### Tasks

- [ ] `pip install aiortc aiohttp`
- [ ] Create `mimic/server.py`: an aiohttp server that serves `static/index.html` and handles WebRTC offer/answer signaling
- [ ] Implement a custom `VideoStreamTrack` subclass whose `recv()` returns the next avatar frame from the rendering queue
- [ ] Create `static/index.html`: video element, Start button, latency/FPS overlay updating from a DataChannel
- [ ] Send the capture timestamp over a WebRTC DataChannel so the browser can compute end-to-end latency including network
- [ ] Test on localhost first, then from a phone on the same WiFi pointed at `http://YOUR_LAN_IP:8080` (a real network hop makes the latency numbers much more interesting)

### Gotchas

- aiortc needs the video frames in `av.VideoFrame` format, not numpy — see `VideoFrame.from_ndarray(arr, format="bgr24")`
- WebRTC NACK / RTX add jitter; on a clean LAN you should see ~30ms added latency over local display
- Some browsers refuse non-HTTPS WebRTC for non-localhost addresses — Chrome lets `http://` work on the LAN if you toggle a flag; otherwise self-signed cert

### Definition of done

You can open Chrome on your phone, point it at your laptop, click Start, see the avatar, and read the latency in the overlay. **Record a 30-second demo of this for Day 7.**

---

## Day 6 — Cloud GPU benchmarking (~2h)

**Goal:** Get one credible "I ran this on a real GPU and measured the difference" data point.

### Tasks

- [ ] Launch an AWS `g4dn.xlarge` (NVIDIA T4, $0.526/hr us-east-1, Deep Learning AMI Ubuntu)
- [ ] SSH in, clone the repo, install deps. The DL AMI has CUDA pre-installed
- [ ] Replace MediaPipe with an ONNX face-landmark model — options:
  - Convert MediaPipe's TFLite model to ONNX via [tflite2onnx](https://github.com/zhenhuaw-me/tflite2onnx)
  - Or use a different model like FAN, MobileFaceNet, or YOLOv8-face from the ONNX model zoo (faster path)
- [ ] Run inference under three configurations on the same input video:
  - `onnxruntime` (CPU)
  - `onnxruntime-gpu` (CUDA execution provider)
  - TensorRT (only if Days 1–5 are clean and you have time)
- [ ] Record p50 and p95 inference latency for each — save the numbers to `docs/benchmarks.md`
- [ ] Stop the instance immediately when done. Total cost should be under $3

### Gotchas

- TensorRT conversion from ONNX often fails on unusual ops; budget at most 30 minutes before falling back to ONNX-CUDA only
- The "fair" benchmark is *inference time only*, not end-to-end — isolate the model call so you're not measuring queue overhead
- Use the same input frames for all three runs (e.g. a pre-recorded 30-second sample) so the comparison is real

### Definition of done

A table in `docs/benchmarks.md` with CPU vs GPU numbers and a one-paragraph interpretation. If you got TensorRT working too, even better.

---

## Day 7 — Polish, demo, narrative (~2h)

**Goal:** The repo looks like a senior engineer's work, the demo is shareable, and you have a 5-minute interview story rehearsed.

### Tasks

- [ ] Update `README.md` with actual measured numbers in the "Profiling targets" table
- [ ] Add `docs/profile.svg` and `docs/benchmarks.md`
- [ ] Record a 30-second screen capture of the demo (phone or laptop, doesn't matter), upload to YouTube unlisted or commit a GIF
- [ ] Add the demo link to the top of the README
- [ ] Flip repo to public
- [ ] Add the GitHub topics (see README for the list)
- [ ] Push the repo link to your CV / interview email
- [ ] **Write out a 5-minute verbal walkthrough** — see "Interview narrative" below — and rehearse it once out loud

---

## Interview narrative (~5 minutes when spoken)

Have these beats ready. Don't memorize a script; know the shape.

1. **The problem framing (~30s)** — "I wanted to build something in the shape of what you do — a real-time video synthesis pipeline taking a motion signal and producing animated video — but small enough to fit in a week on a laptop."

2. **The architecture (~1 min)** — walk through the five-stage pipeline. Mention the choice of MediaPipe blendshapes specifically because they're the ARKit interchange format and the same shape of signal a learned model would output.

3. **The interesting engineering moment (~1.5 min)** — pick *one* concrete decision and go deep. Best candidates: the multiprocessing-vs-asyncio comparison; the queue sizing decision and backpressure trade-off; the CPU-vs-GPU benchmark and what changed. Bring numbers.

4. **What you'd do differently / what's missing (~1 min)** — honesty about the limits. Examples: the procedural cartoon is a placeholder for what would normally be a learned synthesis model; you didn't tackle adaptive bitrate; you simulated batching but didn't implement it; TensorRT was rough. Showing you know what's missing is more impressive than pretending it's complete.

5. **The connection (~30s)** — "The same shape of problem at your scale is harder in ways A, B, C, and that's what I'd love to work on." Reference something specific from their public material.

---

## Risk mitigation

If you fall behind schedule, drop in this order:

1. Day 6 first (cloud GPU benchmark) — it adds polish but the project works without it
2. Day 5's network-hop demo (keep localhost-only WebRTC)
3. Day 4's asyncio comparison (keep just the multiprocessing version)

**Never drop:** Day 3's avatar (the demoable moment), Day 4's profiling (the engineering substance).

If something is completely stuck for more than 45 minutes, switch to the simplest alternative and write up what you tried. "I tried X, hit problem Y, fell back to Z" is a perfectly good interview answer — better than "I got everything working" delivered shakily.

---

## Daily checklist (paste into your terminal or a sticky note)

```
[ ] Day 0: Pre-flight done
[ ] Day 1: Webcam → window via GStreamer
[ ] Day 2: MediaPipe blendshapes streaming
[ ] Day 3: Avatar mirrors face — DEMO RECORDED
[ ] Day 4: Multi-process pipeline + profile + flame graph
[ ] Day 5: WebRTC to browser working
[ ] Day 6: Cloud GPU benchmark numbers
[ ] Day 7: README polished, demo uploaded, narrative rehearsed
```

Good luck.
