"""3-listener-advanced.py

Advanced, still-readable listener implementing debounce, buffer-windows,
min-duration, grace-period, cooldown, and optional snippet saving.

Usage examples:
  python3 3-listener-advanced.py --model model/best_model.pt --device cpu
  python3 3-listener-advanced.py --test some.wav --verbose
  python3 3-listener-advanced.py --input-device 1 --save-snippets

Requires: torch, numpy, librosa, sounddevice. Optional: soundfile or scipy for saving snippets.
"""

import argparse
import collections
import os
import time
import sys

import numpy as np
import torch
import librosa
import sounddevice as sd

from firealarm_net import FireAlarmCNN


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="model/best_model.pt")
    ap.add_argument("--threshold", type=float, default=0.75, help="probability threshold for fire_alarm")
    ap.add_argument("--window", type=float, default=2.0, help="analysis window (s)")
    ap.add_argument("--hop", type=float, default=0.5, help="hop between analyses (s)")
    ap.add_argument("--debounce", type=int, default=3, help="number of positive windows in the recent buffer required to trigger")
    ap.add_argument("--buffer-windows", type=int, default=6, help="how many recent windows to consider for debounce")
    ap.add_argument("--cooldown", type=float, default=10.0, help="seconds to suppress further alerts after a detection")
    ap.add_argument("--min-duration", type=float, default=0.0, help="minimum seconds of continuous detection before alerting (0=disabled)")
    ap.add_argument("--grace-period", type=float, default=2.0, help="seconds to allow gaps in detection before resetting timer")
    ap.add_argument("--device", default="cpu", help="torch device, e.g. cpu or cuda:0")
    ap.add_argument("--input-device", default=None, help="sounddevice input device index or name (optional)")
    ap.add_argument("--verbose", action="store_true", help="print per-window probabilities")
    ap.add_argument("--save-snippets", action="store_true", help="save short audio snippets when prob exceeds snippet-threshold (debug)")
    ap.add_argument("--snippet-threshold", type=float, default=0.2, help="prob threshold to save snippet for debugging")
    ap.add_argument("--snippet-cooldown", type=float, default=2.0, help="seconds to wait before saving another debug snippet")
    ap.add_argument("--min-rms", type=float, default=0.005, help="minimum RMS energy required to consider a window (silence gate)")
    ap.add_argument("--ignore-classes", nargs='+', default=[], help="class names to ignore (e.g., siren appliance)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--test", help="path to a WAV file to run in non-realtime test mode")
    return ap.parse_args()


def load_model(path, device):
    # If requested path doesn't exist, try sensible fallbacks in ./model/
    if not os.path.exists(path):
        model_dir = os.path.dirname(path) or 'model'
        candidates = []
        if os.path.isdir(model_dir):
            for f in os.listdir(model_dir):
                if f.endswith('.pt') or f.endswith('.pth'):
                    candidates.append(os.path.join(model_dir, f))
        if candidates:
            found = sorted(candidates)[0]
            print(f"Warning: requested model not found at {path}. Using first candidate: {found}")
            path = found
        else:
            raise FileNotFoundError(f"Model file not found: {path} (no .pt in {model_dir})")

    model = FireAlarmCNN(num_classes=3)
    state = torch.load(path, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    print('Loaded model from', path)
    return model


def save_wav(path, samples, sr):
    # Try soundfile first, then scipy fallback
    try:
        import soundfile as sf

        sf.write(path, samples, sr)
        return True
    except Exception:
        try:
            from scipy.io.wavfile import write as wavwrite

            int16 = np.int16(np.clip(samples, -1.0, 1.0) * 32767)
            wavwrite(path, sr, int16)
            return True
        except Exception:
            return False


def run_test_wav(model, wav_path, args):
    y, sr = librosa.load(wav_path, sr=int(16000))
    window = int(args.window * sr)
    hop = int(args.hop * sr)

    buf_windows = collections.deque(maxlen=args.buffer_windows)
    last_snip_save = 0.0
    last_alert = -1e9

    t = 0
    detection_state = False
    detection_start = None
    last_positive_time = None

    while t + window <= len(y):
        seg = y[t:t + window]
        rms = float(np.sqrt(np.mean(seg ** 2) + 1e-12))
        now = t / sr
        if rms < args.min_rms:
            buf_windows.append(False)
            # manage grace
            if detection_state and (now - last_positive_time) > args.grace_period:
                detection_state = False
                detection_start = None
            t += hop
            continue

        # preprocess + predict
        mel = librosa.feature.melspectrogram(y=seg, sr=sr, n_mels=64)
        mel_db = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
        mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-8)
        x = torch.from_numpy(mel_db)[None, None, :, :]
        with torch.inference_mode():
            probs = torch.softmax(model(x.to(next(model.parameters()).device)), dim=1).cpu().numpy()[0]
        prob_fire = float(probs[1])
        is_pos = prob_fire >= args.threshold
        buf_windows.append(is_pos)

        if args.verbose:
            print(f"t={now:.1f}s prob_fire={prob_fire:.3f} positives_in_buffer={sum(buf_windows)}/{len(buf_windows)}")

        if is_pos:
            last_positive_time = now

        # debug snippet
        if args.save_snippets and prob_fire >= args.snippet_threshold and (now - last_snip_save) >= args.snippet_cooldown:
            out = f"snippet_{int(now)}.wav"
            ok = save_wav(out, seg, sr)
            if ok:
                print('Saved debug snippet to', out)
            last_snip_save = now

        # debounce
        if sum(buf_windows) >= args.debounce:
            if not detection_state:
                detection_state = True
                detection_start = now
            # check min-duration
            if args.min_duration <= 0 or (now - detection_start) >= args.min_duration:
                if (now - last_alert) >= args.cooldown:
                    print(f"[TEST] Fire Alarm Detected at ~{now:.1f}s conf={prob_fire:.2f}")
                    last_alert = now
                    detection_state = False
                    detection_start = None
                    buf_windows.clear()
        else:
            # if in detection_state allow grace period, else reset
            if detection_state and (now - last_positive_time) > args.grace_period:
                detection_state = False
                detection_start = None

        t += hop

    print('Test run complete')


def run_realtime(model, args):
    sr = 16000
    window = int(args.window * sr)
    hop = int(args.hop * sr)

    # ring buffer for audio context (keep 10s)
    recent_audio = collections.deque(maxlen=sr * 10)
    stream_buf = []
    buf_windows = collections.deque(maxlen=args.buffer_windows)

    last_snip_save = 0.0
    last_alert = -1e9
    detection_state = False
    detection_start = None
    last_positive_time = None

    device = args.input_device
    if device is not None:
        try:
            # try to set default device (index or name)
            sd.default.device = int(device) if str(device).isdigit() else device
            print('Using input device:', sd.default.device)
        except Exception as e:
            print('Warning: could not set input device:', e)

    def callback(indata, frames, time_info, status):
        nonlocal stream_buf, recent_audio, buf_windows, last_snip_save, last_alert
        nonlocal detection_state, detection_start, last_positive_time
        if status:
            # optionally print status in verbose mode
            if args.verbose:
                print('Stream status:', status)
            return
        samples = indata[:, 0].astype(np.float32)
        recent_audio.extend(samples.tolist())
        stream_buf.extend(samples.tolist())

        # process when we have a full window
        while len(stream_buf) >= window:
            seg = np.array(stream_buf[:window], dtype=np.float32)
            del stream_buf[:hop]
            now = time.monotonic()

            rms = float(np.sqrt(np.mean(seg ** 2) + 1e-12))
            if rms < args.min_rms:
                buf_windows.append(False)
                if detection_state and (now - last_positive_time) > args.grace_period:
                    detection_state = False
                    detection_start = None
                continue

            mel = librosa.feature.melspectrogram(y=seg, sr=sr, n_mels=64)
            mel_db = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
            mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-8)
            x = torch.from_numpy(mel_db)[None, None, :, :]
            with torch.inference_mode():
                probs = torch.softmax(model(x.to(next(model.parameters()).device)), dim=1).cpu().numpy()[0]
            prob_fire = float(probs[1])
            is_pos = prob_fire >= args.threshold
            buf_windows.append(is_pos)

            if args.verbose:
                print(f"prob_fire={prob_fire:.3f} positives_in_buffer={sum(buf_windows)}/{len(buf_windows)}")

            if is_pos:
                last_positive_time = now

            # debug snippet
            if args.save_snippets and prob_fire >= args.snippet_threshold and (now - last_snip_save) >= args.snippet_cooldown:
                out = f"snippet_{int(now)}.wav"
                # take last window of audio from recent_audio
                arr = np.array(list(recent_audio)[-sr * int(max(1, args.window)) :])
                ok = save_wav(out, arr, sr)
                if ok:
                    print('Saved debug snippet to', out)
                last_snip_save = now

            # debounce
            if sum(buf_windows) >= args.debounce:
                if not detection_state:
                    detection_state = True
                    detection_start = now
                if args.min_duration <= 0 or (now - detection_start) >= args.min_duration:
                    if (now - last_alert) >= args.cooldown:
                        print(f"Fire Alarm Detected! conf={prob_fire:.2f}")
                        last_alert = now
                        detection_state = False
                        detection_start = None
                        buf_windows.clear()
            else:
                if detection_state and (now - last_positive_time) > args.grace_period:
                    detection_state = False
                    detection_start = None

    print('Listening (press Enter to stop)')
    try:
        with sd.InputStream(callback=callback, channels=1, samplerate=16000, dtype='float32'):
            try:
                input()
            except KeyboardInterrupt:
                pass
    except Exception as e:
        print('Failed to open InputStream:', e)


def main():
    args = parse_args()
    # device mapping for torch
    device = torch.device(args.device)
    try:
        model = load_model(args.model, device)
    except Exception as e:
        print('Failed to load model:', e)
        sys.exit(1)

    if args.dry_run:
        # quick forward test
        t = np.linspace(0, args.window, int(args.window * 16000), False)
        tone = 0.1 * np.sin(2 * np.pi * 1000 * t).astype(np.float32)
        mel = librosa.feature.melspectrogram(y=tone, sr=16000, n_mels=64)
        mel_db = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
        mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-8)
        x = torch.from_numpy(mel_db)[None, None, :, :].to(device)
        with torch.inference_mode():
            out = model(x)
            probs = torch.softmax(out, dim=1).cpu().numpy()[0]
        print('Dry-run probs:', probs)
        return

    if args.test:
        run_test_wav(model, args.test, args)
    else:
        run_realtime(model, args)


if __name__ == '__main__':
    main()
