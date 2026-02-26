import asyncio

from networking.wrappers.server_wrapper import QuicServer
import SETTINGS as S
import struct

class MyServer:

    def __init__(self):
        self.serverNumber = 2
        self.serverData = S.SERVERS[self.serverNumber - 1]
        self.nearOverlaps = [getNearOverlaps(self.serverNumber - 1)]
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
        cmd = struct.unpack_from('B', data, 0)[0]

        if (cmd == S.CMDS["LB_ADDING_PLAYER"]):
            x, y = struct.unpack_from('!hh', data, 1)
            self.player = {
                "x": x,
                "y": y
            }
            print(self.player)

        elif (cmd == S.CMDS["MOVE"]):
            # CLIENT GAVE US DIRECTION, WE RETURN POS
            print(f"GOT MOVE PACKET")
            xDir, yDir = struct.unpack_from('bb', data, 1)
            xVel = xDir * S.PLAYER_VEL
            yVel = yDir * S.PLAYER_VEL
            self.player["x"] += xVel
            self.player["y"] += yVel

            if (self.player["x"] < 0): self.player["x"] = 0
            if (self.player["x"] + S.PLAYER_SIZE > S.WINDOW_WIDTH): self.player["x"] = S.WINDOW_WIDTH - S.PLAYER_SIZE
            if (self.player["y"] < 0): self.player["y"] = 0
            if (self.player["y"] + S.PLAYER_SIZE > S.WINDOW_HEIGHT): self.player["y"] = S.WINDOW_HEIGHT - S.PLAYER_SIZE

            # SEND MOVE
            pk = struct.pack('!bhh', S.CMDS["MOVE"], self.player["x"], self.player["y"])
            self.server.send(connection_id, pk)

            # NOW THAT WE UPDATED POSITION, WE CAN CHECK FOR RANGES
            # CHECK FOR OVERLAPS
            inOverlaps = []
            for OverlapObj in self.nearOverlaps:
                iOverlap = OverlapObj["overlapIndex"]
                inOverlap = point_in_rect(self.player["x"], self.player["y"], S.OVERLAPS[iOverlap]["x"], 0, S.GENERAL_OVERLAP, S.WINDOW_HEIGHT)
                inOverlaps.append(inOverlap)

            inServer = point_in_rect(self.player["x"], self.player["y"], self.serverData["x"], 0, self.serverData["width"], S.WINDOW_HEIGHT)

            for i, inOverlap in enumerate(inOverlaps):    # WILL ALWAYS BE ONLY 1 of them
                if (inOverlap):
                    pk = struct.pack('!bb', S.CMDS["OVERLAP"], self.nearOverlaps[i]["dir"])
                    self.server.send(connection_id, pk)

            if (not inServer):
                pk = struct.pack('!b', S.CMDS["SWITCH_SERVER"])
                self.server.send(connection_id, pk)
        elif (cmd == S.CMDS["POS_DONT_RESPOND"]):
            x, y = struct.unpack_from('!hh', data, 1)
            self.player = {
                "x": x,
                "y": y
            }
            print(f"GOT OVERLAP PACKET")

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

def getNearOverlaps(serverIndex):
    if serverIndex == 0:
        return {"overlapIndex": serverIndex, "dir": "r"}
    elif serverIndex == S.SERVER_NUMBER - 1:
        return {"overlapIndex": serverIndex - 1, "dir": "l"}
    else:
        return {"overlapIndex": serverIndex - 1, "dir": "l"}, {"overlapIndex": serverIndex, "dir": "r"}


if __name__ == "__main__":
    s = MyServer()
    asyncio.run(s.run())