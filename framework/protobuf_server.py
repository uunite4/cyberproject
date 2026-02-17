import asyncio

from wrappers.server_wrapper import QuicServer

EXAMPLE_SERVER_IP = "127.0.0.1"
EXAMPLE_SERVER_PORT = 8000


class ServerExample:

    def __init__(self):
        self.server = QuicServer(
            ip=EXAMPLE_SERVER_IP,
            port=EXAMPLE_SERVER_PORT,
            cert_file="../certificate/cert.pem",
            key_file="../certificate/key.pem",
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

        while True:
            await self.server.broadcast(b"hi to everyone")
            await asyncio.sleep(1)


if __name__ == '__main__':
    s = ServerExample()
    asyncio.run(s.run())
