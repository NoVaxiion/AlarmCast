from util import Client
import librosa
import librosa.display
import matplotlib.pyplot as plt
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


def mel_spectrogram(audio: np.ndarray, sr = 16000, n_mels = 64, fmax = None, show = False) -> np.ndarray:
    
    if not isinstance(audio, np.ndarray):
        raise TypeError("Audio must be a numpy.ndarray containing audio samples")

    sig = audio

    if sig.ndim == 2:
        sig = sig.mean(axis=1)

    sig = sig.astype(np.float32).reshape(-1)

    if fmax is None:
        fmax = sr // 2

    mel = librosa.feature.melspectrogram(y=sig, sr=sr, n_mels=n_mels, fmax=fmax)
    S_dB = librosa.power_to_db(mel, ref=np.max)

    if show:
        plt.figure(figsize=(8, 4))
        librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel', fmax=fmax)
        plt.colorbar(format='%+2.0f dB')
        plt.title('Mel spectrogram')
        plt.tight_layout()
        plt.show()

    return S_dB
                  
if __name__ == "__main__":
    test_record_for_sending()