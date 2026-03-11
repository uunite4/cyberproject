import os
import socket
import struct
import sys

from Player import PlayerData, handle_input, health_bar_update, S_health_bar_update
from map import draw_map
from Bullet import *
from map_data import *
from DroppedWeapon import *
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
    dx, dy, dspeed, dire, attack, current_weapon ,pickup,fart= handle_input()

    try:
        sock.sendall(qc3_pack(CMD_INPUT, struct.pack("!bbbbbbbb", dx, dy, dspeed, dire, attack, current_weapon,pickup,fart)))
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
        if off + 19 > len(payload):
            break

        pid, x, y, health, pdire, patt, pweapon, pgroup = struct.unpack(
            "!IIIHHBBB", payload[off:off + 19]
        )
        off += 19
        active_ids.add(pid)

        if pid not in players:
            players[pid] = PlayerData(pid, x, y, pdire, pgroup, 0)

        players[pid].update_from_server(x, y, health, pdire, patt, pweapon, pgroup)
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
        if d.weapon_type == 1:
            screen.blit(DAGGERS.get(3, DEFAULT_DAGGER), (dx, dy))
        elif d.weapon_type == 2:
            pygame.draw.circle(screen, "yellow", (dx, dy), BULLET_SIZE)

def draw_players(screen, players, my_id, cam_x, cam_y, SPRITES1, DEFAULT_SPRITE1, SPRITES2, DEFAULT_SPRITE2, DAGGERS, DEFAULT_DAGGER):
    for pid, p in players.items():
        px = int(p.x - cam_x - PLAYER_SIZE // 2)
        py = int(p.y - cam_y - PLAYER_SIZE // 2)

        if p.group == 1:
            sprite = SPRITES1.get(p.dir, DEFAULT_SPRITE1)
        else:
            sprite = SPRITES2.get(p.dir, DEFAULT_SPRITE2)

        screen.blit(sprite, (px, py))

        if p.attack == 1 and p.current_weapon == 1:
            d = p.dir if p.dir != 0 else 3
            vx, vy = dir_to_vec(d)
            dagger_x = int((p.x + vx * TILE_SIZE) - cam_x - TILE_SIZE // 2)
            dagger_y = int((p.y + vy * TILE_SIZE) - cam_y - TILE_SIZE // 2)
            screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))

        if pid == my_id:
            health_bar_update(p.health, screen)
        else:
            S_health_bar_update(p.health, screen, px, py)



def draw_frame(screen, players, bullets,dropped, my_id, map_w, map_h, SPRITES1, DEFAULT_SPRITE1, SPRITES2, DEFAULT_SPRITE2, DAGGERS, DEFAULT_DAGGER):
    screen.fill((0, 0, 0))

    if my_id is None or my_id not in players:
        return

    me = players[my_id]
    cam_x, cam_y = camera_from_pos(me.x, me.y, map_w, map_h)

    draw_map(screen, MAP, cam_x, cam_y, WINDOW_W, WINDOW_H)
    draw_dropped(screen, dropped, DAGGERS, DEFAULT_DAGGER, cam_x, cam_y)
    draw_bullets(screen, bullets, cam_x, cam_y)
    draw_players(screen, players, my_id, cam_x, cam_y, SPRITES1, DEFAULT_SPRITE1, SPRITES2, DEFAULT_SPRITE2, DAGGERS, DEFAULT_DAGGER)


# ---------- main ----------
def run():
    pygame.init()
    pygame.display.set_caption("QC3 Client")
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))

    # load sprites
    SPRITES1 = load_player_sprites(1)
    DEFAULT_SPRITE1 = SPRITES1[3]
    SPRITES2 = load_player_sprites(2)
    DEFAULT_SPRITE2 = SPRITES2[3]
    DAGGERS = load_dagger_sprites()
    DEFAULT_DAGGER = DAGGERS[3]

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

        # input
        if not send_input(sock):
            running = False

        # network
        ok, my_id, map_w, map_h = recv_network(sock, stream, players, bullets,dropped, my_id, map_w, map_h)
        if not ok:
            running = False

        # draw
        draw_frame(screen, players, bullets,dropped, my_id, map_w, map_h, SPRITES1, DEFAULT_SPRITE1, SPRITES2, DEFAULT_SPRITE2, DAGGERS, DEFAULT_DAGGER)

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