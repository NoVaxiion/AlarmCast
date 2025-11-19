import socket
from threading import Thread
import numpy as np
import os

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
            client = {'client_id': client_id, 'socket': client_socket}

            print("Client ID: " + client_id)

            Server.Clients.append(client)
            Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        client_socket = client['socket']
        while True:
            try:
                message = np.frombuffer(client_socket.recv(1024), dtype=np.float32)
                if message.any():
                    print(f"Message from {client['client_id']}: {message}") # For demonstration, just print the message
                else:
                    break
            except ConnectionResetError:
                break
        print(f"Connection closed for client {client['client_id']}")
        client['socket'].close()
        Server.Clients.remove(client)

if __name__ == "__main__":
    server = Server()
    server.listen()
