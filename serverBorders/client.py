import asyncio
import struct

import pygame

import Player
import SETTINGS as S
from networking.wrappers.client_wrapper import QuicClient


class MyClient:

    def __init__(self):
        self.client = None
        self.connections = []
        self.iControl = 0
        self.iInActive = None
        self.running = True
        pygame.init()
        self.screen = pygame.display.set_mode((S.WINDOW_WIDTH, S.WINDOW_HEIGHT))
        pygame.display.set_caption("Game")
        self.player = Player.Player()

    # ----------
    # RECEIVE DATA
    # ----------
    def on_receive(self, connection_id: int, data: bytes):
        cmd = struct.unpack_from('B', data, 0)[0]

        if (cmd == S.CMDS["INIT_LB"]):
            self.iControl = struct.unpack_from('!b', data, 1)

        elif (cmd == S.CMDS["MOVE"]):
            moveOffPackt(data, self.player)

        elif (cmd == S.CMDS["OVERLAP"]):
            # SEND POS TO SECOND SERVER

            dir = struct.unpack_from('!b', data, 1)
            if (dir == "r"):
                self.iInActive = self.iControl + 1
            elif (dir == "l"):
                self.iInActive = self.iControl - 1

            pk = struct.pack("!bhh", S.CMDS["POS_DONT_RESPOND"], self.player.x, self.player.y)
            self.client.send(self.serverIDs["inactive"], pk)

        elif (cmd == S.CMDS["SWITCH_SERVER"]):
            # SWITCH BETWEEN CONTROL AND INACTIVE
            # temp = self.serverIDs["control"]
            self.serverIDs["control"] = self.serverIDs["inactive"]
            self.iControl = None

    # ----------
    # RUNNING
    # ----------
    async def run(self):
        self.client = QuicClient(
            cert_file="../networking/certificate/cert.pem",
            on_receive=self.on_receive
        )

        # Connect to all servers
        for server in S.SERVERS:
            server_id = await self.client.connect(
                server_ip=server["ip"],
                server_port=server["port"],
            )
            self.connections.append(server_id)

        # connect to LB and send initial
        lb_id = await self.client.connect(
            server_ip=S.LOAD_BALANCER["ip"],
            server_port=S.LOAD_BALANCER["port"]
        )
        pk = struct.pack("!b", S.CMDS["INIT_LB"])
        self.client.send(lb_id, pk)


        # SEND INITIAL POS
        # pk = struct.pack("!bhh", S.CMDS["INIT_POS"], self.player.x, self.player.y)
        # self.client.send(server_id, pk)

        while self.running:
            # Check for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # KEYS (GET INPUTS)
            inputs, pressed = getInputs()

            # SEND INPUTS
            if (pressed): sendInputs(self, inputs)

            # DRAW
            self.screen.fill((30, 30, 30))  # BG
            drawServers(self.screen)  # SERVERS (FRONTEND)
            self.player.draw(self.screen)  # PLAYER

            pygame.display.flip()
            await asyncio.sleep(1 / 60)

        pygame.quit()


def drawServers(screen):

    for server in S.SERVERS:
        sRect = pygame.Rect(server["x"], 0,  S.GENERAL_SERVER["width"], S.WINDOW_HEIGHT)
        pygame.draw.rect(screen, S.GENERAL_SERVER["color"], sRect)

    for overlap in S.OVERLAPS:
        oRect = pygame.Rect(overlap["x"], 0, S.GENERAL_OVERLAP["width"], S.WINDOW_HEIGHT)
        pygame.draw.rect(screen, S.GENERAL_OVERLAP["color"], oRect)

def moveOffPackt(pkStruct, player):
    x, y = struct.unpack_from('!hh', pkStruct, 1)
    player.tp(x, y)

def getInputs():
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

    return inputs, pressed

def sendInputs(self, inputs):
    xAxisDirection = inputs['d'] - inputs['a']
    yAxisDirection = inputs['s'] - inputs['w']
    pk = struct.pack('!bbb', S.CMDS["MOVE"], xAxisDirection, yAxisDirection)  # b is signed byte
    self.client.send(self.connections[self.iControl], pk)


if __name__ == "__main__":
    c = MyClient()
    asyncio.run(c.run())
