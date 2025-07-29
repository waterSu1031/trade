from ib_insync import IB


class ConnectIBKR:

    def __init__(self, host, port, client_id=10):
        self.host = host
        self.port = port
        self.client_id = client_id
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

    def reconnect(self, host, port) -> None:
        self.ib.disconnect()
        self.ib.sleep(1)
        self.ib.connect(host, port, clientId=self.client_id)
