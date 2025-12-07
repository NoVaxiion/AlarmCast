from firealarm_net import FireAlarmCNN
import sounddevice as sd
import torch
import librosa
import numpy as np
import time

sample_rate= 16000
mel_bands = 64
window_size = sample_rate * 1 # Changed from 5s then to 2s to finally 1s
hop = int(sample_rate * 0.5)  # Changed from 1s to 0.5s 
confidence_threshold = 0.60   # Slightly lower the threshold
required_hits = 2   
reset_time = 3.0              # Reset faster
min_rms = 0.01                # Sensitivity gate

# Load the Trained Model
model = FireAlarmCNN(num_classes=4)
try:
    state = torch.load('model/model.pt')
    model.load_state_dict(state)
    print("Model loaded successfully.")

except Exception as e:
    print(f"Error loading model: {e}")
    exit()

model.eval()
classes = ['appliance', 'carbon', 'siren', 'smoke']

# State
buffer = []
hits = 0
last_alert = 0.0

# sounddevice library requires four of these parameters to function, two which are placeholders
def audio_callback(indata, frames, time_info, status):
    global buffer, hits, last_alert
    
    if status:
        print(f"Status: {status}")
        return

    # Capture Audio
    buffer.extend(indata[:, 0].astype(np.float32))
    
    # Wait until we have enough data for a 1s window_sizedow
    if len(buffer) < window_size:
        return

    # Extract Segment
    seg = np.array(buffer[:window_size], dtype=np.float32)
    del buffer[:hop] # Remove the data (by sliding the window)

    # Silence Gate
    rms = float(np.sqrt(np.mean(seg**2) + 1e-12))
    if rms < min_rms:
        hits = 0
        return

    # Preprocess
    mel = librosa.feature.melspectrogram(y=seg, sr=sample_rate, n_mels=mel_bands)
    mel_db = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
    
    # Normalize 
    mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-8)

    # Inference
    x = torch.from_numpy(mel_db)[None, None, :, :]
    with torch.inference_mode():
        probs = torch.softmax(model(x), dim=1).numpy()[0]
    
    pred = int(np.argmax(probs))
    conf = float(probs[pred])
    predicted_class = classes[pred]

    # Logic & Debouncing
    print(f"Heard: {predicted_class} ({conf:.2f})") 

    if predicted_class in ('smoke', 'carbon') and conf >= confidence_threshold:
        hits += 1
    else:
        hits = 0

    now = time.monotonic()
    if hits >= required_hits and (now - last_alert) >= reset_time:
        print(f'\n {predicted_class.capitalize()} Detected! Conf: {conf:.2f}\n')
        last_alert = now
        hits = 0

print(f'Listening... (window: {window_size/sample_rate}s)')
with sd.InputStream(callback=audio_callback, channels=1, samplerate=sample_rate, dtype='float32'):
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nstopping...")