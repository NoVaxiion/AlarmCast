from firealarm_net import FireAlarmCNN
import sounddevice as sd
import torch
import librosa
import numpy as np
import time

class FireAlarmListener:
    def __init__(self, model_path='model/model.pt'):
        #Configuration
        self.sample_rate= 16000
        self.mel_bands = 64
        self.window_size = int(self.sample_rate * 1) # Changed from 5s then to 2s to finally 1s
        self.hop = int(self.sample_rate * 0.5)  # Changed from 5s to 1s then to 0.5s 
        self.confidence_threshold = 0.60   # Slightly lower the threshold
        self.required_hits = 2   
        self.reset_time = 3.0              # Reset faster
        self.min_rms = 0.01                # Sensitivity gate

        # State
        self.buffer = []
        self.hits = 0
        self.last_alert = 0.0
        self.running = False
        self.stream = None

        # Load the Trained Model
        self.classes = ['appliance', 'fire_alarm', 'siren']
        self.model = FireAlarmCNN(num_classes=3)

        try:
            state = torch.load(model_path)
            self.model.load_state_dict(state)
            print("Model loaded successfully.")

        except Exception as e:
            print(f"Error loading model: {e}")
            exit()


    # sounddevice library requires four of these parameters to function, two which are placeholders
    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Status: {status}")
            return

        # Capture Audio
        self.buffer.extend(indata[:, 0].astype(np.float32))
        
        # Wait until we have enough data for a 1s window_sizedow
        if len(self.buffer) < self.window_size:
            return

        # Extract Segment
        seg = np.array(self.buffer[:self.window_size], dtype=np.float32)
        del self.buffer[:self.hop] # Remove the data (by sliding the window)

        # Silence Gate
        rms = float(np.sqrt(np.mean(seg**2) + 1e-12))
        if rms < self.min_rms:
            self.hits = 0
            return

        # Preprocess
        mel = librosa.feature.melspectrogram(y=seg, sr=self.sample_rate, n_mels=self.mel_bands)
        mel_db = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
        
        # Normalize 
        mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-8)

        # Inference
        x = torch.from_numpy(mel_db)[None, None, :, :]
        with torch.inference_mode():
            probs = torch.softmax(self.model(x), dim=1).numpy()[0]
        
        pred = int(np.argmax(probs))
        conf = float(probs[pred])
        predicted_class = self.classes[pred]

        # Logic & Debouncing
        # print(f"Heard: {predicted_class} ({conf:.2f})") 

        if predicted_class == 'fire_alarm' and conf >= self.confidence_threshold:
            self.hits += 1
        else:
            self.hits = 0

        now = time.monotonic()
        if self.hits >= self.required_hits and (now - self.last_alert) >= self.reset_time:
            self.on_alarm_detected(conf)
            self.last_alert = now
            self.hits = 0

    def on_alarm_detected(self, confidence):
        #Override this method or pass a callback to handle the alarm.
        print(f'\n*** Fire Alarm Detected! Conf: {confidence:.2f} ***\n')
    
    def start_listening(self):
        #Starts the audio stream in the background.
        if self.running:
            return
            
        print(f'Listening... (window: {self.window_size/self.sample_rate}s)')
        self.running = True
        
        # sounddevice streams run in a separate thread by default
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=self.sample_rate,
            dtype='float32'
        )
        self.stream.start()
    
    def stop_listening(self):
        #Stops the audio stream.
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.running = False
        print("Listener stopped.")

if __name__ == "__main__":
    listener = FireAlarmListener()
    listener.start_listening()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        listener.stop_listening()