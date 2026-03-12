import json
import socket
import sounddevice as sd
import requests


class Client:
    def __init__(self, client_id, api_base="http://10.194.53.115:8000", device_id=1, hub_id=1, timeout=10):
        self.socket = None
        self.socket_connected = False

        try:
            self.socket = socket.socket()
            self.socket.connect((get_host(), get_port()))
            self.socket.send(client_id.encode())
            self.socket_connected = True
        except Exception:
            self.socket = None
            self.socket_connected = False

        self.client_id = client_id
        self.api_base = api_base.rstrip("/")
        self.device_id = device_id
        self.hub_id = hub_id
        self.timeout = timeout

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
        while True:
            if input().lower() == '':
                self.send_audio()

    def send_audio(self):
        if not self.socket_connected or self.socket is None:
            print("Socket server not connected; skipping audio socket send.")
            return

        index = 0
        while index < 6:
            client_message = self.record_for_recognition(10, 16000, 1)
            client_package = self.package(client_message)
            self.socket.send(client_package)
            index += 1

    def record_for_recognition(self, duration, samplerate, channels):
        frames = int(samplerate * duration)
        audio_data = sd.rec(frames, samplerate=samplerate, channels=channels, dtype='float32')
        sd.wait()
        return audio_data

    def package(self, data):
        package_dict = {
            "client_id": self.client_id,
            "data": data
        }
        package_json = json.dumps(package_dict, default=str) + "\n"
        return package_json.encode()

    def send_package(self, package):
        if not self.socket_connected or self.socket is None:
            print("Socket server not connected; package not sent.")
            return
        self.socket.send(package)

    def normalize_alarm_type(self, alarm_type):
        value = (alarm_type or "").strip().lower()
        if value == "Fire Alarm":
            return "Fire Alarm"
        if value == "Carbon Monoxide":
            return "Fire Alarm"
        if value == "fire":
            return "FIRE"
        if value == "carbon":
            return "CARBON"
        if value == "smoke":
            return "SMOKE"
        if value == "co":
            return "CO"
        if value == "test":
            return "TEST"
        return value.upper()

    def send_alarm_notification(self, alarm_type, confidence, alarm_datetime):
        normalized_alarm_type = self.normalize_alarm_type(alarm_type)

        event_url = f"{self.api_base}/api/devices/{self.device_id}/events"
        event_payload = {
            "event_type": normalized_alarm_type
        }

        event_response = requests.post(event_url, json=event_payload, timeout=self.timeout)

        if not event_response.ok:
            return {
                "http": f"POST {event_url}",
                "confidence": confidence,
                "status_code": event_response.status_code,
                "ok": False,
                "response": event_response.text,
                "alarm_type": normalized_alarm_type,
                "alarm_datetime": str(alarm_datetime),
                "client_id": self.client_id
            }

        event_data = event_response.json()
        device_event_id = event_data.get("device_event_id")

        if not device_event_id:
            return {
                "http": f"POST {event_url}",
                "confidence": confidence,
                "status_code": event_response.status_code,
                "ok": False,
                "response": "device_event_id missing from response",
                "alarm_type": normalized_alarm_type,
                "alarm_datetime": str(alarm_datetime),
                "client_id": self.client_id
            }

        alert_url = f"{self.api_base}/api/alerts"
        alert_payload = {
            "hub_id": self.hub_id,
            "device_event_id": device_event_id
        }

        alert_response = requests.post(alert_url, json=alert_payload, timeout=self.timeout)

        response_data = (
            alert_response.json()
            if "application/json" in alert_response.headers.get("Content-Type", "")
            else alert_response.text
        )

        return {
            "http": [f"POST {event_url}", f"POST {alert_url}"],
            "confidence": confidence,
            "status_code": [event_response.status_code, alert_response.status_code],
            "ok": alert_response.ok,
            "response": response_data,
            "alarm_type": normalized_alarm_type,
            "alarm_datetime": str(alarm_datetime),
            "client_id": self.client_id
        }

    def get_configuration(self):
        return {
            "socket_connected": self.socket_connected,
            "client_id": self.client_id,
            "api_base": self.api_base,
            "device_id": self.device_id,
            "hub_id": self.hub_id
        }


def get_host():
    return "127.0.0.1"


def get_port():
    return 65432