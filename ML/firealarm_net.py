import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset


# CNN Model: improved with BatchNorm, Dropout and safer flattening
# A Convolutional Neural Network (CNN) that takes in a Mel Spectrogram
# (a 2D "image" of sound) and predicts which sound class it belongs to:

class FireAlarmCNN(nn.Module):
    def __init__(self, num_classes=4, dropout=0.3):
        super().__init__()

        # Convolutional blocks with BatchNorm for training stability
        self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)

        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(32)

        self.conv3 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)

        # Pooling and regularization
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(dropout)

        # Final classifier (global pooled to 64 features)
        self.fc = nn.Linear(64, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))

        # Adaptive pooling -> (batch, 64, 1, 1)
        x = F.adaptive_avg_pool2d(x, 1)
        # Flatten safely to (batch, 64)
        x = x.view(x.size(0), -1)
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


print("Apple")