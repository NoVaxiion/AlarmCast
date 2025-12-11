import json
import socket
import sounddevice as sd

class Client:

    # When creating a client, connect to the server
    def __init__(self, client_id):
        self.socket = socket.socket()
        self.socket.connect((get_host(), get_port()))
        self.client_id = client_id

        print(sd.query_devices())
        device_index = int(input("Input device index: "))
        sd.default.device = device_index
        
        self.socket.send(self.client_id.encode())
        self.listen_for_trigger()

    def listen_for_trigger(self):
        """
        Listens for audio trigger to start audio sending.
        """
        while True:
            if input().lower() == '':
                self.send_audio()
    
    def send_audio(self):
        """
        Records and sends audio data to the server in chunks.

        Returns:
            None
        """
        index = 0
        while index < 6:
            client_message = self.record_for_sending(10, 16000, 1)
            client_package = self.package(client_message, index)
            self.socket.send(client_package)
            index += 1

    def record_for_sending(self, duration, samplerate, channels):
        """
        Records audio from the microphone for a specified duration.
        
        Args:
            duration (float): Duration in seconds to record.
            samplerate (int): Sampling rate for the recording (Hz).
            channels (int): Number of audio channels.
            
        Returns:
            numpy.ndarray: Recorded audio data.
        """
        # Calculate the total number of frames to record
        frames = int(samplerate * duration)

        # Record the audio in a blocking manner
        audio_data = sd.rec(frames, samplerate=samplerate, channels=channels, dtype='float32')

        sd.wait()  # Wait until recording is finished
        return audio_data

    def package(self, audio_data, index):
        """
        Packages the audio data with an index for sending.
        
        Args:
            audio_data (numpy.ndarray): The audio data to package.
            index (int): The index of the audio chunk.
        """
        package_dict = {
            'index': index,
            'audio_data': audio_data.tolist()
        }
        package_json = json.dumps(package_dict) + "\n"
        return package_json.encode()

def get_host():
    # Stub function to return localhost for testing purposes
    return "127.0.0.1"
def get_port():
    # Stub function to return a test port number
    return 65432
