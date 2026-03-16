import os
import socket
import struct
import sys
import math
from Player import PlayerData, handle_input, health_bar_update, S_health_bar_update
from map import draw_map
from Bullet import *
from map_data import *
from DroppedWeapon import *

poopb=pygame.image.load(poop).convert_alpha()
inventoryb = pygame.image.load(inventory1).convert_alpha()
selectb = pygame.image.load(select1).convert_alpha()
bolbolb = pygame.image.load(bolbol).convert_alpha()
lcon28b = pygame.image.load(lcon28).convert_alpha()
lcon1b = pygame.image.load(lcon1).convert_alpha()
lcon5b = pygame.image.load(lcon5).convert_alpha()
scissorsb = pygame.image.load(scissors).convert_alpha()
lazerb = pygame.image.load(lazer).convert_alpha()
gunb = pygame.image.load(gun).convert_alpha()
# ---------- network helpers ----------
def qc3_pack(cmd: int, payload: bytes = b"") -> bytes:
    body = bytes([cmd]) + payload
    return struct.pack("!I", len(body)) + body


class QC3Stream:
    def __init__(self):
        self.buf = bytearray()

    def feed(self, data: bytes):
        self.buf.extend(data)

    def pop_messages(self):
        msgs = []
        while True:
            if len(self.buf) < 4:
                break
            (length,) = struct.unpack("!I", self.buf[:4])
            if len(self.buf) < 4 + length:
                break
            body = bytes(self.buf[4:4 + length])
            del self.buf[:4 + length]
            cmd = body[0]
            payload = body[1:]
            msgs.append((cmd, payload))
        return msgs


# ---------- camera ----------
def camera_from_pos(x, y, map_w, map_h):
    cam_x = int(x - WINDOW_W // 2)
    cam_y = int(y - WINDOW_H // 2)
    cam_x = max(0, min(map_w - WINDOW_W, cam_x))
    cam_y = max(0, min(map_h - WINDOW_H, cam_y))
    return cam_x, cam_y


def rot(img, deg):
    return pygame.transform.rotate(img, deg)


def load(name: str, rotations_dir) -> pygame.Surface:
    path = os.path.join(rotations_dir, name)
    img = pygame.image.load(path).convert_alpha()
    if img.get_width() != PLAYER_SIZE or img.get_height() != PLAYER_SIZE:
        img = pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
    return img


def load_player_sprites(group):
    if group == 1:
        rotations_dir = os.path.join(os.path.dirname(__file__), "rotations")
    else:
        rotations_dir = os.path.join(os.path.dirname(__file__), "rotations1")

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

def load_inventory_sprites(i):
    if i == 1:
        i = bolbolb
    elif i == 2 :
        i = gunb
    elif i == 3:
        i = lcon1b
    elif i == 4:
        i = lcon5b
    elif i == 5:
        i = lcon28b
    elif i == 6:
        i = scissorsb
    elif i ==7:
        i=lazerb
    else : i = poopb
    return  i


def load_dagger_sprites() -> dict[int, pygame.Surface]:
    base_path = os.path.join(os.path.dirname(__file__), "DAGGER-NORTH.png")
    base = pygame.image.load(base_path).convert_alpha()

    if base.get_width() != TILE_SIZE or base.get_height() != TILE_SIZE:
        base = pygame.transform.scale(base, (TILE_SIZE, TILE_SIZE))

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

def load_fart_sprites() -> dict[int, pygame.Surface]:
    base_path = os.path.join(os.path.dirname(__file__), "FARTS.png")
    base = pygame.image.load(base_path).convert_alpha()

    if base.get_width() != TILE_SIZE or base.get_height() != TILE_SIZE:
        base = pygame.transform.scale(base, (TILE_SIZE, TILE_SIZE))

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


# ---------- extracted logic (no state dict) ----------

def send_input(sock) -> bool:
    dx, dy, dspeed, dire, attack, current_weapon ,pickup,fart,teleport,outo= handle_input()

    try:
        sock.sendall(qc3_pack(CMD_INPUT, struct.pack("!bbbbbbbbbb", dx, dy, dspeed, dire, attack, current_weapon,pickup,fart,teleport,outo)))
        return True
    except BlockingIOError:
        return True
    except Exception as e:
        print("Send error:", e)
        return False

def welcome(payload):
    if len(payload) != 12:
        return None
    return struct.unpack("!III", payload)  # my_id, map_w, map_h

def update_players(payload,off, players):
    if off >= len(payload):
        return

    count = payload[off]
    active_ids = set()
    off += 1

    for _ in range(count):
        if off + 31 > len(payload):
            break

        pid, x, y, health, pdire, patt, pweapon, pgroup,fartp ,fcool,tcool,invesibel,cw,la= struct.unpack("!IIIHHBBBBIIBBB", payload[off:off + 31])
        off += 31
        active_ids.add(pid)
        #!@#$%^&*()_
        print (pweapon)
        count = payload[off]
        wepons = list()
        off += 1
        for _ in range(count):
            if off + 1 > len(payload):
                break
            W = struct.unpack("!B", payload[off:off + 1])[0]
            off += 1
            wepons.append(W)




        if pid not in players:
            players[pid] = PlayerData(pid, x, y, pdire, pgroup, 0,fcool,tcool)

        players[pid].update_from_server(x, y, health, pdire, patt, pweapon, pgroup,fartp,fcool,tcool,invesibel,wepons,cw,la)
    return off, active_ids

def remove_inactive_players(players, active_ids):
    for pid_to_remove in list(players.keys()):
        if pid_to_remove not in active_ids:
            del players[pid_to_remove]

def update_bullets(payload, off, bullets11):
    if off >= len(payload):
        return

    count1 = payload[off]
    off += 1

    active_bull = set()

    for _ in range(count1):
        if off + 14 > len(payload):
            break

        bullet_x, bullet_y, bullet_id, dirb = struct.unpack("!iiHi", payload[off:off + 14])
        off += 14

        active_bull.add(bullet_id)

        if bullet_id not in bullets11:
            bullets11[bullet_id] = Bullet(bullet_id, bullet_x, bullet_y, dirb, 0, 0)

        bullets11[bullet_id].update_from_server_bull(bullet_x, bullet_y)

    for bull_to_remove in list(bullets11.keys()):
        if bull_to_remove not in active_bull:
            del bullets11[bull_to_remove]
    return off

def update_drop(payload,off, dropped):
    if off >= len(payload):
        return

    count1 = payload[off]
    off += 1

    dropped_rn = set()

    for _ in range(count1):
        if off + 9 > len(payload):
            break
        item_id, x, y, type = struct.unpack("!IHHB", payload[off:off + 9])
        off += 9
        dropped_rn.add(item_id)

        # עדכון או יצירת החפץ ברשימה של הקליינט
        if item_id not in dropped:
            # כאן אנחנו יוצרים את הישות החדשה (וודא שיש לך קלאס כזה בקליינט)
            dropped[item_id] = DroppedWeapon(item_id, x, y, type)
        else:
            dropped[item_id].x = x
            dropped[item_id].y = y

        # מחיקת חפצים שכבר לא קיימים בשרת (מישהו הרים אותם)
    for oid in list(dropped.keys()):
        if oid not in dropped_rn:
            del dropped[oid]
    return off

def handle_cmd(payload, players, bullets,dropped):
    if not payload:
        return
    off =0
    off = update_drop(payload,off, dropped)
    off, active_ids = update_players(payload,off, players)
    remove_inactive_players(players, active_ids)
    off = update_bullets(payload, off, bullets)

def recv_network(sock, stream, players, bullets,dropped, my_id, map_w, map_h):
    try:
        data = sock.recv(4096)
        if not data:
            return True, my_id, map_w, map_h

        stream.feed(data)
        for cmd, payload in stream.pop_messages():
            if cmd == CMD_WELCOME:
                welcomed = welcome(payload)
                if welcomed is not None:
                    my_id, map_w, map_h = welcomed

            elif cmd == CMD_STATE:
                handle_cmd(payload, players, bullets,dropped)

        return True, my_id, map_w, map_h

    except BlockingIOError:
        return True, my_id, map_w, map_h
    except Exception as e:
        print("Network error:", e)
        return False, my_id, map_w, map_h

def draw_bullets(screen, bullets, cam_x, cam_y):
    for _, b in bullets.items():
        bx = b.x - cam_x
        by = b.y - cam_y
        pygame.draw.circle(screen, "yellow", (bx, by), BULLET_SIZE)

def draw_dropped(screen, dropped, DAGGERS,DEFAULT_DAGGER, cam_x, cam_y):
    for _, d in dropped.items():
        dx = d.x - cam_x
        dy = d.y - cam_y
        print (int(d.id), int(d.x), int(d.y), d.weapon_type)
        weponn = load_inventory_sprites(d.weapon_type)
        screen.blit(weponn, (dx, dy))

def draw_players(screen, players, my_id, cam_x, cam_y, SPRITES1, DEFAULT_SPRITE1, SPRITES2, DEFAULT_SPRITE2, DAGGERS, DEFAULT_DAGGER,FARTS,DEFAULT_FARTS):
    for pid, p in players.items():
        px = int(p.x - cam_x - PLAYER_SIZE // 2)
        py = int(p.y - cam_y - PLAYER_SIZE // 2)

        if p.group == 1:
            sprite = SPRITES1.get(p.dir, DEFAULT_SPRITE1)
        else:
            sprite = SPRITES2.get(p.dir, DEFAULT_SPRITE2)
        if p.invesebel==0:
            screen.blit(sprite, (px, py))

        if p.attack == 1 and p.current_weapon == 1:
            d = p.dir if p.dir != 0 else 3
            vx, vy = dir_to_vec(d)
            dagger_x = int((p.x + vx * TILE_SIZE) - cam_x - TILE_SIZE // 2)
            dagger_y = int((p.y + vy * TILE_SIZE) - cam_y - TILE_SIZE // 2)
            screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))

        if p.fartp ==1:
            d = p.dir if p.dir != 0 else 3
            vx, vy = dir_to_vec(d)
            vx,vy=vx*(-1),vy*(-1)
            fart_x = int((p.x + vx * TILE_SIZE) - cam_x - TILE_SIZE // 2)
            fart_y = int((p.y + vy * TILE_SIZE) - cam_y - TILE_SIZE // 2)
            screen.blit(FARTS.get(d, DEFAULT_FARTS), (fart_x, fart_y))

        if pid == my_id:
            health_bar_update(p.health, screen)
            if p.f_cooldown == 0:
                x = WINDOW_W - 50
                y = WINDOW_H - 50
                screen.blit(poopb, (x, y))

            if p.t_cooldown == 0:
                x = WINDOW_W - 80
                y = WINDOW_H - 50
                screen.blit(poopb, (x, y))

        else:
            S_health_bar_update(p.health, screen, px, py)

        if p.laser_event == 1:
            # 1. חישוב וקטור הכיוון ונקודת ההתחלה (טיפה אחרי מרכז השחקן)
            vx, vy = dir_to_vec(p.dir)
            offset = 20  # המרחק שבו הלייזר מתחיל מהשחקן

            # מרכז השחקן על המסך
            center_x = px + PLAYER_SIZE // 2
            center_y = py + PLAYER_SIZE // 2

            # נקודת ההתחלה של הלייזר (מוזזת ב-offset)
            start_x = center_x + vx * offset
            start_y = center_y + vy * offset

            # נקודת הסיום (לפי הטווח המקסימלי)
            end_x = start_x + vx * LASER_DIS
            end_y = start_y + vy * LASER_DIS

            # --- שלב א': ציור ה"מסגרת" האדומה (החלק החיצוני) ---
            # מציירים קו אדום עבה
            pygame.draw.line(screen, (255, 0, 0), (start_x, start_y), (end_x, end_y), 7)
            # מציירים עיגול אדום בבסיס (טיפה יותר גדול מהלבן)
            pygame.draw.circle(screen, (255, 0, 0), (int(start_x), int(start_y)), 8)

            flicker = random.randint(-1, 2)  # רעידה אקראית
            pygame.draw.line(screen, (255, 0, 0), (start_x, start_y), (end_x, end_y), 7 + flicker)
            pygame.draw.line(screen, (255, 255, 255), (start_x, start_y), (end_x, end_y), 3)
            pygame.draw.circle(screen, (255, 255, 255), (int(start_x), int(start_y)), 5)
def draw_fps(clock, fps_font, screen):
    fps_val = int(clock.get_fps())
    fps_surface = fps_font.render(f"FPS: {fps_val}", True, (0, 255, 0))
    screen.blit(fps_surface, (WINDOW_W-100, 20))
    # מחקנו את flip ו-tick מכאן!
def draw_inventori(screen,players,m):
    x = (WINDOW_W//2)-40*4
    y = WINDOW_H - 50
    for pid, p in players.items():
        if pid == m:
            screen.blit(inventoryb, (x-1, y-8))
            for i in range(len(p.weapons)):
                #print(p.current_weapon)
                if p.weapons[i] != 0:

                    screen.blit(load_inventory_sprites(p.weapons[i]), (x+38*i, y))
                if i== p.ccw and p.ccw != 0 :
                    screen.blit(selectb, (x + 38*(i-1) -2, y - 3))
def draw_inventory_overlay(screen, players, my_id, font):
    if my_id not in players:
        return
    p = players[my_id]

    # 1. יצירת השכבה השקופה (ה-Overlay)
    # יוצרים משטח בגודל כל המסך שתומך בשקיפות
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    # ממלאים אותו בשחור עם רמת שקיפות (160 מתוך 255)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # 2. הגדרת המלבן המרכזי (הפעם הוא יהיה אטום מעט יותר כדי שהטקסט יבלוט)
    inv_w, inv_h = 600, 350
    inv_x = (WINDOW_W - inv_w) // 2
    inv_y = (WINDOW_H - inv_h) // 2
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
        color = (50, 50, 50) if (i + 1) != p.ccw else (80, 80, 40)
        pygame.draw.rect(screen, color, slot_rect)
        pygame.draw.rect(screen, (150, 150, 150), slot_rect, 1)

        if p.weapons[i] != 0:
            img = load_inventory_sprites(p.weapons[i])
            icon = pygame.transform.scale(img, (30, 30))
            ix = slot_rect.x + (slot_size - icon.get_width()) // 2
            iy = slot_rect.y + (slot_size - icon.get_height()) // 2
            screen.blit(icon, (ix, iy))

        if i + 1 == p.ccw:
            pygame.draw.rect(screen, (255, 255, 0), slot_rect, 2)

    # 5. הנשק הגדול (Preview)
    current_w = p.weapons[p.ccw - 1] if p.ccw > 0 else 0
    if current_w != 0:
        big_img = load_inventory_sprites(current_w)
        big_img = pygame.transform.scale(big_img, (130, 130))

        bx = inv_rect.centerx - (big_img.get_width() // 2)
        by = slots_y + slot_size + 30

        # במה קטנה לנשק
        pygame.draw.ellipse(screen, (20, 20, 20), (inv_rect.centerx - 60, by + 120, 120, 20))
        screen.blit(big_img, (bx, by))

        # שם הנשק
        w_names = {1: 'BOLBOL', 2: 'GUN', 3: 'HEALTH', 4: 'SPEED', 5: 'INVIS', 6: 'SHIELD', 7: 'LASER'}
        name_txt = font.render(w_names.get(current_w, "---"), True, (255, 255, 255))
        screen.blit(name_txt, (inv_rect.centerx - (name_txt.get_width() // 2), by + 140))
def draw_frame(screen, players, bullets,dropped, my_id, map_w, map_h, SPRITES1, DEFAULT_SPRITE1, SPRITES2, DEFAULT_SPRITE2, DAGGERS, DEFAULT_DAGGER,FARTS,DEFAULT_FARTS,clock , fps_font,open):
    screen.fill((0, 0, 0))

    if my_id is None or my_id not in players:
        return

    me = players[my_id]
    cam_x, cam_y = camera_from_pos(me.x, me.y, map_w, map_h)

    draw_map(screen, MAP, cam_x, cam_y, WINDOW_W, WINDOW_H)
    draw_dropped(screen, dropped, DAGGERS, DEFAULT_DAGGER, cam_x, cam_y)
    draw_bullets(screen, bullets, cam_x, cam_y)
    draw_players(screen, players, my_id, cam_x, cam_y, SPRITES1, DEFAULT_SPRITE1, SPRITES2, DEFAULT_SPRITE2, DAGGERS, DEFAULT_DAGGER,FARTS,DEFAULT_FARTS)

    draw_fps(clock , fps_font ,screen)
    if open:
        draw_inventory_overlay(screen, players, my_id, fps_font)
    else :
        draw_inventori(screen, players, my_id)
# ---------- main ----------
def run():
    pygame.init()
    pygame.display.set_caption("QC3 Client")
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    inventory_open = False
    pygame.font.init()

    fps_font = pygame.font.SysFont("Arial", 20, bold=True)
    # load sprites
    SPRITES1 = load_player_sprites(1)
    DEFAULT_SPRITE1 = SPRITES1[3]
    SPRITES2 = load_player_sprites(2)
    DEFAULT_SPRITE2 = SPRITES2[3]
    DAGGERS = load_dagger_sprites()
    DEFAULT_DAGGER = DAGGERS[3]
    FARTS = load_fart_sprites()
    DEFAULT_FARTS = FARTS[3]
    # connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, PORT))
    sock.setblocking(False)

    stream = QC3Stream()

    try:
        sock.sendall(qc3_pack(CMD_JOIN))
    except Exception:
        pass

    my_id = None
    map_w = MAP_W
    map_h = MAP_H
    players = {}
    bullets = {}
    dropped = {}
    running = True
    while running:
        # events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:  # לחיצה על I
                    inventory_open = not inventory_open
        # input
        if not send_input(sock):
            running = False

        # network
        ok, my_id, map_w, map_h = recv_network(sock, stream, players, bullets,dropped, my_id, map_w, map_h)
        if not ok:
            running = False

        # draw
        draw_frame(screen, players, bullets,dropped, my_id, map_w, map_h, SPRITES1, DEFAULT_SPRITE1, SPRITES2, DEFAULT_SPRITE2, DAGGERS, DEFAULT_DAGGER,FARTS,DEFAULT_FARTS,clock, fps_font,inventory_open)

        pygame.display.flip()
        clock.tick(60)


    try:
        sock.close()
    except Exception:
        pass

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()