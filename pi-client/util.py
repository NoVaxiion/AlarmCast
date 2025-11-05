import numpy as np
import socket
import sounddevice as sd

def get_host():
    # Stub function to return localhost for testing purposes
    return "127.0.0.1"
def get_port():
    # Stub function to return a test port number
    return 65432

class Client:

    # When creating a client, connect to the server
    def __init__(self, client_id):
        self.socket = socket.socket()
        self.socket.connect((get_host(), get_port()))
        self.client_id = client_id
        
        self.talk_to_server()

    def talk_to_server(self):
        self.socket.send(self.client_id.encode())
        self.send_audio()
    
    def send_audio(self):
        while True:
            client_message = self.record_for_sending(.25, 16000, 1)
            self.socket.send(client_message.encode())

    def record_for_sending(duration, samplerate, channels):
        """
        Records audio from the microphone for a specified duration.
        
        Args:
            duration (float): Duration in seconds to record.
            samplerate (int): Sampling rate for the recording (Hz).
            channels (int): Number of audio channels.
            
        Returns:
            numpy.ndarray: Recorded audio data.
        """
        print(f"Recording for {duration} seconds...")
        # Calculate the total number of frames to record
        frames = int(samplerate * duration)

        # Record the audio in a blocking manner
        audio_data = sd.rec(frames, samplerate=samplerate, channels=channels, dtype='float32')

        sd.wait()  # Wait until recording is finished
        print("Recording complete.")
        return audio_data
    
