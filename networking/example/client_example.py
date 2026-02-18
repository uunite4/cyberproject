import asyncio

from networking.wrappers.client_wrapper import QuicClient
from server_example import EXAMPLE_SERVER_IP, EXAMPLE_SERVER_PORT


class ClientExample:

    def __init__(self):
        self.client = None

    def on_receive(self, connection_id: int, data: bytes):
        print(f"{connection_id}: {data.decode()}")

    async def run(self):
        self.client = QuicClient(
            cert_file="../certificate/cert.pem",
            on_receive=self.on_receive
        )

        server_id = await self.client.connect(
            server_ip=EXAMPLE_SERVER_IP,
            server_port=EXAMPLE_SERVER_PORT,
        )

        while True:
            self.client.send(server_id, b'hi server')
            await asyncio.sleep(1)


if __name__ == '__main__':
    c = ClientExample()
    asyncio.run(c.run())
