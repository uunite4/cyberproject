import struct
import pygame
import asyncio
from quicFolder.quickquic import EasyQUIC
import SETTINGS as S
import Player

def drawServers(screen):
    server1Rect = pygame.Rect(S.SERVER1["x"], 0, S.SERVER1["width"], S.WINDOW_HEIGHT)
    server2Rect = pygame.Rect(S.SERVER2["x"], 0, S.SERVER2["width"], S.WINDOW_HEIGHT)
    overlapRect = pygame.Rect(S.OVERLAP["x"], 0, S.OVERLAP["width"], S.WINDOW_HEIGHT)
    pygame.draw.rect(screen, S.SERVER1["color"], server1Rect)
    pygame.draw.rect(screen, S.SERVER2["color"], server2Rect)
    pygame.draw.rect(screen, S.OVERLAP["color"], overlapRect)

def handleRes(resStruct, player):
    cmd = struct.unpack_from('B', resStruct, 0)[0]

    if (cmd == S.CMDS["INIT_POS"]):
        return

    elif (cmd == S.CMDS["MOVE"]):
        x, y = struct.unpack_from('!hh', resStruct, 1)
        print(x, y)
        player.tp(x, y)

    elif (cmd == S.CMDS["KEEP_SERVER"]):                            # WE SENT CORDS, NEED TO STAY IN THE SAME SERVER
        return "stay"
    elif (cmd == S.CMDS["CHANGE_SERVER"]):                          # WE SENT CORDS, NEED TO CHANGE SERVER
        print("! CHANGING SERVER !")
        newServer = struct.unpack_from('b', resStruct, 1)[0]
        # 1 = SERVER1 | 2 = SERVER2 | ...
        if (newServer == 1):
            return S.SERVER1["ip"], S.SERVER1["port"]
        elif (newServer == 2):
            return S.SERVER2["ip"], S.SERVER2["port"]


async def main():
    # 1. Initialize
    pygame.init()
    screen = pygame.display.set_mode((S.WINDOW_WIDTH, S.WINDOW_HEIGHT))
    pygame.display.set_caption("Game")
    running = True

    # SET UP CLIENT
    currentClient = EasyQUIC(S.SERVER1["ip"], S.SERVER1["port"])
    await currentClient.connect()

    # Create player
    myPlayer = Player.Player()
    pressed = False

    # SEND INITIAL POS
    pk = struct.pack("!bbb", S.CMDS["INIT_POS"], myPlayer.x, myPlayer.y)
    response = await currentClient.send(pk)
    handleRes(response, myPlayer)

    # --- THE GAME LOOP ---
    while running:
        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # KEYS (GET INPUTS)
        inputs = {
            "w": 0,
            "a": 0,
            "s": 0,
            "d": 0,
        }
        pressed = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            inputs["w"] = 1
            pressed = True
        if keys[pygame.K_s]:
            inputs["s"] = 1
            pressed = True
        if keys[pygame.K_a]:
            inputs["a"] = 1
            pressed = True
        if keys[pygame.K_d]:
            inputs["d"] = 1
            pressed = True

        # SEND INPUTS
        if (pressed):
            xAxisDirection = inputs['d'] - inputs['a']
            yAxisDirection = inputs['s'] - inputs['w']
            pk = struct.pack('!bbb', S.CMDS["MOVE"], xAxisDirection, yAxisDirection) # b is signed byte
            response = await currentClient.send(pk)
            handleRes(response, myPlayer)

        # DRAW
        screen.fill((30, 30, 30))   # BG
        drawServers(screen)         # SERVERS (FRONTEND)
        myPlayer.draw(screen)       # PLAYER

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())