import asyncio
import random
import secrets
import string

from game.networking.wrappers.server_wrapper import QuicServer
import SETTINGS as S
import struct

from game.classes.Player import *


class LoadBalancer:

    def __init__(self):
        self.server = QuicServer(
            ip=S.LOAD_BALANCER["ip"],
            port=S.LOAD_BALANCER["port"],
            cert_file="networking/certificate/cert.pem",
            key_file="networking/certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )
        self.connections = []
        self.login = 0

    # ----------
    # RECEIVE DATA
    # ----------
    def on_receive(self, connection_id: int, data: bytes):
        cmd = struct.unpack_from('!b', data, 0)[0]

        if cmd == S.CMDS["TRANSFER_P"]:
            print("GOT TRANSFER")
            nS = data[17]
            self.server.send(self.connections[nS-1], data)
        elif cmd == S.CMDS["CLIENT_DATA"]:
            self.login = connection_id
            server = data[17]
            print("transfering package to server ", server)
            self.server.send(self.connections[server], data)
        elif cmd == S.CMDS["PLAYER_LEFT"]:
            print("transfering player")
            login_data = struct.unpack_from(f"b16siib{S.INVENTORY_SIZE}b", data)
            print(login_data)
            self.server.send(self.login, data)

    def on_connect(self, connection_id: int):
        pass
        # print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        pass
        # print(f"{connection_id} disconnected")

    async def run(self):
        await self.server.start()
        print("Server started")

        # Connect to all servers
        for server in S.SERVERS:
            server_id = await self.server.connect_to_server(
                ip=server["ip"],
                port=server["port"],
            )
            self.connections.append(server_id)
            pk = struct.pack("!b", S.CMDS["HELLO_FROM_LB"])
            self.server.send(server_id, pk)
            print(server_id)

        await asyncio.Future()

if __name__ == "__main__":
    s = LoadBalancer()
    asyncio.run(s.run())