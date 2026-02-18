import os
import pygame
import socket
import struct
import sys

from Player import PlayerData, handle_input, health_bar_update, S_health_bar_update
from settings import *
from map_data import MAP
from map import draw_map


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


def load_player_sprites():
    """
    Loads rotation sprites from: ./rotations/
    Must exist next to client.py
    Returns dict dir->Surface
    dir mapping:
      1=east, 2=south-east, 3=south, 4=south-west,
      5=west, 6=north-west, 7=north, 8=north-east
    """
    rotations_dir = os.path.join(os.path.dirname(__file__), "rotations")

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
    if d == 1: return (1, 0)
    if d == 2: return (1, 1)
    if d == 3: return (0, 1)
    if d == 4: return (-1, 1)
    if d == 5: return (-1, 0)
    if d == 6: return (-1, -1)
    if d == 7: return (0, -1)
    if d == 8: return (1, -1)
    return (0, 1)


def run():
    pygame.init()
    pygame.display.set_caption("QC3 Client")
    clock = pygame.time.Clock()

    # create window here (do NOT create screen inside map.py)
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))

    # load sprites
    SPRITES = load_player_sprites()
    DEFAULT_SPRITE = SPRITES[3]  # south if dir==0

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
                            if off + 14 > len(payload): break
                            pid, x, y, health, pdire, patt, pweapon = struct.unpack("!IHHHHBB", payload[off:off + 14])
                            off += 14
                            active_ids.add(pid)

                            if pid not in players:
                                # PlayerData in your project expects: (pid, x, y, dir1, group)
                                players[pid] = PlayerData(pid, x, y, pdire, 0)

                            players[pid].update_from_server(x, y, health, pdire, patt, pweapon)

                        # remove players who left
                        for pid_to_remove in list(players.keys()):
                            if pid_to_remove not in active_ids:
                                del players[pid_to_remove]

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

        # draw all players as sprites
        for pid, p in players.items():
            px = int(p.x - cam_x - PLAYER_SIZE // 2)
            py = int(p.y - cam_y - PLAYER_SIZE // 2)

            sprite = SPRITES.get(p.dir, DEFAULT_SPRITE)
            screen.blit(sprite, (px, py))

            # d = p.dir if p.dir != 0 else 3
            # vx, vy = dir_to_vec(d)
            # if local_attack == 1:
            #     d = me.dir if me.dir != 0 else 3
            #     vx, vy = dir_to_vec(d)
            #
            #     dagger_x = int((me.x + vx * TILE_SIZE) - cam_x - TILE_SIZE // 2)
            #     dagger_y = int((me.y + vy * TILE_SIZE) - cam_y - TILE_SIZE // 2)
            #
            #     screen.blit(DAGGERS.get(d, DEFAULT_DAGGER), (dagger_x, dagger_y))

            if getattr(p, "attack", 0) == 1 and getattr(p, "current_weapon", 1) == 1:
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
