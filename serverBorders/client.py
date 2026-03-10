import asyncio
import os
import struct

import pygame

import Player
import SETTINGS as S
from networking.wrappers.client_wrapper import QuicClient
from map import *
from map_data import *

class MyClient:

    def __init__(self):
        self.client = None
        self.pid = None
        self.connections = []
        self.iControl = 0
        self.iInActive = None
        self.running = True
        self.players = []  # list of other players which are relevant works in [i]={"x":...,...}
        pygame.init()
        self.screen = pygame.display.set_mode((S.WINDOW_WIDTH, S.WINDOW_HEIGHT))
        pygame.display.set_caption("Game")
        self.player = Player.Player()
    # ----------
    # RECEIVE DATA
    # ----------
    def on_receive(self, connection_id: int, data: bytes):
        cmd = struct.unpack_from('!b', data, 0)[0]
        print(cmd)
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
            if self.iInActive != None:
                self.iControl = self.iInActive
                self.iInActive = None
            else:
                print("fuck")
        elif (cmd == S.CMDS["RENDER"]):
            # render the screen
            if connection_id == self.connections[self.iControl] or (self.iInActive != None and connection_id == self.connections[self.iInActive]):
                self.players = []
                count = struct.unpack_from('!h', data, 1)[0]
                for i in range(count):
                    offset = 3+4*i
                    x, y = struct.unpack_from('!hh', data, offset)
                    self.players.append({"x":x,"y": y})

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

        SPRITES1 = load_player_sprites(1)
        DEFAULT_SPRITE1 = SPRITES1[3]



        while self.running:
            # Check for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # KEYS (GET INPUTS)
            inputs, pressed = getInputs()
            # SEND INPUTS
            if (pressed):
                self.sendInputs(inputs)


            # DRAW
            self.draw_frame(self.screen, S.MAP_WIDTH, S.MAP_HEIGHT, DEFAULT_SPRITE1)
            pygame.display.flip()
            """self.screen.fill((30, 30, 30))  # BG
            drawServers(self.screen)  # SERVERS (FRONTEND)
            self.player.draw(self.screen)  # PLAYER

            if self.players != [] and len(self.players) >1: print(self.players)
            for dic in self.players:
                x,y = dic["x"], dic["y"]
                if x != self.player.x or y != self.player.y:
                    draw_player(screen=self.screen, x=x, y=y)"""

            await asyncio.sleep(1 / 60)

        pygame.quit()

    def sendInputs(self, inputs):
        xAxisDirection = inputs['d'] - inputs['a']
        yAxisDirection = inputs['s'] - inputs['w']
        pk = struct.pack('!b16sbb', S.CMDS["MOVE"], self.pid.encode("utf-8"), xAxisDirection, yAxisDirection)  # b is signed byte
        self.client.send(self.connections[self.iControl], pk)

    def draw_frame(self, screen, map_w, map_h, DEFAULT_SPRITE1):
        screen.fill((0, 0, 0))

        cam_x, cam_y = camera_from_pos(self.player.x, self.player.y, map_w, map_h)

        draw_map(screen, MAP, cam_x, cam_y, S.WINDOW_WIDTH, S.WINDOW_HEIGHT)
        draw_players(screen, self.player.x, self.player.y, self.players, cam_x, cam_y, DEFAULT_SPRITE1)

def draw_players(screen, x, y, players, cam_x, cam_y, DEFAULT_SPRITE1):
    for p in players:
        px = int(p["x"] - cam_x - S.PLAYER_SIZE // 2)
        py = int(p["y"] - cam_y - S.PLAYER_SIZE // 2)

        sprite =  DEFAULT_SPRITE1
        screen.blit(sprite, (px, py))
    px = int(x - cam_x - S.PLAYER_SIZE // 2)
    py = int(y - cam_y - S.PLAYER_SIZE // 2)
    sprite = DEFAULT_SPRITE1
    screen.blit(sprite, (px, py))

def load(name: str, rotations_dir) -> pygame.Surface:
    path = os.path.join(rotations_dir, name)
    img = pygame.image.load(path).convert_alpha()
    if img.get_width() != S.PLAYER_SIZE or img.get_height() != S.PLAYER_SIZE:
        img = pygame.transform.scale(img, (S.PLAYER_SIZE, S.PLAYER_SIZE))
    return img

def load_player_sprites(group):
    if group == 1:
        rotations_dir = os.path.join(os.path.dirname(__file__), "rotations")
    else:
        rotations_dir = os.path.join(os.path.dirname(__file__), "rotation1")

    return {
        1: load("east.png", rotations_dir),
        2: load("south-east.png", rotations_dir),
        3: load("south.png", rotations_dir),
        4: load("south-west.png", rotations_dir),
        5: load("west.png", rotations_dir),
        6: load("north-west.png", rotations_dir),
        7: load("north.png", rotations_dir),
        8: load("north-east.png", rotations_dir),
    }

def camera_from_pos(x, y, map_w, map_h):
    cam_x = int(x - S.WINDOW_WIDTH // 2)
    cam_y = int(y - S.WINDOW_HEIGHT // 2)
    cam_x = max(0, min(map_w - S.WINDOW_WIDTH, cam_x))
    cam_y = max(0, min(map_h - S.WINDOW_HEIGHT, cam_y))
    return cam_x, cam_y

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

def draw_player(screen, x, y):
    playerRect = pygame.Rect(x, y, 40, 40)
    pygame.draw.rect(screen, (0, 190, 190), playerRect)


def drawServers(screen):
    for server in S.SERVERS:
        sRect = pygame.Rect(server["x"], 0, S.GENERAL_SERVER["width"], S.WINDOW_HEIGHT)
        pygame.draw.rect(screen, S.GENERAL_SERVER["color"], sRect)

    for overlap in S.OVERLAPS:
        oRect = pygame.Rect(overlap["x"], 0, S.GENERAL_OVERLAP["width"], S.WINDOW_HEIGHT)
        pygame.draw.rect(screen, S.GENERAL_OVERLAP["color"], oRect)


if __name__ == "__main__":
    c = MyClient()
    asyncio.run(c.run())
