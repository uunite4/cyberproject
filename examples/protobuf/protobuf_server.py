import asyncio

from protobufs import protobuf_compiler
from protobufs.compiled_protobufs.example_pb2 import *
from wrappers.server_wrapper import QuicServer

PROTOBUF_SERVER_IP = "127.0.0.1"
PROTOBUF_SERVER_PORT = 8000


class ServerExample:

    def __init__(self):
        self.server = QuicServer(
            ip=PROTOBUF_SERVER_IP,
            port=PROTOBUF_SERVER_PORT,
            cert_file="../../certificate/cert.pem",
            key_file="../../certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )

    def on_receive(self, connection_id: int, data: bytes):
        request = ClientRequest()
        request.ParseFromString(data)
        print(f"{connection_id}: {request}")

        response = ServerResponse(isAlive=True)
        self.server.send(connection_id, response.SerializeToString())

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    async def run(self):
        await self.server.start()
        print("Server started")

        try:
            await asyncio.Future()  # run forever

        except asyncio.CancelledError:
            print("Server shutting down...")

        finally:
            await self.server.stop()
            print("Server shut down")


if __name__ == '__main__':
    protobuf_compiler.recompile_all()
    s = ServerExample()
    asyncio.run(s.run())
