import asyncio
import random
import secrets
import string

from networking.wrappers.server_wrapper import QuicServer
import SETTINGS as S
import struct

from serverBorders.gameServer2 import check_collision_with_stone


class MyServer:

    def __init__(self):
        self.server = QuicServer(
            ip=S.LOAD_BALANCER["ip"],
            port=S.LOAD_BALANCER["port"],
            cert_file="../networking/certificate/cert.pem",
            key_file="../networking/certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )
        self.connections = []

    # ----------
    # RECEIVE DATA
    # ----------
    def on_receive(self, connection_id: int, data: bytes):
        cmd = struct.unpack_from('B', data, 0)[0]
        if (cmd == S.CMDS["INIT_LB"]):
            print("GOT INIT")
            x,y, iServer, pid = get_random_position()
            print("DECIDED ON POS: ", x, y, " | SERVER INDEX: ", iServer)
            # send server index to client
            pk2Client = struct.pack("!b16sbhh", S.CMDS["INIT_LB"], pid.encode("utf-8"), iServer, x, y)
            self.server.send(connection_id, pk2Client)
            # send pos to server
            pk2Server = struct.pack("!b16shh", S.CMDS["LB_ADDING_PLAYER"], pid.encode("utf-8"), x, y)
            self.server.send(self.connections[iServer], pk2Server)


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

        await asyncio.Future()

def point_in_rect(px, py, rx, ry, w, h):
    return (
        rx <= px <= rx + w and
        ry <= py <= ry + h
    )

def get_random_position():

    # Choose a random server
    server_index = random.randint(0, S.SERVER_NUMBER - 1)
    server = S.SERVERS[server_index]

    left = server["x"]
    right = server["x"] + S.SERVER_WIDTH

    # Remove overlap zones
    if server_index > 0:
        left += S.OVERLAP_WIDTH

    if server_index < S.SERVER_NUMBER - 1:
        right -= S.OVERLAP_WIDTH

    while True:

        # Random position inside safe horizontal zone
        x = random.randint(left, right - 1)
        y = random.randint(0, S.MAP_HEIGHT - 1)
        if not check_collision_with_stone(x,y,S.PLAYER_SIZE): #and collision with lava
            return x, y, server_index, generateToken()

def generateToken(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    s = MyServer()
    asyncio.run(s.run())