import socket
import select
import struct
import itertools
import time

from Player import PlayerData, new_place, check_collision_with_stone, check_collision_with_lava, check_bullet_hit
from settings import *
from map_data import MAP
from Bullet import *

def clamp(v, lo, hi):
    return max(lo, min(hi, v))


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


# -------- server socket --------
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
server.setblocking(False)

clients = {}  # sock -> {"stream": QC3Stream, "player": PlayerData, "last": float}
id_gen = itertools.count(1)

last_broadcast = time.time()

print(f"QC3 Server listening on {HOST}:{PORT}")


def broadcast_state(all_bullets):
    count = min(255, len(clients))
    payload = bytearray()
    payload.append(count)

    for i, c in enumerate(clients.values()):
        if i >= count:
            break
        p = c["player"]

        payload += struct.pack(
            "!IHHHH",
            int(p.id),
            int(p.x),
            int(p.y),
            int(p.health),
            int(p.dir),
        )
    payload.append(len(all_bullets))
    for b in all_bullets:
        payload += struct.pack(
            "!HHHH",
            int(b.x),
            int(b.y),
            int(b.id),
            int(b.dir))
    packet = qc3_pack(CMD_STATE, bytes(payload))

    dead = []
    for s in list(clients.keys()):
        try:
            s.sendall(packet)
        except BlockingIOError:
            pass
        except Exception:
            dead.append(s)

    for s in dead:
        try:
            s.close()
        except Exception:
            pass
        clients.pop(s, None)

bullets = []
bullet_id_gen = itertools.count(10000)
# -------- main loop --------
while True:
    now = time.time()

    rlist = [server] + list(clients.keys())
    readable, _, _ = select.select(rlist, [], [], 0.02)

    for s in readable:
        # new client
        if s is server:
            conn, addr = server.accept()
            conn.setblocking(False)

            pid = next(id_gen)
            px, py = new_place()

            # PlayerData signature: (pid, x, y, dir1, group)
            clients[conn] = {
                "stream": QC3Stream(),
                "player": PlayerData(pid, px, py, 3,0, 0),  # start facing south
                "last": now
            }

            print("CONNECT", addr, "id=", pid)

            welcome_payload = struct.pack("!IHH", pid, MAP_W, MAP_H)
            try:
                conn.sendall(qc3_pack(CMD_WELCOME, welcome_payload))
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
                clients.pop(conn, None)

        # existing client
        else:
            try:
                data = s.recv(4096)
                if not data:
                    raise ConnectionError()

                clients[s]["stream"].feed(data)

                for cmd, payload in clients[s]["stream"].pop_messages():
                    clients[s]["last"] = now

                    if cmd == CMD_INPUT and len(payload) == 5 :
                        dx, dy, dsprint, dire ,shot= struct.unpack("!bbbbb", payload)

                        p = clients[s]["player"]

                        


                        if dire != 0:
                            p.dir = int(dire)

                        if shot ==1:
                            if p.gun_cooldown == 0:
                                b_id = next(bullet_id_gen)
                                new_bullet = Bullet(b_id,p.x, p.y, p.dir, BULLET_DISTANS )
                                bullets.append(new_bullet)
                                p.gun_cooldown=BULLET_COOLDOWN
                            else: p.gun_cooldown -=1

                        speed = SPEED + (SPEED * dsprint)

                        nx = clamp(p.x + dx * speed, 0, MAP_W)
                        ny = clamp(p.y + dy * speed, 0, MAP_H)

                        # axis-separated collision
                        if not check_collision_with_stone(p, nx, p.y):
                            p.x = nx
                        if not check_collision_with_stone(p, p.x, ny):
                            p.y = ny

                        # lava damage + respawn
                        if check_collision_with_lava(p, p.x, p.y):
                            p.health -= 0.5
                            if p.health <= 0:
                                p.x, p.y = new_place()
                                p.health = 100

                        for b in bullets[:]:
                            if check_bullet_hit(p,b):
                                p.health -= 0.5

                    # בסוף הלולאה הראשית, מחוץ ל-readable
                    for b in bullets[:]:
                        # קריאה לשם הפונקציה המדויק מהקלאס שלך
                        is_dead = b.update_bullet()
                        if is_dead:
                            bullets.remove(b)

            except Exception:
                pid = None
                try:
                    pid = clients[s]["player"].id
                except Exception:
                    pass

                print("DISCONNECT", pid)

                try:
                    s.close()
                except Exception:
                    pass
                clients.pop(s, None)

    # timeout dead clients
    for s in list(clients.keys()):
        if now - clients[s]["last"] > 10:
            pid = clients[s]["player"].id
            print("TIMEOUT", pid)
            try:
                s.close()
            except Exception:
                pass
            clients.pop(s, None)

    # broadcast at 20Hz
    if now - last_broadcast >= 0.05:
        broadcast_state(bullets)
        last_broadcast = now
