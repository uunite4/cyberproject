
import os
import pygame
import socket
import struct
import sys

from Player import PlayerData, handle_input, health_bar_update, S_health_bar_update
from settings import *
from map_data import MAP
from map import draw_map
from Bullet import *

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


def load_player_sprites(group):
    """
    Loads rotation sprites from: ./rotations/
    Must exist next to client.py
    Returns dict dir->Surface
    dir mapping:
      1=east, 2=south-east, 3=south, 4=south-west,
      5=west, 6=north-west, 7=north, 8=north-east
    """
    if group == 1:
        rotations_dir = os.path.join(os.path.dirname(__file__), "rotations")
    else:
        rotations_dir = os.path.join(os.path.dirname(__file__), "rotation1")

    def load(name: str) -> pygame.Surface:
        path = os.path.join(rotations_dir, name)
        img = pygame.image.load(path).convert_alpha()
        if img.get_width() != PLAYER_SIZE or img.get_height() != PLAYER_SIZE:
            img = pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
        return img

    sprites = {
        1: load("east.png"),
        2: load("south-east.png"),
        3: load("south.png"),
        4: load("south-west.png"),
        5: load("west.png"),
        6: load("north-west.png"),
        7: load("north.png"),
        8: load("north-east.png"),
    }

    return sprites
def load_dagger_sprites() -> dict[int, pygame.Surface]:
    base_path = os.path.join(os.path.dirname(__file__), "DAGGER-NORTH.png")
    base = pygame.image.load(base_path).convert_alpha()

    if base.get_width() != TILE_SIZE or base.get_height() != TILE_SIZE:
        base = pygame.transform.scale(base, (TILE_SIZE, TILE_SIZE))

    def rot(img, deg):
        return pygame.transform.rotate(img, deg)

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
    # מיפוי כיוונים לוקטורים (x, y)
    # 1=מזרח, 2=דרום-מזרח, 3=דרום, 4=דרום-מערב, 5=מערב... וכן הלאה
    vectors = {
        1: (1, 0),   # East
        2: (1, 1),   # South-East
        3: (0, 1),   # South
        4: (-1, 1),  # South-West
        5: (-1, 0),  # West
        6: (-1, -1), # North-West
        7: (0, -1),  # North
        8: (1, -1)   # North-East
    }
    return vectors.get(d, (0, 0)) # אם הכיוון לא ידוע, אל תזיז


def run():
    pygame.init()
    pygame.display.set_caption("QC3 Client")
    clock = pygame.time.Clock()

    # create window here (do NOT create screen inside map.py)
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))

    # load sprites
    SPRITES1 = load_player_sprites(1)
    DEFAULT_SPRITE1 = SPRITES1[3]  # south if dir==0
    SPRITES2 = load_player_sprites(2)
    DEFAULT_SPRITE2 = SPRITES2[3]  # south if dir==0
    DAGGERS = load_dagger_sprites()
    DEFAULT_DAGGER = DAGGERS[3]
    # ---- connect ----
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, PORT))
    sock.setblocking(False)

    stream = QC3Stream()

    # optional join
    try:
        sock.sendall(qc3_pack(CMD_JOIN))
    except Exception:
        pass

    my_id = None
    map_w = MAP_W
    map_h = MAP_H

    players = {}  # pid -> PlayerData
    bullets11 = {}
    running = True
    while running:
        # -------- window events --------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # -------- input -> server --------
        dx, dy, dspeed, dire,attack,current_weapon = handle_input()
        local_attack = attack
        try:
            sock.sendall(qc3_pack(CMD_INPUT, struct.pack("!bbbbbb", dx, dy, dspeed, dire,attack,current_weapon)))
        except BlockingIOError:
            # normal on non-blocking sockets
            pass
        except Exception as e:
            print("Send error:", e)
            running = False

        # -------- recv from server --------
        try:
            data = sock.recv(4096)
            if data:
                stream.feed(data)
                for cmd, payload in stream.pop_messages():
                    if cmd == CMD_WELCOME and len(payload) == 8:
                        my_id, map_w, map_h = struct.unpack("!IHH", payload)

                    elif cmd == CMD_STATE:
                        if not payload:
                            continue
                        count = payload[0]
                        off = 1
                        active_ids = set()

                        for _ in range(count):
                            if off + 15 > len(payload):
                                break
                            pid, x, y, health, pdire, patt, pweapon, pgroup = struct.unpack("!IHHHHBBB",payload[off:off + 15])
                            off += 15
                            active_ids.add(pid)

                            if pid not in players:
                                players[pid] = PlayerData(pid, x, y, pdire, pgroup, 0)

                            players[pid].update_from_server(x, y, health, pdire, patt, pweapon, pgroup)


                        # remove players who left
                        for pid_to_remove in list(players.keys()):
                            if pid_to_remove not in active_ids:
                                del players[pid_to_remove]


                        #shot
                        count1 = payload[off]
                        off += 1
                        active_bull = set()
                        for _ in range(count1):
                            if off + 8 > len(payload):
                                break
                            bullet_x ,bullet_y  , bullet_id, dirb= struct.unpack("!hhHh", payload[off:off + 8])
                            off += 8
                            active_bull.add(bullet_id)
                            if bullet_id not in bullets11:

                                bullets11[bullet_id] = Bullet(bullet_id, bullet_x, bullet_y ,dirb,0,0)
                            bullets11[bullet_id].update_from_server_bull(bullet_x, bullet_y)

                        for bull_to_remove in list(bullets11.keys()):
                            if bull_to_remove not in active_bull:
                                del bullets11[bull_to_remove]

        except BlockingIOError:
            pass
        except Exception as e:
            print("Network error:", e)
            running = False

        # -------- draw --------
        screen.fill((0, 0, 0))

        if my_id is None or my_id not in players:
            pygame.display.flip()
            clock.tick(60)
            continue

        me = players[my_id]
        cam_x, cam_y = camera_from_pos(me.x, me.y, map_w, map_h)

        # draw map
        draw_map(screen, MAP, cam_x, cam_y, WINDOW_W, WINDOW_H)

        # =====draw bull
        for bullet_id, b in bullets11.items():
            bx = b.x - cam_x
            by = b.y - cam_y
            pygame.draw.circle(screen, "yellow", (bx,by), 10)

        # draw all players as sprites
        for pid, p in players.items():
            px = int(p.x - cam_x - PLAYER_SIZE // 2)
            py = int(p.y - cam_y - PLAYER_SIZE // 2)
            if(p.group == 1):
                sprite = SPRITES1.get(p.dir, DEFAULT_SPRITE1)
            else:
                sprite = SPRITES2.get(p.dir, DEFAULT_SPRITE1)
            screen.blit(sprite, (px, py))

            if p.attack == 1 and p.current_weapon == 1:

                d = p.dir if p.dir != 0 else 3
                vx, vy = dir_to_vec(d)  # same helper you already added earlier
                dagger_x = int((p.x + vx * TILE_SIZE) - cam_x - TILE_SIZE // 2)
                dagger_y = int((p.y + vy * TILE_SIZE) - cam_y - TILE_SIZE // 2)
                screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))

            # health bars
            if pid == my_id:
                health_bar_update(p.health, screen)
            else:
                S_health_bar_update(p.health, screen, px, py)

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
