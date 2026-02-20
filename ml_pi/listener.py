from firealarm_net import FireAlarmCRNN
import sounddevice as sd
import numpy as np
import librosa
import joblib
import torch
import time

class FireAlarmListener:
    def __init__(self, model_path='model/model.pt', rf_path='model/rf_model.pkl'):
        """ Loading both CNN and RF Models with Configurations"""

        self.sample_rate = 16000
        self.mel_bands = 32
        self.window_size = int(self.sample_rate * 5) # 5 seconds
        self.hop = int(self.sample_rate * 1)         # Slide 1 sec at a time
        
        # Alert Settings
        self.required_hits = 2   
        self.reset_time = 3.0
        self.min_rms = 0.001  # Minimum volume to even bother processing
        
        # State
        self.buffer = []
        self.hits = 0
        self.last_alert = 0.0
        self.running = False
        self.stream = None

        # CLASS NAMES (Alphabetical to match LabelEncoder) 
        self.classes = ['appliance', 'carbon', 'fire', 'siren']

        # LOAD MODEL 1: CNN (Visual)
        self.cnn_model = FireAlarmCRNN(num_classes=4)
        try:
            checkpoint = torch.load(model_path, map_location="cpu")
            if "state_dict" in checkpoint:
                self.cnn_model.load_state_dict(checkpoint["state_dict"])
            else:
                self.cnn_model.load_state_dict(checkpoint)
            self.cnn_model.eval()
            print("CNN Model loaded.")
        except Exception as e:
            print(f"Error loading CNN: {e}")
            exit()

        # LOAD BRAIN 2: Random Forest (Math)
        try:
            self.rf_model = joblib.load(rf_path)
            print("Random Forest loaded.")
        except Exception as e:
            print(f"Error loading RF: {e}")
            exit()

    def extract_rf_features(self, audio_data):
        """Extracts the exact same 1D stats vector we used in training."""
        sr = self.sample_rate
        try:
            mfcc = np.mean(librosa.feature.mfcc(y=audio_data, sr=sr, n_mfcc=40).T, axis=0)
            centroid = np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sr))
            rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio_data, sr=sr))
            bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=audio_data, sr=sr))
            contrast = np.mean(librosa.feature.spectral_contrast(y=audio_data, sr=sr).T, axis=0)
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio_data))
            rms = np.mean(librosa.feature.rms(y=audio_data))
            chroma = np.mean(librosa.feature.chroma_stft(y=audio_data, sr=sr).T, axis=0)
            
            return np.hstack([mfcc, centroid, rolloff, bandwidth, contrast, zcr, rms, chroma])
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return np.zeros(288)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Status: {status}")
            return

        # 1. Capture Audio
        self.buffer.extend(indata[:, 0].astype(np.float32))
        
        if len(self.buffer) < self.window_size:
            return

        # 2. Extract 5s Segment
        seg = np.array(self.buffer[:self.window_size], dtype=np.float32)
        del self.buffer[:self.hop] 

        # 3. Silence Gate (Save CPU)
        vol = np.sqrt(np.mean(seg**2))
        if vol < self.min_rms:
            self.hits = 0
            return

        # CNN PREDICTION
        mel = librosa.feature.melspectrogram(y=seg, sr=self.sample_rate, n_mels=self.mel_bands)
        mel_db = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
        mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-8)
        
        x = torch.from_numpy(mel_db)[None, None, :, :]
        with torch.inference_mode():
            cnn_probs = torch.softmax(self.cnn_model(x), dim=1).numpy()[0]

        # RF PREDICTION
        rf_feats = self.extract_rf_features(seg)
        rf_probs = self.rf_model.predict_proba([rf_feats])[0]

        # BOTH VOTES
        final_probs = (cnn_probs + rf_probs) / 2
        
        # Identify Winner
        pred_idx = np.argmax(final_probs)
        predicted_class = self.classes[pred_idx]
        conf = final_probs[pred_idx]

        # CO ALARM FREQUENCY BOOST 
        spectral_centroid = rf_feats[40] 
        if spectral_centroid > 2500 and predicted_class == 'carbon':
             conf += 0.15 
             print(f"High Frequency ({spectral_centroid:.0f}Hz) detected - Boosting CO confidence.")

        # --- SAFETY & LOGIC ---
        print(f"\n📢 Prediction: {predicted_class.upper()} ({conf:.2f})")
        print(f"   [CNN Vote]: {dict(zip(self.classes, np.round(cnn_probs, 2)))}")
        print(f"   [RF  Vote]: {dict(zip(self.classes, np.round(rf_probs, 2)))}")

        is_danger = predicted_class in ['fire', 'carbon']
        
        if is_danger and conf > 0.80:
            self.hits += 1
        elif is_danger and conf > 0.40:
            print("⚠️ POTENTIAL DANGER - Low Confidence.")
            self.hits += 1 
        else:
            self.hits = 0

        # Trigger Event
        now = time.monotonic()
        if self.hits >= self.required_hits and (now - self.last_alert) >= self.reset_time:
            self.on_alarm_detected(conf, predicted_class) 
            self.last_alert = now
            self.hits = 0

    def on_alarm_detected(self, confidence, alarm_type="Alarm"):
        print(f'\n🚨 {alarm_type.replace("_", " ").upper()} DETECTED! (Conf: {confidence:.2f})\n')
        yield f'{alarm_type.replace("_", " ").upper()} DETECTED! (Conf: {confidence:.2f})'    

    def start_listening(self):
        if self.running: return
        print(f'🎧 Listening... (Ensembling Mode)')
        self.running = True
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=self.sample_rate,
            dtype='float32'
        )
        self.stream.start()
    
    def stop_listening(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.running = False
        print("Listener stopped.")

if __name__ == "__main__":
    listener = FireAlarmListener()
    try:
        listener.start_listening()
        while True: time.sleep(0.1)
    except KeyboardInterrupt:
        listener.stop_listening()