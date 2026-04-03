import numpy as np
import wave
import time
import os
from datetime import datetime
from collections import deque


COOLDOWN      = 60.0   # Seconds before another recording can be saved
CLIP_DURATION = 10     # Seconds of audio to save per event
SAVE_DIR      = "recordings"


class AudioSaver:
    def __init__(self, sample_rate):
        self.sample_rate  = sample_rate
        self.last_save    = 0.0
        self.buffer_size  = sample_rate * CLIP_DURATION

        # Rolling buffer — keeps last 10 seconds of audio at all times
        # deque with maxlen auto-discards oldest samples when full
        self.rolling = deque(maxlen=self.buffer_size)

        os.makedirs(SAVE_DIR, exist_ok=True)

    def feed(self, chunk):
        """Feed incoming audio chunk into the rolling buffer. Call from audio_callback."""
        self.rolling.extend(chunk)

    def save(self, alarm_type):
        """Save the last 10 seconds of audio to a WAV file. Enforces 60s cooldown."""
        now = time.monotonic()
        if (now - self.last_save) < COOLDOWN:
            return  # Still in cooldown, skip

        if len(self.rolling) < self.buffer_size:
            return  # Not enough audio buffered yet

        self.last_save = now

        # Convert rolling buffer to numpy float32 array
        audio = np.array(self.rolling, dtype=np.float32)

        # Convert float32 [-1.0, 1.0] → int16 for WAV compatibility
        audio_int16 = (audio * 32767).clip(-32768, 32767).astype(np.int16)

        # Build filename: "recordings/SMOKE_2026-04-02_14-33-07.wav"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        label     = "SMOKE" if alarm_type == "fire_alarm" else "CO"
        filename  = os.path.join(SAVE_DIR, f"{label}_{timestamp}.wav")

        with wave.open(filename, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2) # 2 bytes = int16
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        print(f"Audio saved: {filename}")
