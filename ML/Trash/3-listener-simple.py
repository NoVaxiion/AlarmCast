"""3-listener-simple.py

Minimal, commented fire-alarm listener with a --test mode to run on a WAV file.
Keeps the runtime small and is easy to read and tweak.
"""

import argparse
import time
import numpy as np
import torch
import librosa
import sounddevice as sd
from firealarm_net import FireAlarmCNN
import argparse

# --- Configuration (small and readable) ---
SR = 16000             # sampling rate used in training
N_MELS = 64            # mel bands used in training
WIN = 2 * SR           # 2 second window
HOP = 1 * SR           # 1 second hop
THRESH = 0.90          # per-hop confidence threshold for 'fire_alarm'
REQUIRED_HITS = 3      # number of consecutive hops needing positive to trigger
COOLDOWN = 5.0         # seconds to wait after a detection
MIN_RMS = 0.015        # simple silence gate

CLASSES = ['appliance', 'fire_alarm', 'siren']


# Small helper: prepare model (CPU)
def load_model(path='model/best_model.pt'):
    model = FireAlarmCNN(num_classes=3)
    state = torch.load(path, map_location='cpu')
    model.load_state_dict(state)
    model.eval()
    return model


# Predict a single 2s numpy segment -> (pred_label, confidence)
def predict_segment(model, segment):
    # compute mel spectrogram
    mel = librosa.feature.melspectrogram(y=segment, sr=SR, n_mels=N_MELS)
    mel_db = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
    # simple normalization (same as training preprocessing)
    mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-8)
    # convert to torch tensor and forward
    x = torch.from_numpy(mel_db)[None, None, :, :]
    with torch.inference_mode():
        probs = torch.softmax(model(x), dim=1).numpy()[0]
    idx = int(np.argmax(probs))
    return CLASSES[idx], float(probs[idx])


# Minimal realtime listener callback
def realtime_listener(model):
    buf = []
    hits = 0
    last_alert = 0.0

    def callback(indata, frames, time_info, status):
        nonlocal buf, hits, last_alert
        if status:
            return
        buf.extend(indata[:, 0].astype(np.float32))
        if len(buf) < WIN:
            return
        # grab window and advance by hop
        seg = np.array(buf[:WIN], dtype=np.float32)
        del buf[:HOP]

        # silence gate
        rms = float(np.sqrt(np.mean(seg**2) + 1e-12))
        if rms < MIN_RMS:
            hits = 0
            return

        # predict
        label, conf = predict_segment(model, seg)
        if label == 'fire_alarm' and conf >= THRESH:
            hits += 1
        else:
            hits = 0

        now = time.monotonic()
        if hits >= REQUIRED_HITS and (now - last_alert) >= COOLDOWN:
            print(f"Fire Alarm Detected! conf={conf:.2f}")
            last_alert = now
            hits = 0

    print('Listening for fire alarms (press Enter to stop)')
    with sd.InputStream(callback=callback, channels=1, samplerate=SR, dtype='float32'):
        try:
            input()
        except KeyboardInterrupt:
            pass


# Test mode: run the same logic over a WAV file (non-realtime)
def test_wav(model, wav_path):
    y, sr = librosa.load(wav_path, sr=SR)
    hits = 0
    t = 0
    detections = []

    while t + WIN <= len(y):
        seg = y[t:t+WIN]
        rms = float(np.sqrt(np.mean(seg**2) + 1e-12))
        if rms >= MIN_RMS:
            label, conf = predict_segment(model, seg)
            if label == 'fire_alarm' and conf >= THRESH:
                hits += 1
            else:
                hits = 0
            now_sec = t / SR
            if hits >= REQUIRED_HITS and (now_sec - (detections[-1] if detections else -999)) >= COOLDOWN:
                detections.append(now_sec)
                print(f'Detected fire at ~{now_sec:.1f}s (conf={conf:.2f})')
        t += HOP

    if not detections:
        print('No fire alarms detected in WAV')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', default='model/best_model.pt')
    p.add_argument('--test', help='Path to WAV file to run test mode')
    p.add_argument('--device', type=int, default=None, help='Sounddevice input device index (optional)')
    args = p.parse_args()

    model = load_model(args.model)

    if args.test:
        test_wav(model, args.test)
    else:
        # print device info if provided
        if args.device is not None:
            try:
                sd.default.device = args.device
                print('Using audio device index:', args.device)
            except Exception as e:
                print('Failed to set audio device:', e)
        try:
            realtime_listener(model)
        except Exception as e:
            print('Realtime listener failed:', e)


if __name__ == '__main__':
    main()
