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

poopb=pygame.image.load(S.poop).convert_alpha()
inventoryb = pygame.image.load(S.inventory1).convert_alpha()
selectb = pygame.image.load(S.select1).convert_alpha()
bolbolb = pygame.image.load(S.bolbol).convert_alpha()
lcon28b = pygame.image.load(S.lcon28).convert_alpha()
lcon1b = pygame.image.load(S.lcon1).convert_alpha()
lcon5b = pygame.image.load(S.lcon5).convert_alpha()
scissorsb = pygame.image.load(S.scissors).convert_alpha()
lazerb = pygame.image.load(S.lazer).convert_alpha()
gunb = pygame.image.load(S.gun).convert_alpha()
class MyClient:

    def __init__(self):
        self.client = None
        self.pid = None
        self.connections = []
        self.iControl = 0
        self.iInActive = None
        self.running = True
        self.players = []  # list of other players which are relevant works in [i]={"x":...,...}
        self.bullets = []
        self.dropped = []
        self.open = False
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
            self.player.weapon = 1

            pk = struct.pack("!b16s", S.CMDS["HELLO"], self.pid.encode("utf-8"))
            self.client.send(self.connections[self.iControl], pk)
        elif (cmd == S.CMDS["MOVE"]):
            moveOffPackt(data, self.player)

        elif (cmd == S.CMDS["OVERLAP"]):
            # SEND POS TO SECOND SERVER
            if self.iInActive != None:
                pk = struct.pack("!b16shhh", S.CMDS["POS_DONT_RESPOND"], self.pid.encode("utf-8"), self.player.x,
                                 self.player.y, self.player.dir)
                self.client.send(self.connections[self.iInActive], pk)
            else:
                dir = struct.unpack_from('!1s', data, 1)[0].decode("utf-8")
                if (dir == "r"):
                    self.iInActive = self.iControl + 1
                elif (dir == "l"):
                    self.iInActive = self.iControl - 1

                print(self.iInActive)

                pk = struct.pack("!b16shhhhbbb", S.CMDS["ADD_ME"], self.pid.encode("utf-8"), self.player.x,
                                 self.player.y,
                                 self.player.dir, self.player.health, self.player.att, self.player.weapon, self.player.fartp)
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
                fart, invi, laser = struct.unpack_from('!bbb', data, 1)
                self.player.fartp = fart
                self.player.invisible = invi
                self.player.laser = laser
                if fart == 1:
                    print("farting")
                self.players = []
                count = struct.unpack_from('!h', data, 4)[0]
                for i in range(count):
                    offset = 6+12*i
                    x, y, dir, health, att, weapon, fart, invi = struct.unpack_from('!hhhhbbbb', data, offset)
                    self.players.append({"x":x,"y": y, "dir": dir, "hp": health, "att": att, "weapon": weapon, "fart": fart, "invi": invi})
                offset = 6+12*count
                self.bullets = []
                countb = struct.unpack_from('!h', data, offset)[0]
                offset += 2
                for i in range(countb):
                    bx, by = struct.unpack_from('!hh', data, offset)
                    self.bullets.append({"x":bx, "y":by})
                    offset+=4
                    print("bullet in ", bx, " ", by)
                offset = 8+12*count+4*countb
                self.dropped = []
                counti = struct.unpack_from('!h', data, offset)[0]
                offset += 2
                for i in range(counti):
                    ix, iy, iw = struct.unpack_from('!hhb', data, offset)
                    self.dropped.append({"x":ix, "y":iy, "weapon_type":iw})
                    offset+=5

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
            self.player.weapons = S.INVENTORI
            if self.iInActive != None:
                pk = struct.pack("!b16s", S.CMDS["REMOVE_ME"], self.pid.encode("utf-8"))
                self.client.send(self.connections[self.iInActive], pk)
        elif (cmd == S.CMDS["DELETE_ITEM"]):
            index = struct.unpack_from('!b', data, 1)[0]
            self.player.weapons[index] = 0
        elif (cmd == S.CMDS["FART_READY"]):
            self.player.fart_ready = 1
        elif (cmd == S.CMDS["ADD_ITEM"]):
            weapon_type, i = struct.unpack_from('!bb', data, 1)
            weapon = S.INVENTORY_MAP[weapon_type]

            self.player.weapons[i] = weapon


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
        FARTS = load_fart_sprites()
        DEFAULT_FARTS = FARTS[3]
        clock = pygame.time.Clock()

        while self.running:
            # Check for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # KEYS (GET INPUTS)
            inputs, pressedM, pressedA, fart = getInputs()
            # SEND INPUTS
            if inputs["sp"] == 1: #attacking...
                if self.player.att == 0:
                    sendAttack(self, 1)
                    self.player.att = 1
            elif self.player.att == 1:
                sendAttack(self, 0)
                self.player.att = 0

            if pressedA !=0:
                if self.player.weapon != pressedA:
                    self.player.weapon = pressedA
                    pk = struct.pack("!b16sb", S.CMDS["CHANGE_WEAPON"], self.pid.encode("utf-8"), pressedA)
                    self.client.send(self.connections[self.iControl], pk)
                    if self.iInActive != None:
                        self.client.send(self.connections[self.iInActive], pk)

            if fart == 1: #farting...
                if self.player.fartp == 0 and self.player.fart_ready == 1:
                    self.player.fart_ready = 0
                    print("sent fart")
                    sendFart(self, 1)

            if inputs["i"] == 1: #toggle inventory
                self.open = not self.open
            if inputs["e"] == 1:
                pk = struct.pack("!b16s", S.CMDS["PICKUP_ITEM"], self.pid.encode("utf-8"))
                self.client.send(self.connections[self.iControl], pk)
            if (pressedM): #movement related inputs
                self.sendInputs(inputs)


            # DRAW
            self.draw_frame(self.screen, S.MAP_WIDTH, S.MAP_HEIGHT, DEFAULT_SPRITE1, SPRITES1 , DEFAULT_DAGGER, DAGGERS, DEFAULT_FARTS, FARTS, clock)
            pygame.display.flip()
            clock.tick(60)

            await asyncio.sleep(1 / 60)

        pygame.quit()

    def sendInputs(self, inputs):
        xAxisDirection = inputs['d'] - inputs['a']
        yAxisDirection = inputs['s'] - inputs['w']
        pk = struct.pack('!b16sbbb', S.CMDS["MOVE"], self.pid.encode("utf-8"), xAxisDirection, yAxisDirection, inputs["sf"])  # b is signed byte
        self.client.send(self.connections[self.iControl], pk)

    def draw_frame(self, screen, map_w, map_h, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER, DAGGERS, DEFAULT_FARTS, FARTS, clock):
        screen.fill((0, 0, 0))

        cam_x, cam_y = camera_from_pos(self.player.x, self.player.y, map_w, map_h)

        draw_map(screen, MAP, cam_x, cam_y, S.WINDOW_WIDTH, S.WINDOW_HEIGHT)
        draw_bullets(screen, self.bullets, cam_x, cam_y)
        draw_dropped(screen, self.dropped, cam_x, cam_y)
        draw_players(screen, self.player, self.players, cam_x, cam_y, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER, DAGGERS, DEFAULT_FARTS, FARTS)

        fps_font = pygame.font.SysFont("Arial", 20, bold=True)
        draw_fps(clock, fps_font,screen)
        if self.open:
            draw_inventory_overlay(screen,self.player, fps_font)
        else:
            draw_inventori(screen, self.player)

def draw_players(screen, player, players, cam_x, cam_y, DEFAULT_SPRITE1, SPRITES1, DEFAULT_DAGGER, DAGGERS, DEFAULT_FARTS, FARTS):
    # DRAW OTHER PLAYERS
    for p in players:
        px = int(p["x"] - cam_x - S.PLAYER_SIZE // 2)
        py = int(p["y"] - cam_y - S.PLAYER_SIZE // 2)
        if p["invi"] == 0:
            sprite = SPRITES1.get(p["dir"], DEFAULT_SPRITE1)
            screen.blit(sprite, (px, py))
            S_health_bar_update(p["hp"], screen, px, py)

        if p["att"]==1 and p["weapon"]==1: #daggers
            print("A PLAYER IS daggering")
            d = p["dir"]
            vx, vy = dir_to_vec(d)
            dagger_x = int((p["x"] + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
            dagger_y = int((p["y"] + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
            screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))
        if p["att"]==1 and p["weapon"]==7:
            draw_laser(screen, p["dir"], px, py)
        if p["fart"] == 1:
            d = p["dir"]
            vx, vy = dir_to_vec(d)
            vx,vy=vx*(-1),vy*(-1)
            fart_x = int((p["x"] + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
            fart_y = int((p["y"] + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
            screen.blit(FARTS.get(d, DEFAULT_FARTS), (fart_x, fart_y))


    # DRAW OWN PLAYER
    px = int(player.x - cam_x - S.PLAYER_SIZE // 2)
    py = int(player.y - cam_y - S.PLAYER_SIZE // 2)
    if player.invisible == 0:
        sprite = SPRITES1.get(player.dir, DEFAULT_SPRITE1)
        screen.blit(sprite, (px, py))

    if player.att == 1 and player.weapons[player.weapon-1] == 'da':  # daggers
        d = player.dir
        vx, vy = dir_to_vec(d)
        dagger_x = int((player.x + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
        dagger_y = int((player.y + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
        screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))

    if player.att == 1 and player.laser == 1:
        draw_laser(screen, player.dir, px, py)

    if player.fartp ==1:
        d = player.dir
        vx, vy = dir_to_vec(d)
        vx,vy=vx*(-1),vy*(-1)
        fart_x = int((player.x + vx * S.TILE_SIZE) - cam_x - S.TILE_SIZE // 2)
        fart_y = int((player.y + vy * S.TILE_SIZE) - cam_y - S.TILE_SIZE // 2)
        screen.blit(FARTS.get(d, DEFAULT_FARTS), (fart_x, fart_y))

    if player.fart_ready == 1:
        x = S.WINDOW_WIDTH - 50
        y = S.WINDOW_HEIGHT - 50
        screen.blit(poopb, (x, y))

    health_bar_update(player.health, screen)

def draw_bullets(screen, bullets, cam_x, cam_y):
    for b in bullets:
        bx = b["x"] - cam_x
        by = b["y"] - cam_y

        pygame.draw.circle(screen, "red", (bx, by), S.BULLET_SIZE)
        pygame.draw.circle(screen, "orange", (bx, by), S.BULLET_SIZE-1)
        pygame.draw.circle(screen, "yellow", (bx, by), S.BULLET_SIZE-3)

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
    screen.blit(fps_surface, (S.WINDOW_WIDTH-100, 20))
    # מחקנו את flip ו-tick מכאן!

def draw_inventori(screen,player):
    x = (S.WINDOW_WIDTH//2)-40*4
    y = S.WINDOW_HEIGHT - 50
    screen.blit(inventoryb, (x-1, y-8))
    for i in range(len(player.weapons)):
        #print(p.current_weapon)
        if player.weapons[i] != 0:

            screen.blit(load_inventory_sprites(player.weapons[i]), (x+38*i, y))
        if i== player.weapon and player.weapon != 0:
            screen.blit(selectb, (x + 38*(i-1) -2, y - 3))
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
    elif i == 'gu' or  i == 2:
        i = gunb
    elif i == 'h' or i == 3:
        i = lcon1b
    elif i == 's' or i == 4:
        i = lcon5b
    elif i == 'i' or i == 5:
        i = lcon28b
    elif i == 'b' or i == 6:
        i = scissorsb
    elif i =='la' or i == 7:
        i=lazerb
    else : i = poopb
    return  i

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
        "i": 0,
        "e": 0,
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
    fart = int(keys[pygame.K_f])

    return inputs, pressedM, pressedA, fart

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
    c = MyClient()
    asyncio.run(c.run())
