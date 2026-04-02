# AlarmCast Audio Listener Documentation

## Overview

The audio detection system is split across three files:

| File                 | Role                                                                                                 |
| -------------------- | ---------------------------------------------------------------------------------------------------- |
| `base_listener.py`   | All shared logic — YAMNet loading, inference, ring buffer, worker thread, hit counter, alarm trigger |
| `usb_listener.py`    | Subclass for USB microphone (48kHz)                                                                  |
| `camera_listener.py` | Subclass for camera microphone (16kHz)                                                               |

Only one listener runs at a time, selected via `startup.py`.

---

## base_listener.py

### Constants

| Constant        | Value | Description                                                      |
| --------------- | ----- | ---------------------------------------------------------------- |
| `REQUIRED_HITS` | 2     | Consecutive danger predictions needed before triggering an alarm |
| `RESET_TIME`    | 3.0s  | Cooldown period before alarm can trigger again                   |
| `MIN_RMS`       | 0.001 | Silence gate — windows below this RMS are skipped                |

### YAMNet Class Indices

YAMNet outputs scores for 521 audio classes. Only 5 are used:

| Index | Class          | Role                       |
| ----- | -------------- | -------------------------- |
| 394   | Fire alarm     | Primary fire signal        |
| 393   | Smoke detector | Secondary fire signal      |
| 382   | Alarm          | Supporting signal for both |
| 475   | Beep, bleep    | Primary CO signal          |
| 392   | Buzzer         | Primary CO signal          |

### Detection Rules

Rules are evaluated in order. First match wins.

**Rule 1 — Fire Alarm:**

```
fire > 0.30
OR (fire > 0.15 AND smoke > 0.25)
OR (fire > 0.15 AND alarm > 0.22)
```

Fire must be the dominant signal, either alone or corroborated by smoke or alarm scores.

**Rule 2 — CO Alarm:**

```
(beep > 0.15 OR buzzer > 0.15) AND fire < 0.30 AND smoke < 0.25
```

Beep/buzzer dominant with fire and smoke both low.

**Rule 3 — Ambiguous:**

```
alarm > 0.20 OR smoke > 0.20
```

Something alarm-like but unclear. Tiebreaks on whether fire >= beep + buzzer.

**Rule 4 — No Detection:**
Nothing crossed any threshold. Classified as `Random`.

### Confidence Scoring

| Class | Formula                                            |
| ----- | -------------------------------------------------- |
| Fire  | `fire + smoke * 0.3 + alarm * 0.2` (capped at 1.0) |
| CO    | `(beep + buzzer) * 1.2` (capped at 1.0)            |

### Hit Counter

Detection requires `REQUIRED_HITS` (2) consecutive danger predictions:

| Condition                   | Action                    |
| --------------------------- | ------------------------- |
| `is_danger AND conf > 0.60` | Danger hit                |
| `is_danger AND conf > 0.35` | Low confidence danger hit |
| Neither                     | Resets hit counter to 0   |

Once hits reach `REQUIRED_HITS` and the cooldown has passed, `trigger_alarm()` fires and sends a notification via `client.send_alarm_notification()`.

### Audio Pipeline

The audio pipeline is designed to keep the audio callback as lightweight as possible to prevent buffer overruns.

```
Hardware Mic
    │
    ▼
audio_callback()         ← Runs on audio thread, must be fast
    │  Write chunk into ring buffer (numpy slice assignment)
    │  Increment samples_since_hop counter
    │  Once HOP_SIZE samples accumulated → put write index into infer_queue
    │
    ▼
infer_queue (maxsize=2)  ← Drops new items if full (backlog protection)
    │
    ▼
_inference_worker()      ← Runs on background thread
    │  Reconstruct chronological window from ring buffer
    │  Downsample if needed (e.g. 48kHz → 16kHz via ::3 slice)
    │  Silence gate check
    │  YAMNet inference
    │  Apply detection rules
    │  Update hit counter
    │  Trigger alarm if threshold reached
```

### Ring Buffer

A pre-allocated numpy array of size `SAMPLE_RATE * 4` (4 seconds of audio). A write pointer (`w_idx`) tracks the current position. When a chunk wraps past the end of the buffer it is split into two slice writes. The worker reconstructs chronological order by concatenating `ring[w_idx:]` + `ring[:w_idx]`.

### BaseAlarmListener Class

```python
class BaseAlarmListener:
    SAMPLE_RATE = None  # Set by subclass
    DOWNSAMPLE  = 1     # Set by subclass (e.g. 3 for 48kHz → 16kHz)
    BLOCK_SIZE  = None  # Set by subclass
```

**Methods:**

| Method                                  | Description                                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `__init__(client)`                      | Loads YAMNet, caches input/output details, initializes ring buffer and worker thread             |
| `_inference_worker()`                   | Background thread — reconstructs window, downsamples, runs YAMNet, applies rules, triggers alarm |
| `audio_callback(...)`                   | Audio thread — writes into ring buffer, enqueues write index every hop                           |
| `trigger_alarm(alarm_type, confidence)` | Prints detection and calls `client.send_alarm_notification()`                                    |
| `start_listening()`                     | Abstract — subclass must implement with device-specific `sd.InputStream`                         |
| `stop_listening()`                      | Stops stream, signals worker to exit, joins thread                                               |

---

## usb_listener.py

Used when the Raspberry Pi is connected to a **USB microphone**.

```python
class FireAlarmListener(BaseAlarmListener):
    SAMPLE_RATE = 48000  # USB mic native rate, clean 3:1 ratio to YAMNet's 16kHz
    DOWNSAMPLE  = 3      # 48000 → 16000 via ::3 slice in worker
    BLOCK_SIZE  = 96000  # 2s hardware buffer, matches HOP_SIZE
```

**Stream configuration:**

- `device=2` — USB mic device index on the Pi
- `channels=1` — Mono
- `dtype='float32'` — No conversion needed in callback

**Downsampling:** Since 48000 / 16000 = exactly 3, downsampling is a single `seg[::3]` slice — no interpolation, near-zero cost.

---

## camera_listener.py

Used when the Raspberry Pi is connected to a **camera module with built-in microphone**.

```python
class FireAlarmListener(BaseAlarmListener):
    SAMPLE_RATE = 16000  # Camera mic captures at 16kHz, matches YAMNet directly
    DOWNSAMPLE  = 1      # No downsampling needed
    BLOCK_SIZE  = 32000  # 2s hardware buffer, matches HOP_SIZE
```

**Stream configuration:**

- `device=2` — Camera mic device index on the Pi
- `channels=1` — Mono
- `dtype='float32'` — No conversion needed in callback

**No downsampling:** Camera mic natively captures at 16kHz, which is exactly what YAMNet expects. The `DOWNSAMPLE = 1` flag skips the downsample step entirely.

---

## Switching Between Listeners

In `startup.py`, swap the import line to select the active listener:

```python
# USB microphone
from ml_pi.usb_listener import FireAlarmListener

# Camera microphone
# from ml_pi.camera_listener import FireAlarmListener
```

---

## Timing and Window Behavior

| Parameter           | USB                         | Camera             |
| ------------------- | --------------------------- | ------------------ |
| Capture rate        | 48000 Hz                    | 16000 Hz           |
| Window size         | 4s (192000 samples)         | 4s (64000 samples) |
| Hop size            | 2s (96000 samples)          | 2s (32000 samples) |
| Block size          | 96000 (2s)                  | 32000 (2s)         |
| YAMNet input rate   | 16000 Hz (after downsample) | 16000 Hz           |
| Inference frequency | Every 2s                    | Every 2s           |
| Min detection time  | ~4s (2 hits × 2s hop)       | ~4s                |

---

## Issues Encountered During Development

### 1. Buffer Overruns (`input overflow`)

**Problem:** `camera_listener.py` originally ran YAMNet inference directly inside the audio callback. Since inference takes 50–150ms per call and the callback must return immediately to accept new audio, the hardware buffer overflowed constantly.

**Fix:** Moved all inference to a background worker thread. The callback now only writes audio into a ring buffer and enqueues a single integer (the write index). Inference runs entirely on the worker thread, decoupled from the audio thread.

### 2. Python List Buffer in camera_listener

**Problem:** The original `camera_listener.py` used a Python list (`self.buffer`) for audio accumulation, calling `.extend()` and `del buffer[:HOP_SIZE]` inside the callback. List deletion is O(n) and triggers garbage collection, adding unpredictable latency inside the audio thread.

**Fix:** Replaced with a pre-allocated numpy ring buffer. All writes are fast numpy slice assignments with no memory allocation.

### 3. blocksize Too Large (usb_listener)

**Problem:** `blocksize=96000` (2 seconds) meant the OS only needed to schedule the audio callback once every 2 seconds. On a busy Pi, OS scheduling jitter could delay that callback long enough to overflow the hardware buffer. It also meant inference fired every 2s even though HOP_SIZE was 1s.

**Fix:** Reduced `blocksize` to match `HOP_SIZE` so inference fires at the intended rate. Later set to `24000` (0.5s) on the delete\_ test version to further reduce overflow risk.

### 4. `get_input_details()` / `get_output_details()` Called Every Inference

**Problem:** Both calls were inside `yamnet_predict()`, so they ran on every single inference invocation, adding unnecessary overhead.

**Fix:** Called once in `__init__` after loading the interpreter and cached as `self.input_details` / `self.output_details`. Passed into `yamnet_predict()` as arguments.

### 5. Fire vs CO Misclassification

**Problem:** YAMNet's `fire_alarm` class (394) is trained on wailing/siren-style fire alarms. A beeping-pattern fire alarm (T3 pattern) produces high beep/buzzer scores that are indistinguishable from a CO alarm at the default threshold of `fire > 0.15`.

**Attempts:**

- Raised fire threshold to `0.30` — fixed CO false positives but caused fire to be missed
- Added smoke as secondary fire signal (`fire > 0.15 AND smoke > 0.25`) — partial improvement
- Tested `Siren` (390) and `Fire engine` (319) class indices — both scored near-zero for both alarm types, no useful signal
- Added alarm score as tiebreaker (`fire > 0.15 AND alarm > 0.22`) — improved fire detection

**Root cause:** The fire alarm used in testing was a beeping pattern identical to CO at the frequency level. YAMNet cannot distinguish them by score alone. The issue was ultimately resolved by adjusting the alarm volume during testing, which produced clearer fire scores. The current three-condition Rule 1 handles the overlap.

### 6. Duplicate Code Across Listeners

**Problem:** `usb_listener.py` and `camera_listener.py` contained identical inference logic, detection rules, ring buffer implementation, and worker thread — only the sample rate and blocksize differed.

**Fix:** Refactored into `base_listener.py` with a `BaseAlarmListener` class. Each listener is now a thin subclass that only defines `SAMPLE_RATE`, `DOWNSAMPLE`, `BLOCK_SIZE`, and `start_listening()`.

### 7. Misindented Comment Breaking Worker Thread

**Problem:** During refactoring, a comment was accidentally indented inside the `if w_idx is None: break` block in `_inference_worker()`. This would have made the entire worker body unreachable after the break condition.

**Fix:** Corrected indentation so the comment and all subsequent worker logic sits outside the break block.
