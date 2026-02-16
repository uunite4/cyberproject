import asyncio
from quicFolder.quickquic import EasyQUICServer
import SETTINGS as S
import struct

thisServer = S.SERVER1
player = {}

def point_in_rect(px, py, rx, ry, w, h):
    return (
        rx <= px <= rx + w and
        ry <= py <= ry + h
    )

def reqHandle(req):
    global res
    global player
    cmd = struct.unpack_from('B', req, 0)[0]

    if (cmd == S.CMDS["INIT_POS"]):

        x, y = struct.unpack_from('bb', req, 1)
        player = {
            "x": x,
            "y": y
        }
        print(player)
        res = struct.pack('!b', S.CMDS["INIT_POS"]) # SEND BACK EMPTY

    elif (cmd == S.CMDS["MOVE"]):
        # CLIENT GAVE US DIRECTION, WE RETURN POS
        xDir, yDir = struct.unpack_from('bb', req, 1)
        xVel = xDir * S.PLAYER_VEL
        yVel = yDir * S.PLAYER_VEL
        player["x"] += xVel
        player["y"] += yVel
        global useCmd
        # CHECK OVERLAP / SERVER 2
        inOverlap = point_in_rect(player["x"], player["y"], S.OVERLAP["x"], 0, S.OVERLAP["width"], S.WINDOW_HEIGHT)
        inServer = point_in_rect(player["x"], player["y"], thisServer["x"], 0, thisServer["width"], S.WINDOW_HEIGHT)
        if (inOverlap): useCmd = S.CMDS["MOVE+OVERLAP"]
        elif (not inServer): useCmd = S.CMDS["MOVE+SWITCH_SERVER"]
        else: useCmd = S.CMDS["MOVE"]
        # FINAL PACKET
        res = struct.pack('!bhh', useCmd, player["x"], player["y"])

    return res

async def main():
    # SETUP SERVER
    server = EasyQUICServer(thisServer["ip"], thisServer["port"], S.CERT, S.KEY)
    await server.start(reqHandle)

if __name__ == "__main__":
    asyncio.run(main())