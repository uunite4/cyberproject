import asyncio
import struct

import pygame

import Player
import SETTINGS as S
from networking.wrappers.client_wrapper import QuicClient


class MyClient:

    def __init__(self):
        self.client = None
        self.pid = None
        self.connections = []
        self.iControl = 0
        self.iInActive = None
        self.running = True
        self.players = [] #list of other players which are relevent
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
            pid, controlIndex, x, y = struct.unpack_from('!16sbhh', data, 1)
            print(pid, controlIndex, x, y)
            self.iControl = controlIndex
            self.pid = pid.decode("utf-8")
            print("RESPONSE FROM LB (SERVER INDEX): ", self.iControl, "(X,Y): (", x, ",", y, ")", "PID", self.pid)
            self.player.x = x
            self.player.y = y

        elif (cmd == S.CMDS["MOVE"]):
            moveOffPackt(data, self.player)

        elif (cmd == S.CMDS["OVERLAP"]):
            # SEND POS TO SECOND SERVER

            dir = struct.unpack_from('!1s', data, 1)[0].decode("utf-8")
            if (dir == "r"):
                self.iInActive = self.iControl + 1
            elif (dir == "l"):
                self.iInActive = self.iControl - 1

            pk = struct.pack("!b16shh", S.CMDS["POS_DONT_RESPOND"], self.pid.encode("utf-8"), self.player.x, self.player.y)
            self.client.send(self.connections[self.iInActive], pk)

        elif (cmd == S.CMDS["SWITCH_SERVER"]):
            # SWITCH BETWEEN CONTROL AND INACTIVE
            self.iControl = self.iInActive
        elif (cmd == S.CMDS["RENDER"]):
            # render the screen
            count = struct.unpack_from('!h', data, 1)
            self.players = []
            for i in range(count):
                x,y = struct.unpack_from('!hh', data, 2+i*2)
                self.players.append((x,y))


    # ----------
    # RUNNING
    # ----------
    async def run(self):
        self.client = QuicClient(
            cert_file="../networking/certificate/cert.pem",
            on_receive=self.on_receive
        )
        print("hi")
        # Connect to all servers
        for server in S.SERVERS:
            server_id = await self.client.connect(
                server_ip=server["ip"],
                server_port=server["port"],
            )
            self.connections.append(server_id)
        print("hi")
        # connect to LB and send initial
        lb_id = await self.client.connect(
            server_ip=S.LOAD_BALANCER["ip"],
            server_port=S.LOAD_BALANCER["port"]
        )
        print("hi")
        pk = struct.pack("!b", S.CMDS["INIT_LB"])
        self.client.send(lb_id, pk)
        print("hi")

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
            for x,y in self.players:
                draw_player(screen=self.screen, x=x, y=y)


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
    pk = struct.pack('!b16sbb', S.CMDS["MOVE"], self.pid.encode("utf-8"), xAxisDirection, yAxisDirection)  # b is signed byte
    print(self.iControl)
    self.client.send(self.connections[self.iControl], pk)

def draw_player(screen,x,y):
    playerRect = pygame.Rect(x, y, 40, 40)
    pygame.draw.rect(screen, (0, 190, 190), playerRect)

if __name__ == "__main__":
    c = MyClient()
    asyncio.run(c.run())
