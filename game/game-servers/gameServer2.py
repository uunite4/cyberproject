import asyncio
import struct
from game.classes import Fart, Dagger, Entity
from game.classes.Bullet import *
from game.classes.DroppedWeapon import *
from game.classes.enemy import *
from game.general_func import *
import game.SETTINGS as S
from game.networking.wrappers.server_wrapper import QuicServer


class GameServer:

    def __init__(self):
        self.serverNumber = 2
        self.serverData = S.SERVERS[self.serverNumber - 1]
        self.nearOverlaps = getNearOverlaps(self.serverNumber - 1)
        self.load_id = None
        self.clients = {}
        self.bullets = []
        self.items = []
        self.farts = []
        self.monsters = []
        self.server = QuicServer(
            ip=self.serverData["ip"],
            port=self.serverData["port"],
            cert_file="../networking/certificate/cert.pem",
            key_file="../networking/certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )

    # ----------
    # RECEIVE DATA
    # ----------
    def on_receive(self, connection_id: int, data: bytes):
        cmd = struct.unpack_from('!b', data, 0)[0]

        if (cmd == S.CMDS["HELLO_FROM_LB"]):
            print("got load")
            self.load_id = connection_id
        elif connection_id == self.load_id:

            if (cmd == S.CMDS["CLIENT_DATA"]):
                print("GOT LB PACKET")
                info = struct.unpack_from(f'!16sbiib{S.INVENTORY_SIZE}b', data, 1)
                pid = info[0].decode('utf-8')
                inv = [None] * S.INVENTORY_SIZE
                for i in range(S.INVENTORY_SIZE):
                    weapon = S.INVENTORY_MAP[info[i + 5]]
                    inv[i] = weapon
                self.clients[pid] = {
                    "x": info[2],
                    "y": info[3],
                    "inOverlap": False,
                    "dir": 3,
                    "hp": info[4],
                    "cid": connection_id,
                    "imOverlap": False,
                    "att": 0,
                    "weapons": 1,
                    "inventory": inv,
                    "gun_cd": S.BULLET_COOLDOWN,
                    "fart": 0,
                    "f_cooldown": 0,
                    "f_timer": 0,
                    "invis": 0,
                    "i_timer": 0,
                    "speed": 0,
                    "speed_timer": 0,
                    "laser_timer": 0,
                    "laser_cooldown": S.LASER_COOLDOWN,
                    "brit_timer": 0,
                }
                print("PLAYERS INITIAL POS: ", self.clients[pid]["x"], self.clients[pid]["y"], "PLAYERS ID: ", pid)
            elif (cmd == S.CMDS["TRANSFER_P"]):
                print("got player")
                pid = struct.unpack_from('!16s', data, 1)[0].decode("utf-8")
                take_client(self, pid, data)
        else:
            pid = struct.unpack_from('!16s', data, 1)[0].decode("utf-8")

            if (cmd == S.CMDS["HELLO"]):
                self.clients[pid]["cid"] = connection_id
                print("connected to client", pid)
            elif (cmd == S.CMDS["ADD_ME"] and pid not in self.clients):
                print("added player ", pid)
                x, y, dir, health, att, weapon, fart, invis, laser, brit = struct.unpack_from('!iibbbbhhhh', data, 17)

                if check_overlap_side(self.serverNumber - 1, x) == False:
                    return
                if not 0 <= y <= S.MAP_HEIGHT:
                    return
                if dir not in [1, 2, 3, 4, 5, 6, 7, 8]:
                    return
                if not 0 <= health <= S.PLAYER_HEALTH:
                    return
                if att not in [0, 1]:
                    return

                self.clients[pid] = {
                    "x": x,
                    "y": y,
                    "inOverlap": True,
                    "imOverlap": True,
                    "dir": dir,
                    "hp": health,
                    "att": att,
                    "weapons": weapon,
                    "gun_cd": S.BULLET_COOLDOWN,
                    "inventory": S.BASIC_INV,  # needs to be recieved!!!!
                    "fart": 1 if fart > 0 else 0,
                    "f_cooldown": S.FART_COOLDOWN,
                    "f_timer": fart,
                    "cid": connection_id,
                    "invis": 1 if invis > 0 else 0,
                    "i_timer": invis,
                    "speed": 0,
                    "speed_timer": 0,
                    "laser_timer": laser,
                    "laser_cooldown": S.LASER_COOLDOWN,
                    "brit_timer": brit,
                }

                if fart > 0:
                    print("added fart")
                    f_id = pid
                    new_fart = Fart.Fart(f_id, x, y, dir, fart)
                    self.farts.append(new_fart)

            elif pid in self.clients:
                if (cmd == S.CMDS["MOVE"]):
                    currentClient = self.clients[pid]

                    # CLIENT GAVE US DIRECTION, WE RETURN POS
                    xDir, yDir, sprint = struct.unpack_from('!bbb', data, 17)

                    if not (xDir in [-1, 0, 1] and yDir in [-1, 0, 1] and sprint in [0, 1]):
                        return

                    nx, ny = apply_movement(currentClient["x"], currentClient["y"], xDir, yDir,
                                            sprint + 2 * currentClient["speed"])
                    currentClient["dir"] = get_dir(nx - currentClient["x"], ny - currentClient["y"])
                    currentClient["x"], currentClient["y"] = nx, ny
                    currentClient["cid"] = connection_id

                    # SEND MOVE
                    pk = struct.pack('!biib', S.CMDS["MOVE"], currentClient["x"], currentClient["y"],
                                     currentClient["dir"])
                    self.server.send(connection_id, pk)

                    # NOW THAT WE UPDATED POSITION, WE CAN CHECK FOR RANGES
                    # CHECK FOR OVERLAPS

                    inServer = point_in_rect(currentClient["x"], self.serverData["x"], self.serverData["width"])

                    side = check_overlap_side(self.serverNumber - 1, currentClient["x"])
                    if (side != False and currentClient["inOverlap"] == False):
                        overlapDir = side.encode("utf-8")
                        pk = struct.pack('!b1s', S.CMDS["OVERLAP"], overlapDir)
                        self.server.send(connection_id, pk)
                        print("in overlap")
                        currentClient["inOverlap"] = True

                    if (side == False and inServer and currentClient["inOverlap"] == True):
                        # NOT IN OVERLAP (and was before)
                        pk = struct.pack('!b', S.CMDS["OUT_OF_OVERLAP"])
                        self.server.send(connection_id, pk)
                        currentClient["inOverlap"] = False

                    if (not inServer):
                        print("not in server")
                        if currentClient["x"] < self.serverData["x"]:
                            nServer = self.serverNumber - 1
                        else:
                            nServer = self.serverNumber + 1
                        pk = build_total_client(pid, currentClient, nServer)
                        self.server.send(self.load_id, pk)
                        print("sent to load_b")
                        pk = struct.pack('!b', S.CMDS["SWITCH_SERVER"])
                        self.server.send(connection_id, pk)
                        del self.clients[pid]
                elif (cmd == S.CMDS["POS_DONT_RESPOND"] and self.clients[pid]["imOverlap"]):
                    x, y, dir = struct.unpack_from('!iib', data, 17)
                    if check_overlap_side(self.serverNumber - 1, x) == False:
                        return
                    if not 0 <= y <= S.MAP_HEIGHT:
                        return
                    new_data = {
                        "x": x,
                        "y": y,
                        "dir": dir,
                    }
                    self.clients[pid].update(new_data)
                    print(f"GOT OVERLAP PACKET")
                elif (cmd == S.CMDS["HP_DONT_RESPOND"]):
                    nhp = struct.unpack_from('!b', data, 17)[0]
                    if nhp < 0 or 100 < nhp:
                        return
                    self.clients[pid]["hp"] = nhp
                elif (cmd == S.CMDS["REMOVE_ME"]):
                    del self.clients[pid]
                elif (cmd == S.CMDS["INVIS"]):
                    self.clients[pid]["invis"] = 1
                    self.clients[pid]["i_timer"] = S.INVESIBEL_TIME
                elif (cmd == S.CMDS["LASER"]):
                    if self.clients[pid]["laser_cooldown"] <= 0:
                        self.clients[pid]["laser_timer"] = S.LASER_TIME
                        self.clients[pid]["laser_cooldown"] = S.LASER_COOLDOWN
                elif (cmd == S.CMDS["BRIT"]):
                    self.clients[pid]["brit_timer"] = S.BRIT_TIMER
                elif (cmd == S.CMDS["FARTING"]):
                    if self.clients[pid]["f_cooldown"] <= 0:
                        self.clients[pid]["fart"] = 1
                        self.clients[pid]["f_timer"] = S.FART_TIME
                        print("added fart")
                        f_id = pid
                        new_fart = Fart.Fart(f_id, self.clients[pid]["x"], self.clients[pid]["y"],
                                             self.clients[pid]["dir"],
                                             S.FART_TIME)
                        self.farts.append(new_fart)
                        self.clients[pid]["f_cooldown"] = S.FART_COOLDOWN

                elif (cmd == S.CMDS["ATTACK"]):
                    att = struct.unpack_from('!b', data, 17)[0]
                    if att not in [0, 1]:
                        return
                    self.clients[pid]["att"] = att
                    print("attacking with weapons ", self.clients[pid]["weapons"])
                    if att != 1 or self.clients[pid]["imOverlap"]:
                        return
                    if nameToWeapon(self.clients[pid]) == 2 and self.clients[pid]["gun_cd"] <= 0:
                        b_id = get_next_bullet_id(self.bullets)
                        new_bullet = Bullet(b_id, self.clients[pid]["x"], self.clients[pid]["y"],
                                            self.clients[pid]["dir"], S.BULLET_DISTANS, pid)
                        self.bullets.append(new_bullet)
                        self.clients[pid]["gun_cd"] = S.BULLET_COOLDOWN

                    elif nameToWeapon(self.clients[pid]) == 3:
                        if self.clients[pid]["hp"] < 100:
                            self.clients[pid]["hp"] = min(self.clients[pid]["hp"] + 50, 100)
                            pk = struct.pack('!bb', S.CMDS["DAMAGE"], int(self.clients[pid]["hp"]))
                            self.server.send(connection_id, pk)
                            self.clients[pid]["inventory"][self.clients[pid]["weapons"] - 1] = 0
                            destroyItem(self, self.clients[pid]["cid"], self.clients[pid]["weapons"] - 1)


                    elif nameToWeapon(self.clients[pid]) == 4:
                        self.clients[pid]["speed"] = 1
                        self.clients[pid]["speed_timer"] = S.SPEED_POSSION_TIME
                        self.clients[pid]["inventory"][self.clients[pid]["weapons"] - 1] = 0
                        destroyItem(self, self.clients[pid]["cid"], self.clients[pid]["weapons"] - 1)


                    elif nameToWeapon(self.clients[pid]) == 5:
                        self.clients[pid]["invis"] = 1
                        self.clients[pid]["i_timer"] = S.INVESIBEL_TIME
                        self.clients[pid]["inventory"][self.clients[pid]["weapons"] - 1] = 0
                        destroyItem(self, self.clients[pid]["cid"], self.clients[pid]["weapons"] - 1)


                    elif nameToWeapon(self.clients[pid]) == 6:
                        self.clients[pid]["brit_timer"] = S.BRIT_TIMER
                        self.clients[pid]["inventory"][self.clients[pid]["weapons"] - 1] = 0
                        destroyItem(self, self.clients[pid]["cid"], self.clients[pid]["weapons"] - 1)

                    elif nameToWeapon(self.clients[pid]) == 7 and self.clients[pid]["laser_cooldown"] <= 0:
                        self.clients[pid]["laser_timer"] = S.LASER_TIME
                        self.clients[pid]["laser_cooldown"] = S.LASER_COOLDOWN

                elif (cmd == S.CMDS["CHANGE_WEAPON"]):
                    weapon = struct.unpack_from('!b', data, 17)[0]
                    if weapon not in [1, 2, 3, 4, 5, 6, 7, 8]:
                        return
                    self.clients[pid]["weapons"] = weapon
                    print("changed weapons to ", weapon)
                    if nameToWeapon(self.clients[pid]) == 2:
                        self.clients[pid]["gun_cd"] = S.BULLET_COOLDOWN
                    if nameToWeapon(self.clients[pid]) != 7:
                        self.clients[pid]["laser_timer"] = 0
                elif (cmd == S.CMDS["FART"]):
                    fart = struct.unpack_from('!b', data, 17)[0]
                    if fart not in [0, 1]:
                        return
                    print("got fart")
                    if fart == 1:
                        if self.clients[pid]["f_cooldown"] <= 0:
                            self.clients[pid]["fart"] = fart
                            self.clients[pid]["f_timer"] = S.FART_TIME
                            print("added fart")
                            f_id = pid
                            new_fart = Fart.Fart(f_id, self.clients[pid]["x"], self.clients[pid]["y"],
                                                 self.clients[pid]["dir"], S.FART_TIME)
                            self.farts.append(new_fart)
                            self.clients[pid]["f_cooldown"] = S.FART_COOLDOWN

                elif (cmd == S.CMDS["PICKUP_ITEM"]):
                    pickup_weapons(self.server, self.clients[pid], self.items)

    def on_connect(self, connection_id: int):
        print(f"connected {connection_id}")

    def on_disconnect(self, connection_id: int):
        print(f"disconnected {connection_id}")
        for pid, client in self.clients.items():
            if not client["imOverlap"] and connection_id == client["cid"]:
                inv = get_inventory_in_format(client["inventory"])
                pk = struct.pack(f"b16siib{S.INVENTORY_SIZE}b", S.CMDS["PLAYER_LEFT"], pid.encode('utf-8'), client["x"],
                                 client["y"], client["hp"], *inv)
                print(client["x"], client["y"], client["hp"], *inv)
                self.server.send(self.load_id, pk)
                del self.clients[pid]
                break

    async def broadcast_loop(self):
        lastBroadcast = time.time()
        dagger = Dagger.Dagger()

        keep_ai_count(self, "GOBLIN", 25)
        keep_ai_count(self, "BEAR", 50)

        while True:
            now = time.time()
            if now - lastBroadcast >= S.BROADCAST_INTERVAL:
                if len(self.monsters) < 40:
                    num = random.randint(0, 1)
                    if num == 1:
                        keep_ai_count(self, "BEAR", 50)
                    else:
                        keep_ai_count(self, "GOBLIN", 50)

                tick_cooldowns(self.server, self.clients, self.farts)
                broadcast(self, dagger)
                update_bullets(self.bullets)
                update_fart(self.farts, self.clients)
                enemy_treatment(self)
                if self.bullets:
                    for e, last in self.monsters:
                        apply_bullet_hits_for_enemy(e, self.bullets, self.serverNumber, self.items)
                if self.farts:
                    for e, last in self.monsters:
                        fart_enemy(e, self.farts, self.serverNumber, self.items)

            await asyncio.sleep(0.001)

    async def run(self):
        await self.server.start()
        print("Server started")

        asyncio.create_task(self.broadcast_loop())

        await asyncio.Future()  # keep program running


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def apply_movement(x, y, dx, dy, sprint):
    speed = S.PLAYER_VEL + sprint * S.PLAYER_VEL

    nx = clamp(x + dx * speed, 0, S.MAP_WIDTH)
    ny = clamp(y + dy * speed, 0, S.MAP_HEIGHT)

    # axis-separated collision
    if not check_collision_with_stone(nx, y, S.PLAYER_SIZE):
        x = nx
    if not check_collision_with_stone(x, ny, S.PLAYER_SIZE):
        y = ny
    return x, y


def point_in_rect(px, rx, w):
    return rx <= px <= rx + w


def keep_ai_count(self, type, num):
    while len(self.monsters) < num:
        while True:
            x = random.randint(self.serverData["x"], self.serverData["x"] + self.serverData["width"])
            y = random.randint(0, S.MAP_HEIGHT)

            if not check_collision_with_stone(x, y, S.MONSTERS[type]["size"]) and not check_collision_with_lava(x, y,
                                                                                                                S.MONSTERS[
                                                                                                                    type][
                                                                                                                    "size"]):
                dir = 1
                obj = Entity(x, y, dir, S.MONSTERS[type]["health"], 0, type)
                e = Enemy(obj, id, type)
                self.monsters.append((e, (None, None)))

            if len(self.monsters) == num:
                break


def player_pos(player_list):
    ids = []
    positions = []

    for pid, player in player_list.items():
        if player["invis"] == 0:
            # 1. Add the ID to the id list
            ids.append(pid)

            # 2. Add the (x, y) coordinates as a tuple to the positions list
            positions.append((player["x"], player["y"]))
        else:
            print("player is invis")

    return ids, positions


def enemy_treatment(self):
    list_id, list_pos = player_pos(self.clients)  # lists of all the players in the server
    i = 0
    for e, last_target in self.monsters:
        see_id_list, see_pos_list = e.Big_check(list_id, list_pos)  # return ordred 2 lists of see radius

        target_x, target_y, id = e.get_target(see_id_list, see_pos_list, last_target)
        self.monsters[i] = (e, (target_x, target_y))

        dx = target_x - e.entity.x
        dy = target_y - e.entity.y
        new_dir = get_dir_from_vector(dx, dy)
        if new_dir:
            e.entity.dir = new_dir

        final_x, final_y = next_pos2(e.entity.x, e.entity.y, target_x, target_y, S.MONSTERS[e.type]["speed"])
        # 1. Calculate potential next positions
        # 2. Check X movement
        if not check_collision_with_stone(final_x, e.entity.y, S.MONSTERS[e.type]["size"]) and \
                not check_collision_with_lava(final_x, e.entity.y, 100):  # Added lava check
            e.entity.x = final_x

        # 3. Check Y movement
        if not check_collision_with_stone(e.entity.x, final_y, S.MONSTERS[e.type]["size"]) and \
                not check_collision_with_lava(e.entity.x, final_y, 100):  # Added lava check
            e.entity.y = final_y
        if S.MONSTERS[e.type]["type"] == "ranged":
            attack_bullet(id, e, self.bullets)

        i += 1


def attack_bullet(target_id, e, bullets):
    if target_id is not None:
        now = time.time()
        # Check if 1.5 seconds have passed since the last attack
        if now - e.last_att > S.ENEMY_COOLDOWN:
            new_bullet = Bullet(0, e.entity.x, e.entity.y, e.entity.dir, S.BULLET_DISTANS, 0)
            bullets.append(new_bullet)
            # Update last_att so they don't shoot again immediately
            e.last_att = now


def apply_bullet_hits_for_enemy(e, bullets, num, items):
    i = 0
    for b in bullets:
        if b.player_id != 0:
            if check_bullet_hitE(e.entity, b):
                e.entity.health -= S.BULLET_DAMEG
                del bullets[i]
                if e.entity.health <= 0:
                    e.entity.health = S.MONSTERS[e.type]["health"]
                    # drop 2 random weapons
                    weapon_type = random.randint(2, 7)
                    drop_weapon_for_enemy(items, e, weapon_type)
                    weapon_type = random.randint(2, 7)
                    drop_weapon_for_enemy(items, e, weapon_type)

                    e.entity.x, e.entity.y = respawn(num - 1)
        i += 1


def getNearOverlaps(serverIndex):
    nearOverlaps = []
    if serverIndex == 0:
        nearOverlaps.append({"overlapIndex": serverIndex, "dir": "r"})
    elif serverIndex == S.SERVER_NUMBER - 1:
        nearOverlaps.append({"overlapIndex": serverIndex - 1, "dir": "l"})
    else:
        nearOverlaps.append({"overlapIndex": serverIndex - 1, "dir": "l"})
        nearOverlaps.append({"overlapIndex": serverIndex, "dir": "r"})

    return nearOverlaps


def check_overlap_side(server_num, x):
    """
    Checks if a given x-coordinate falls within an overlap region
    for a specific server and returns the side.

    Args:
        server_num (int): The index of the server (0 to SERVER_NUMBER - 1).
        x (float/int): The x-coordinate to check.

    Returns:
        str or bool: "left" if in the left overlap, "right" if in the right overlap,
                     or False if not in any overlap.
    """

    # 1. Check the LEFT overlap (shared with the previous server)
    if server_num > 0:
        left_overlap_start = server_num * S.SERVER_STEP
        left_overlap_end = left_overlap_start + S.OVERLAP_WIDTH

        if left_overlap_start <= x <= left_overlap_end:
            return "l"

    # 2. Check the RIGHT overlap (shared with the next server)
    if server_num < S.SERVER_NUMBER - 1:
        right_overlap_start = (server_num + 1) * S.SERVER_STEP
        right_overlap_end = right_overlap_start + S.OVERLAP_WIDTH

        if right_overlap_start <= x <= right_overlap_end:
            return "r"

    # Not in any overlap zone for this specific server
    return False


def check_attack_enemy_and_build_payload(bullets, items, enemies, clients):
    arr = [False] * len(clients)
    payload = []
    countb = len(bullets)
    payload.append(countb)
    format = "h" + "ii" * countb
    for b in bullets:
        payload.append(int(b.x))
        payload.append(int(b.y))

    counti = len(items)
    payload.append(counti)
    format += "h" + "iib" * counti
    for i in items:
        payload.append(int(i.x))
        payload.append(int(i.y))
        payload.append(int(i.weapon_type))

    counte = len(enemies)
    payload.append(counte)
    format += "h" + "iibbb" * counte
    now = time.time()
    for e, pos in enemies:
        i = e.entity
        payload.append(int(i.x))
        payload.append(int(i.y))
        payload.append(int(i.dir))
        payload.append(int(i.health))
        payload.append(int(S.MONSTERS[e.type]["code"]))

        if check_collision_with_lava(i.x, i.y, S.MONSTERS[e.type]["size"]):
            i.health -= 1

        if S.MONSTERS[e.type]["type"] == "melee":
            if now - e.last_att > S.ENEMY_COOLDOWN:
                i = 0
                for client in clients.values():
                    if client["invis"] == 0:
                        dis = distance(client["x"], client["y"], e.entity.x, e.entity.y)
                        if dis < S.MONSTERS[e.type]["att_radius"]:
                            client["hp"] -= S.MONSTERS[e.type]["damage"]
                            print("attacking player")
                            arr[i] = True
                            e.attacked()
                    i += 1
    return payload, format, arr


def broadcast(self, dagger):
    payload, format, hp_change = check_attack_enemy_and_build_payload(self.bullets, self.items, self.monsters,
                                                                      self.clients)  # does their health change and need updating?
    i = 0
    global pk
    for pid, client in self.clients.items():
        temp = copy_dic(self.clients)
        del temp[pid]
        pk = build_state_payload(temp, payload, format, client)
        self.server.send(client["cid"], pk)
        if client["fart"] == 1:
            print("player is farting ", i)
        # health related changes
        if client["att"] == 1 and nameToWeapon(client) == 1:  # daggers
            print("player attacking", i)
            arr = attack(dagger, client, self.clients, self.monsters, self.items, self.serverNumber)
            j = 0
            for boo in arr:
                if boo:
                    hp_change[j] = True
                j += 1
        if client["laser_timer"] > 0:
            arr = check_laser_hit(pid, client, self.clients, self.monsters, self.serverNumber, self.items)
            j = 0
            for boo in arr:
                if boo:
                    hp_change[j] = True
                j += 1

        if self.bullets:  # != []
            boo = apply_bullet_hits_for_player(pid, client, self.bullets)
            if boo:
                hp_change[i] = True
        if self.farts:  # != []
            boo = fart(self.farts, client, pid)
            if boo:
                hp_change[i] = True
        if check_collision_with_lava(client["x"], client["y"], S.PLAYER_SIZE):  # daggers
            client["hp"] -= 1
            hp_change[i] = True
        i += 1
    i = 0
    for client in self.clients.values():
        if hp_change[i]:
            if client["hp"] > 0:
                print("damage taken")
                pk = struct.pack('!bb', S.CMDS["DAMAGE"], int(client["hp"]))
            elif client["hp"] <= 0:
                drop_weapons(client, self.items)
                x, y = respawn(self.serverNumber - 1)
                print("DECIDED ON POS: ", x, y)
                client["x"], client["y"], client["hp"] = x, y, S.PLAYER_HEALTH
                # send information to client
                pk = struct.pack("!bii", S.CMDS["RESPAWN"], x, y)
            self.server.send(client["cid"], pk)
        i += 1


def respawn(server_number):
    # Choose a random server
    server = S.SERVERS[server_number]

    left = server["x"]
    right = server["x"] + S.SERVER_WIDTH

    # Remove overlap zones
    if server_number > 0:
        left += S.OVERLAP_WIDTH
    if server_number < S.SERVER_NUMBER - 1:
        right -= S.OVERLAP_WIDTH
    while True:
        # Random position inside safe horizontal zone
        x = random.randint(left, right - 1)
        y = random.randint(0, S.MAP_HEIGHT - 1)
        if not check_collision_with_stone(x, y, S.PLAYER_SIZE) and not check_collision_with_lava(x, y,
                                                                                                 S.PLAYER_SIZE):  # and collision with lava
            return x, y


def copy_dic(dic):
    ndic = {}
    for k, v in dic.items():
        ndic[k] = v
    return ndic


def build_state_payload(clients, paylo, end_format, client):
    count = len(clients)
    format = "!bhhhhh" + "iibbbbbb" * count  # the b is for byte - 0\1
    payload = [S.CMDS["RENDER"], int(client["f_timer"]), int(client["i_timer"]), int(client["laser_timer"]),
               int(client["brit_timer"]), count]

    for c in clients.values():
        payload.append(int(c["x"]))
        payload.append(int(c["y"]))
        payload.append(int(c["dir"]))
        payload.append(int(c["hp"]))
        payload.append(int(c["att"]))
        wp = nameToWeapon(c)
        payload.append(int(wp))
        payload.append(int(c["fart"]))
        payload.append(int(c["invis"]))

    format += end_format

    payload.extend(paylo)

    return struct.pack(format, *payload)


def build_total_client(pid, client, nServer):
    inv = get_inventory_in_format(client["inventory"])
    return struct.pack(
        f"!b16sbiibbbb{S.INVENTORY_SIZE}bhbhhbhbhhhh",
        S.CMDS["TRANSFER_P"],
        pid.encode("utf-8"),  # 0: 16s
        int(nServer),
        int(client["x"]),  # 1: h
        int(client["y"]),  # 2: h
        int(client["dir"]),  # 3: b
        int(client["hp"]),  # 4: b
        int(client["att"]),  # 5: b
        int(client["weapons"]),  # 6: b
        *inv,  # 7 עד 11: מפרק את רשימת ה-5 בתים לארגומנטים נפרדים
        int(client["gun_cd"]),  # 12: h
        int(client["fart"]),  # 13: b
        int(client["f_cooldown"]),  # 14: h
        int(client["f_timer"]),  # 15: h
        int(client["invis"]),  # 15: b
        int(client["i_timer"]),  # 16: h
        int(client["speed"]),  # 17: b
        int(client["speed_timer"]),  # 18: h
        int(client["laser_timer"]),  # 19: h
        int(client["laser_cooldown"]),  # 20: h
        int(client["brit_timer"])  # 21: h
    )


def take_client(self, pid, data):
    # הפורמט חייב להיות זהה לחלוטין לפונקציית ה-build שלך
    fmt = f"!biibbbb{S.INVENTORY_SIZE}bhbhhbhbhhhh"

    # פריקת כל הנתונים לתוך משתנה אחד (Tuple)
    unpacked = (struct.unpack_from(fmt, data, 17))

    nServer = unpacked[0]  # אם אתה צריך לדעת מאיזה שרת זה הגיע או לוודא שזה השרת הנכון
    if nServer != self.serverNumber:
        return

    # --- חילוץ האינוונטרי ---
    # בפורמט שלנו, האינוונטרי מתחיל באינדקס 9
    inv_start = 7
    inv_end = inv_start + S.INVENTORY_SIZE
    inventory = list(unpacked[inv_start:inv_end])
    inv_names = numToNames(inventory)
    print(inv_names)

    # saving the cid
    cid = self.clients[pid]["cid"]

    # --- בניית מילון השחקן ---
    self.clients[pid] = {
        "x": unpacked[1],
        "y": unpacked[2],
        "dir": unpacked[3],
        "hp": unpacked[4],
        "att": unpacked[5],
        "weapons": unpacked[6],
        "inventory": inv_names,
        "gun_cd": unpacked[inv_end],
        "fart": unpacked[inv_end + 1],
        "f_cooldown": unpacked[inv_end + 2],
        "f_timer": unpacked[inv_end + 3],
        "invis": unpacked[inv_end + 4],
        "i_timer": unpacked[inv_end + 5],
        "speed": unpacked[inv_end + 6],
        "speed_timer": unpacked[inv_end + 7],
        "laser_timer": unpacked[inv_end + 8],
        "laser_cooldown": unpacked[inv_end + 9],
        "brit_timer": unpacked[inv_end + 10],
        "inOverlap": False,
        "imOverlap": False,
        "cid": cid,
    }
    return


def get_inventory_in_format(inv):
    new_inv = []
    for ch in inv:
        if ch == 0:
            new_inv.append(0)
        else:
            new_inv.append(nameTOnum(ch))
    return new_inv


def nameToWeapon(client):
    weapon = client["inventory"][client["weapons"] - 1]
    return nameTOnum(weapon)


def nameTOnum(b):
    if b == 'da':
        return 1
    if b == 'gu':
        return 2
    if b == 'h':
        return 3
    if b == 's':
        return 4
    if b == 'i':
        return 5
    if b == 'b':
        return 6
    if b == 'la':
        return 7
    return 0


def numToNames(arr):
    new_names = []
    for i in arr:
        if i == 0:
            new_names.append(0)
        else:
            new_names.append(S.INVENTORY_MAP[i])
    return new_names


def get_dir(dx, dy):
    global direc
    if dx > 0:
        if dy > 0:
            direc = 2
        elif dy == 0:
            direc = 1
        elif dy < 0:
            direc = 8
    elif dx < 0:
        if dy > 0:
            direc = 4
        elif dy < 0:
            direc = 6
        elif dy == 0:
            direc = 5
    elif dx == 0:
        if dy > 0:
            direc = 3
        elif dy < 0:
            direc = 7
        elif dy == 0:
            direc = 3
    return direc


def tick_cooldowns(server, clients, farts):
    for c in clients.values():
        if nameToWeapon(c) == 2 and c["gun_cd"] > 0:
            c["gun_cd"] -= 1
        if c["f_cooldown"] > 0:
            c["f_cooldown"] -= 1
            if c["f_cooldown"] == 0:
                pk = struct.pack("!b", S.CMDS["FART_READY"])
                server.send(c["cid"], pk)
        if c["f_timer"] > 0:
            c["f_timer"] -= 1
        if c["speed"] == 1 and c["speed_timer"] > 0:
            c["speed_timer"] -= 1
            if c["speed_timer"] <= 0:
                c["speed_timer"] = 0
                c["speed"] = 0
        if c["invis"] == 1 and c["i_timer"] > 0:
            c["i_timer"] -= 1
            if c["i_timer"] == 0:
                c["invis"] = 0
        if nameToWeapon(c) == 7 and c["laser_cooldown"] > 0:
            c["laser_cooldown"] -= 1
            if c["laser_timer"] > 0:
                c["laser_timer"] -= 1
            else:
                c["laser_timer"] = 0
        if c["brit_timer"] > 0:
            c["brit_timer"] -= 1
            if c["brit_timer"] < 0:
                c["brit_timer"] = 0

    for f in farts:
        if f.duration > 0:
            f.duration -= 1


def update_bullets(bullets):
    i = 0
    for b in bullets:
        is_dead = b.update_bullet()  # שם הפונקציה שלך
        if is_dead:
            del bullets[i]
        i += 1


def update_fart(farts, c):
    for f in farts:
        if f.duration <= 0:
            c[f.id]["fart"] = 0
            farts.remove(f)
        else:
            f.x = c[f.id]["x"]
            f.y = c[f.id]["y"]


def apply_bullet_hits_for_player(pid, p, bullets):
    back = False
    i = 0
    for b in bullets:
        # לא פוגע בעצמו
        if b.player_id == pid:
            continue
        if check_bullet_hit(p, b):
            print(pid, " hit")
            p["hp"] -= S.BULLET_DAMEG
            del bullets[i]
            back = True
        i += 1
    return back


def check_laser_hit(pid, attacker, clients, monsters, num, items):
    vx, vy = dir_to_vec(attacker["dir"])
    arr = []
    for id, target in clients.items():
        arr.append(False)
        if id == pid:
            continue

        dx = target["x"] - attacker["x"]
        dy = target["y"] - attacker["y"]
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if dist <= S.LASER_DIS:

            target_angle = math.atan2(dy, dx)
            if target_angle < 0: target_angle += 2 * math.pi

            attacker_angle = math.atan2(vy, vx)
            if attacker_angle < 0: attacker_angle += 2 * math.pi

            angle_diff = abs(target_angle - attacker_angle)
            if angle_diff > math.pi:  # תיקון למעגל
                angle_diff = 2 * math.pi - angle_diff

            if angle_diff < 0.1:
                target["hp"] -= S.LASER_DAMEG
                arr[-1] = True

    for e, pos in monsters:
        dx = e.entity.x - attacker["x"]
        dy = e.entity.y - attacker["y"]
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if dist <= S.LASER_DIS:
            target_angle = math.atan2(dy, dx)
            if target_angle < 0: target_angle += 2 * math.pi

            attacker_angle = math.atan2(vy, vx)
            if attacker_angle < 0: attacker_angle += 2 * math.pi

            angle_diff = abs(target_angle - attacker_angle)
            if angle_diff > math.pi:  # תיקון למעגל
                angle_diff = 2 * math.pi - angle_diff

            if angle_diff < 0.1:
                e.entity.health -= S.LASER_DAMEG
                if e.entity.health <= 0:
                    e.entity.health = S.MONSTERS[e.type]["health"]
                    # drop 2 random weapons
                    weapon_type = random.randint(2, 7)
                    drop_weapon_for_enemy(items, e, weapon_type)
                    weapon_type = random.randint(2, 7)
                    drop_weapon_for_enemy(items, e, weapon_type)

                    # random respwon
                    e.entity.x, e.entity.y = respawn(num)

    return arr


def attack(dagger, attacker, clients, monsters, items, num):
    if not dagger.ready(attacker["cid"]):
        return [False] * len(clients)

    dagger.trigger_cooldown(attacker["cid"])

    hitbox = dagger.build_hitbox(attacker)

    arr = []
    boo = False
    i = 0
    for target in clients.values():

        if target["cid"] == attacker["cid"]:
            arr.append(False)
            i = len(arr) - 1
            continue

        target_box = player_rect(target)
        if rects_overlap(hitbox, target_box):
            if target["brit_timer"] == 0:
                arr.append(True)
                target["hp"] -= dagger.damage
            else:
                boo = True
                arr.append(False)
                attacker["hp"] -= dagger.damage
        else:
            arr.append(False)
    if boo:
        arr[i] = True

    for e, pos in monsters:
        target_box = enemy_rect(e)
        print("check attack enemy")
        if rects_overlap(hitbox, target_box):
            e.entity.health -= dagger.damage
            print("enemy got hit")
            if e.entity.health <= 0:
                e.entity.health = S.MONSTERS[e.type]["health"]
                # drop 2 random weapons
                weapon_type = random.randint(2, 7)
                drop_weapon_for_enemy(items, e, weapon_type)
                weapon_type = random.randint(2, 7)
                drop_weapon_for_enemy(items, e, weapon_type)

                # random respwon
                e.entity.x, e.entity.y = respawn(num)

    return arr


def rects_overlap(a, b):
    # a,b: (left, top, right, bottom)
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def player_rect(p):
    half = S.PLAYER_SIZE // 2
    # player is centered at (p.x, p.y)
    return (p["x"] - half, p["y"] - half, p["x"] + half - 1, p["y"] + half - 1)


def enemy_rect(e):
    half = S.MONSTERS[e.type]["size"] // 2
    # player is centered at (p.x, p.y)
    return (e.entity.x - half, e.entity.y - half, e.entity.x + half - 1, e.entity.y + half - 1)


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


def fart(farts, p, pid):
    boo = False
    for f in farts:
        # לא פוגע בעצמו
        if f.id == pid:
            continue
        low, high = Fart.get_angle_from_dir(f.dir)
        if check_fart_hit(p, f, low, high):
            p["hp"] -= S.FART_DAMEG
            boo = True
    return boo


def fart_enemy(e, farts, num, items):
    for f in farts:

        low, high = Fart.get_angle_from_dir(f.dir)

        if check_fart_hit_enemy(e, f, low, high):
            e.entity.health -= S.FART_DAMEG
            if e.entity.health <= 0:
                e.entity.health = S.MONSTERS[e.type]["health"]
                # drop 2 random weapons
                weapon_type = random.randint(2, 7)
                drop_weapon_for_enemy(items, e, weapon_type)
                weapon_type = random.randint(2, 7)
                drop_weapon_for_enemy(items, e, weapon_type)

                # random respawn
                e.entity.x, e.entity.y = respawn(num)


def destroyItem(self, cid, item):
    pk = struct.pack('!bb', S.CMDS["DELETE_ITEM"], int(item))
    self.server.send(cid, pk)


def drop_weapons(player, dropped_list):
    for w_type in player["inventory"]:
        if w_type != 0:
            w_type = nameTOnum(w_type)
            angle = random.uniform(0, 2 * math.pi)
            print(angle)
            radius = 40
            drop_x = player["x"] + math.cos(angle) * radius
            drop_y = player["y"] + math.sin(angle) * radius
            if w_type != 1:
                item = DroppedWeapon(1, drop_x, drop_y, w_type)
                dropped_list.append(item)

    player["inventory"] = S.BASIC_INV.copy()
    player["weapons"] = 0


def drop_weapon_for_enemy(items, e, weaponNum):
    angle = random.uniform(0, 2 * math.pi)
    radius = 40
    drop_x = e.entity.x + math.cos(angle) * radius
    drop_y = e.entity.y + math.sin(angle) * radius
    item = DroppedWeapon(1, drop_x, drop_y, weaponNum)
    items.append(item)


def pickup_weapons(server, player, dropped_list):
    min_dis = 80
    closest_item = None
    wt_map = {1: 'da', 2: 'gu', 3: 'h', 4: 's', 5: 'i', 6: 'b', 7: 'la'}
    for weapon in dropped_list:
        dis = ((player["x"] - weapon.x) ** 2 + (player["y"] - weapon.y) ** 2) ** 0.5
        if dis < min_dis:

            wt = wt_map.get(weapon.weapon_type)

            if wt:

                if wt not in player["inventory"] or wt in ['h', 's', 'i', 'b']:
                    min_dis = dis
                    closest_item = weapon

    if closest_item:
        wt = wt_map.get(closest_item.weapon_type)
        for i in range(len(player["inventory"])):
            if player["inventory"][i] == 0:
                player["inventory"][i] = wt
                dropped_list.remove(closest_item)
                pk = struct.pack("!bbb", S.CMDS["ADD_ITEM"], closest_item.weapon_type, i)
                server.send(player["cid"], pk)
                break
    return


if __name__ == "__main__":
    s = GameServer()
    asyncio.run(s.run())
