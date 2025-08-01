from ib_insync import IB
from app.config import settings


class ConnectIBKR:

    def __init__(self, host=None, port=None, client_id=None):
        self.host = host or settings.ib_host
        self.port = port or settings.ib_port
        self.client_id = client_id or settings.ib_client_id
        self.ib = IB()

    def connect(self):
        self.ib.connect(self.host, self.port, clientId=self.client_id)

    def get_client(self):
        self.connect()
        return self.ib

    def run(self):
        self.ib.run()

    def is_connected(self) -> bool:
        return self.ib.isConnected()

    def reconnect(self, host=None, port=None) -> None:
        self.ib.disconnect()
        self.ib.sleep(1)
        if host:
            self.host = host
        if port:
            self.port = port
        self.ib.connect(self.host, self.port, clientId=self.client_id)