import asyncio
import json
import os
import sys

import pygame

from game.chat.protobufs.chat_pb2 import ChatMessagesList, ChatMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import struct

from game.classes import Player
# from Player import *
from game.networking.wrappers.client_wrapper import QuicClient
from map import *
from game.map_data import MAP
import SETTINGS as S

poopb = pygame.image.load(S.poop).convert_alpha()
inventoryb = pygame.image.load(S.inventory1).convert_alpha()
selectb = pygame.image.load(S.select1).convert_alpha()
bolbolb = pygame.image.load(S.bolbol).convert_alpha()
lcon28b = pygame.image.load(S.lcon28).convert_alpha()
lcon1b = pygame.image.load(S.lcon1).convert_alpha()
lcon5b = pygame.image.load(S.lcon5).convert_alpha()
scissorsb = pygame.image.load(S.scissors).convert_alpha()
lazerb = pygame.image.load(S.lazer).convert_alpha()
gunb = pygame.image.load(S.gun).convert_alpha()

class Client:

    def __init__(self):
        self.username = None
        self.client = None
        self.pid = None
        self.connections = []
        self.iControl = 0
        self.iInActive = None
        self.running = True
        self.players = []  # list of other players which are relevant works in [i]={"x":...,...}
        self.bullets = []
        self.dropped = []
        self.enemies = []
        self.open = False
        pygame.init()
        self.screen = pygame.display.set_mode((S.WINDOW_WIDTH, S.WINDOW_HEIGHT))
        pygame.display.set_caption("Game")
        self.player = Player()

        # login-server data client
        self.status_msg = None
        self.login_server_id = None

        # event used to signal server response
        self.response_event = asyncio.Event()

        self.chat_server_id = None
        self.chat_active: bool = False
        self.chat_message: str = ""
        self.chat_received_messages: list[tuple[str, str]] = []

    # ----------
    # RECEIVE DATA
    # ----------
    def on_receive(self, connection_id: int, data: bytes):

        if connection_id == self.chat_server_id:
            self.chat_on_receive(connection_id, data)

        elif connection_id == self.login_server_id:
            cmd = struct.unpack_from('!b', data, 0)[0]
            self.status_msg = []
            if (cmd == S.CMDS["ERROR"]):
                self.status_msg.append("ERROR")
                typeE, action = struct.unpack_from('!bb', data, 1)
                self.status_msg.append(S.BYTESERRORS[typeE])
                self.status_msg.append(S.BYTESERRORS[action])
            elif (cmd == S.CMDS["CLIENT_DATA"]):
                info = struct.unpack_from(f'!16sbiib{S.INVENTORY_SIZE}b', data, 1)
                self.pid = info[0].decode("utf-8")
                print(self.pid)
                self.iControl = info[1]
                print(info)
                self.player.x = info[2]
                self.player.y = info[3]
                self.player.dir = 3
                self.player.health = info[4]
                self.player.att = 0
                self.player.weapon = 1
                self.player.weapons = [None] * S.INVENTORY_SIZE
                for i in range(S.INVENTORY_SIZE):
                    weapon = S.INVENTORY_MAP[info[i + 5]]
                    self.player.weapons[i] = weapon
                print(self.player.weapons)

                self.status_msg = ["OK"]
                self.running = False
            print(f"login-server server: {self.status_msg}")

            # notify response received
            self.response_event.set()
        else:
            cmd = struct.unpack_from('!b', data, 0)[0]

            if (cmd == S.CMDS["MOVE"]):
                moveOffPackt(data, self.player)
                if self.iInActive != None:
                    pk = struct.pack("!b16siib", S.CMDS["POS_DONT_RESPOND"], self.pid.encode("utf-8"), self.player.x,
                                     self.player.y, self.player.dir)
                    self.client.send(self.connections[self.iInActive], pk)
            elif (cmd == S.CMDS["OVERLAP"]):
                dir = struct.unpack_from('!1s', data, 1)[0].decode("utf-8")
                if (dir == "r"):
                    self.iInActive = self.iControl + 1
                elif (dir == "l"):
                    self.iInActive = self.iControl - 1

                print("self.inActive", self.iInActive)
                pk = struct.pack("!b16siibbbbhhhh", S.CMDS["ADD_ME"], self.pid.encode("utf-8"), self.player.x,
                                 self.player.y,
                                 self.player.dir, self.player.health, self.player.att, self.player.weapon,
                                 self.player.fart_timer,
                                 self.player.invis_timer, self.player.laser_timer, self.player.brit)
                self.client.send(self.connections[self.iInActive], pk)

            elif (cmd == S.CMDS["OUT_OF_OVERLAP"]):
                # SEND TO INACTIVE SERVER TO REMOVE ME
                print("left overlap")
                pk = struct.pack("!b16s", S.CMDS["REMOVE_ME"], self.pid.encode("utf-8"))
                self.client.send(self.connections[self.iInActive], pk)
                self.iInActive = None

            elif (cmd == S.CMDS["SWITCH_SERVER"]):
                # SWITCH BETWEEN CONTROL AND INACTIVE
                if self.iInActive != None:
                    print("switching server to ", self.iInActive)
                    pk = struct.pack("!b16s", S.CMDS["REMOVE_ME"], self.pid.encode("utf-8"))
                    self.client.send(self.connections[self.iControl], pk)
                    self.iControl = self.iInActive
                    self.iInActive = None
                else:
                    print("fuck")
            elif (cmd == S.CMDS["RENDER"]):
                # render the screen
                if connection_id == self.connections[self.iControl] or (
                        self.iInActive != None and connection_id == self.connections[self.iInActive]):
                    fart, invi, laser, brit = struct.unpack_from('!hhhh', data, 1)
                    if fart > 0:
                        if self.iInActive != None and self.player.laser == 0:
                            pk = struct.pack("!b16s", S.CMDS["FARTING"], self.pid.encode("utf-8"))
                            self.client.send(self.connections[self.iInActive], pk)
                        self.player.fartp = 1
                    else:
                        self.player.fartp = 0
                    self.player.fart_timer = fart

                    if invi > 0:
                        if self.iInActive != None and self.player.invisible == 0:
                            pk = struct.pack("!b16s", S.CMDS["INVIS"], self.pid.encode("utf-8"))
                            self.client.send(self.connections[self.iInActive], pk)
                        self.player.invisible = 1
                    else:
                        self.player.invisible = 0
                    self.player.invis_timer = invi

                    if laser > 0:
                        if self.iInActive != None and self.player.laser == 0:
                            pk = struct.pack("!b16s", S.CMDS["LASER"], self.pid.encode("utf-8"))
                            self.client.send(self.connections[self.iInActive], pk)
                        self.player.laser = 1
                    else:
                        self.player.laser = 0
                    self.player.laser_timer = laser

                    if brit > 0:
                        if self.iInActive != None and self.player.brit == 0:
                            pk = struct.pack("!b16s", S.CMDS["BRIT"], self.pid.encode("utf-8"))
                            self.client.send(self.connections[self.iInActive], pk)
                    self.player.brit = brit

                    if connection_id == self.connections[self.iControl]:
                        self.players = []
                        self.bullets = []
                        self.dropped = []
                        self.enemies = []

                    count = struct.unpack_from('!h', data, 9)[0]
                    for i in range(count):
                        offset = 11 + 14 * i
                        x, y, dir, health, att, weapon, fart, invi = struct.unpack_from('!iibbbbbb', data, offset)
                        self.players.append(
                            {"x": x, "y": y, "dir": dir, "hp": health, "att": att, "weapons": weapon, "fart": fart,
                             "invi": invi})
                    offset = 11 + 14 * count
                    countb = struct.unpack_from('!h', data, offset)[0]
                    offset += 2
                    for i in range(countb):
                        bx, by = struct.unpack_from('!ii', data, offset)
                        self.bullets.append({"x": bx, "y": by})
                        offset += 8
                    offset = 13 + 14 * count + 8 * countb
                    counti = struct.unpack_from('!h', data, offset)[0]
                    offset += 2
                    for i in range(counti):
                        ix, iy, iw = struct.unpack_from('!iib', data, offset)
                        self.dropped.append({"x": ix, "y": iy, "weapon_type": iw})
                        offset += 9
                    offset = 15 + 14 * count + 8 * countb + 9 * counti
                    counte = struct.unpack_from('!h', data, offset)[0]
                    offset += 2
                    for i in range(counte):
                        ex, ey, dir, hp, type = struct.unpack_from('!iibbb', data, offset)
                        if type == 0:
                            type = "GOBLIN"
                        elif type == 1:
                            type = "BEAR"
                        self.enemies.append({"x": ex, "y": ey, "dir": dir, "hp": hp, "type": type})
                        offset += 11

            elif (cmd == S.CMDS["DAMAGE"]):
                print("got damage")
                nhp = struct.unpack_from('!b', data, 1)[0]
                self.player.health = nhp
                if self.iInActive != None:
                    pk = struct.pack("!b16sb", S.CMDS["HP_DONT_RESPOND"], self.pid.encode("utf-8"), nhp)
                    self.client.send(self.connections[self.iInActive], pk)
            elif (cmd == S.CMDS["RESPAWN"]):
                print("respawn pls")
                x, y = struct.unpack_from('!ii', data, 1)
                self.player.tp(x, y, 3)
                self.player.health = S.PLAYER_HEALTH
                self.player.weapons = S.BASIC_INV
                if self.iInActive != None:
                    pk = struct.pack("!b16s", S.CMDS["REMOVE_ME"], self.pid.encode("utf-8"))
                    self.client.send(self.connections[self.iInActive], pk)
            elif (cmd == S.CMDS["DELETE_ITEM"]):
                index = struct.unpack_from('!b', data, 1)[0]
                self.player.weapons[index] = 0
                print("deleting item ", index)
            elif (cmd == S.CMDS["FART_READY"]):
                self.player.fart_ready = 1
            elif (cmd == S.CMDS["TELEPORT_READY"]):
                self.player.teleport = 1
            elif (cmd == S.CMDS["ADD_ITEM"]):
                weapon_type, i = struct.unpack_from('!bb', data, 1)
                weapon = S.INVENTORY_MAP[weapon_type]
                if self.player.weapons[i] == 0:
                    self.player.weapons[i] = weapon
                else:
                    if connection_id == self.connections[self.iControl]:
                        self.player.weapons[i] = weapon
                print("adding item ", weapon)

    # -----------
    # running login-server
    # -----------
    async def main_menu(self):
        # Variables to track what we are typing
        username = ""
        password = ""
        active_field = "username"  # Toggle between username and password
        mode = "START"  # START, LOGIN_INPUT, SIGNUP_INPUT
        status_msg = ["ERROR", "WAITING", "ROOM"]  # This is our 'waiting room'

        while self.running:
            await asyncio.sleep(0.001)
            screen.fill(S.WHITE)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if mode == "START":
                        if event.key == pygame.K_l:
                            mode = "LOGIN_INPUT"
                        if event.key == pygame.K_s:
                            mode = "SIGNUP_INPUT"

                    elif "INPUT" in mode:
                        if event.key == pygame.K_ESCAPE:
                            mode = "START"
                            # Optional: Clear the text so it's empty when you come back
                            username = ""
                            password = ""
                            status_msg = ["ERROR", "WAITING", "ROOM"]  # This is our 'waiting room'
                        if event.key == pygame.K_TAB:  # Switch fields
                            active_field = "password" if active_field == "username" else "username"
                        elif event.key == pygame.K_RETURN:  # SEND TO SERVER
                            print("username: " + username)
                            print("password: " + password)
                            status_msg = await self.send_to_server(
                                username,
                                password,
                                "LOGIN" if mode == "LOGIN_INPUT" else "SIGNUP"
                            )
                        elif event.key == pygame.K_BACKSPACE:
                            if active_field == "username":
                                username = username[:-1]
                            else:
                                password = password[:-1]
                        else:
                            if active_field == "username":
                                username += event.unicode
                            else:
                                password += event.unicode

            # --- DRAWING LOGIC ---
            if mode == "START":
                self.draw_text("Welcome to the MMORPG", 230, 150)
                self.draw_text("Press 'L' for Login", 250, 250)
                self.draw_text("Press 'S' for Signup", 250, 300)

            elif "INPUT" in mode:
                if status_msg[0] == "ERROR":
                    success = [False, False]
                    self.draw_text(f"Mode: {mode}", 50, 50)
                    self.draw_text(f"Username: {username} {'|' if active_field == 'username' else ''}", 100, 150)
                    self.draw_text(f"Password: {'*' * len(password)} {'|' if active_field == 'password' else ''}", 100,
                                   200)
                    self.draw_text("Press TAB to switch, ENTER to submit, ESC to go back", 100, 300)

                    if status_msg[1] == "ERROR: with signup":
                        self.draw_text("SignUp failed!", 100, 400, color=(255, 0, 0))
                    elif status_msg[1] == "ERROR: with login-server":
                        self.draw_text("Login Failed!", 100, 400, color=(255, 0, 0))
                    elif status_msg[1] == "ERROR: username is empty" or status_msg[1] == "ERROR: password is empty":
                        self.draw_text("password or username is empty", 100, 400, color=(255, 0, 0))
                    else:
                        success[0] = True
                        self.draw_text("the key: " + status_msg[1], 100, 400, color=(255, 0, 0))  # SUCCESSFULL
                    if status_msg[2] == "NO USER FOUND":
                        self.draw_text("NO USER FOUND ", 100, 460, color=(255, 0, 0))
                    elif status_msg[2] == "User already found":
                        self.draw_text("USER FOUND ", 100, 460, color=(255, 0, 0))
                    elif status_msg[1] == "ERROR: username is empty" or status_msg[1] == "ERROR: password is empty":
                        self.draw_text("password or username is empty", 100, 400, color=(255, 0, 0))
                    else:
                        success[1] = True
                        self.draw_text("the next server: " + status_msg[2], 100, 460, color=(255, 0, 0))  # SUCCESFULL


            elif status_msg[0] == "OK":
                print("login-server\ sighup was successful")

            pygame.display.flip()
        self.username = username

    def draw_text(self, text, x, y, color=S.BLACK):
        font = pygame.font.SysFont("Arial", 24)
        img = font.render(text, True, color)
        screen.blit(img, (x, y))

    async def send_to_server(self, u, p, action):
        data = json.dumps({"username": u, "password": p, "action": action})

        # reset event before sending
        self.response_event.clear()
        self.send_to_login_server(data.encode())

        try:
            # wait for server response
            await asyncio.wait_for(self.response_event.wait(), timeout=2)

        except asyncio.TimeoutError:
            print("Connection timeout")
            return ["ERROR", "TIMEOUT", ""]

        status_msg = self.status_msg
        self.status_msg = None

        return status_msg

    def send_to_login_server(self, data):
        self.client.send(self.login_server_id, data)

    def send_message_to_chat_server(self, message: str):
        response = ChatMessage(
            message=message,
            username=self.username
        ).SerializeToString()

        self.client.send(self.chat_server_id, response)

    def handle_chat_input(self, event):
        if event.key == pygame.K_LCTRL:

            if self.chat_active:
                print('chat disabled')
                self.chat_active = False

            else:
                print('chat activated')
                self.chat_active = True

        elif self.chat_active:

            if event.key == pygame.K_RETURN:
                if self.chat_message == "": # if invalid
                    return

                self.send_message_to_chat_server(self.chat_message) # optional - add a buffer
                self.chat_received_messages.append((self.username, self.chat_message))
                self.chat_received_messages = self.chat_received_messages[-CHAT_MESSAGE_AMOUNT:]

                self.chat_message = "" # reset message

            elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                self.chat_message = self.chat_message[:-1]  # remove last char

            else:
                # Only allow English Letters and numbers
                if event.unicode.isalnum():
                    self.chat_message += event.unicode

    def chat_on_receive(self, connection_id: int, data: bytes):
        if connection_id == self.chat_server_id:
            message_list = ChatMessagesList()
            message_list.ParseFromString(data)

            for m in message_list.messages: # received messages
                self.chat_received_messages.append((m.username, m.message))

            # only display last 10 messages
            self.chat_received_messages = self.chat_received_messages[-CHAT_MESSAGE_AMOUNT:]

    def draw_chat(self):
        surface = pygame.Surface((CHAT_WIDTH, CHAT_HEIGHT))
        surface.fill(CHAT_BG_COLOR)

        chat_font = pygame.font.SysFont("arial", 20)

        y = 10
        for username, message in self.chat_received_messages:
            # Username
            name_surface = chat_font.render(f"{username}:", True, CHAT_USERNAME_COLOR)
            surface.blit(name_surface, (10, y))

            # Message
            msg_surface = chat_font.render(message, True, CHAT_TEXT_COLOR)
            surface.blit(msg_surface, (100, y))

            y += 25  # line spacing

        # Input Box
        input_box_height = 50
        pygame.draw.rect(surface, CHAT_INPUT_BG, (0, CHAT_HEIGHT - input_box_height, CHAT_WIDTH, input_box_height))

        # Render input text inside input box with some padding
        input_surface = chat_font.render(self.chat_message, True, CHAT_TEXT_COLOR)
        surface.blit(input_surface, (10, CHAT_HEIGHT - input_box_height + 10))

        # Blit the chat surface onto the main screen
        self.screen.blit(surface, (0, 0))


    async def run(self):

        self.client = QuicClient(
            cert_file="networking/certificate/cert.pem",
            on_receive=self.on_receive
        )
        """
        -------------------------------------------------------------------------
        LOGIN
        -------------------------------------------------------------------------
        """
        self.login_server_id = await self.client.connect(
            server_ip=S.LOGIN_SERVER["ip"],
            server_port=S.LOGIN_SERVER["port"],
        )
        print('connected to login server')

        try:

            pygame_task = asyncio.create_task(self.main_menu())
            print("got out main")
            await asyncio.gather(pygame_task)
            print("pygame task shit...")
            print("future fuck")
        except asyncio.CancelledError:
            print("Client shutting down...")
            await self.client.stop()
            print("Client shut down")

        """
        -------------------------------------------------------------------------
        GAME PLAY
        -------------------------------------------------------------------------
        """

        print("logged in!")

        """
        CHAT
        """

        self.running = True

        self.chat_server_id = await self.client.connect(
            server_ip=CHAT_SERVER_IP,
            server_port=CHAT_SERVER_PORT,
        )

        print('chat server is up!')

        # Connect to all servers
        for server in S.SERVERS:
            server_id = await self.client.connect(
                server_ip=server["ip"],
                server_port=server["port"],
            )
            self.connections.append(server_id)

        print('connected to all game servers')

        pk = struct.pack("!b16s", S.CMDS["HELLO"], self.pid.encode("utf-8"))
        self.client.send(self.connections[self.iControl], pk)

        # pk = struct.pack("!b", S.CMDS["INIT_LB"])
        # self.client.send(lb_id, pk)

        # SEND INITIAL POS
        # pk = struct.pack("!bhh", S.CMDS["INIT_POS"], self.player.x, self.player.y)
        # self.client.send(server_id, pk)

        SPRITES1 = load_player_sprites(1)
        DEFAULT_SPRITE1 = SPRITES1[3]
        SPRITES2 = load_player_sprites(2)
        DEFAULT_SPRITE2 = SPRITES2[3]
        DAGGERS = load_dagger_sprites()
        DEFAULT_DAGGER = DAGGERS[3]
        FARTS = load_fart_sprites()
        DEFAULT_FARTS = FARTS[3]
        SPRITES1ENEMY = load_enemy_sprites(1)
        DEFAULT_SPRITES1ENEMY = SPRITES1ENEMY[1]
        SPRITES2ENEMY = load_enemy_sprites(2)
        DEFAULT_SPRITES2ENEMY = SPRITES2ENEMY[1]

        clock = pygame.time.Clock()

        while self.running:

            pressed_i = False
            pressed_p = False

            # Check for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    self.handle_chat_input(event)
                    if event.key == pygame.K_i:
                        pressed_i = True
                    elif event.key == pygame.K_p:
                        pressed_p = True

            if not self.chat_active:
                inputs, pressedM, pressedA = get_inputs()

                if pressed_p:
                    self.player.server_num = self.iControl
                    self.player.idle = not self.player.idle

                # SEND INPUTS
                if inputs["sp"] == 1:  # attacking...
                    if self.player.att == 0:
                        sendAttack(self, 1)
                        self.player.att = 1
                elif self.player.att == 1:
                    sendAttack(self, 0)
                    self.player.att = 0

                if pressedA != 0:
                    if self.player.weapon != pressedA:
                        self.player.weapon = pressedA
                        pk = struct.pack("!b16sb", S.CMDS["CHANGE_WEAPON"], self.pid.encode("utf-8"), pressedA)
                        self.client.send(self.connections[self.iControl], pk)
                        if self.iInActive != None:
                            self.client.send(self.connections[self.iInActive], pk)

                if inputs["f"]:  # farting...
                    if self.player.fartp == 0 and self.player.fart_ready == 1:
                        self.player.fart_ready = 0
                        print("sent fart")
                        sendFart(self, 1)

                if pressed_i:  # toggle inventory
                    self.open = not self.open
                if inputs["e"] == 1:
                    pk = struct.pack("!b16s", S.CMDS["PICKUP_ITEM"], self.pid.encode("utf-8"))
                    self.client.send(self.connections[self.iControl], pk)
                    if self.iInActive != None:
                        self.client.send(self.connections[self.iInActive], pk)

                if inputs["t"] == 1:
                    if self.player.teleport == 1:
                        self.player.teleport = 0
                        pk = struct.pack('!b16s', S.CMDS["TELEPORT"], self.pid.encode("utf-8"))  # b is signed byte
                        self.client.send(self.connections[self.iControl], pk)
                        if self.iInActive != None:
                            self.client.send(self.connections[self.iInActive], pk)

                if not self.player.idle:
                    if pressedM:  # movement related inputs
                        self.sendInputs(inputs)
                else:
                    new_inputs = self.player.move_idle()
                    new_inputs['sf'] = inputs['sf']
                    self.sendInputs(new_inputs)

            # DRAW
            self.draw_frame(self.screen, S.MAP_WIDTH, S.MAP_HEIGHT, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER, DAGGERS,
                            DEFAULT_FARTS, FARTS, SPRITES1ENEMY, DEFAULT_SPRITES1ENEMY, SPRITES2ENEMY,
                            DEFAULT_SPRITES2ENEMY, clock)

            if self.chat_active:
                self.draw_chat()

            pygame.display.flip()
            clock.tick(60)

            await asyncio.sleep(1 / 60)

        pygame.quit()

    def sendInputs(self, inputs):
        xAxisDirection = inputs['d'] - inputs['a']
        yAxisDirection = inputs['s'] - inputs['w']
        pk = struct.pack('!b16sbbb', S.CMDS["MOVE"], self.pid.encode("utf-8"), xAxisDirection, yAxisDirection,
                         inputs["sf"])  # b is signed byte
        self.client.send(self.connections[self.iControl], pk)

    def draw_frame(self, screen, map_w, map_h, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER, DAGGERS, DEFAULT_FARTS, FARTS,
                   ENEMY_SPRITES, DEFAULT_SPRITE_ENEMY, SPRITES2ENEMY,
                   DEFAULT_SPRITES2ENEMY, clock):
        screen.fill((0, 0, 0))

        cam_x, cam_y = camera_from_pos(self.player.x, self.player.y, map_w, map_h)
        draw_map(screen, MAP, cam_x, cam_y, S.WINDOW_WIDTH, S.WINDOW_HEIGHT)
        draw_bullets(screen, self.bullets, cam_x, cam_y)
        draw_dropped(screen, self.dropped, cam_x, cam_y)
        draw_players(screen, self.player, self.players, cam_x, cam_y, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER,
                     DAGGERS, DEFAULT_FARTS, FARTS)
        draw_enemy(screen, self.enemies, cam_x, cam_y, ENEMY_SPRITES, DEFAULT_SPRITE_ENEMY, SPRITES2ENEMY,
                   DEFAULT_SPRITES2ENEMY)
        fps_font = pygame.font.SysFont("Arial", 20, bold=True)
        draw_fps(clock, fps_font, screen)
        if self.open:
            draw_inventory_overlay(screen, self.player, fps_font)
        else:
            draw_inventori(screen, self.player)


def draw_players(screen, player, players, cam_x, cam_y, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER, DAGGERS,
                 DEFAULT_FARTS, FARTS):
    # DRAW OTHER PLAYERS
    for p in players:
        px = int(p["x"] - cam_x - S.PLAYER_SIZE // 2)
        py = int(p["y"] - cam_y - S.PLAYER_SIZE // 2)
        if p["invi"] == 0:
            sprite = SPRITES1.get(p["dir"], DEFAULT_SPRITE1)
            screen.blit(sprite, (px, py))
            S_health_bar_update(p["hp"], screen, px, py, S.PLAYER_HEALTH)

        if p["att"] == 1 and p["weapons"] == 1:  # daggers
            print("A PLAYER IS daggering")
            d = p["dir"]
            vx, vy = dir_to_vec(d)
            dagger_x = int((p["x"] + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
            dagger_y = int((p["y"] + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
            screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))
        if p["att"] == 1 and p["weapons"] == 7:
            draw_laser(screen, p["dir"], px, py)
        if p["fart"] == 1:
            d = p["dir"]
            vx, vy = dir_to_vec(d)
            vx, vy = vx * (-1), vy * (-1)
            fart_x = int((p["x"] + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
            fart_y = int((p["y"] + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
            screen.blit(FARTS.get(d, DEFAULT_FARTS), (fart_x, fart_y))

    # DRAW OWN PLAYER
    px = int(player.x - cam_x - S.PLAYER_SIZE // 2)
    py = int(player.y - cam_y - S.PLAYER_SIZE // 2)
    sprite = SPRITES1.get(player.dir, DEFAULT_SPRITE1)
    if player.invisible == 0:
        screen.blit(sprite, (px, py))
    else:
        temp_sprite = sprite.copy()
        temp_sprite.set_alpha(100)
        screen.blit(temp_sprite, (px, py))

    if player.att == 1 and player.weapons[player.weapon - 1] == 'da':  # daggers
        d = player.dir
        vx, vy = dir_to_vec(d)
        dagger_x = int((player.x + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
        dagger_y = int((player.y + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
        screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))

    if player.att == 1 and player.laser == 1:
        draw_laser(screen, player.dir, px, py)

    if player.fartp == 1:
        d = player.dir
        vx, vy = dir_to_vec(d)
        vx, vy = vx * (-1), vy * (-1)
        fart_x = int((player.x + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
        fart_y = int((player.y + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
        screen.blit(FARTS.get(d, DEFAULT_FARTS), (fart_x, fart_y))

    if player.fart_ready == 1:
        x = S.WINDOW_WIDTH - 50
        y = S.WINDOW_HEIGHT - 50
        screen.blit(poopb, (x, y))

    if player.teleport == 1:
        x = S.WINDOW_WIDTH - 80
        y = S.WINDOW_HEIGHT - 50
        screen.blit(poopb, (x, y))

    health_bar_update(player.health, screen)


def draw_enemy(screen, enemys, cam_x, cam_y, ENEMY_SPRITES, DEFAULT_SPRITE, SPRITES2ENEMY, DEFAULT_SPRITES2ENEMY):
    # print(enemys)
    for e in enemys:
        ex = int(e["x"] - cam_x - S.MONSTERS[e["type"]]["size"] // 2)
        ey = int(e["y"] - cam_y - S.MONSTERS[e["type"]]["size"] // 2)
        if e["type"] == "GOBLIN":
            sprite = ENEMY_SPRITES.get(e["dir"], DEFAULT_SPRITE)
        else:
            sprite = SPRITES2ENEMY.get(e["dir"], DEFAULT_SPRITES2ENEMY)

        screen.blit(sprite, (ex, ey))
        S_health_bar_update(e["hp"], screen, ex, ey, S.MONSTERS[e["type"]]["health"])


def draw_bullets(screen, bullets, cam_x, cam_y):
    for b in bullets:
        bx = b["x"] - cam_x
        by = b["y"] - cam_y

        pygame.draw.circle(screen, "red", (bx, by), S.BULLET_SIZE)
        pygame.draw.circle(screen, "orange", (bx, by), S.BULLET_SIZE - 1)
        pygame.draw.circle(screen, "yellow", (bx, by), S.BULLET_SIZE - 3)


def draw_laser(screen, dir, px, py):
    # 1. חישוב וקטור הכיוון ונקודת ההתחלה (טיפה אחרי מרכז השחקן)
    vx, vy = dir_to_vec(dir)
    offset = 20  # המרחק שבו הלייזר מתחיל מהשחקן

    # מרכז השחקן על המסך
    center_x = px + S.PLAYER_SIZE // 2
    center_y = py + S.PLAYER_SIZE // 2

    # נקודת ההתחלה של הלייזר (מוזזת ב-offset)
    start_x = center_x + vx * offset
    start_y = center_y + vy * offset

    # נקודת הסיום (לפי הטווח המקסימלי)
    end_x = start_x + vx * S.LASER_DIS
    end_y = start_y + vy * S.LASER_DIS

    # --- שלב א': ציור ה"מסגרת" האדומה (החלק החיצוני) ---
    # מציירים קו אדום עבה
    pygame.draw.line(screen, (255, 0, 0), (start_x, start_y), (end_x, end_y), 7)
    # מציירים עיגול אדום בבסיס (טיפה יותר גדול מהלבן)
    pygame.draw.circle(screen, (255, 0, 0), (int(start_x), int(start_y)), 8)

    flicker = random.randint(-1, 2)  # רעידה אקראית
    pygame.draw.line(screen, (255, 0, 0), (start_x, start_y), (end_x, end_y), 7 + flicker)
    pygame.draw.line(screen, (255, 255, 255), (start_x, start_y), (end_x, end_y), 3)
    pygame.draw.circle(screen, (255, 255, 255), (int(start_x), int(start_y)), 5)


def draw_dropped(screen, dropped, cam_x, cam_y):
    for d in dropped:
        dx = d["x"] - cam_x
        dy = d["y"] - cam_y
        weponn = load_inventory_sprites(d["weapon_type"])
        screen.blit(weponn, (dx, dy))


def draw_fps(clock, fps_font, screen):
    fps_val = int(clock.get_fps())
    fps_surface = fps_font.render(f"FPS: {fps_val}", True, (0, 255, 0))
    screen.blit(fps_surface, (S.WINDOW_WIDTH - 100, 20))
    # מחקנו את flip ו-tick מכאן!


def draw_inventori(screen, player):
    x = (S.WINDOW_WIDTH // 2) - 40 * 4
    y = S.WINDOW_HEIGHT - 50
    screen.blit(inventoryb, (x - 1, y - 8))
    for i in range(len(player.weapons)):
        # print(p.current_weapon)
        if player.weapons[i] != 0:
            screen.blit(load_inventory_sprites(player.weapons[i]), (x + 38 * i, y+5))
        if i+1 == player.weapon and player.weapon != 0:
            screen.blit(selectb, (x + 38 * (i) - 2, y - 3))


def draw_inventory_overlay(screen, p, font):
    # 1. יצירת השכבה השקופה (ה-Overlay)
    # יוצרים משטח בגודל כל המסך שתומך בשקיפות
    overlay = pygame.Surface((S.WINDOW_WIDTH, S.WINDOW_HEIGHT), pygame.SRCALPHA)
    # ממלאים אותו בשחור עם רמת שקיפות (160 מתוך 255)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # 2. הגדרת המלבן המרכזי (הפעם הוא יהיה אטום מעט יותר כדי שהטקסט יבלוט)
    inv_w, inv_h = 600, 350
    inv_x = (S.WINDOW_WIDTH - inv_w) // 2
    inv_y = (S.WINDOW_HEIGHT - inv_h) // 2
    inv_rect = pygame.Rect(inv_x, inv_y, inv_w, inv_h)

    # ציור תיבת האינבנטורי - צבע כהה מאוד
    pygame.draw.rect(screen, (30, 30, 30), inv_rect)
    pygame.draw.rect(screen, (0, 255, 255), inv_rect, 3)  # מסגרת טורקיז

    # 3. HP - בתוך המלבן
    health_txt = font.render(f"HP: {int(p.health)}/100", True, (255, 50, 50))
    screen.blit(health_txt, (inv_rect.x + 20, inv_rect.y + 20))

    # 4. משבצות הנשקים
    num_slots = len(p.weapons)
    slot_size = 50
    gap = 10
    total_w = (num_slots * slot_size) + ((num_slots - 1) * gap)
    slots_x = inv_rect.centerx - (total_w // 2)
    slots_y = inv_rect.y + 70

    for i in range(num_slots):
        slot_rect = pygame.Rect(slots_x + (i * (slot_size + gap)), slots_y, slot_size, slot_size)

        # צבע משבצת
        color = (50, 50, 50) if (i + 1) != p.weapon else (80, 80, 40)
        pygame.draw.rect(screen, color, slot_rect)
        pygame.draw.rect(screen, (150, 150, 150), slot_rect, 1)

        if p.weapons[i] != 0:
            img = load_inventory_sprites(p.weapons[i])
            icon = pygame.transform.scale(img, (30, 30))
            ix = slot_rect.x + (slot_size - icon.get_width()) // 2
            iy = slot_rect.y + (slot_size - icon.get_height()) // 2
            screen.blit(icon, (ix, iy))

        if i + 1 == p.weapon:
            pygame.draw.rect(screen, (255, 255, 0), slot_rect, 2)

    # 5. הנשק הגדול (Preview)
    current_w = p.weapons[p.weapon - 1] if p.weapon > 0 else 0
    if current_w != 0:
        big_img = load_inventory_sprites(current_w)
        big_img = pygame.transform.scale(big_img, (130, 130))

        bx = inv_rect.centerx - (big_img.get_width() // 2)
        by = slots_y + slot_size + 30

        # במה קטנה לנשק
        pygame.draw.ellipse(screen, (20, 20, 20), (inv_rect.centerx - 60, by + 120, 120, 20))
        screen.blit(big_img, (bx, by))

        # שם הנשק
        w_names = {'da': 'DAGGER', 'gu': 'GUN', 'h': 'HEALTH', 's': 'SPEED', 'i': 'INVIS', 'b': 'SHIELD', 'la': 'LASER'}
        name_txt = font.render(w_names.get(current_w, "---"), True, (255, 255, 255))
        screen.blit(name_txt, (inv_rect.centerx - (name_txt.get_width() // 2), by + 140))


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


def health_bar_update(health, screen):
    green1 = (S.HEALTH_BAR_SIZE_X / S.PLAYER_HEALTH) * health
    red1 = S.HEALTH_BAR_SIZE_X - green1
    pygame.draw.rect(screen, "green", (20, 20, green1, S.HEALTH_BAR_SIZE_Y))
    pygame.draw.rect(screen, "red", (20 + green1, 20, red1, S.HEALTH_BAR_SIZE_Y))


def S_health_bar_update(health, screen, x, y, maxHP):
    green1 = (S.S_HEALTH_BAR_SIZE_X / maxHP) * health
    red1 = S.S_HEALTH_BAR_SIZE_X - green1
    pygame.draw.rect(screen, "green", (x, y - 40, green1, S.S_HEALTH_BAR_SIZE_Y))
    pygame.draw.rect(screen, "red", (x + green1, y - 40, red1, S.S_HEALTH_BAR_SIZE_Y))


def load(name: str, rotations_dir) -> pygame.Surface:
    path = os.path.join(rotations_dir, name)
    img = pygame.image.load(path).convert_alpha()
    if img.get_width() != S.PLAYER_SIZE or img.get_height() != S.PLAYER_SIZE:
        img = pygame.transform.scale(img, (S.PLAYER_SIZE, S.PLAYER_SIZE))
    return img


def load_player_sprites(group):
    if group == 1:
        rotations_dir = os.path.join(os.path.dirname(__file__), "sprites/white-player-rotations")
    else:
        rotations_dir = os.path.join(os.path.dirname(__file__), "sprites/black-player-rotations")

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
    base_path = os.path.join(os.path.dirname(__file__), S.dagger)
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


def load_inventory_sprites(i):
    if i == 'da' or i == 1:
        i = bolbolb
    elif i == 'gu' or i == 2:
        i = gunb
    elif i == 'h' or i == 3:
        i = lcon1b
    elif i == 's' or i == 4:
        i = lcon5b
    elif i == 'i' or i == 5:
        i = lcon28b
    elif i == 'b' or i == 6:
        i = scissorsb
    elif i == 'la' or i == 7:
        i = lazerb
    else:
        i = poopb
    return i


def load_fart_sprites() -> dict[int, pygame.Surface]:
    base_path = os.path.join(os.path.dirname(__file__), S.fart)
    base = pygame.image.load(base_path).convert_alpha()

    if base.get_width() != S.TILE_SIZE or base.get_height() != S.TILE_SIZE:
        base = pygame.transform.scale(base, (S.TILE_SIZE, S.TILE_SIZE))

    # base = NORTH (dir 7)
    return {
        2: base,
        3: rot(base, -45),
        4: rot(base, -90),
        5: rot(base, -135),
        6: rot(base, 180),
        7: rot(base, 135),
        8: rot(base, 90),
        1: rot(base, 45),
    }


def load_enemy_sprites(group):
    if group == 1:
        rotationsenemy_dir = os.path.join(os.path.dirname(__file__), "sprites\\red-enemy-rotations")
    else:
        rotationsenemy_dir = os.path.join(os.path.dirname(__file__), "sprites\\green-enemy-rotations")

    return {
        1: load("right.png", rotationsenemy_dir),
        2: load("down_right.png", rotationsenemy_dir),
        3: load("down.png", rotationsenemy_dir),
        4: load("down_left.png", rotationsenemy_dir),
        5: load("left.png", rotationsenemy_dir),
        6: load("up_left.png", rotationsenemy_dir),
        7: load("up.png", rotationsenemy_dir),
        8: load("up_right.png", rotationsenemy_dir),
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
    x, y, dir = struct.unpack_from('!iib', pkStruct, 1)
    player.tp(x, y, dir)


def get_inputs():
    inputs = {
        "w": 0,
        "a": 0,
        "s": 0,
        "d": 0,
        "sf": 0,
        "sp": 0,
        "i": 0,
        "e": 0,
        "t": 0,
        "f": 0,
    }
    pressedM = False
    pressedA = 0
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
    if keys[pygame.K_i]:
        inputs["i"] = 1
    if keys[pygame.K_e]:
        inputs["e"] = 1
    if keys[pygame.K_t]:
        inputs["t"] = 1
    if keys[pygame.K_f]:
        inputs["f"] = 1
    if keys[pygame.K_1]:
        pressedA = 1
    elif keys[pygame.K_2]:
        pressedA = 2
    elif keys[pygame.K_3]:
        pressedA = 3
    elif keys[pygame.K_4]:
        pressedA = 4
    elif keys[pygame.K_5]:
        pressedA = 5
    elif keys[pygame.K_6]:
        pressedA = 6
    elif keys[pygame.K_7]:
        pressedA = 7
    elif keys[pygame.K_8]:
        pressedA = 8

    return inputs, pressedM, pressedA


def sendAttack(self, boo):
    pk = struct.pack('!b16sb', S.CMDS["ATTACK"], self.pid.encode("utf-8"), boo)  # b is signed byte
    self.client.send(self.connections[self.iControl], pk)
    if self.iInActive != None:
        self.client.send(self.connections[self.iInActive], pk)


def sendFart(self, boo):
    pk = struct.pack('!b16sb', S.CMDS["FART"], self.pid.encode("utf-8"), boo)  # b is signed byte
    self.client.send(self.connections[self.iControl], pk)
    if self.iInActive != None:
        self.client.send(self.connections[self.iInActive], pk)


if __name__ == "__main__":
    c = Client()
    asyncio.run(c.run())
