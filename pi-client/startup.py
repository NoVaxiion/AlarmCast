from datetime import datetime
from util import Client
import ml_pi
import socket


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
        # Attempt to connect to Google's public DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def get_configuration():
    print("Configuration: __ __ __ __")

# Ask if new configuration is needed


# If new configuration is needed prompt configuration
def set_configuration():
    pass

# Send test packets to server
def test_pi():
    pass

def startup():
    print(ALARMCAST)
    print("Welcome to the configuration interface")

    internetConnection = check_internet()
    if internetConnection:
        print(f"{GREEN}Connected to internet{RESET}")

    hostname = socket.gethostname()

    flag = False
    while not flag:
        try:
            client = Client(client_id=hostname)
            flag = True
        except Exception as e:
            answer = input(f"Unable to initialize: [{RED}{e}{RESET}] Try again? (y/n): ")
            while answer.lower() != "y" and answer.lower() != "n":
                answer = input("Invalid input, re-enter: (y/n): ")
    
            if answer == "n":
                return
    
    # print(f"{GREEN}Successfully established socket connection with server{RESET}"

    config = client.get_configuration()
    
    answer = input("Is new configuration needed? (y/n): ")
    while answer.lower() != "y" and answer.lower() != "n":
        answer = input("Invalid input, try again: (y/n): ")
    
    if answer == "y":
        client.configure()
    else:
        print("New configuration not needed")
    
    demo(client)

def demo(client):
    answer = input(f"Demo for alarm alert, manual input or audio recognition? (m/a): ")
    while answer.lower() != "m" and answer.lower() != "a":
        answer = input("Invalid input, re-enter: (y/n): ")

    if answer == "m":
        while True:
            answer = "None"
            while(answer != "" and answer.lower() != "q"):
                answer = input("Press enter to initiate (q to quit): ")

            if answer.lower() == "q":
                break
            
            current_time = datetime.now()
            recognition_status = True

            data = {"alarm_datetime": current_time, "recognition_status": recognition_status}
            client_package = client.package(data)
            client.send_package(client_package)
    else:
       l = ml_pi.listener.FireAlarmListener()
       while alert := next(l, None):
           current_time = datetime.now()
           recognition_status = True
    
           data = {"alarm_datetime": current_time, "recognition_status": recognition_status}
           client_package = client.package(data)
           client.send_package(client_package)

           # Call api, send notification that alarm sounded:
           # Should send alarm_datetime, alarm_type, confidence, client_id: username or email etc, status_code

if __name__ == "__main__":
    startup()