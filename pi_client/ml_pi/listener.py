from util import Client
import sounddevice as sd
import tensorflow as tf
import numpy as np
import client 
import time
from datetime import datetime

# Configuration
SAMPLE_RATE   = 16000
WINDOW_SIZE   = int(SAMPLE_RATE * 4)  # 4 second window
HOP_SIZE      = int(SAMPLE_RATE * 1)  # Slide 1 second at a time
MIN_RMS       = 0.001                 # Silence gate

# Alert Settings 
REQUIRED_HITS = 2    # Consecutive danger predictions before triggering alarm
RESET_TIME    = 3.0  # Seconds before alarm can trigger again

# Key YAMNet Class Indices From CSV
# Fire  → IDX_FIRE_ALARM (394) high (0.15+), IDX_SMOKE (393) high (0.40+)
# CO    → IDX_BEEP (475) + IDX_BUZZER (392) high, IDX_FIRE_ALARM low (<0.15)
IDX_FIRE_ALARM = 394  # "Fire alarm"      — Most exclusive fire indicator
IDX_SMOKE      = 393  # "Smoke detector"  — High for fire, moderate for CO
IDX_ALARM      = 382  # "Alarm"           — High for both
IDX_BEEP       = 475  # "Beep, bleep"     — Key CO indicator
IDX_BUZZER     = 392  # "Buzzer"          — Key CO indicator


def load_yamnet():
    try:
        interpreter = tf.lite.Interpreter(model_path="ml_pi/model/yamnet.tflite")
        interpreter.allocate_tensors()
        return interpreter
    
    except Exception as e:
        print(f"Failed to load YAMNet: {e}")
        exit(1)


def yamnet_predict(interpreter, audio_data):
    input_details  = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Yamnet Input shape is [1 x 15600]
    # As Live Audio Input is [1 x 16000]
    CHUNK_SIZE = 15600  # 0.975s at 16kHz

    # Run YAMNet on each 0.975s chunk of the 4-second window
    all_scores = []
    for start in range(0, len(audio_data) - CHUNK_SIZE + 1, CHUNK_SIZE):
        chunk = audio_data[start:start + CHUNK_SIZE].astype(np.float32) # Slice 15600 samples
        interpreter.set_tensor(input_details[0]['index'], chunk.reshape(15600)) # Load into YAMNet
        interpreter.invoke() # Run inference
        scores = interpreter.get_tensor(output_details[0]['index'])[0] # Pull 521 class scores
        all_scores.append(scores) # Collect for averaging

    # Each chunk through the loop produces a (521,) array of different scores
    mean_scores = np.mean(all_scores, axis=0)  

    # Extract the 5 relevant class scores from the averaged 521-class output
    score_fire  = float(mean_scores[IDX_FIRE_ALARM])
    score_smoke = float(mean_scores[IDX_SMOKE])
    score_alarm = float(mean_scores[IDX_ALARM])
    score_beep  = float(mean_scores[IDX_BEEP])
    score_buzz  = float(mean_scores[IDX_BUZZER])

    # Rule 1 — Fire Alarm: Fire class dominant, or smoke very high with some fire signal
    if score_fire > 0.15 or (score_smoke > 0.40 and score_fire > 0.08):
        predicted = 'fire_alarm'
        conf = min(score_fire + score_smoke * 0.3 + score_alarm * 0.2, 1.0)

    # Rule 2 — CO: Beep/Buzzer dominant, fire and smoke alarm both low
    elif (score_beep > 0.15 or score_buzz > 0.15) and score_fire < 0.15 and score_smoke < 0.25:
        predicted = 'carbon_alarm'
        conf = min((score_beep + score_buzz) * 1.2, 1.0)

    # Rule 3 — Ambiguous: something alarm-like but unclear, tiebreak on raw scores
    elif score_alarm > 0.20 or score_smoke > 0.20:
        if score_fire >= score_beep + score_buzz:
            predicted = 'fire_alarm'
            conf      = min(score_fire + score_smoke * 0.2, 1.0)
        else:
            predicted = 'carbon_alarm'
            conf      = min(score_beep + score_buzz + score_alarm * 0.2, 1.0)
    
    # Rule 4 — Nothing crossed any threshold
    else:
        predicted = 'Random'
        conf      = max(0.0, 1.0 - max(score_fire, score_beep, score_alarm))

    # Package scores for logging as fire and CO are the primary signals, rest are supporting
    breakdown = {
        'fire':   round(score_fire,  3),
        'co':     round(max(score_beep, score_buzz), 3),
        'smoke':  round(score_smoke, 3),
        'alarm':  round(score_alarm, 3),
        'beep':   round(score_beep,  3),
        'buzzer': round(score_buzz,  3),
    }

    return predicted, conf, breakdown


class FireAlarmListener:
    def __init__(self, client):
        self.interpreter  = load_yamnet()
        self.hits         = 0
        self.last_alert   = 0.0
        self.buffer       = []
        self.stream       = None
        self.client       = client

    def audio_callback(self, indata, frames, time_info, status):
        # Sounddevice Error Handler. Catches mic buffer overruns or hardware issues
        if status:
            print(f"Stream status: {status}")
            return

        # 1. Capture Audio (Known as Buffer)
        self.buffer.extend(indata[:, 0].astype(np.float32))

        if len(self.buffer) < WINDOW_SIZE:
            return

        # 2. Extract 4 Second Segment and Advance Buffer by 1 Second
        seg = np.array(self.buffer[:WINDOW_SIZE], dtype=np.float32)
        del self.buffer[:HOP_SIZE]

        # 3. Silence gate. (Skips silences and resets beep hits)
        if np.sqrt(np.mean(seg**2)) < MIN_RMS:
            self.hits = 0
            return

        # 4. Predict
        try:
            predicted_class, conf, breakdown = yamnet_predict(self.interpreter, seg)
        except Exception as e:
            print(f"Prediction error: {e}")
            return

        # 5. Log prediction
        is_danger = predicted_class in ['fire_alarm', 'carbon_alarm']

        if is_danger:
            print(f"\n\n\n{predicted_class.upper()} ({conf:.2f})")
            print(f"   🔥 Fire: {breakdown['fire']:.3f}  💨 CO: {breakdown['co']:.3f}")
            print(f"   Smoke={breakdown['smoke']}  Alarm={breakdown['alarm']}  Beep={breakdown['beep']}  Buzzer={breakdown['buzzer']}")

        # 6. Hit counter. Requires consecutive danger predictions
        if is_danger and conf > 0.60:
            self.hits += 1
            print(f"   ⚠️  Danger hit {self.hits}/{REQUIRED_HITS}")

        elif is_danger and conf > 0.35:
            self.hits += 1
            print(f"   ⚠️  Low confidence danger hit {self.hits}/{REQUIRED_HITS}")

        else:
            self.hits = 0

        # 7. Trigger alarm if enough consecutive hits and cooldown passed
        now = time.monotonic()
        if self.hits >= REQUIRED_HITS and (now - self.last_alert) >= RESET_TIME:
            self.trigger_alarm(predicted_class, conf)
            self.last_alert = now
            self.hits       = 0

    def trigger_alarm(self, alarm_type, confidence):
        if alarm_type == "fire_alarm":
            label = "SMOKE"
        else:
            label = "CO"
        
        ##print(f"   🚨 {label.upper()} DETECTED! (Conf: {confidence:.2f})")
        alarm_datetime = datetime.now()
        self.client.send_alarm_notification(label, confidence, alarm_datetime) 


    def start_listening(self):
        print("Listening...")
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=SAMPLE_RATE,
            dtype='float32'
        )
        self.stream.start()
    
    def stop_listening(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        print("\nListener stopped.")


if __name__ == "__main__":
    listener = FireAlarmListener()
    try:
        listener.start_listening()
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        listener.stop_listening()