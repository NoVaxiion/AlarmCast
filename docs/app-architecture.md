This file details the app architecture


penpot UI design of the app: 
https://design.penpot.app/#/workspace?page-id=5b786374-066f-8104-8006-fde875ddb700&file-id=5b786374-066f-8104-8006-fde875ddb6ff&team-id=10e879d4-e5a6-801a-8006-fde5da74b66e&layout=layers

# FireWatch App Architecture

## 1. Overview
The FireWatch system is a mobile-based smart alert platform that connects a **Raspberry Pi** fire/sound detection device to an **Expo React Native mobile app**.  
When the Raspberry Pi detects fire or abnormal sound events, it sends a signal to the backend server, which then notifies users through push notifications.

## 2. High-Level Structure

- **Raspberry Pi**: Collects sensor or microphone input and triggers alerts.
- **Backend Server**: Receives alerts, stores them, and distributes notifications to users.
- **Mobile App**: Allows users to register, log in, receive notifications, and view history.

## 3. Components
### 3.1 Frontend (Mobile App)
- Built with **Expo (React Native)** for cross-platform compatibility (iOS + Android).
- Core pages include:
  - **Login / Register**
  - **Dashboard (alerts overview)**
  - **History (past alerts)**
  - **Settings (user & system preferences)**

### 3.2 Backend
- Written in **Python (Flask or FastAPI)**.
- Provides RESTful APIs for:
  - Authentication
  - Device registration
  - Event reporting
  - Notification management

### 3.3 Communication
- The Raspberry Pi communicates via HTTP or MQTT to send alert data.
- Notifications are sent using Expo Push API or Twilio SMS (if configured).

## 4. Data Flow
1. Fire or sound event is detected by Raspberry Pi.  
2. Event is sent to backend via API or MQTT.  
3. Backend saves data and triggers push notification.  
4. Mobile app receives alert and displays it on the dashboard.