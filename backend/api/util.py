import json
import numpy as np
import os
import socket

from pathlib import Path
from scipy.io.wavfile import write
from threading import Thread

BASE_DIR = Path(__file__).resolve().parent
recordings_dir = BASE_DIR / "audio-temp-storage"
recordings_dir.mkdir(exist_ok=True)

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
            print("Connection from: " + str(address))

            # The first message will be the client id
            client_id = client_socket.recv(1024).decode()
            client = {'client_id': client_id, 'socket': client_socket, 'index': 0}

            print("Client ID: " + client_id)

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
                        index = message['index']
                        audio_data = np.array(message['audio_data'], dtype=np.float32)
                        write(f"{recordings_dir}/{client['client_id']}_file_{index}.wav", 16000, audio_data)
                else:
                    break
            except ConnectionResetError:
                break
        print(f"Connection closed for client {client['client_id']}")
        client['socket'].close()
        Server.Clients.remove(client)


