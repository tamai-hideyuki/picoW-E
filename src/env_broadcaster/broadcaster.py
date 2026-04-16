import socket
import json


class Broadcaster:
    def __init__(self, addr, port):
        self._addr = (addr, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def send(self, payload):
        data = json.dumps(payload).encode("utf-8")
        self._sock.sendto(data, self._addr)

    def close(self):
        self._sock.close()
