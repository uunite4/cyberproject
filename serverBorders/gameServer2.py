import asyncio
import struct
import time

import SETTINGS as S
from networking.wrappers.server_wrapper import QuicServer


class MyServer:

    def __init__(self):
        self.serverNumber = 2
        self.serverData = S.SERVERS[self.serverNumber - 1]
        self.nearOverlaps = getNearOverlaps(self.serverNumber - 1)
        self.clients = {}
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
        cmd, pid = struct.unpack_from('!b16s', data, 0)
        pid = pid.decode("utf-8")

        if (cmd == S.CMDS["LB_ADDING_PLAYER"]):
            print("GOT LB PACKET")
            x, y = struct.unpack_from('!hh', data, 17)
            self.clients[pid] = {
                "x": x,
                "y": y
            }
            print("PLAYERS INITIAL POS: ", self.clients[pid]["x"], self.clients[pid]["y"])

        elif (cmd == S.CMDS["MOVE"]):

            currentClient = self.clients[pid]

            # CLIENT GAVE US DIRECTION, WE RETURN POS
            print(f"GOT MOVE PACKET")
            xDir, yDir = struct.unpack_from('!bb', data, 17)
            xVel = xDir * S.PLAYER_VEL
            yVel = yDir * S.PLAYER_VEL
            currentClient["x"] += xVel
            currentClient["y"] += yVel

            if (currentClient["x"] < 0): currentClient["x"] = 0
            if (currentClient["x"] + S.PLAYER_SIZE > S.WINDOW_WIDTH): currentClient[
                "x"] = S.WINDOW_WIDTH - S.PLAYER_SIZE
            if (currentClient["y"] < 0): currentClient["y"] = 0
            if (currentClient["y"] + S.PLAYER_SIZE > S.WINDOW_HEIGHT): currentClient[
                "y"] = S.WINDOW_HEIGHT - S.PLAYER_SIZE

            # SEND MOVE
            pk = struct.pack('!bhh', S.CMDS["MOVE"], currentClient["x"], currentClient["y"])
            self.server.send(connection_id, pk)

            # NOW THAT WE UPDATED POSITION, WE CAN CHECK FOR RANGES
            # CHECK FOR OVERLAPS
            inOverlaps = []
            for OverlapObj in self.nearOverlaps:
                iOverlap = OverlapObj["overlapIndex"]
                inOverlap = point_in_rect(currentClient["x"], currentClient["y"], S.OVERLAPS[iOverlap]["x"], 0,
                                          S.GENERAL_OVERLAP["width"], S.WINDOW_HEIGHT)
                inOverlaps.append(inOverlap)

            inServer = point_in_rect(currentClient["x"], currentClient["y"], self.serverData["x"], 0,
                                     self.serverData["width"], S.WINDOW_HEIGHT)

            for i, inOverlap in enumerate(inOverlaps):  # WILL ALWAYS BE ONLY 1 of them
                if (inOverlap):
                    overlapDir = self.nearOverlaps[i]["dir"].encode("utf-8")
                    pk = struct.pack('!b1s', S.CMDS["OVERLAP"], overlapDir)
                    self.server.send(connection_id, pk)

            if (not inServer):
                pk = struct.pack('!b', S.CMDS["SWITCH_SERVER"])
                self.server.send(connection_id, pk)
        elif (cmd == S.CMDS["POS_DONT_RESPOND"]):
            x, y = struct.unpack_from('!hh', data, 17)
            self.clients[pid] = {
                "x": x,
                "y": y
            }
            print(f"GOT OVERLAP PACKET")

    def on_connect(self, connection_id: int):
        print(f"connected {connection_id}")

    def on_disconnect(self, connection_id: int):
        print(f"disconnected {connection_id}")

    async def broadcast_loop(self):
        lastBroadcast = time.time()

        while True:
            now = time.time()

            if now - lastBroadcast >= S.BROADCAST_INTERVAL:
                broadcast(self)
                lastBroadcast = now

            await asyncio.sleep(0.001)

    async def run(self):
        await self.server.start()
        print("Server started")

        asyncio.create_task(self.broadcast_loop())

        await asyncio.Future()  # keep program running


def point_in_rect(px, py, rx, ry, w, h):
    return (
            rx <= px <= rx + w and
            ry <= py <= ry + h
    )


def getNearOverlaps(serverIndex):
    nearOverlaps = []
    if serverIndex == 0:
        nearOverlaps.append({"overlapIndex": serverIndex, "dir": "r"})
    elif serverIndex == S.SERVER_NUMBER - 1:
        nearOverlaps.append({"overlapIndex": serverIndex - 1, "dir": "l"})
    else:
        nearOverlaps.append({"overlapIndex": serverIndex - 1, "dir": "l"})
        nearOverlaps.append({"overlapIndex": serverIndex, "dir": "r"})

    return nearOverlaps


def broadcast(self):
    pk = build_state_payload(clients=self.clients)
    if pk != b'\x08\x00\x00':
        print(pk)
    self.server.broadcast(pk)


def build_state_payload(clients):
    count = min(255, len(clients))
    format = "!bh" + "hh" * count
    payload = [S.CMDS["RENDER"], count]

    for c in clients.values():
        payload.append(int(c["x"]))
        payload.append(int(c["y"]))

    return struct.pack(format, *payload)


if __name__ == "__main__":
    s = MyServer()
    asyncio.run(s.run())
