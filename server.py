import socket
import select
import struct
import itertools
import time

from Player import *
from settings import *
from map_data import MAP
from weapon import Dagger


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
dagger = Dagger()
last_broadcast = time.time()

print(f"QC3 Server listening on {HOST}:{PORT}")


def broadcast_state():
    count = min(255, len(clients))
    payload = bytearray()
    payload.append(count)

    for i, c in enumerate(clients.values()):
        if i >= count:
            break
        p = c["player"]
        payload += struct.pack(
            "!IHHHHBB",
            int(p.id),
            int(p.x),
            int(p.y),
            int(p.health),
            int(p.dir),
            int(p.attack),
            int(p.current_weapon),
        )

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
                "player": PlayerData(pid, px, py, 3, 0),  # start facing south
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

                    if cmd == CMD_INPUT and len(payload) == 6:
                        dx, dy, dsprint, dire, attack, current_weapon = struct.unpack("!bbbbbb", payload)

                        p = clients[s]["player"]
                        p.attack = int(attack)
                        if current_weapon == 0:
                            p.current_weapon = p.current_weapon
                        else:
                            p.current_weapon = current_weapon

                        # only dagger attacks when weapon == 1
                        if p.attack == 1 and p.current_weapon == 1:
                            dagger.attack(p, clients, new_place)

                        if dire != 0:
                            p.dir = int(dire)

                        speed = SPEED + (SPEED * dsprint)

                        nx = clamp(p.x + dx * speed, 0, MAP_W)
                        ny = clamp(p.y + dy * speed, 0, MAP_H)

                        if not check_collision_with_stone(p, nx, p.y):
                            p.x = nx
                        if not check_collision_with_stone(p, p.x, ny):
                            p.y = ny

                        if check_collision_with_lava(p, p.x, p.y):
                            p.health -= 0.5
                            if p.health <= 0:
                                p.x, p.y = new_place()
                                p.health = 100



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
        broadcast_state()
        last_broadcast = now
