import socket
import select
import struct
import itertools
import math
import time

from Player import PlayerData, new_place, check_collision_with_stone, check_collision_with_lava, check_bullet_hit,check_fart_hit
from settings import *
from map_data import *
from Bullet import *
from Dagger import *
from Fart import *
from DroppedWeapon import *
dropped_items = []
item_id_counter = itertools.count(0)

# ----------------- helpers -----------------

def id_to_group(player_id, clients):
    for data in clients.values():
        if data["player"].id == player_id:
            return data["player"].group
    return None


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


# ----------------- networking / lifecycle -----------------

def choose_group(clients):
    g1 = 0
    g2 = 0
    for c in clients.values():
        if c["player"].group == 1:
            g1 += 1
        elif c["player"].group == 2:
            g2 += 1
    return 1 if g1 <= g2 else 2


def accept_new_client(server_sock, clients, id_gen, now):
    conn, addr = server_sock.accept()
    conn.setblocking(False)

    pid = next(id_gen)
    group = choose_group(clients)
    px, py = new_place()

    clients[conn] = {
        "stream": QC3Stream(),
        "player": PlayerData(pid, px, py, 3, group, 0,0,0 ),  # start facing south
        "last": now
    }

    print("CONNECT", addr, "id=", pid)

    welcome_payload = struct.pack("!III", pid, MAP_W, MAP_H)
    try:
        conn.sendall(qc3_pack(CMD_WELCOME, welcome_payload))
    except Exception:
        disconnect_client(conn, clients)


def disconnect_client(sock, clients):
    pid = None
    try:
        pid = clients[sock]["player"].id
    except Exception:
        pass

    if pid is not None:
        print("DISCONNECT", pid)

    try:
        sock.close()
    except Exception:
        pass

    clients.pop(sock, None)


def timeout_clients(clients, now, timeout_sec=10):
    dead = []
    for s in list(clients.keys()):
        if now - clients[s]["last"] > timeout_sec:
            dead.append(s)

    for s in dead:
        pid = clients[s]["player"].id
        print("TIMEOUT", pid)
        disconnect_client(s, clients)


# ----------------- game logic -----------------

def tick_cooldowns(clients,farts):
    for c in clients.values():
        p = c["player"]
        if hasattr(p, "gun_cooldown") and p.gun_cooldown > 0:
            p.gun_cooldown -= 1

        if hasattr(p, "f_cooldown") and p.f_cooldown > 0:
            p.f_cooldown -= 1

        if hasattr(p, "t_cooldown") and p.t_cooldown > 0:
            p.t_cooldown -= 1

    for f in farts:
        if hasattr(f, "duration") and f.duration > 0:
            f.duration -= 1

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

def apply_movement(p, dx, dy, dsprint,teleport):
    if teleport and p.t_cooldown == 0:
        p.t_cooldown = TELEPORT_COOLDOWN
        speed =SPEED*200
        dx,dy =dir_to_vec(p.dir)
        nx = clamp(p.x + dx * speed, 0, MAP_W)
        ny = clamp(p.y + dy * speed, 0, MAP_H)
    else:
        speed = SPEED + (SPEED * dsprint*50)
        nx = clamp(p.x + dx * speed, 0, MAP_W)
        ny = clamp(p.y + dy * speed, 0, MAP_H)

    # axis-separated collision
    if not check_collision_with_stone(p, nx, p.y):
        p.x = nx
    if not check_collision_with_stone(p, p.x, ny):
        p.y = ny

def apply_lava_and_respawn(p):
    if check_collision_with_lava(p, p.x, p.y):
        p.health -= 0.5
        if p.health <= 0:
            drop_weapons(p, dropped_items)
            p.x, p.y = new_place()
            p.health = 100

def try_attack(p, attack, bullets,farts, clients, dagger ,fartp):
    p.attack = 0
    if fartp==1:
        if p.f_cooldown==0:
            p.fartp = 1
            f_id = p.id
            new_fart = Fart(f_id, p.x, p.y,p.dir,FART_TIME)
            farts.append(new_fart)
            p.f_cooldown = FART_COOLDOWN

    if attack != 1:
        return

    p.attack = 1


    if p.weapons[p.current_weapon-1] == 'gu' and attack ==1:
        if p.gun_cooldown == 0:
            b_id = get_next_bullet_id(bullets)
            new_bullet = Bullet(b_id, p.x, p.y, p.dir, BULLET_DISTANS, p.id)
            bullets.append(new_bullet)
            p.gun_cooldown = BULLET_COOLDOWN

    elif p.weapons[p.current_weapon-1] == 'h' and attack ==1:
        p.weapons[p.current_weapon - 1] = 0
        p.health = 100


        #elif p.weapons[p.current_weapon-1] == 'da':# and dagger.attack(p, clients, new_place):
     #   drop_weapons(p, dropped_items)
      #  dagger.attack(p, clients, new_place)

def drop_weapons(player, dropped_list):
    for w_type in player.weapons:
        if w_type != 0 :
            new_id = next(item_id_counter)
            if w_type == 'da':
                w_type = 1
            elif w_type == 'gu':
                w_type = 2

            angle = random.uniform(0, 2 * math.pi)
            print (angle)
            radius = 40
            drop_x = player.x + math.cos(angle) * radius
            drop_y = player.y + math.sin(angle) * radius

            item = DroppedWeapon(new_id, drop_x,drop_y, w_type)
            dropped_list.append(item)

    player.weapons = INVENTORI
    player.current_weapon = 0

def pickup_weapons(player, dropped_list):
    min_dis = 80
    closest_item = None
    for wepon in dropped_list:
        dis= ((player.x - wepon.x) ** 2 + (player.y - wepon.y) ** 2) ** 0.5
        if dis < min_dis:

            wt = 'da' if wepon.weapon_type == 1 else 'gu'


            if wt not in player.weapons:
                min_dis = dis
                closest_item = wepon

        if closest_item:
            if closest_item.weapon_type == 1:
                wt = 'da'
            elif closest_item.weapon_type == 2:
                wt = 'gu'

            for i in range(len(player.weapons)-1):
                if player.weapons[i] == 0:
                    player.weapons[i] = wt
                    dropped_list.remove(closest_item)
                    print(f"Player {player.id} picked up {wt}")
                    break

def apply_bullet_hits_for_player(p, bullets, clients):
    for b in bullets[:]:
        shooter_group = id_to_group(b.player_id, clients)

        # לא פוגע בעצמו
        if b.player_id == p.id:
            continue

        # אם לא מוצאים קבוצה (יורה התנתק) - אפשר לבחור להתעלם
        if shooter_group is None:
            continue

        if shooter_group != p.group:
            if check_bullet_hit(p, b):
                p.health -= BULLET_DAMEG
                bullets.remove(b)
                if p.health <= 0:
                    drop_weapons(p, dropped_items)
                    p.x, p.y = new_place()
                    p.health = 100

def update_bullets(bullets):
    for b in bullets[:]:
        is_dead = b.update_bullet()  # שם הפונקציה שלך
        if is_dead:
            bullets.remove(b)

def fart(farts,p,clients):
    for f in farts[:]:
        low, high = get_angle_from_dir(f.dir)
        shooter_group = id_to_group(f.id, clients)
        # לא פוגע בעצמו
        if f.id == p.id:
            continue
        if shooter_group is None:
            continue
        if shooter_group != p.group:
            if check_fart_hit(p, f,low,high):
                p.health -= FART_DAMEG
                if p.health <= 0:
                    p.x, p.y = new_place()
                    p.health = 100

def update_fart(farts,c):
    for f in farts[:]:
        if f.duration<= 0:
            for p in c.values():
                if p["player"].id == f.id:
                    p["player"].fartp = 0
            farts.remove(f)

def handle_input_message(p, payload, bullets,farts, clients, dagger):
    if len(payload) != 9:
        return

    dx, dy, dsprint, dire, attack, current_weapon ,pickup,fartp,teleport= struct.unpack("!bbbbbbbbb", payload)
    # weapon switch

    if current_weapon != 0 and p.weapons[current_weapon-1] in p.weapons:
        p.current_weapon = current_weapon

    # direction update
    if dire != 0:
        p.dir = int(dire)

    # attack
    try_attack(p, attack, bullets,farts, clients, dagger,fartp)

    apply_movement(p, dx, dy, dsprint,teleport)
    apply_lava_and_respawn(p)


    if pickup==1:
        pickup_weapons(p,dropped_items)

def handle_client_read(sock, clients, bullets,farts, dagger, now):
    try:
        data = sock.recv(4096)
        if not data:
            raise ConnectionError()

        clients[sock]["stream"].feed(data)
        clients[sock]["last"] = now

        for cmd, payload in clients[sock]["stream"].pop_messages():
            if cmd == CMD_INPUT:
                p = clients[sock]["player"]
                handle_input_message(p, payload, bullets,farts, clients, dagger)

    except Exception:
        disconnect_client(sock, clients)


# ----------------- state broadcast -----------------

def build_state_payload(clients, bullets):
    icount = min(255, len(dropped_items))
    payload = bytearray()
    payload.append(icount)

    for i in range(icount):
        item = dropped_items[i]
        print (int(item.id), int(item.x), int(item.y), item.weapon_type)
        payload += struct.pack("!IHHB", int(item.id), int(item.x), int(item.y), item.weapon_type)


    count = min(255, len(clients))

    payload.append(count)

    for i, c in enumerate(clients.values()):
        if i >= count:
            break
        p = c["player"]
        wepon = 0
        if p.weapons[p.current_weapon - 1] == 'da':
            wepon = 1
        elif p.weapons[p.current_weapon - 1] == 'gu':
            wepon = 2
        payload += struct.pack(
            "!IIIHHBBBBII",
            int(p.id),
            int(p.x),
            int(p.y),
            max(0, int(p.health)),
            int(p.dir),
            int(p.attack),
            int(wepon),
            int(p.group),
            int(p.fartp),
            int(p.f_cooldown),
            int(p.t_cooldown)
        )

    # bullets (limit to 255 to keep one byte length safe)
    bcount = min(255, len(bullets))
    payload.append(bcount)

    for i in range(bcount):
        b = bullets[i]
        payload += struct.pack("!iiHi", int(b.x), int(b.y), int(b.id), int(b.dir))



    return bytes(payload)


def broadcast_state(server_cmd, clients, bullets):
    payload = build_state_payload(clients, bullets)
    packet = qc3_pack(server_cmd, payload)

    dead = []
    for s in list(clients.keys()):
        try:
            s.sendall(packet)
        except BlockingIOError:
            pass
        except Exception:
            dead.append(s)

    for s in dead:
        disconnect_client(s, clients)


# ----------------- main -----------------

def main():
    # server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    server.setblocking(False)

    clients = {}  # sock -> {"stream": QC3Stream, "player": PlayerData, "last": float}
    id_gen = itertools.count(1)

    dagger = Dagger()
    bullets = []
    farts = []
    last_broadcast = time.time()
    print(f"QC3 Server listening on {HOST}:{PORT}")

    while True:
        now = time.time()

        # read sockets
        rlist = [server] + list(clients.keys())
        readable, _, _ = select.select(rlist, [], [], 0.02)

        # cooldowns tick each loop
        tick_cooldowns(clients,farts)

        for s in readable:
            if s is server:
                accept_new_client(server, clients, id_gen, now)
            else:
                handle_client_read(s, clients, bullets,farts, dagger, now)

        # world updates
        update_bullets(bullets)

        # apply bullet hits for every player
        if bullets:
            for c in clients.values():
                apply_bullet_hits_for_player(c["player"], bullets, clients)

        update_fart(farts,clients)

        if farts:
            for c in clients.values():
                fart( farts, c["player"], clients)
        # timeouts
        timeout_clients(clients, now, timeout_sec=10)

        # broadcast at 20Hz
        if now - last_broadcast >= 0.05:
            broadcast_state(CMD_STATE, clients, bullets)
            last_broadcast = now


if __name__ == "__main__":
    main()