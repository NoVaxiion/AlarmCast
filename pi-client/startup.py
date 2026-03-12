from datetime import datetime
from util import Client
import ml_pi
import socket
import time


RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RESET = '\033[0m'
ALARMCAST = f"""
         {RED}_    _{RESET}                                    _       
  _     {RED}/ \\  | | __ _ _ __ _ __ ___{RESET}   ___ __ _ ___| |_   _ 
 (_)   {RED}/ _ \\ | |/ _` | '__| '_ ` _ \\{RESET} / __/ _` / __| __| (_)
  _   {RED}/ ___ \\| | (_| | |  | | | | | |{RESET} (_| (_| \\__ \\ |_   _ 
 (_) {RED}/_/   \\_\\_|\\__,_|_|  |_| |_| |_|{RESET}\\___\\__,_|___/\\__| (_)
                                                           """

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def get_configuration():
    print("Configuration: __ __ __ __")

def set_configuration():
    pass

def test_pi():
    pass

def startup():
    print(ALARMCAST)
    print("Welcome to the configuration interface")

    internetConnection = check_internet()
    if internetConnection:
        print(f"{GREEN}Connected to internet{RESET}")
    else:
        print(f"{YELLOW}No internet connection detected{RESET}")

    hostname = socket.gethostname()

    try:
        client = Client(client_id=hostname)
    except Exception as e:
        print(f"{RED}Unable to initialize client: {e}{RESET}")
        return

    config = client.get_configuration()
    print(f"{GREEN}Client ready:{RESET} {config}")

    answer = input("Is new configuration needed? (y/n): ")
    while answer.lower() != "y" and answer.lower() != "n":
        answer = input("Invalid input, try again: (y/n): ")

    if answer == "y":
        client.configure()
    else:
        print("New configuration not needed")

    demo(client)

def demo(client):
    answer = input("Demo for alarm alert, manual input or audio recognition? (m/a): ")
    while answer.lower() != "m" and answer.lower() != "a":
        answer = input("Invalid input, re-enter: (m/a): ")

    if answer == "m":
        while True:
            answer = input("Press enter to initiate (q to quit): ")

            if answer.lower() == "q":
                break

            current_time = datetime.now()

            result = client.send_alarm_notification(
                alarm_type="fire",
                confidence=0.99,
                alarm_datetime=current_time
            )

            print(f"{GREEN}Notification result:{RESET} {result}")

    else:
        listener = ml_pi.listener.FireAlarmListener()

        def alarm_hook(confidence, alarm_type="Alarm"):
            current_time = datetime.now()

            print(
                f"{YELLOW}Automatic detection trigger:{RESET} "
                f"type={alarm_type}, confidence={confidence:.2f}"
            )

            result = client.send_alarm_notification(
                alarm_type=alarm_type,
                confidence=round(float(confidence), 2),
                alarm_datetime=current_time
            )

            print(f"{GREEN}Notification result:{RESET} {result}")

        listener.on_alarm_detected = alarm_hook

        try:
            listener.start_listening()
            print(f"{GREEN}Automatic audio detection active. Press Ctrl+C to stop.{RESET}")

            while True:
                time.sleep(0.2)

        except KeyboardInterrupt:
            print(f"{YELLOW}Stopping listener...{RESET}")
            listener.stop_listening()

if __name__ == "__main__":
    startup()