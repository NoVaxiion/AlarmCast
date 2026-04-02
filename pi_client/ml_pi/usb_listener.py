from ml_pi.base_listener import BaseAlarmListener
import sounddevice as sd
import time


class FireAlarmListener(BaseAlarmListener):
    SAMPLE_RATE = 48000  # Supported by USB mic, clean 3:1 ratio to YAMNet's 16kHz (It gets sliced into 15600Hz in base_listener)
    DOWNSAMPLE  = 3      # 48000 → 16000
    BLOCK_SIZE  = 96000  # 2s hardware buffer - matches HOP_SIZE

    def start_listening(self):
        print("Listening...")
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=self.SAMPLE_RATE,
            dtype='float32',
            blocksize=self.BLOCK_SIZE,
            device=2
        )
        self.stream.start()


if __name__ == "__main__":
    from util import Client
    import socket
    listener = FireAlarmListener(Client(client_id=socket.gethostname()))
    try:
        listener.start_listening()
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        listener.stop_listening()
