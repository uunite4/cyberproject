import asyncio

from networking.example.server_example import BASIC_SERVER_IP, BASIC_SERVER_PORT
from networking.wrappers.client_wrapper import QuicClient


class BasicClient:

    def __init__(self):
        self.client = QuicClient(
            cert_file="../../certificate/cert.pem",
            on_receive=self.on_receive
        )

    def on_receive(self, connection_id: int, data: bytes):
        print(f"{connection_id}: {data.decode()}")

    async def run(self):
        server_id = await self.client.connect(
            server_ip=BASIC_SERVER_IP,
            server_port=BASIC_SERVER_PORT,
        )
        print('connected to server')

        try:
            while True:
                self.client.send(server_id, b'hi server')
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            print("Client shutting down...")

        finally:
            await self.client.stop()
            print("Client shut down")


if __name__ == '__main__':
    c = BasicClient()
    asyncio.run(c.run())
