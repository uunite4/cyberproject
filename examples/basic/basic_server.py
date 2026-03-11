import asyncio

from wrappers.server_wrapper import QuicServer

BASIC_SERVER_IP = "127.0.0.1"
BASIC_SERVER_PORT = 8080


class BasicServer:

    def __init__(self):
        self.server = QuicServer(
            ip=BASIC_SERVER_IP,
            port=BASIC_SERVER_PORT,
            cert_file="../../certificate/certs/server.crt",
            key_file="../../certificate/certs/server.key",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )

    def on_receive(self, connection_id: int, data: bytes):
        print(f"{connection_id}: {data.decode()}")
        # self.server.send(connection_id, b'echo!')

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    async def loop(self):
        while True:
            self.server.broadcast(b"broadcast")
            await asyncio.sleep(15)

    async def run(self):
        await self.server.start()
        print("Server started")

        try:
            asyncio.create_task(self.loop())
            await asyncio.Future()

        except asyncio.CancelledError:
            print("Server shutting down...")

        finally:
            await self.server.stop()
            print("Server shut down")


if __name__ == '__main__':
    s = BasicServer()
    asyncio.run(s.run())
