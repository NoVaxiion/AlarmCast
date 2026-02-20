import sounddevice as sd
from scipy.io.wavfile import write

def configure_audio_device():
    """
    Configures the audio input device by listing available devices and
    prompting the user to select one.

    Returns:
        int: The index of the selected audio input device.
    """
    print(sd.query_devices())
    device_index = int(input("Input device index: "))
    sd.default.device = device_index
    return device_index

def record_audio(duration, samplerate, channels, filename):
    """
    Records audio from the microphone and saves it to a WAV file.

    Args:
        duration (float): Duration in seconds to record.
        samplerate (int): Sampling rate for the recording (Hz).
        channels (int): Number of audio channels.
        filename (str): The name of the file to save the recording.
    """
    # Calculate the total number of frames to record
    frames = int(samplerate * duration)

    # Record the audio in a blocking manner
    audio_data = sd.rec(frames, samplerate=samplerate, channels=channels, dtype='float32')

    sd.wait()  # Wait until recording is finished

    # Save the recorded audio to a WAV file
    write(filename, samplerate, audio_data)

if __name__ == "__main__":
    configure_audio_device()
    record_audio(duration=5, samplerate=16000, channels=1, filename="test_recording.wav")
