import asyncio

from wrappers.server_wrapper import QuicServer

BASIC_SERVER_IP = "127.0.0.1"
BASIC_SERVER_PORT = 8000


class BasicServer:

    def __init__(self):
        self.server = QuicServer(
            ip=BASIC_SERVER_IP,
            port=BASIC_SERVER_PORT,
            cert_file="../../certificate/cert.pem",
            key_file="../../certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )

    def on_receive(self, connection_id: int, data: bytes):
        print(f"{connection_id}: {data.decode()}")
        self.server.send(connection_id, b'echo!')

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    async def run(self):
        await self.server.start()
        print("Server started")

        try:
            while True:
                self.server.broadcast(b"broadcast")
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            print("Server shutting down...")

        finally:
            await self.server.stop()
            print("Server shut down")


if __name__ == '__main__':
    s = BasicServer()
    asyncio.run(s.run())
