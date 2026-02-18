import asyncio
import struct

import pygame

import Player
import SETTINGS as S
from networking.wrappers.client_wrapper import QuicClient


class MyClient:

    def __init__(self):
        self.client = None
        self.running = True

        pygame.init()
        self.screen = pygame.display.set_mode((S.WINDOW_WIDTH, S.WINDOW_HEIGHT))
        pygame.display.set_caption("Game")

        self.player = Player.Player()

    # ----------
    # RECIEVE DATA
    # ----------
    def on_receive(self, connection_id: int, data: bytes):
        print("Server ID ", connection_id, " sent data")
        cmd = struct.unpack_from('B', data, 0)[0]

        if (cmd == S.CMDS["MOVE"]):
            moveOffPackt(data, self.player)

        elif (cmd == S.CMDS["MOVE+OVERLAP"]):
            moveOffPackt(data, self.player)
            # TODO: CHECK IF ALREADY CONNECTED TO SERVER 2
            # If not connected, connect pos
            # If connected, send pos

        elif (cmd == S.CMDS["MOVE+SWITCH_SERVER"]):
            moveOffPackt(data, self.player)
            # TODO: CHANGE ROLES

    # ----------
    # RUNNING
    # ----------
    async def run(self):
        self.client = QuicClient(
            cert_file="../networking/certificate/cert.pem",
            on_receive=self.on_receive
        )

        server_id = await self.client.connect(
            server_ip=S.SERVER1["ip"],
            server_port=S.SERVER1["port"],
        )

        # SEND INITIAL POS
        pk = struct.pack("!bhh", S.CMDS["INIT_POS"], self.player.x, self.player.y)
        self.client.send(server_id, pk)

        while self.running:
            # Check for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

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
                pk = struct.pack('!bbb', S.CMDS["MOVE"], xAxisDirection, yAxisDirection)  # b is signed byte
                print("Sending ", pk, " to server ID ", server_id)
                self.client.send(server_id, pk)

            # DRAW
            self.screen.fill((30, 30, 30))  # BG
            drawServers(self.screen)  # SERVERS (FRONTEND)
            self.player.draw(self.screen)  # PLAYER

            pygame.display.flip()

        pygame.quit()


def drawServers(screen):
    server1Rect = pygame.Rect(S.SERVER1["x"], 0, S.SERVER1["width"], S.WINDOW_HEIGHT)
    server2Rect = pygame.Rect(S.SERVER2["x"], 0, S.SERVER2["width"], S.WINDOW_HEIGHT)
    overlapRect = pygame.Rect(S.OVERLAP["x"], 0, S.OVERLAP["width"], S.WINDOW_HEIGHT)
    pygame.draw.rect(screen, S.SERVER1["color"], server1Rect)
    pygame.draw.rect(screen, S.SERVER2["color"], server2Rect)
    pygame.draw.rect(screen, S.OVERLAP["color"], overlapRect)

def moveOffPackt(pkStruct, player):
    x, y = struct.unpack_from('!hh', pkStruct, 1)
    player.tp(x, y)


if __name__ == "__main__":
    c = MyClient()
    asyncio.run(c.run())
