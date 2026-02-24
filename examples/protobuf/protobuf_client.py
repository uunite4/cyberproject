import asyncio

from examples.protobuf.protobuf_server import PROTOBUF_SERVER_IP, PROTOBUF_SERVER_PORT
from protobufs import protobuf_compiler
from protobufs.compiled_protobufs.example_pb2 import *
from wrappers.client_wrapper import QuicClient


class ClientExample:

    def __init__(self):
        self.server_id = None
        self.client = None

    def on_receive(self, connection_id: int, data: bytes):
        server_response = ServerResponse()
        server_response.ParseFromString(data)
        print(f"{connection_id}: {server_response}")

    def send(self):
        response = ClientRequest(
            number=12,
            name="232"
        ).SerializeToString()

        self.client.send_buffer(self.server_id, response)

    async def run(self):
        self.client = QuicClient(
            cert_file="../../certificate/cert.pem",
            on_receive=self.on_receive
        )

        self.server_id = await self.client.connect(
            server_ip=PROTOBUF_SERVER_IP,
            server_port=PROTOBUF_SERVER_PORT,
        )

        try:
            while True:
                self.send()
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            print("Client shutting down...")

        finally:
            await self.client.stop()
            print("Client shut down")


if __name__ == '__main__':
    protobuf_compiler.recompile_all()
    c = ClientExample()
    asyncio.run(c.run())
