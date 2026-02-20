from util import Client
import socket

hostname = socket.gethostname()
client = Client(client_id=hostname)



