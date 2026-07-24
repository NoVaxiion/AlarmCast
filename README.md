# 🚨 AlarmCast — Smart Alarm Detection and Remote Alerts

**AlarmCast** is a senior design project that extends the reach of traditional
fire and carbon-monoxide alarms. A Raspberry Pi listens for alarm sounds,
classifies them locally with a YAMNet-based audio pipeline, and reports detected
events to a backend service. The service records the event and can notify users
through a companion mobile application, push notifications, and configured
contacts.

The project explores how edge machine learning, inexpensive hardware, and mobile
software can make existing alarms more accessible when a resident is away from
home or unable to hear them.

> **Important:** AlarmCast is an educational prototype. It is not a certified
> life-safety device and must not replace approved smoke or carbon-monoxide
> alarms, emergency services, or established safety procedures.

## 💡 Project Overview

AlarmCast connects three main systems:

1. **Raspberry Pi listener** — captures microphone audio and performs local
   fire-alarm and carbon-monoxide-alarm classification.
2. **Flask API** — receives device events, stores users, hubs, devices, members,
   and alert history in SQLite, and coordinates notifications.
3. **Expo mobile app** — provides registration, monitoring controls, alert
   history, notification details, and device settings.

```text
Alarm sound
    ↓
Raspberry Pi + microphone
    ↓  Local YAMNet inference
Flask API + SQLite
    ↓
Expo push notification / configured contact alert
    ↓
AlarmCast mobile app
```

## 🎯 Purpose and Outcomes

The project was built to:

- detect recognizable fire and carbon-monoxide alarm patterns at the edge;
- reduce unnecessary network traffic by processing audio locally;
- notify users when an alarm is detected while they are away;
- maintain a history of devices, alerts, and monitoring activity;
- support multiple household members and emergency contacts through hubs; and
- explore a complete IoT workflow spanning hardware, machine learning, backend
  development, databases, and mobile interfaces.

## 🔊 Audio Detection

The listener uses a TensorFlow Lite YAMNet model to score alarm-related audio
classes. The current implementation combines YAMNet scores with rule-based
classification for:

- fire alarms and smoke detectors;
- carbon-monoxide beeps and buzzers; and
- a narrow-frequency fallback for a locally tested CO-alarm tone.

Audio is processed through a four-second ring buffer. Inference runs on a
background worker every two seconds so the microphone callback remains
responsive. Multiple detections are required before an alert is triggered,
helping reduce isolated false positives.

The repository includes listeners for:

- a Raspberry Pi with a USB microphone;
- a camera microphone operating at 16 kHz; and
- macOS development and testing.

See [`pi_client/ml_pi/LISTENER_DOCS.md`](pi_client/ml_pi/LISTENER_DOCS.md) for
the detailed pipeline, thresholds, and hardware-specific behavior.

## 🧩 Tech Stack

| Layer | Technologies |
| --- | --- |
| Edge device | Raspberry Pi, Python, NumPy, SoundDevice |
| Audio ML | YAMNet, TensorFlow Lite / LiteRT |
| Backend | Python, Flask, Flask-CORS |
| Database | SQLite |
| Mobile app | React Native, Expo, Expo Router, TypeScript |
| Notifications | Expo Push API, email-to-SMS gateways |

## 📁 Project Structure

```text
alarmcast/
├── backend/
│   ├── api/                 Flask API, models, and server utilities
│   └── requirements.txt     Backend Python dependencies
├── firealarm/
│   ├── app/                 Expo Router screens
│   ├── components/          Reusable React Native components
│   ├── constants/           API and theme configuration
│   ├── services/            Notification services
│   └── src/db/              Mobile-side database helpers and schema
├── pi_client/
│   ├── ml_pi/               Audio listeners and bundled YAMNet model
│   ├── startup.py           Pi configuration and listener entry point
│   ├── util.py              Backend client implementation
│   └── requirements.txt     Edge-device Python dependencies
└── docs/                    Architecture and database documentation
```

Audio evaluation datasets, generated results, uploaded recordings, environment
files, and dependency folders are intentionally excluded from Git.

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/NoVaxiion/AlarmCast.git
cd AlarmCast
```

### 2. Start the Flask API

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd api
python main.py
```

The development API runs on `http://localhost:8000`. Confirm it is available at
`http://localhost:8000/health`.

Optional notification features require environment-specific credentials:

```bash
export ALERT_EMAIL_USER="your-email@example.com"
export ALERT_EMAIL_PASS="your-app-password"
export PUBLIC_BASE_URL="http://YOUR_SERVER_IP:8000"
```

Do not commit credentials or `.env` files.

### 3. Start the mobile application

```bash
cd firealarm
npm install
npx expo start
```

Update the API host in `firealarm/constants/api.ts` so a physical phone can
reach the backend computer over the same network. `localhost` refers to the phone
itself when the app is running on a physical device.

### 4. Start the audio listener

```bash
cd pi_client
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python startup.py
```

Before starting, update `pi_client/config.py` with the backend machine's local
IP address. Select the appropriate listener import in `pi_client/startup.py` for
the Raspberry Pi microphone, camera microphone, or macOS test environment.

## ⚠️ Current Limitations

- The backend and device client currently require local network configuration.
- Push notifications require a physical device, a valid Expo push token, and
  internet access.
- Email-to-SMS delivery depends on external carrier gateways and configured
  email credentials.
- Audio classification quality depends on microphone placement, background
  noise, alarm model, room acoustics, and detection thresholds.
- The bundled rules were developed with a limited collection of alarm samples
  and are not a substitute for broad validation or safety certification.
- The repository does not include private evaluation audio or production
  credentials.

## 📚 Documentation

- [Application architecture](docs/app-architecture.md)
- [Hardware architecture](docs/hardware-architecture.md)
- [Database schema](docs/database-schema.md)
- [Backend API](backend/api/README.md)
- [Audio listener internals](pi_client/ml_pi/LISTENER_DOCS.md)

## 👥 Contributors

- **Kenneth Maeda** — machine learning, Raspberry Pi audio detection, backend,
  integration, and evaluation
- **Jackson Annese** — project development and integration
- **Zhuangyi Yuan** — project development and integration
- **Basil Alrawabdeh** — project development and integration
- **Hailey Reed** — project development and integration

Developed as a University of Connecticut senior design project.

## 📖 Educational Use

AlarmCast is provided for educational, research, and portfolio purposes. Anyone
building on this work should independently validate the hardware and software,
protect user and household data, secure all network endpoints, and follow local
fire-safety and carbon-monoxide-alarm requirements.
