import asyncio

from chat.chat_server import CHAT_SERVER_PORT, CHAT_SERVER_IP
from protobufs.compiled_protobufs.chat_pb2 import *
from wrappers.client_wrapper import QuicClient


class ChatClient:

    def __init__(self):
        self.server_id = None
        self.client = None
        self.running = True
        self.username = input("enter username")

        self.client = QuicClient(
            cert_file="../certificate/cert.pem",
            on_receive=self.on_receive
        )

    def on_receive(self, connection_id: int, data: bytes):
        response = ChatMessage()
        response.ParseFromString(data)
        print(f"{response.username}: {response.message}")

    def send(self, message: str):
        response = ChatMessage(
            message=message,
            username=self.username
        ).SerializeToString()

        self.client.send(self.server_id, response)

    async def run(self):
        self.server_id = await self.client.connect(
            server_ip=CHAT_SERVER_IP,
            server_port=CHAT_SERVER_PORT,
        )
        print("Connected to Server")

        try:
            while self.running:
                message = await asyncio.to_thread(input)
                self.send(message)

        except asyncio.CancelledError:
            print("Client shutting down...")

        finally:
            await self.client.stop()
            print("Client shut down")


if __name__ == '__main__':
    c = ChatClient()
    asyncio.run(c.run())
