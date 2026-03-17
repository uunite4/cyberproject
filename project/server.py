import socket
import select
import struct
import itertools
import time

from Player import PlayerData, new_place, check_collision_with_stone, check_collision_with_lava, check_bullet_hit
from settings import *
from map_data import MAP
from Bullet import *
from Dagger import *
from enemy import *


# ----------------- helpers -----------------

def id_to_group(player_id, clients, enemies):
    for data in clients.values():
        if data["player"].id == player_id:
            return data["player"].group
    for e in enemies.values():
        if e.id == player_id:
            return "enemy"
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
        "player": PlayerData(pid, px, py, 3, group, 0),  # start facing south
        "last": now
    }

    print("CONNECT", addr, "id=", pid)

    welcome_payload = struct.pack("!IHH", pid, MAP_W, MAP_H)
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

def player_pos(player_list):
    ids = []
    positions = []

    for player_data in player_list.values():
        # Access the 'player' object stored inside the dictionary
        player = player_data["player"]
        # 1. Add the ID to the id list
        ids.append(player.id)

        # 2. Add the (x, y) coordinates as a tuple to the positions list
        positions.append((player.x, player.y))

    return ids, positions

def enemy_treatment(enemies, players, memory_list, bullets,id_gen):
    list_id, list_pos = player_pos(players)  # lists of all the players in the server
    for eid, e in enemies.items():
        see_id_list, see_pos_list = e.Big_check(list_id, list_pos) #return ordred 2 lists of see radius

        last_target = memory_list.get(eid)
        target_x, target_y, id = e.get_target(see_id_list, see_pos_list, last_target)
        memory_list[eid] = (target_x, target_y)

        dx = target_x - e.entity.x
        dy = target_y - e.entity.y
        new_dir = get_dir_from_vector(dx, dy)
        if new_dir:
            e.entity.dir = new_dir

        final_x, final_y = next_pos2(e.entity.x, e.entity.y, target_x, target_y, S.MONSTERS[e.type]["speed"])
        if final_y<0: final_y = 0
        if not check_collision_with_stone(final_x, e.entity.y, S.MONSTERS[e.type]["size"]):
            e.entity.x = final_x
        if not check_collision_with_stone(e.entity.x, final_y, S.MONSTERS[e.type]["size"]):
            e.entity.y = final_y
        isenemy_att = attack_bullet(id, e, target_x, target_y,bullets ,id_gen)
    return isenemy_att ,memory_list

def attack_bullet(target_id, e, target_x, target_y,bullets ,id_gen):
    now = time.time()
    isenemy_att=0
    if target_id is not None:
        isenemy_att =1
        # Check if 1.5 seconds have passed since the last attack
        if now - e.last_att > 0.5:
            new_bullet = Bullet(next(id_gen), e.entity.x, e.entity.y, e.entity.dir, BULLET_DISTANS, e.id)
            bullets.append(new_bullet)

            # Update last_att so they don't shoot again immediately
            e.last_att = now
    return isenemy_att

def tick_cooldowns(clients):
    for c in clients.values():
        p = c["player"]
        if hasattr(p, "gun_cooldown") and p.gun_cooldown > 0:
            p.gun_cooldown -= 1


def apply_movement(p, dx, dy, dsprint):
    speed = SPEED + (SPEED * dsprint)

    nx = clamp(p.x + dx * speed, 0, MAP_W)
    ny = clamp(p.y + dy * speed, 0, MAP_H)

    # axis-separated collision
    if not check_collision_with_stone(nx, p.y, PLAYER_SIZE):
        p.x = nx
    if not check_collision_with_stone(p.x, ny, PLAYER_SIZE):
        p.y = ny


def apply_lava_and_respawn(p):
    if check_collision_with_lava(p, p.x, p.y):
        p.health -= 0.5
        if p.health <= 0:
            p.x, p.y = new_place()
            p.health = 100


def try_attack(p, attack, bullets, clients,enemies, dagger):
    p.attack = 0
    if attack != 1:
        return

    p.attack = 1

    if p.current_weapon == 2:
        if p.gun_cooldown == 0:
            b_id = get_next_bullet_id(bullets)
            new_bullet = Bullet(b_id, p.x, p.y, p.dir, BULLET_DISTANS, p.id)
            bullets.append(new_bullet)
            p.gun_cooldown = BULLET_COOLDOWN

    elif p.current_weapon == 1:
        dagger.attack(p, clients,enemies, new_place)


def apply_bullet_hits_for_player(p, bullets, clients,enemies):
    for b in bullets[:]:
        shooter_group = id_to_group(b.player_id, clients, enemies)

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
                    p.x, p.y = new_place()
                    p.health = 100

def apply_bullet_hits_for_enemy(e, bullets, clients,enemies):
    for b in bullets[:]:
        shooter_group = id_to_group(b.player_id, clients, enemies)

        # לא פוגע בעצמו
        if b.player_id == e.id:
            continue

        # אם לא מוצאים קבוצה (יורה התנתק) - אפשר לבחור להתעלם
        if shooter_group is None:
            continue

        if shooter_group != "enemy":
            if check_bullet_hit(e.entity, b):
                e.entity.health -= BULLET_DAMEG
                bullets.remove(b)
                if e.entity.health <= 0:
                    e.entity.x, e.entity.y = new_place()
                    e.entity.health = S.MONSTERS[e.type]["health"]


def update_bullets(bullets):
    for b in bullets[:]:
        is_dead = b.update_bullet()  # שם הפונקציה שלך
        if is_dead:
            bullets.remove(b)
def handle_input_message(p, payload, bullets, clients,enemies, dagger):
    if len(payload) != 6:
        return

    dx, dy, dsprint, dire, attack, current_weapon = struct.unpack("!bbbbbb", payload)

    # weapon switch
    if current_weapon != 0:
        p.current_weapon = current_weapon

    # direction update
    if dire != 0:
        p.dir = int(dire)

    # attack
    try_attack(p, attack, bullets, clients,enemies, dagger)

    # movement + env
    apply_movement(p, dx, dy, dsprint)
    apply_lava_and_respawn(p)


def handle_client_read(sock, clients,enemies, bullets, dagger, now):
    try:
        data = sock.recv(4096)
        if not data:
            raise ConnectionError()

        clients[sock]["stream"].feed(data)
        clients[sock]["last"] = now

        for cmd, payload in clients[sock]["stream"].pop_messages():
            if cmd == CMD_INPUT:
                p = clients[sock]["player"]
                handle_input_message(p, payload, bullets, clients,enemies, dagger)

    except Exception:
        disconnect_client(sock, clients)

def generate_id(length=5) -> str:
    # We manually define the "pool" of characters
    # This is exactly what string.ascii_letters + string.digits does
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    # Pick 5 random characters and join them
    new_id = "".join(random.choice(chars) for _ in range(length))
    return new_id


def keep_ai_count(type, list,num):
    while len(list) < num:
        while True:
            x = random.randint(0, MAP_W)
            y = random.randint(0, MAP_H)

            if not check_collision_with_stone(x, y, 40):
                dir = 1
                id = generate_id()
                obj = Entity(x, y, dir, S.MONSTERS[type]["health"], id, type)
                list[id] = Enemy(obj, id, type)
            break
    return list

# ----------------- state broadcast -----------------

def build_state_payload(clients, enemies, bullets, isenemy_att):
    p_count = min(255, len(clients))
    payload = bytearray()
    payload.append(p_count)


    for i, c in enumerate(clients.values()):
        if i >= p_count:
            break
        p = c["player"]

        payload += struct.pack(
            "!IhhhhBBB",
            int(p.id),
            int(p.x),
            int(p.y),
            max(0, int(p.health)),
            int(p.dir),
            int(p.attack),
            int(p.current_weapon),
            int(p.group)
        )

    # 2. Pack Enemies
    e_count = min(255, len(enemies))
    payload.append(e_count)
    for i, e in enumerate(enemies.values()):
        if i >= e_count:
            break
        if e.type == "GOBLIN":
            etype = 1
        else:
            etype = 0
        payload += struct.pack(
            "!5shhhhBB",
            e.id.encode('ascii'),  # Convert string 'irgnx' to bytes,
            int(e.entity.x),
            int(e.entity.y),
            max(0, int(e.health)),
            int(e.entity.dir),
            isenemy_att,
            etype,
        )

    # bullets (limit to 255 to keep one byte length safe)
    bcount = min(255, len(bullets))
    payload.append(bcount)

    for i in range(bcount):
        b = bullets[i]
        payload += struct.pack("!hhHh", int(b.x), int(b.y), int(b.id), int(b.dir))

    return bytes(payload)


def broadcast_state(server_cmd, clients,enemies, bullets, isenemy_att):
    payload = build_state_payload(clients, enemies, bullets, isenemy_att)
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

    enemies = {}
    memory_list ={}#list of the last targets the enemy got - prevent ADHD

    last_broadcast = time.time()
    print(f"QC3 Server listening on {HOST}:{PORT}")

    count_ticks = 0
    while True:
        now = time.time()

        #is there enough enemies?
        enemies = keep_ai_count( "GOBLIN", enemies,50)
        enemies = keep_ai_count( "BEAR", enemies,50)

        # read sockets
        rlist = [server] + list(clients.keys())
        readable, _, _ = select.select(rlist, [], [], 0.02)

        # cooldowns tick each loop
        tick_cooldowns(clients)

        for s in readable:
            if s is server:
                accept_new_client(server, clients, id_gen, now)
            else:
                handle_client_read(s, clients, enemies, bullets, dagger, now)

        # world updates
        update_bullets(bullets)

        #enemy
        isenemy_att, memory_list = enemy_treatment(enemies, clients, memory_list, bullets, id_gen)

        # apply bullet hits for every player
        if bullets:
            for c in clients.values():
                apply_bullet_hits_for_player(c["player"], bullets, clients,enemies)
            for e in enemies.values():
                apply_bullet_hits_for_enemy(e, bullets, clients,enemies)

        # timeouts
        timeout_clients(clients, now, timeout_sec=10)


        # broadcast at 20Hz
        if now - last_broadcast >= 0.05:
            broadcast_state(CMD_STATE, clients,enemies, bullets, isenemy_att)
            last_broadcast = now


if __name__ == "__main__":
    main()