import asyncio

from examples.twoservers.settings_test import TEST1_SERVER_PORT, TEST1_SERVER_IP
from wrappers.server_wrapper import QuicServer


class ServerTest1:

    def __init__(self):
        self.server = QuicServer(
            ip=TEST1_SERVER_IP,
            port=TEST1_SERVER_PORT,
            cert_file="../../certificate/cert.pem",
            key_file="../../certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )

    def on_receive(self, connection_id: int, data: bytes):
        print(f"{connection_id}: {data.decode()}")

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    async def run(self):
        await self.server.start()
        print("Server started")

        try:
            while True:
                self.server.broadcast(b'S1')
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            print("Server shutting down...")

        finally:
            await self.server.stop()
            print("Server shut down")


if __name__ == '__main__':
    s = ServerTest1()
    asyncio.run(s.run())
