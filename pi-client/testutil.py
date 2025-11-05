
import numpy as np

def test_record_for_sending():
    print("test")
    duration = 0.5  # seconds
    samplerate = 16000  # Hz
    channels = 1  # mono

    audio_data = Client.record_for_sending(duration, samplerate, channels)

    assert isinstance(audio_data, np.ndarray), "Recorded data should be a numpy array"
    assert audio_data.ndim == 2, "Recorded data should have 2 dimensions (frames, channels)"
    assert audio_data.shape[0] == int(samplerate * duration), "Number of frames should match the expected count"
    assert audio_data.shape[1] == channels, "Number of channels should match the expected count"
    print("test_record_for_sending passed.")

if __name__ == "__main__":
    test_record_for_sending()