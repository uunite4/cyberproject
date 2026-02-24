import asyncio

from protobufs.compiled_protobufs.chat_pb2 import *
from wrappers.server_wrapper import QuicServer

CHAT_SERVER_IP = "127.0.0.1"
CHAT_SERVER_PORT = 8000
SEND_FPS: int = 10

"""

not sure if it should use a buffer
or just broadcast each message to anyone but the sender once received

"""


class ChatServer:

    def __init__(self):
        self.server = QuicServer(
            ip=CHAT_SERVER_IP,
            port=CHAT_SERVER_PORT,
            cert_file="../certificate/cert.pem",
            key_file="../certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )
        self.message_buffer: list[ChatMessage] = list()

    def on_receive(self, connection_id: int, data: bytes):
        message = ChatMessage()
        message.ParseFromString(data)
        self.message_buffer.append(message)

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    def send_buffer(self):

        if not self.message_buffer:
            return

        message_list = ChatMessagesList()

        for m in self.message_buffer:
            message = message_list.messages.add()
            message.username = m.username
            message.message = m.message

        self.server.broadcast(message_list.SerializeToString())
        self.message_buffer.clear()

    async def run(self):
        await self.server.start()
        print("Server started")

        try:
            while True:
                self.send_buffer()
                await asyncio.sleep(1 / SEND_FPS)

        except asyncio.CancelledError:
            print("Server shutting down...")

        finally:
            await self.server.stop()
            print("Server shut down")


if __name__ == '__main__':
    s = ChatServer()
    asyncio.run(s.run())
