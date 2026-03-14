import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import struct

import pygame
import Player
#from Player import *
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
        if (cmd == S.CMDS["INIT_LB"]):
            pid, controlIndex, x, y = struct.unpack_from('!16sbhh', data, 1)
            print(pid, controlIndex, x, y)
            self.iControl = controlIndex
            self.pid = pid.decode("utf-8")
            print("RESPONSE FROM LB (SERVER INDEX): ", self.iControl, "(X,Y): (", x, ",", y, ")", "PID", self.pid)
            self.player.x = x
            self.player.y = y
            self.player.dir = 3
            self.player.health = S.PLAYER_HEALTH
            self.player.att = 0

        elif (cmd == S.CMDS["MOVE"]):
            moveOffPackt(data, self.player)

        elif (cmd == S.CMDS["OVERLAP"]):
            # SEND POS TO SECOND SERVER

            dir = struct.unpack_from('!1s', data, 1)[0].decode("utf-8")
            if (dir == "r"):
                self.iInActive = self.iControl + 1
            elif (dir == "l"):
                self.iInActive = self.iControl - 1

            print(self.iInActive)

            pk = struct.pack("!b16shhhhb", S.CMDS["POS_DONT_RESPOND"], self.pid.encode("utf-8"), self.player.x,
                             self.player.y,
                             self.player.dir, self.player.health, self.player.att)
            self.client.send(self.connections[self.iInActive], pk)

        elif (cmd == S.CMDS["OUT_OF_OVERLAP"]):
            # SEND TO INACTIVE SERVER TO REMOVE ME
            pk = struct.pack("!b16s", S.CMDS["REMOVE_ME"], self.pid.encode("utf-8"))
            self.client.send(self.connections[self.iInActive], pk)
            self.iInActive = None

        elif (cmd == S.CMDS["SWITCH_SERVER"]):
            # SWITCH BETWEEN CONTROL AND INACTIVE
            if self.iInActive != None:
                pk = struct.pack("!b16s", S.CMDS["REMOVE_ME"], self.pid.encode("utf-8"))
                self.client.send(self.connections[self.iControl], pk)
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
                    offset = 3+9*i
                    x, y, dir, health, att = struct.unpack_from('!hhhhb', data, offset)
                    self.players.append({"x":x,"y": y, "dir": dir, "hp": health, "att": att})
        elif (cmd == S.CMDS["DAMAGE"]):
            nhp = struct.unpack_from('!h', data, 1)[0]
            self.player.health = nhp
            if self.iInActive != None:
                pk = struct.pack("!b16shhhhb", S.CMDS["HP_DONT_RESPOND"], self.pid.encode("utf-8"), nhp)
                self.client.send(self.connections[self.iInActive], pk)
        elif (cmd == S.CMDS["RESPAWN"]):
            x,y = struct.unpack_from('!hh', data, 1)
            self.player.tp(x,y,3)
            self.player.health = S.PLAYER_HEALTH
            if self.iInActive != None:
                pk = struct.pack("!b16s", S.CMDS["REMOVE_ME"], self.pid.encode("utf-8"))
                self.client.send(self.connections[self.iInActive], pk)



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
        SPRITES2 = load_player_sprites(2)
        DEFAULT_SPRITE2 = SPRITES2[3]
        DAGGERS = load_dagger_sprites()
        DEFAULT_DAGGER = DAGGERS[3]


        while self.running:
            # Check for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # KEYS (GET INPUTS)
            inputs, pressedM, pressedA = getInputs()
            # SEND INPUTS
            if inputs["sp"] == 1:
                if self.player.att == 0:
                    pk = struct.pack('!b16sb', S.CMDS["ATTACK"], self.pid.encode("utf-8"), inputs["sp"])  # b is signed byte
                    self.client.send(self.connections[self.iControl], pk)
                    if self.iInActive != None:
                        self.client.send(self.connections[self.iInActive], pk)
                    self.player.att = 1
            elif self.player.att == 1:
                pk = struct.pack('!b16sb', S.CMDS["ATTACK"], self.pid.encode("utf-8"), inputs["sp"])  # b is signed byte
                self.client.send(self.connections[self.iControl], pk)
                if self.iInActive != None:
                    self.client.send(self.connections[self.iInActive], pk)
                self.player.att = 0
            if (pressedM): #movement related inputs
                self.sendInputs(inputs)


            # DRAW
            self.draw_frame(self.screen, S.MAP_WIDTH, S.MAP_HEIGHT, DEFAULT_SPRITE1, SPRITES1 , DEFAULT_DAGGER, DAGGERS)
            pygame.display.flip()

            await asyncio.sleep(1 / 60)

        pygame.quit()

    def sendInputs(self, inputs):
        xAxisDirection = inputs['d'] - inputs['a']
        yAxisDirection = inputs['s'] - inputs['w']
        pk = struct.pack('!b16sbbb', S.CMDS["MOVE"], self.pid.encode("utf-8"), xAxisDirection, yAxisDirection, inputs["sf"])  # b is signed byte
        self.client.send(self.connections[self.iControl], pk)

    def draw_frame(self, screen, map_w, map_h, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER, DAGGERS):
        screen.fill((0, 0, 0))

        cam_x, cam_y = camera_from_pos(self.player.x, self.player.y, map_w, map_h)

        draw_map(screen, MAP, cam_x, cam_y, S.WINDOW_WIDTH, S.WINDOW_HEIGHT)
        draw_players(screen, self.player, self.players, cam_x, cam_y, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER, DAGGERS)

def draw_players(screen, player, players, cam_x, cam_y, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER, DAGGERS):
    # DRAW OTHER PLAYERS
    for p in players:
        px = int(p["x"] - cam_x - S.PLAYER_SIZE // 2)
        py = int(p["y"] - cam_y - S.PLAYER_SIZE // 2)

        sprite = SPRITES1.get(p["dir"], DEFAULT_SPRITE1)
        screen.blit(sprite, (px, py))
        S_health_bar_update(p["hp"], screen, px, py)

        if p["att"]==1: #daggers
            print("A PLAYER IS ATTACKING")
            d = p["dir"]
            vx, vy = dir_to_vec(d)
            dagger_x = int((p["x"] + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
            dagger_y = int((p["y"] + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
            screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))

    # DRAW OWN PLAYER
    px = int(player.x - cam_x - S.PLAYER_SIZE // 2)
    py = int(player.y - cam_y - S.PLAYER_SIZE // 2)
    sprite = SPRITES1.get(player.dir, DEFAULT_SPRITE1)
    screen.blit(sprite, (px, py))
    if player.att == 1:  # daggers
        d = player.dir
        vx, vy = dir_to_vec(d)
        dagger_x = int((player.x + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
        dagger_y = int((player.y + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
        screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))

    health_bar_update(player.health, screen)

def dir_to_vec(d: int) -> tuple[int, int]:
    vectors = {
        1: (1, 0),
        2: (1, 1),
        3: (0, 1),
        4: (-1, 1),
        5: (-1, 0),
        6: (-1, -1),
        7: (0, -1),
        8: (1, -1)
    }
    return vectors.get(d, (0, 0))

def health_bar_update(health,screen):
    green1 =  (S.HEALTH_BAR_SIZE_X /S.PLAYER_HEALTH)*health
    red1= S.HEALTH_BAR_SIZE_X - green1
    pygame.draw.rect(screen, "green", (20, 20, green1, S.HEALTH_BAR_SIZE_Y))
    pygame.draw.rect(screen, "red", (20+green1, 20, red1, S.HEALTH_BAR_SIZE_Y))

def S_health_bar_update(health,screen,x,y):
    green1 =  (S.S_HEALTH_BAR_SIZE_X /S.PLAYER_HEALTH)*health
    red1= S.S_HEALTH_BAR_SIZE_X - green1
    pygame.draw.rect(screen, "green", (x, y-40, green1, S.S_HEALTH_BAR_SIZE_Y))
    pygame.draw.rect(screen, "red", (x+green1, y-40, red1, S.S_HEALTH_BAR_SIZE_Y))

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
def load_dagger_sprites() -> dict[int, pygame.Surface]:
    base_path = os.path.join(os.path.dirname(__file__), "..\sprites\DAGGER-NORTH.png")
    base = pygame.image.load(base_path).convert_alpha()

    if base.get_width() != S.TILE_SIZE or base.get_height() != S.TILE_SIZE:
        base = pygame.transform.scale(base, (S.TILE_SIZE, S.TILE_SIZE))

    # base = NORTH (dir 7)
    return {
        7: base,
        8: rot(base, -45),
        1: rot(base, -90),
        2: rot(base, -135),
        3: rot(base, 180),
        4: rot(base, 135),
        5: rot(base, 90),
        6: rot(base, 45),
    }

def rot(img, deg):
    return pygame.transform.rotate(img, deg)

def camera_from_pos(x, y, map_w, map_h):
    cam_x = int(x - S.WINDOW_WIDTH // 2)
    cam_y = int(y - S.WINDOW_HEIGHT // 2)
    cam_x = max(0, min(map_w - S.WINDOW_WIDTH, cam_x))
    cam_y = max(0, min(map_h - S.WINDOW_HEIGHT, cam_y))
    return cam_x, cam_y

def moveOffPackt(pkStruct, player):
    x, y, dir = struct.unpack_from('!hhh', pkStruct, 1)
    player.tp(x, y, dir)


def getInputs():
    inputs = {
        "w": 0,
        "a": 0,
        "s": 0,
        "d": 0,
        "sf": 0,
        "sp": 0,
    }
    pressedM, pressedA = False, False
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        inputs["w"] = 1
        pressedM = True
    if keys[pygame.K_s]:
        inputs["s"] = 1
        pressedM = True
    if keys[pygame.K_a]:
        inputs["a"] = 1
        pressedM = True
    if keys[pygame.K_d]:
        inputs["d"] = 1
        pressedM = True
    if keys[pygame.K_LSHIFT]:
        inputs["sf"] = 1
    if keys[pygame.K_SPACE]:
        inputs["sp"] = 1
        pressedA = True

    return inputs, pressedM, pressedA


if __name__ == "__main__":
    c = MyClient()
    asyncio.run(c.run())
