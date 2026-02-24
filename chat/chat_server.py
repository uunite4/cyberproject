import asyncio

from protobufs.compiled_protobufs.chat_pb2 import *
from wrappers.server_wrapper import QuicServer

CHAT_SERVER_IP = "127.0.0.1"
CHAT_SERVER_PORT = 8000

"""

ideas:

1. maybe only send every X ms instead of when received
2. save a map of connection_id to username (and make a method to convert)
3. save the username only once, when a connection is made
4. then, only send the message, and not the username

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
        self.clients: list[int] = list()  # connection ids

    def on_receive(self, connection_id: int, data: bytes):
        request = ChatMessage()
        request.ParseFromString(data)

        # only send the message to the other clients
        for id in self.clients:

            if id != connection_id:
                self.server.send(id, data)

    def on_connect(self, connection_id: int):
        self.clients.append(connection_id)
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        self.clients.remove(connection_id)
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
    s = ChatServer()
    asyncio.run(s.run())
