import socket
from threading import Thread

def get_host():
    # Stub function to return localhost for testing purposes
    return "127.0.0.1"

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
            message = client_socket.recv(1024).decode()
            if message:
                print(f"Message from {client['client_id']}: {message}") # For demonstration, just print the message
            else:
                break
        except ConnectionResetError:
            break
    print(f"Connection closed for client {client['client_id']}")
    client['socket'].close()
    Server.Clients.remove(client)

if __name__ == "__main__":
    server = Server('127.0.0.1', 65432)
    server.listen()
