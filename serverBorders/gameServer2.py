import asyncio
import struct
import time
import random
from xmlrpc.client import boolean
import Dagger
import Fart
from Bullet import *
from Player import *
from DroppedWeapon import *
import SETTINGS as S
from networking.wrappers.server_wrapper import QuicServer
from map_data import *

class MyServer:

    def __init__(self):
        self.serverNumber = 2
        self.serverData = S.SERVERS[self.serverNumber - 1]
        self.nearOverlaps = getNearOverlaps(self.serverNumber - 1)
        self.clients = {}
        self.bullets = []
        self.items = []
        self.farts = []
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
        cmd, pid = struct.unpack_from('!b16s', data, 0)
        pid = pid.decode("utf-8")

        if (cmd == S.CMDS["LB_ADDING_PLAYER"]):
            print("GOT LB PACKET")
            x, y = struct.unpack_from('!hh', data, 17)
            self.clients[pid] = {
                "x": x,
                "y": y,
                "inOverlap": False,
                "dir": 3,
                "hp": S.PLAYER_HEALTH,
                "cid":connection_id,
                "imOverlap": False,
                "att": 0,
                "weapon": 1,
                "inventory": S.INVENTORI,
                "gun_cd": S.BULLET_COOLDOWN,
                "fart": 0,
                "f_cooldown": 0,
                "invis": 0,
                "i_timer": 0,
                "speed": 0,
                "speed_timer": 0,
                "laser_timer": 0,
                "laser_cooldown": S.LASER_COOLDOWN,
                "brit_timer": 0,
            }
            print("PLAYERS INITIAL POS: ", self.clients[pid]["x"], self.clients[pid]["y"], "PLAYERS ID: ", pid)
        elif (cmd == S.CMDS["HELLO"]):
            self.clients[pid]["cid"] = connection_id
        elif (cmd == S.CMDS["MOVE"]):
            currentClient = self.clients[pid]

            if currentClient["imOverlap"]:
                currentClient["imOverlap"] = False
                currentClient["inOverlap"] = False
            # CLIENT GAVE US DIRECTION, WE RETURN POS
            print(f"GOT MOVE PACKET")
            xDir, yDir, sprint = struct.unpack_from('!bbb', data, 17)

            nx,ny = apply_movement(currentClient["x"],currentClient["y"],xDir,yDir, sprint + 2*currentClient["speed"])
            currentClient["dir"] = get_dir(nx-currentClient["x"],ny-currentClient["y"])
            currentClient["x"], currentClient["y"] = nx, ny
            currentClient["cid"] = connection_id

            # SEND MOVE
            pk = struct.pack('!bhhh', S.CMDS["MOVE"], currentClient["x"], currentClient["y"], currentClient["dir"])
            self.server.send(connection_id, pk)


            # NOW THAT WE UPDATED POSITION, WE CAN CHECK FOR RANGES
            # CHECK FOR OVERLAPS
            inOverlaps = []
            for OverlapObj in self.nearOverlaps:
                iOverlap = OverlapObj["overlapIndex"]
                inOverlap = point_in_rect(currentClient["x"], currentClient["y"], S.OVERLAPS[iOverlap]["x"], 0,
                                          S.GENERAL_OVERLAP["width"], S.MAP_HEIGHT)
                inOverlaps.append(inOverlap)

            inServer = point_in_rect(currentClient["x"], currentClient["y"], self.serverData["x"], 0,
                                     self.serverData["width"], S.MAP_HEIGHT)

            counter = 0
            for i, inOverlap in enumerate(inOverlaps):  # WILL ALWAYS BE ONLY 1 of them
                if (inOverlap):
                    counter += 1
                    overlapDir = self.nearOverlaps[i]["dir"].encode("utf-8")
                    pk = struct.pack('!b1s', S.CMDS["OVERLAP"], overlapDir)
                    self.server.send(connection_id, pk)
                    print("in overlap")
                    currentClient["inOverlap"] = True

            if (counter == 0 and inServer and currentClient["inOverlap"] == True):
                # NOT IN OVERLAP (and was before)
                pk = struct.pack('!b', S.CMDS["OUT_OF_OVERLAP"])
                self.server.send(connection_id, pk)
                currentClient["inOverlap"] = False

            if (not inServer):
                pk = struct.pack('!b', S.CMDS["SWITCH_SERVER"])
                self.server.send(connection_id, pk)
                del self.clients[pid]
        elif (cmd == S.CMDS["POS_DONT_RESPOND"]):
            x, y, dir = struct.unpack_from('!hhh', data, 17)
            new_data = {
                "x": x,
                "y": y,
                "dir": dir,
            }
            self.clients[pid].update(new_data)
            print(f"GOT OVERLAP PACKET")
        elif (cmd == S.CMDS["HP_DONT_RESPOND"]):
            nhp = struct.unpack_from('!h', data, 17)[0]
            self.clients[pid]["hp"] = nhp
        elif (cmd == S.CMDS["REMOVE_ME"]):
            del self.clients[pid]
        elif (cmd == S.CMDS["ADD_ME"]):
            print("added player ", pid)
            x, y, dir, health, att, weapon, fart = struct.unpack_from('!hhhhbbb', data, 17)
            self.clients[pid] = {
                "x": x,
                "y": y,
                "inOverlap": True,
                "imOverlap": True,
                "dir": dir,
                "hp": health,
                "att": att,
                "weapon": weapon,
                "gun_cd": S.BULLET_COOLDOWN,
                "inventory": S.INVENTORI, #needs to be recieved!!!!
                "fart":fart,
                "f_cooldown": 0,
                "cid": connection_id,
            }

        elif (cmd == S.CMDS["ATTACK"]):
            att = struct.unpack_from('!b', data, 17)[0]
            self.clients[pid]["att"] = att
            print("attacking with weapon ", self.clients[pid]["weapon"])
            if att != 1:
                return
            if nameToWeapon(self.clients[pid]) == 2 and self.clients[pid]["gun_cd"] <= 0:
                b_id = get_next_bullet_id(self.bullets)
                new_bullet = Bullet(b_id, self.clients[pid]["x"], self.clients[pid]["y"], self.clients[pid]["dir"], S.BULLET_DISTANS, pid)
                self.bullets.append(new_bullet)
                self.clients[pid]["gun_cd"] = S.BULLET_COOLDOWN

            elif nameToWeapon(self.clients[pid]) == 3:
                    if self.clients[pid]["hp"] < 100:
                        self.clients[pid]["hp"] = min(self.clients[pid]["hp"]+50, 100)
                        pk = struct.pack('!bh', S.CMDS["DAMAGE"], int(self.clients[pid]["hp"]))
                        self.server.send(connection_id, pk)
                        self.clients[pid]["inventory"][self.clients[pid]["weapon"] - 1] = 0
                        destroyItem(self, self.clients[pid]["cid"], self.clients[pid]["weapon"] - 1)


            elif nameToWeapon(self.clients[pid]) == 4:
                self.clients[pid]["speed"] = 1
                self.clients[pid]["speed_timer"] = S.SPEED_POSSION_TIME
                self.clients[pid]["inventory"][self.clients[pid]["weapon"] - 1] = 0
                destroyItem(self, self.clients[pid]["cid"], self.clients[pid]["weapon"] - 1)


            elif nameToWeapon(self.clients[pid]) == 5:
                self.clients[pid]["invis"] = 1
                self.clients[pid]["i_cooldown"] = S.INVESIBEL_TIME
                self.clients[pid]["inventory"][self.clients[pid]["weapon"] - 1] = 0
                destroyItem(self, self.clients[pid]["cid"], self.clients[pid]["weapon"] - 1)


            elif nameToWeapon(self.clients[pid]) == 6:
                self.clients[pid]["brit_timer"] = S.BRIT_TIMER
                self.clients[pid]["inventory"][self.clients[pid]["weapon"] - 1] = 0
                destroyItem(self, self.clients[pid]["cid"], self.clients[pid]["weapon"] - 1)

            elif nameToWeapon(self.clients[pid]) == 7 and self.clients[pid]["laser_cooldown"] <= 0:
                self.clients[pid]["laser_timer"] = S.LASER_TIME
                self.clients[pid]["laser_cooldown"] = S.LASER_COOLDOWN

        elif (cmd == S.CMDS["CHANGE_WEAPON"]):
            weapon = struct.unpack_from('!b', data, 17)[0]
            self.clients[pid]["weapon"] = weapon
            print("changed weapon to ", weapon)
            if nameToWeapon(self.clients[pid]) == 2:
                self.clients[pid]["gun_cd"] = S.BULLET_COOLDOWN
            if nameToWeapon(self.clients[pid]) != 7:
                self.clients[pid]["laser_timer"] = 0
        elif (cmd == S.CMDS["FART"]):
            fart = struct.unpack_from('!b', data, 17)[0]
            print("got fart")
            if fart == 1:
                if self.clients[pid]["f_cooldown"] <= 0:
                    self.clients[pid]["fart"] = fart
                    print("added fart")
                    f_id = pid
                    new_fart = Fart.Fart(f_id, self.clients[pid]["x"], self.clients[pid]["y"], self.clients[pid]["dir"], S.FART_TIME)
                    self.farts.append(new_fart)
                    self.clients[pid]["f_cooldown"] = S.FART_COOLDOWN

        elif (cmd == S.CMDS["PICKUP_ITEM"]):
            pickup_weapons(self.server, self.clients[pid], self.items)



    def on_connect(self, connection_id: int):
        print(f"connected {connection_id}")

    def on_disconnect(self, connection_id: int):
        print(f"disconnected {connection_id}")
        for pid, client in self.clients.items():
            if connection_id == client["cid"]:
                del self.clients[pid]
                break

    async def broadcast_loop(self):
        lastBroadcast = time.time()
        dagger = Dagger.Dagger()

        while True:
            now = time.time()

            if now - lastBroadcast >= S.BROADCAST_INTERVAL:
                tick_cooldowns(self.server,self.clients,self.farts)
                broadcast(self, dagger)
                update_bullets(self.bullets)
                update_fart(self.farts, self.clients)

                lastBroadcast = now

            await asyncio.sleep(0.001)

    async def run(self):
        await self.server.start()
        print("Server started")

        asyncio.create_task(self.broadcast_loop())

        await asyncio.Future()  # keep program running

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def apply_movement(x,y, dx, dy, sprint):
    speed = S.PLAYER_VEL + sprint*S.PLAYER_VEL

    nx = clamp(x + dx * speed, 0, S.MAP_WIDTH)
    ny = clamp(y + dy * speed, 0, S.MAP_HEIGHT)

    # axis-separated collision
    if not check_collision_with_stone(nx, y, S.PLAYER_SIZE):
        x = nx
    if not check_collision_with_stone(x, ny, S.PLAYER_SIZE):
        y = ny
    return x, y

def point_in_rect(px, py, rx, ry, w, h):
    return (
            rx <= px <= rx + w and
            ry <= py <= ry + h
    )


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


def broadcast(self, dagger):
    hp_change = [False] * len(self.clients) #does their health change and need updating?
    i = 0
    for pid,client in self.clients.items():
        temp = copy_dic(self.clients)
        del temp[pid]
        pk = build_state_payload(temp, self.bullets, self.items, client["fart"], client["invis"], min(1,client["laser_timer"]))
        self.server.send(client["cid"],pk)
        if client["fart"] == 1:
            print("player is farting ", i)
        #health related changes
        if client["att"] == 1 and nameToWeapon(client) == 1:  # daggers
            print("player attacking", i)
            arr = dagger.attack(client, self.clients)
            j = 0
            for boo in arr:
                if boo:
                    hp_change[j] = True
                j += 1
        if client["laser_timer"]>0:
            arr = check_laser_hit(pid, client, self.clients)
            j = 0
            for boo in arr:
                if boo:
                    hp_change[j] = True
                j += 1
        if not client["imOverlap"]:
            if self.bullets: #!= []
                boo = apply_bullet_hits_for_player(pid, client, self.bullets)
                if boo:
                    hp_change[i] = True
            if self.farts: #!= []
                boo = fart(self.farts, client, pid)
                if boo:
                    hp_change[i] = True
            if check_collision_with_lava(client["x"], client["y"], S.PLAYER_SIZE): #daggers
                client["hp"] -= 1
                hp_change[i] = True
        i += 1
    i = 0
    for client in self.clients.values():
        if hp_change[i]:
            if client["hp"] > 0:
                print("damage taken")
                pk = struct.pack('!bh', S.CMDS["DAMAGE"], int(client["hp"]))
            elif client["hp"] <= 0:
                drop_weapons(client, self.items)
                x, y = respawn(self.serverNumber-1)
                print("DECIDED ON POS: ", x, y)
                client["x"],client["y"],client["hp"] = x,y,S.PLAYER_HEALTH
                # send information to client
                pk = struct.pack("!bhh", S.CMDS["RESPAWN"], x, y)
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
        if not check_collision_with_stone(x,y,S.PLAYER_SIZE) and not check_collision_with_lava(x,y,S.PLAYER_SIZE): #and collision with lava
            return x, y


def copy_dic(dic):
    ndic = {}
    for k,v in dic.items():
        ndic[k] = v
    return ndic

def build_state_payload(clients, bullets, items, fart, invi, laser):
    count = len(clients)
    format = "!bbbbh" + "hhhhbbbb" * count #the b is for byte - 0\1
    payload = [S.CMDS["RENDER"], fart, invi, laser, count]

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

    countb = len(bullets)
    payload.append(countb)
    format += "h" + "hh" * countb
    for b in bullets:
        payload.append(int(b.x))
        payload.append(int(b.y))

    counti = len(items)
    payload.append(counti)
    format += "h" + "hhb" * counti
    for i in items:
        payload.append(int(i.x))
        payload.append(int(i.y))
        payload.append(int(i.weapon_type))

    return struct.pack(format, *payload)

def build_total_client(pid,client):
    format = "!b16shh"
    payload = [S.CMDS["MOVE_PLAYER"], pid]
    payload.append(client["x"])
    payload.append(client["y"])
    payload.append(client["dir"])
    payload.append(client["hp"])

def nameToWeapon(client):
    weapon = client["inventory"][client["weapon"]-1]
    if weapon == 'da':
        return 1
    if weapon == 'gu':
        return 2
    if weapon == 'h':
        return 3
    if weapon == 's':
        return 4
    if weapon == 'i':
        return 5
    if weapon == 'b':
        return 6
    if weapon == 'la':
        return 7
    return 0

def get_dir(dx,dy):
    if dx > 0:
        if dy > 0:
            dire = 2
        elif dy == 0:
            dire = 1
        elif dy < 0:
            dire = 8
    elif dx < 0:
        if dy > 0:
            dire = 4
        elif dy < 0:
            dire = 6
        elif dy == 0:
            dire = 5
    elif dx == 0:
        if dy > 0:
            dire = 3
        elif dy < 0:
            dire = 7
        elif dy == 0:
            dire = 3
    return dire

def tick_cooldowns(server,clients, farts):
    for c in clients.values():
        if nameToWeapon(c) == 2 and c["gun_cd"] > 0:
            c["gun_cd"] -= 1
        if c["f_cooldown"] > 0:
            c["f_cooldown"] -= 1
            if c["f_cooldown"] == 0:
                pk = struct.pack("!b", S.CMDS["FART_READY"])
                server.send(c["cid"], pk)
        if c["speed"] == 1 and c["speed_timer"] > 0:
            c["speed_timer"] -= 1
            if c["speed_timer"] <= 0:
                c["speed_timer"] = 0
                c["speed"] = 0
        if c["invis"] == 1 and c["i_cooldown"] > 0:
            c["i_cooldown"] -= 1
            if c["i_cooldown"] == 0:
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
    i=0
    for b in bullets:
        is_dead = b.update_bullet()  # שם הפונקציה שלך
        if is_dead:
            del bullets[i]
        i+=1

def update_fart(farts,c):
    for f in farts:
        if f.duration <= 0:
            c[f.id]["fart"] = 0
            farts.remove(f)
        else:
            f.x = c[f.id]["x"]
            f.y = c[f.id]["y"]

def apply_bullet_hits_for_player(pid, p, bullets):
    back = False
    i=0
    for b in bullets:
        # לא פוגע בעצמו
        if b.player_id == pid:
            continue
        if check_bullet_hit(p, b):
            p["hp"] -= S.BULLET_DAMEG
            del bullets[i]
            back = True
        i+=1
    return back
def check_laser_hit(pid, attacker, clients):
    vx, vy = dir_to_vec(attacker["dir"])
    arr = []
    for id,target in clients.items():
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
    return arr

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


def fart(farts,p,pid):
    boo = False
    for f in farts:
        # לא פוגע בעצמו
        if f.id == pid:
            continue
        low, high = Fart.get_angle_from_dir(f.dir)
        if check_fart_hit(p, f,low,high):
            p["hp"] -= S.FART_DAMEG
            boo = True
    return boo
def destroyItem(self, cid, item):
    pk = struct.pack('!bb', S.CMDS["DELETE_ITEM"], int(item))
    self.server.send(cid, pk)

def drop_weapons(player, dropped_list):
    for w_type in player["inventory"]:
        if w_type != 0:
            new_id = 1 #because i can
            if w_type == 'da':
                w_type = 1
            elif w_type == 'gu':
                w_type = 2
            elif w_type == 'h':
                w_type = 3
            elif w_type == 's':
                w_type = 4
            elif w_type == 'i':
                w_type = 5
            elif w_type == 'b':
                w_type = 6
            elif w_type == 'la':
                w_type = 7
            angle = random.uniform(0, 2 * math.pi)
            print (angle)
            radius = 40
            drop_x = player["x"] + math.cos(angle) * radius
            drop_y = player["y"] + math.sin(angle) * radius
            if w_type != 1:
                item = DroppedWeapon(new_id, drop_x,drop_y, w_type)
                dropped_list.append(item)

    player["inventory"] = S.INVENTORI.copy()
    player["weapon"] = 0

def pickup_weapons(server, player, dropped_list):
    min_dis = 80
    closest_item = None
    wt_map = {1: 'da', 2: 'gu', 3: 'h', 4: 's', 5: 'i', 6: 'b',7:'la'}
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
        for i in range(len(player["inventory"])-1):
            if player["inventory"][i] == 0:
                player["inventory"][i] = wt
                if closest_item in dropped_list:
                    dropped_list.remove(closest_item)
                    pk = struct.pack("!bbb", S.CMDS["ADD_ITEM"], closest_item.weapon_type, i)
                    server.send(player["cid"], pk)

    return

if __name__ == "__main__":
    s = MyServer()
    asyncio.run(s.run())
