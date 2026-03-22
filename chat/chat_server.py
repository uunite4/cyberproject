import asyncio

import chat_settings as s
from protobufs.chat_pb2 import *
from wrappers.server_wrapper import QuicServer

"""

not sure if it should use a buffer
or just broadcast each message to anyone but the sender once received

"""


class ChatServer:

    def __init__(self):
        self.server = QuicServer(
            ip=s.CHAT_SERVER_IP,
            port=s.CHAT_SERVER_PORT,
            cert_file="wrappers/server.crt",
            key_fie="wrappers/server.key",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )
        self.message_buffer: list[tuple[int, ChatMessage]] = []

    def on_receive(self, connection_id: int, data: bytes):
        message = ChatMessage()
        message.ParseFromString(data)
        print(f"{message.username}: {message.message}")
        self.message_buffer.append((connection_id, message))

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    def send_buffer(self):

        if not self.message_buffer:
            return

        # Group messages by sender
        messages_by_sender: dict[int, ChatMessagesList] = {}

        for sender_id, m in self.message_buffer:
            if sender_id not in messages_by_sender:
                messages_by_sender[sender_id] = ChatMessagesList()

            msg = messages_by_sender[sender_id].messages.add()
            msg.username = m.username
            msg.message = m.message

        # Send to all except sender
        for connection_id in self.server._connections.keys():
            outgoing = ChatMessagesList()

            for sender_id, msg_list in messages_by_sender.items():
                if sender_id == connection_id:
                    continue

                for m in msg_list.messages:
                    msg = outgoing.messages.add()
                    msg.username = m.username
                    msg.message = m.message

            if outgoing.messages:
                self.server.send(connection_id, outgoing.SerializeToString())

        self.message_buffer.clear()

    async def run(self):
        await self.server.start()
        print("Server started")

        try:
            while True:
                self.send_buffer()
                await asyncio.sleep(1 / s.CHAT_SERVER_SEND_FPS)

        except asyncio.CancelledError:
            print("Server shutting down...")

        finally:
            await self.server.stop()
            print("Server shut down")


if __name__ == '__main__':
    chat = ChatServer()
    asyncio.run(chat.run())
