import socket


class TCPServer:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.bind(8080)

    def bind(self, port):
        self.sock.bind((socket.gethostname(), port))

    def listen(self):
        while True:
            self.sock.listen(5)
            client, address = self.sock.accept()
            print(f"Connection from {address}")
            client.send("Hello from Discord Bot")
            client.close()
        self.sock.close()
