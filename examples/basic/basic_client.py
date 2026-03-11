import asyncio

from examples.basic.basic_server import BASIC_SERVER_IP, BASIC_SERVER_PORT
from wrappers.client_wrapper import QuicClient


class BasicClient:

    def __init__(self):
        self.server_id = None
        self.client = QuicClient(
            cert_file="../../certificate/certs/ca.crt",
            on_receive=self.on_receive
        )

    def on_receive(self, connection_id: int, data: bytes):
        print(f"{connection_id}: {data.decode()}")

    async def loop(self):
        while True:
            self.client.send(self.server_id, b'hi server')
            await asyncio.sleep(15)

    async def run(self):
        self.server_id = await self.client.connect(
            server_ip=BASIC_SERVER_IP,
            server_port=BASIC_SERVER_PORT,
        )
        print('connected to server')

        try:
            asyncio.create_task(self.loop())
            await asyncio.Future()

        except asyncio.CancelledError:
            print("Client shutting down...")

        finally:
            await self.client.stop()
            print("Client shut down")


if __name__ == '__main__':
    c = BasicClient()
    asyncio.run(c.run())
