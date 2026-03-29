import asyncio
import os
import struct

import loadbalancer_settings as s
from wrappers import certificate_generator
from wrappers.server_wrapper import QuicServer


class LoadBalancer:

    def __init__(self):
        certificate_generator.generate_server_cert(os.getenv('LOAD_BALANCER_IP', "127.0.0.1"))
        certificate_generator.generate_client_cert()
        self.server = QuicServer(
            ip="0.0.0.0",
            port=9050,
            server_cert="wrappers/certificate/server.crt",
            server_key="wrappers/certificate/server.key",
            client_cert="wrappers/certificate/client.crt",
            client_key="wrappers/certificate/client.key",
            ca_file="wrappers/certificate/ca.crt",
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

        if cmd == s.CMDS["TRANSFER_P"]:
            print("GOT TRANSFER")
            nS = data[17]
            self.server.send(self.connections[nS - 1], data)
        elif cmd == s.CMDS["CLIENT_DATA"]:
            self.login = connection_id
            server = data[17]
            print("transfering package to server ", server)
            self.server.send(self.connections[server], data)
        elif cmd == s.CMDS["PLAYER_LEFT"]:
            print("transfering player")
            login_data = struct.unpack_from(f"b16siib{s.INVENTORY_SIZE}b", data)
            print(login_data)
            self.server.send(self.login, data)

    def on_connect(self, connection_id: int):
        pass

    def on_disconnect(self, connection_id: int):
        pass

    async def run(self):
        await self.server.start()
        print("Server started")

        # Connect to all servers
        for server in s.SERVERS_ADDRESSES:
            server_id = await self.server.connect_to_server(
                ip=server["ip"],
                port=server["port"],
            )
            self.connections.append(server_id)
            pk = struct.pack("!b", s.CMDS["HELLO_FROM_LB"])
            self.server.send(server_id, pk)
            print(server_id)

        await asyncio.Future()


if __name__ == "__main__":
    load_balancer = LoadBalancer()
    asyncio.run(load_balancer.run())
