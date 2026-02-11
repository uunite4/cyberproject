import asyncio
from quicFolder.quickquic import EasyQUICServer
import SETTINGS as S
import struct

thisServer = S.SERVER2

def point_in_rect(px, py, rx, ry, w, h):
    return (
        rx <= px <= rx + w and
        ry <= py <= ry + h
    )

def reqHandle(req):
    global res
    cmd = struct.unpack_from('B', req, 0)[0]
    if (cmd == S.CMDS["MOVE"]):     # CLIENT GAVE US DIRECTION, WE NEED TO RETURN VELS
        xDir, yDir = struct.unpack_from('bb', req, 1)
        xVel = xDir * S.PLAYER_VEL
        yVel = yDir * S.PLAYER_VEL
        res = struct.pack('!bbb',S.CMDS["MOVE"], xVel, yVel)

    elif (cmd == S.CMDS["CHECK_POS"]):  # CLIENT GAVE US CORDS, WE NEED TO CHECK IF INSIDE THIS SERVER
        if len(req) < 5:
            print(f"Short CHECK_POS packet: {len(req)} bytes")
            return struct.pack('!b',S.CMDS["KEEP_SERVER"])
        playerX, playerY = struct.unpack_from('!hh', req, 1)
        if point_in_rect(playerX, playerY, thisServer["x"], 0, thisServer["width"], S.WINDOW_HEIGHT):
            res = struct.pack('!b',S.CMDS["KEEP_SERVER"])
        else:   # PLAYER OUTSIDE OF SERVER!
            print("DETECTED PLAYER OUT OF RANGE")
            res = struct.pack('!bb',S.CMDS["CHANGE_SERVER"], 1) # 2 is for server2

    return res

async def main():
    # SETUP SERVER
    server = EasyQUICServer(thisServer["ip"], thisServer["port"], S.CERT, S.KEY)
    await server.start(reqHandle)

if __name__ == "__main__":
    asyncio.run(main())