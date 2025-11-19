"""Minimal fire-alarm listener: short and easy to read.

Behavior: 2s windows, 1s hop. Simple RMS gate, per-hop prediction and short hit-count debounce.
"""

from firealarm_net import FireAlarmCNN
import sounddevice as sd
import torch
import librosa
import numpy as np
import time

# Config
SR = 16000
N_MELS = 64
WIN = SR * 2
HOP = SR * 1
THRESH = 0.90
REQUIRED_HITS = 3
COOLDOWN = 5.0
MIN_RMS = 0.015

# Model
model = FireAlarmCNN(num_classes=3)
state = torch.load('model/best_model.pt', map_location='cpu')
model.load_state_dict(state)
model.eval()

CLASSES = ['appliance', 'fire_alarm', 'siren']

buf = []
hits = 0
last_alert = 0.0


def audio_callback(indata, frames, time_info, status):
    global buf, hits, last_alert
    if status:
        return
    buf.extend(indata[:, 0].astype(np.float32))
    if len(buf) < WIN:
        return
    seg = np.array(buf[:WIN], dtype=np.float32)
    del buf[:HOP]

    rms = float(np.sqrt(np.mean(seg**2) + 1e-12))
    if rms < MIN_RMS:
        hits = 0
        return

    mel = librosa.feature.melspectrogram(y=seg, sr=SR, n_mels=N_MELS)
    mel_db = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
    mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-8)

    x = torch.from_numpy(mel_db)[None, None, :, :]
    with torch.inference_mode():
        probs = torch.softmax(model(x), dim=1).numpy()[0]
    pred = int(np.argmax(probs))
    conf = float(probs[pred])

    if CLASSES[pred] == 'fire_alarm' and conf >= THRESH:
        hits += 1
    else:
        hits = 0

    now = time.monotonic()
    if hits >= REQUIRED_HITS and (now - last_alert) >= COOLDOWN:
        print(f'Fire Alarm Detected! conf={conf:.2f}')
        last_alert = now
        hits = 0


print('Listening (press Enter to stop)')
with sd.InputStream(callback=audio_callback, channels=1, samplerate=SR, dtype='float32'):
    try:
        input()
    except KeyboardInterrupt:
        pass