import json
import socket
import sounddevice as sd

class Client:

    # When creating a client, connect to the server
    def __init__(self, client_id):
        self.socket = socket.socket()
        try:
            self.socket.connect((get_host(), get_port()))
        except Exception as e: 
            raise Exception(e)
        self.client_id = client_id
        
        self.socket.send(self.client_id.encode())
    
    def configure(self):
        answer = input("Reconfigure audio? (y/n): ")
        while answer.lower() != "y" and answer.lower() != "n":
            answer = input("Invalid input, try again: (y/n): ")
        
        if answer == "y":
            self.configure_audio()
        else:
            print("New configuration not needed")

    def configure_audio(self):
        print(sd.query_devices())
        print()
        device_index = int(input("Input device index (> highlighted input device recommended): "))
        sd.default.device = device_index

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

    def record_for_recognition(self, duration, samplerate, channels):
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

    def package(self, data):
        """
        Creates package for sending.
        
        Args:
            data (dict): data to be sent.
        """
        package_dict = {
            'client_id': self.client_id,
            'data': data
        }
        package_json = json.dumps(package_dict, default=str) + "\n"
        return package_json.encode()

    def send_package(self, package):
        """
        Sends package to server.
        
        Args:
            package (bstream): byte stream package
        """
        self.socket.send(package)
    
    def get_configuration(self):
        return {"socket": self.socket, "client_id": self.client_id}

def get_host():
    # Stub function to return localhost for testing purposes
    return "127.0.0.1"
def get_port():
    # Stub function to return a test port number
    return 65432
