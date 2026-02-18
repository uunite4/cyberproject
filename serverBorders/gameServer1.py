import asyncio

from networking.wrappers.server_wrapper import QuicServer
import SETTINGS as S
import struct

class MyServer:

    def __init__(self):
        self.serverData = S.SERVER1
        self.player = {}
        self.server = QuicServer(
            ip=self.serverData["ip"],
            port=self.serverData["port"],
            cert_file="../networking/certificate/cert.pem",
            key_file="../networking/certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )

    # ----------
    # RECEIVE DATA
    # ----------
    def on_receive(self, connection_id: int, data: bytes):
        print("Got data ", data, " from client ID ", connection_id)
        cmd = struct.unpack_from('B', data, 0)[0]

        if (cmd == S.CMDS["INIT_POS"]):
            x, y = struct.unpack_from('bb', data, 1)
            self.player = {
                "x": x,
                "y": y
            }
            print(self.player)

        elif (cmd == S.CMDS["MOVE"]):
            # CLIENT GAVE US DIRECTION, WE RETURN POS
            xDir, yDir = struct.unpack_from('bb', data, 1)
            xVel = xDir * S.PLAYER_VEL
            yVel = yDir * S.PLAYER_VEL
            self.player["x"] += xVel
            self.player["y"] += yVel
            global useCmd
            # CHECK OVERLAP / SERVER 2
            inOverlap = point_in_rect(self.player["x"], self.player["y"], S.OVERLAP["x"], 0, S.OVERLAP["width"], S.WINDOW_HEIGHT)
            inServer = point_in_rect(self.player["x"], self.player["y"], self.serverData["x"], 0, self.serverData["width"], S.WINDOW_HEIGHT)
            if (inOverlap):
                useCmd = S.CMDS["MOVE+OVERLAP"]
            elif (not inServer):
                useCmd = S.CMDS["MOVE+SWITCH_SERVER"]
            else:
                useCmd = S.CMDS["MOVE"]
            # FINAL PACKET
            pk = struct.pack('!bhh', useCmd, self.player["x"], self.player["y"])
            self.server.send(pk, connection_id)

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    async def run(self):
        await self.server.start()
        print("Server started")

        await asyncio.Future()

def point_in_rect(px, py, rx, ry, w, h):
    return (
        rx <= px <= rx + w and
        ry <= py <= ry + h
    )

if __name__ == "__main__":
    s = MyServer()
    asyncio.run(s.run())