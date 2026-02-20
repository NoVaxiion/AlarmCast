from torch.utils.data import Dataset
import torch.nn.functional as F
import torch.nn as nn
import torch




"""
CRNN (Convolutional Recurrent Neural Network) Model: improved with BatchNorm, Dropout, and safer flattening.
This hybrid architecture takes in a Mel Spectrogram (a 2D "image" of sound).
- The CNN blocks act as the "eyes," extracting spatial features (specific frequencies/pitches).
- The LSTM block acts as the "memory," tracking temporal sequences (the rhythm/timing of the beeps).
It predicts which of the 4 sound classes the audio belongs to:
appliance, carbon, fire, or siren.
"""

class FireAlarmCRNN(nn.Module):
    def __init__(self, num_classes=4, dropout=0.3, mel_bands=32):
        super().__init__()

        # Convolutional blocks with BatchNorm for training stability
        self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)

        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(32)

        self.conv3 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)

        # Pooling
        self.pool = nn.MaxPool2d(2, 2)
        self.lstm_input_size = (mel_bands // 4) * 64
        
        # LSTM Layer (The Memory)
        # Flattened features after conv blocks: channels * freq -> 64 * 8 = 512
        # Use input_size=512 to match trained checkpoint
        self.lstm = nn.LSTM(input_size=self.lstm_input_size, hidden_size=128, batch_first=True)        
        self.dropout = nn.Dropout(dropout)

        # Final classifier (global pooled to 128 features)
        self.fc = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = F.relu(self.bn3(self.conv3(x)))

        # Prepare for LSTM: (batch, channels, freq, time) -> (batch, time, features)
        # We flatten the frequency and channel dimensions into one "feature" vector per time step
        batch, ch, freq, time = x.size()
        x = x.permute(0, 3, 1, 2).contiguous() 
        x = x.view(batch, time, -1)

        # Pass through LSTM
        x, (hn, cn) = self.lstm(x)
        
        # Take the last time step's output
        x = x[:, -1, :]
        x = self.dropout(x)
        return self.fc(x)
    
class MelDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)
    def __len__(self):
        return len(self.y)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]
