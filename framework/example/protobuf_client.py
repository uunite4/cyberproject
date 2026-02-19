import asyncio

from framework.example.protobuf_server import PROTOBUF_SERVER_IP, PROTOBUF_SERVER_PORT
from framework.protobufs.compiled_protobufs.example_pb2 import *
from wrappers.client_wrapper import QuicClient


class ClientExample:

    def __init__(self):
        self.client = None

    def on_receive(self, connection_id: int, data: bytes):
        response = ServerResponse()
        response.ParseFromString(data)
        print(f"{connection_id}: {response}")

    def build_message(self) -> bytes:
        return ClientRequest(
            number=12,
            name="232"
        ).SerializeToString()

    async def run(self):
        self.client = QuicClient(
            cert_file="../../certificate/cert.pem",
            on_receive=self.on_receive
        )

        server_id = await self.client.connect(
            server_ip=PROTOBUF_SERVER_IP,
            server_port=PROTOBUF_SERVER_PORT,
        )

        while True:
            self.client.send(server_id, self.build_message())
            await asyncio.sleep(1)


if __name__ == '__main__':
    c = ClientExample()
    asyncio.run(c.run())
