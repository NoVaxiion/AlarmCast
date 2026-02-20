import json
import numpy as np
import os
import socket
from datetime import datetime
from pathlib import Path
from threading import Thread

BASE_DIR = Path(__file__).resolve().parent
recordings_dir = BASE_DIR / "audio-temp-storage"
recordings_dir.mkdir(exist_ok=True)

RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RESET = '\033[0m'

def get_host():
    # Bind to all interfaces to accept connections from network
    # Use "127.0.0.1" for localhost-only, "0.0.0.0" for all interfaces
    return os.getenv("SOCKET_HOST", "0.0.0.0")

def get_port():
    # Stub function to return a test port number
    return 65432

class Server:
    Clients = []

    # Create a TCP socket over IPv4, Accept at max 5 connections
    def __init__(self):
        HOST = get_host()
        PORT = get_port()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen(5)
        print('Server waiting for socket connection...')
    
    def listen(self):
        while True:
            client_socket, address = self.socket.accept()
            print(f"{GREEN}Connection from: {address}{RESET}")

            # The first message will be the client id
            client_id = client_socket.recv(1024).decode()
            client = {'client_id': client_id, 'socket': client_socket, 'index': 0}

            print(f"Client ID: {YELLOW}{client_id}{RESET}")

            Server.Clients.append(client)
            Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        client_socket = client['socket']
        buffer = ''

        while True:
            try:
                message = client_socket.recv(1024)
                if message:
                    buffer += message.decode()

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        message = json.loads(line)

                        client_id = message['client_id']
                        data = message['data']
                        time = data['alarm_datetime']

                        format_pattern = "%Y-%m-%d %H:%M:%S.%f"
                        date_object = datetime.strptime(time, format_pattern)

                        print(f"Packet from client: {YELLOW}{client_id}{RESET} at {date_object}. \n    Data:\n{data}")
                        if(data['recognition_status']):
                            self.handle_trigger(client_id, data)
                else:
                    break
            except ConnectionResetError:
                break

        print(f"{RED}Connection closed for client {client['client_id']}{RESET}")
        client['socket'].close()
        Server.Clients.remove(client)

    def handle_trigger(self, client_id, data):
        # API
        pass


