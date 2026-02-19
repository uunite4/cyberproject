import asyncio

from example.server_example import EXAMPLE_SERVER_IP, EXAMPLE_SERVER_PORT
from wrappers.client_wrapper import QuicClient


class ClientExample:

    def __init__(self):
        self.client = QuicClient(
            cert_file="../certificate/cert.pem",
            on_receive=self.on_receive
        )

    def on_receive(self, connection_id: int, data: bytes):
        print(f"{connection_id}: {data.decode()}")

    async def run(self):
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
