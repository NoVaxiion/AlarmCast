import ai_edge_litert.interpreter as tflite
from config import BASE_URL
from datetime import datetime
import sounddevice as sd
from util import Client
import numpy as np
import threading
import tempfile
import requests
import soundfile as sf
import queue
import time
import os


# Alert Settings
REQUIRED_HITS = 2    # Consecutive danger predictions before triggering alarm
RESET_TIME    = 10.0  # Seconds before alarm can trigger again
MIN_RMS       = 0.001
API_BASE = BASE_URL.rstrip("/")


# Key YAMNet Class Indices From CSV
# Fire  → IDX_FIRE_ALARM (394) high (0.30+), or (0.15+ with smoke>0.25 or alarm>0.22)
# CO    → IDX_BEEP (475) + IDX_BUZZER (392) high, IDX_FIRE_ALARM low (<0.30)
IDX_FIRE_ALARM  = 394  # "Fire alarm"      - Most exclusive fire indicator
IDX_SMOKE       = 393  # "Smoke detector"  - High for fire, moderate for CO
IDX_ALARM       = 382  # "Alarm"           - High for both
IDX_BEEP        = 475  # "Beep, bleep"     - Key CO indicator
IDX_BUZZER      = 392  # "Buzzer"          - Key CO indicator


def load_yamnet():
    try:
        interpreter = tflite.Interpreter(model_path="ml_pi/model/yamnet.tflite")
        interpreter.allocate_tensors()
        return interpreter

    except Exception as e:
        print(f"Failed to load YAMNet: {e}")
        exit(1)


def yamnet_predict(interpreter, input_details, output_details, audio_data):
    # Yamnet Input shape is [1 x 15600]
    # As Live Audio Input is [1 x 16000]
    CHUNK_SIZE = 15600  # 0.975s at 16kHz

    # Run YAMNet on each 0.975s chunk of the window
    all_scores = []
    for start in range(0, len(audio_data) - CHUNK_SIZE + 1, CHUNK_SIZE):
        chunk = audio_data[start:start + CHUNK_SIZE].astype(np.float32)
        interpreter.set_tensor(input_details[0]['index'], chunk.reshape(15600))
        interpreter.invoke()
        scores = interpreter.get_tensor(output_details[0]['index'])[0]
        all_scores.append(scores)

    mean_scores = np.mean(all_scores, axis=0)

    # Extract relevant scores
    score_fire  = float(mean_scores[IDX_FIRE_ALARM])
    score_smoke = float(mean_scores[IDX_SMOKE])
    score_alarm = float(mean_scores[IDX_ALARM])
    score_beep  = float(mean_scores[IDX_BEEP])
    score_buzz  = float(mean_scores[IDX_BUZZER])

    # Rule 1 - Fire Alarm: Fire dominant, fire+smoke elevated, or fire+alarm elevated
    if score_fire > 0.30 or (score_fire > 0.15 and score_smoke > 0.25) or (score_fire > 0.15 and score_alarm > 0.22):
        predicted = 'fire_alarm'
        conf = min(score_fire + score_smoke * 0.3 + score_alarm * 0.2, 1.0)

    # Rule 2 - CO: Beep/Buzzer dominant, fire and smoke alarm both low
    elif (score_beep > 0.15 or score_buzz > 0.15) and score_fire < 0.30 and score_smoke < 0.25:
        predicted = 'carbon_alarm'
        conf = min((score_beep + score_buzz) * 1.2, 1.0)

    # Rule 3 - Ambiguous: something alarm-like but unclear, tiebreak on raw scores
    elif score_alarm > 0.20 or score_smoke > 0.20:
        if score_fire >= score_beep + score_buzz:
            predicted = 'fire_alarm'
            conf      = min(score_fire + score_smoke * 0.2, 1.0)
        else:
            predicted = 'carbon_alarm'
            conf      = min(score_beep + score_buzz + score_alarm * 0.2, 1.0)

    # Rule 4 - Nothing crossed any threshold
    else:
        predicted = 'Random'
        conf      = max(0.0, 1.0 - max(score_fire, score_beep, score_alarm))

    # Score breakdown for logging
    breakdown = {
        'fire':   round(score_fire,  3),
        'co':     round(max(score_beep, score_buzz), 3),
        'smoke':  round(score_smoke, 3),
        'alarm':  round(score_alarm, 3),
        'beep':   round(score_beep,  3),
        'buzzer': round(score_buzz,  3),
    }

    return predicted, conf, breakdown


class BaseAlarmListener:
    # Subclasses sets these
    SAMPLE_RATE = None  # Native capture rate
    DOWNSAMPLE  = 1     # Factor to downsample to 16kHz (e.g. 3 for 48kHz → 16kHz)
    BLOCK_SIZE  = None  # Hardware buffer size in samples

    # Clip settings
    PRE_TRIGGER_SECONDS = 3
    POST_TRIGGER_SECONDS = 2

    def __init__(self, client):
        self.interpreter    = load_yamnet()
        self.input_details  = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.hits           = 0
        self.last_alert     = 0.0
        self.stream         = None
        self.client         = client

        window_size     = self.SAMPLE_RATE * 4  # 4 second window
        self.hop_size   = self.SAMPLE_RATE * 2  # 2 second hop

        # Ring buffer - pre-allocated contiguous numpy array
        # Callback does only slice-writes + integer math, worker does all array work
        self.ring              = np.zeros(window_size, dtype=np.float32)
        self.window_size       = window_size
        self.w_idx             = 0
        self.samples_since_hop = 0
        self.ring_full         = False

        # Queue carries only the write index (an int) - zero allocation in callback
        self.infer_queue  = queue.Queue(maxsize=2)
        self.worker       = threading.Thread(target=self._inference_worker, daemon=True)
        self.worker.start()

        # Audio clip recording state
        self.pre_trigger_samples  = self.SAMPLE_RATE * self.PRE_TRIGGER_SECONDS
        self.post_trigger_samples = self.SAMPLE_RATE * self.POST_TRIGGER_SECONDS
        self.rolling_audio = np.array([], dtype=np.float32)

        self.pending_alert = False
        self.pending_alarm_type = None
        self.pending_confidence = None
        self.pending_alarm_datetime = None
        self.pending_pre_trigger_audio = None
        self.pending_post_trigger_audio = np.array([], dtype=np.float32)

    def _inference_worker(self):
        """Runs in background thread - handles all array work and YAMNet inference."""
        while True:
            w_idx = self.infer_queue.get()
            if w_idx is None:
                break

            # 1. Reconstruct chronological window from ring buffer using write index
            #    Two-slice concat done here in worker, not in callback
            seg = np.concatenate([self.ring[w_idx:], self.ring[:w_idx]])

            # 2. Downsample to 16kHz if needed (exact ratio - single slice op, near instant)
            if self.DOWNSAMPLE > 1:
                seg = seg[::self.DOWNSAMPLE]

            # 3. Predict
            try:
                # Silence gate - skips silences and resets hit counter
                if np.sqrt(np.mean(seg**2)) < MIN_RMS:
                    self.hits = 0
                    continue
                predicted_class, conf, breakdown = yamnet_predict(
                    self.interpreter, self.input_details, self.output_details, seg
                )
            except Exception as e:
                print(f"Prediction error: {e}")
                continue

            # 4. Log prediction
            is_danger = predicted_class in ['fire_alarm', 'carbon_alarm']

            if is_danger:
                print(f"\n\n\n{predicted_class.upper()} ({conf:.2f})")
                print(f"   🔥 Fire: {breakdown['fire']:.3f}  💨 CO: {breakdown['co']:.3f}")
                #print(f"   Smoke={breakdown['smoke']}  Alarm={breakdown['alarm']}  Beep={breakdown['beep']}  Buzzer={breakdown['buzzer']}")

            # 5. Hit counter. Requires consecutive danger predictions
            if is_danger and conf > 0.60:
                self.hits += 1
                print(f"   ⚠️  Danger hit {self.hits}/{REQUIRED_HITS}")

            elif is_danger and conf > 0.35:
                self.hits += 1
                print(f"   ⚠️  Low confidence danger hit {self.hits}/{REQUIRED_HITS}")

            else:
                self.hits = 0

            # 6. Trigger alarm if enough consecutive hits and cooldown passed
            now = time.monotonic()
            if self.hits >= REQUIRED_HITS and (now - self.last_alert) >= RESET_TIME:
                self.trigger_alarm(predicted_class, conf)
                self.last_alert = now
                self.hits       = 0

    def audio_callback(self, indata, frames, time_info, status):
        # Sounddevice Error Handler. Catches mic buffer overruns or hardware issues
        if status:
            print(f"Stream status: {status}")

        # 1. Capture Audio - write into ring buffer via fast numpy slice assignment
        #    Wraps around if chunk straddles the end of the buffer
        chunk = indata[:, 0]  # No astype - stream is already float32

        # 2. Maintain rolling pre-trigger audio buffer (native sample rate)
        self.rolling_audio = np.concatenate((self.rolling_audio, chunk))
        if len(self.rolling_audio) > self.pre_trigger_samples:
            self.rolling_audio = self.rolling_audio[-self.pre_trigger_samples:]

        # 3. Collect post-trigger audio after an alarm is detected
        if self.pending_alert:
            self.pending_post_trigger_audio = np.concatenate(
                (self.pending_post_trigger_audio, chunk)
            )
            if len(self.pending_post_trigger_audio) >= self.post_trigger_samples:
                post_audio   = self.pending_post_trigger_audio[:self.post_trigger_samples]
                pre_audio    = self.pending_pre_trigger_audio.copy()
                alarm_type   = self.pending_alarm_type
                confidence   = self.pending_confidence
                alarm_dt     = self.pending_alarm_datetime

                self.pending_alert               = False
                self.pending_alarm_type          = None
                self.pending_confidence          = None
                self.pending_alarm_datetime      = None
                self.pending_pre_trigger_audio   = None
                self.pending_post_trigger_audio  = np.array([], dtype=np.float32)

                full_clip = np.concatenate((pre_audio, post_audio))
                threading.Thread(
                    target=self.process_and_send_alert,
                    args=(alarm_type, confidence, alarm_dt, full_clip),
                    daemon=True
                ).start()

        end   = self.w_idx + frames
        if end <= self.window_size:
            self.ring[self.w_idx:end] = chunk
        else:
            # Chunk wraps around end of ring - split into two writes
            split = self.window_size - self.w_idx
            self.ring[self.w_idx:]               = chunk[:split]
            self.ring[:end - self.window_size]   = chunk[split:]
        self.w_idx = end % self.window_size

        # 2. Track samples and mark buffer full after first complete 4s revolution
        self.samples_since_hop += frames
        if not self.ring_full and self.w_idx == 0:
            self.ring_full = True

        # 3. Wait until buffer is full and a full hop has elapsed (2 seconds)
        #    This limits snapshots to once per hop; keeps callback lightweight
        if not self.ring_full or self.samples_since_hop < self.hop_size:
            return
        self.samples_since_hop = 0

        # 4. Hand off only the write index; zero allocation, just an integer
        try:
            self.infer_queue.put_nowait(self.w_idx)
        except queue.Full:
            pass  # Silently drop; a fresh window next hop is more useful

    def trigger_alarm(self, alarm_type, confidence):
        label = "SMOKE" if alarm_type == "fire_alarm" else "CO"
        print(f"   🚨 {label} DETECTED! (Conf: {confidence:.2f})")

        if not self.pending_alert:
            self.pending_alert              = True
            self.pending_alarm_type         = alarm_type
            self.pending_confidence         = confidence
            self.pending_alarm_datetime     = datetime.now()
            self.pending_pre_trigger_audio  = self.rolling_audio.copy()
            self.pending_post_trigger_audio = np.array([], dtype=np.float32)
            print(f"   Collecting {self.POST_TRIGGER_SECONDS}s of post-trigger audio...")

    def process_and_send_alert(self, alarm_type, confidence, alarm_datetime, full_clip):
        label = "SMOKE" if alarm_type == "fire_alarm" else "CO"
        audio_url     = None
        temp_file_path = None

        try:
            clip = full_clip.astype(np.float32)

            # Downsample to 16kHz if captured at a higher rate
            if self.DOWNSAMPLE > 1:
                clip = clip[::self.DOWNSAMPLE]

            save_rate = self.SAMPLE_RATE // self.DOWNSAMPLE

            # DC offset removal + normalize to 95% peak
            clip = clip - np.mean(clip)
            peak = np.max(np.abs(clip))
            if peak > 0:
                clip = clip / peak
            clip = np.clip(clip * 0.95, -1.0, 1.0)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_file_path = tmp.name

            sf.write(temp_file_path, clip.reshape(-1, 1), save_rate, subtype="PCM_16")
            audio_url = self.upload_audio_file(temp_file_path)
            print(f"   Audio uploaded: {audio_url}")

        except Exception as e:
            print(f"   Audio capture/upload failed: {e}")
            audio_url = None

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass

        try:
            result = self.client.send_alarm_notification(
                label, confidence, alarm_datetime, audio_url=audio_url
            )
            print("   Alert result:", result)
        except Exception as e:
            print(f"   Failed to send alert notification: {e}")

    def start_listening(self):
        raise NotImplementedError("Subclass must implement start_listening()")
    
    def stop_listening(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.infer_queue.put(None)
        self.worker.join()
        print("\nListener stopped.")
    
    def upload_audio_file(self, file_path):
        url = f"{API_BASE}/api/audio/upload"

        with open(file_path, "rb") as audio_file:
            files = {
                "audio": (os.path.basename(file_path), audio_file, "audio/wav")
            }
            response = requests.post(url, files=files, timeout=30)

        response.raise_for_status()
        payload = response.json()
        return payload.get("audio_url")
