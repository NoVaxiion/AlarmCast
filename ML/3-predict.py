from firealarm_net import FireAlarmCNN
import torch
import librosa
import numpy as np
import os
import warnings

#To mute Librosa warnings
warnings.filterwarnings("ignore")

FILE_PATH = "Noises/fire_alarm/fire_018.wav"
#FILE_PATH = "Noises/siren/siren_011.wav"
#FILE_PATH = "Noises/appliance/appliance_001.wav"

sample_rate= 16000
mel_bands = 64
window_size = sample_rate * 1 # Changed from 5s then to 2s to finally 1s
hop = int(sample_rate * 0.5)  # Changed from 1s to 0.5s 
confidence_threshold = 0.60   # Slightly lowering the threshold
required_hits = 2   
reset_time = 3.0              # Reset faster
min_rms = 0.01                # Sensitivity gate

# Load the Trained Model
model = FireAlarmCNN(num_classes=3)
try:
    state = torch.load('model/model.pt')
    model.load_state_dict(state)
    print("Model loaded successfully.")

except Exception as e:
    print(f"Error loading model: {e}")
    exit()

model.eval()
classes = ['appliance', 'fire_alarm', 'siren']

# sounddevice library requires four of these parameters to function, two which are placeholders
def predict(file_path):
    if not file_path or not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    else:
        print(f"Processing: {file_path}\n")
    
    y, sr = librosa.load(file_path, sr=sample_rate)

    # Initialize State Variables inside the function
    hits = 0
    last_alert = 0 

    for i in range(0, len(y) - window_size, hop):
        
        # Extract Segment
        seg = y[i : i + window_size]
        
        # Silence Gate
        rms = float(np.sqrt(np.mean(seg**2) + 1e-12))
        if rms < min_rms:
            continue

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
        
        # Calculate timestamp of where we are in the file
        current_time = i / sample_rate
        
        # Print Output
        print(f"Time: {current_time:.1f}s | Heard: {predicted_class} ({conf:.2f})")

        if predicted_class == 'fire_alarm' and conf >= confidence_threshold:
            hits += 1
        else:
            hits = 0

        if hits >= required_hits and (current_time - last_alert) >= reset_time:
            print(f'\n Fire Alarm Detected! Conf: {conf:.2f}\n')
            last_alert = current_time
            hits = 0

    

if __name__ == "__main__":
    predict(FILE_PATH)