import asyncio
import hashlib
import json
import os
import random
import secrets
import sqlite3
import string
import struct

import login_settings as s
from map_data import MAP as m
from wrappers.server_wrapper import QuicServer

current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, "game.db")


class Login:

    def __init__(self):
        self.loadbalancer_id = None
        self.login_server = QuicServer(
            ip="0.0.0.0",
            port=int(os.getenv("LOGIN_SERVER_PORT")),
            cert_file="wrappers/server.crt",
            key_fie="wrappers/server.key",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )

    def on_receive(self, connection_id: int, data: bytes):

        if connection_id == self.loadbalancer_id:
            self.handle_load_balancer(data)

        else:
            raw_data = data.decode()
            if not raw_data: return
            self.handle_login_client(raw_data, connection_id)

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    async def run(self):
        await self.login_server.start()
        print("Server started")

        self.loadbalancer_id = await self.login_server.connect_to_server(
            ip=s.LOAD_BALANCER["ip"],
            port=s.LOAD_BALANCER["port"]
        )

        try:
            await asyncio.Future()

        except asyncio.CancelledError:
            print("Server shutting down...")

        finally:
            await self.login_server.stop()
            print("Server shut down")

    def hash_password(self, password):
        # We will keep it simple for now so your Login still works
        # Salting requires saving the salt in the DB, which we can add later!
        return hashlib.sha256(password.encode()).hexdigest()

    def hash_password_with_salt(self, password, salt_hex=None):
        # 1. If we are signing up, we need a brand NEW random salt
        if salt_hex is None:
            salt = os.urandom(16)  # Random bytes
            salt_hex = salt.hex()  # Convert to string for the DB
        else:
            # 2. If we are logging in, we use the salt we found in the DB
            salt = bytes.fromhex(salt_hex)

        # 3. ADD the salt to the password (Salt + Password)
        # We use salt (bytes) + password.encode() (bytes)
        combined = salt + password.encode()

        # 4. Hash the combined version
        hash_obj = hashlib.sha256(combined)
        return salt_hex, hash_obj.hexdigest()

    def player_info_get(self, token):
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            curser = conn.cursor()
            curser.execute("SELECT * FROM last_save WHERE token = ?", (token,))
            row = curser.fetchone()
            if row:
                x, y, hp, i1, i2, i3, i4, i5, i6, i7, i8 = row
                print(
                    f"Player is at {x}, {y} with {hp} health. and with the following items {i1, i2, i3, i4, i5, i6, i7, i8}")
                return x, y, hp, i1, i2, i3, i4, i5, i6, i7, i8
            else:
                print("No player found with that token.")
                return None

    def player_info_update(self, token, x_position, y_position, health, item1, item2, item3, item4, item5, item6, item7,
                           item8):
        # self.player_inventory_upload(item1, item2, item3, item4, item5, item6, item7, item8, item9, item10, token)
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            curser = conn.cursor()
            curser.execute("""UPDATE last_save
                              SET x_position = ?,
                                  y_position = ?,
                                  health     = ?,
                                  item1      = ?,
                                  item2      = ?,
                                  item3      = ?,
                                  item4      = ?,
                                  item5      = ?,
                                  item6      = ?,
                                  item7      = ?,
                                  item8      = ?
                              WHERE token = ?""",
                           (x_position, y_position, health, item1, item2, item3, item4, item5, item6, item7, item8,
                            token))

            print(f"Successfully updated stats for Player {token}")
        conn.close()

    def sendTokenToLB(self, token):
        return "38.97.84.242"  # Mock IP for game server

    def get_unique_token(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        while True:
            # 1. Generate a potential token
            new_token = self.generateToken()

            # 2. Ask the DB if anyone is already using it
            cursor.execute("SELECT 1 FROM login WHERE token = ?", (new_token,))
            exists = cursor.fetchone()

            # 3. If 'exists' is None, the token is unique!
            if not exists:
                conn.close()
                return new_token

            # If it's NOT None, the loop runs again to try a different token

    def check_username_exists(self, username):
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            # We only look for the name, ignoring the password
            cursor.execute("SELECT 1 FROM login WHERE username = ?", (username,))
            return cursor.fetchone() is not None

    def handleSignup(self, username, password):
        if self.check_username_exists(username):
            return "ALREADY FOUND"

        token = self.get_unique_token()
        # Generate the salt and the hash
        salt, pass_hash = self.hash_password_with_salt(password)
        x_position, y_position, health, item1, item2, item3, item4, item5, item6, item7, item8 = getStarterPack()
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            # You MUST have a 'salt' column in your 'login' table
            cursor.execute("INSERT INTO login (username, password, salt, token) VALUES (?, ?, ?, ?)",
                           (username, pass_hash, salt, token))
            cursor.execute(
                """INSERT INTO last_save (token, x_position, y_position, health, item1, item2, item3, item4, item5,
                                          item6, item7, item8)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (token, x_position, y_position, health, item1, item2, item3, item4, item5, item6, item7, item8))
            conn.commit()
        return token

    def handleLogin(self, username, password):
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Find the user first to get THEIR specific salt
            cursor.execute("SELECT password, salt, token FROM login WHERE username = ?", (username,))
            user_row = cursor.fetchone()

            if user_row:
                stored_hash = user_row['password']
                stored_salt = user_row['salt']  # This is the 'xyz' or 'abc'

                # 2. Combine the salt they have in the DB with the password they just typed
                _, attempt_hash = self.hash_password_with_salt(password, stored_salt)

                # 3. If the fingerprints match, they are logged in!
                if attempt_hash == stored_hash:
                    return user_row['token']

            return 404

    def generateToken(self, length=16):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def handle_load_balancer(self, data):
        loginData = struct.unpack_from(f"b16siib{s.INVENTORY_SIZE}b", data)

        token = loginData[1].decode('utf-8')
        x_position = loginData[2]
        y_position = loginData[3]
        health = loginData[4]
        item1 = loginData[5]
        item2 = loginData[6]
        item3 = loginData[7]
        item4 = loginData[8]
        item5 = loginData[9]
        item6 = loginData[10]
        item7 = loginData[11]
        item8 = loginData[12]
        print(loginData)
        self.player_info_update(token, x_position, y_position, health, item1, item2, item3, item4, item5, item6, item7,
                                item8)
        print("updated successfully!")

    def createResponsePacket(self, tkn):
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Find the user first to get THEIR specific salt
            cursor.execute("SELECT * FROM last_save WHERE token = ?", (tkn,))
            user_row = cursor.fetchone()

            # Basics
            playerX = user_row["x_position"]
            playerY = user_row["y_position"]
            playerHealth = user_row["health"]
            playerInventory = []

            # Inventory
            for i in range(1, s.INVENTORY_SIZE + 1):
                itemslot = user_row["item" + str(i)]
                playerInventory.append(itemslot)

            serverIndex = None
            for i in range(s.SERVER_NUMBER):
                curServer = s.SERVERS[i]
                print(playerX)
                if (playerX > curServer["x"] and playerX <= curServer["x"] + curServer["width"]):
                    serverIndex = i
                else:
                    print(curServer["x"], curServer["width"])

            print(serverIndex, playerX, playerY, playerHealth, playerInventory)

            pk = struct.pack(f"!b16sbiib{s.INVENTORY_SIZE}b", s.CMDS["CLIENT_DATA"], tkn.encode('utf-8'), serverIndex,
                             playerX, playerY, playerHealth, *playerInventory)
            return pk

    def handle_login_client(self, raw_data, connection_id):
        # still needs to make a new one also for the updating
        # in general make a new system that will be hashed with quic and will not be easy manupulated like the seperation with = sign
        global userToken
        loginData = json.loads(raw_data)
        # loginData[0] = username, [1] = password, [2] = action (LOGIN/SIGNUP)

        username = loginData["username"]
        password = loginData["password"]  # not going to be ""
        action = loginData["action"]
        response_packet = ""

        success = False
        if action == "LOGIN":
            print("login")
            print(username + " is username")
            print(password + " is password")
            print(action + " is action")

            if username == "":
                response_packet = struct.pack("!bbb", s.CMDS["ERROR"], s.ERRORSBYTES["ERROR: username is empty"],
                                              s.ERRORSBYTES["try again"])
            elif password == "":
                response_packet = struct.pack("!bbb", s.CMDS["ERROR"], s.ERRORSBYTES["ERROR: password is empty"],
                                              s.ERRORSBYTES["try again"])
            else:
                userToken = self.handleLogin(username, password)
                print(userToken)
                if userToken == 404:
                    response_packet = struct.pack("!bbb", s.CMDS["ERROR"], s.ERRORSBYTES["ERROR: with login"],
                                                  s.ERRORSBYTES["NO USER FOUND"])
                else:
                    success = True
                    response_packet = self.createResponsePacket(userToken)


        elif action == "SIGNUP":
            print("signup")
            print(username + " is username")
            print(password + " is password")
            print(action + " is action")
            if username == "":
                response_packet = struct.pack("!bbb", s.CMDS["ERROR"], s.ERRORSBYTES["ERROR: username is empty"],
                                              s.ERRORSBYTES["try again"])
            elif password == "":
                response_packet = struct.pack("!bbb", s.CMDS["ERROR"], s.ERRORSBYTES["ERROR: password is empty"],
                                              s.ERRORSBYTES["try again"])
            else:
                userToken = self.handleSignup(username, password)
                print(userToken)
                if userToken == "ALREADY FOUND":
                    response_packet = struct.pack("!bbb", s.CMDS["ERROR"], s.ERRORSBYTES["ERROR: with signup"],
                                                  s.ERRORSBYTES["User already found"])
                else:
                    success = True
                    response_packet = self.createResponsePacket(userToken)

        # Send response and CLOSE this specific client connection
        # SEND TO LOAD BALANCER
        # pk = struct.pack("!b16s", S.CMDS["LOGIN_TO_LB"], userToken)
        if success:
            self.login_server.send(self.loadbalancer_id, response_packet)

        try:
            self.login_server.send(connection_id, response_packet)
            print(f"Handled {action} for {username}. Response sent.")
        except Exception as e:
            print(f"Error handling request: {e}")


def getStarterPack():
    x, y = get_random_position()
    return x, y, 100, 1, 0, 0, 0, 0, 0, 0, 0


def get_random_position():
    # Choose a random server
    server_index = random.randint(0, s.SERVER_NUMBER - 1)
    server = s.SERVERS[server_index]

    left = server["x"]
    right = server["x"] + s.SERVER_WIDTH

    # Remove overlap zones
    if server_index > 0:
        left += s.OVERLAP_WIDTH

    if server_index < s.SERVER_NUMBER - 1:
        right -= s.OVERLAP_WIDTH

    while True:

        # Random position inside safe horizontal zone
        x = random.randint(left, right - 1)
        y = random.randint(0, s.MAP_HEIGHT - 1)
        if (not check_collision_with_stone(x, y, s.PLAYER_SIZE)
                and not check_collision_with_lava(x, y, s.PLAYER_SIZE)):  # and collision with lava
            return x, y


def check_collision_with_stone(next_x, next_y, size):  # True = blocked (stone/outside)
    corners = get_corners(next_x, next_y, size)

    for px, py in corners:  # test each corner
        tile_x = int(px // s.TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // s.TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= s.WIDTH or tile_y < 0 or tile_y >= s.HEIGHT:
            return True

        if m.MAP[tile_y][tile_x] == "x":
            return True
    return False


def check_collision_with_lava(next_x, next_y, size):  # True = lava
    corners = get_corners(next_x, next_y, size)

    for px, py in corners:  # test each corner
        tile_x = int(px // s.TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // s.TILE_SIZE)  # pixel -> tile row
        if tile_x < 0 or tile_x >= s.WIDTH or tile_y < 0 or tile_y >= s.HEIGHT:
            continue
        if m.MAP[tile_y][tile_x] == "b":
            return True
    return False


def get_corners(x, y, size):
    left, right, top, bottom = get_sides(x, y, size)
    corners = [  # 4 corners
        (left, top),
        (right, top),
        (left, bottom),
        (right, bottom),
    ]

    return corners


def get_sides(x, y, size):
    left = x - size // 2  # player box left (pixels)
    right = x + size // 2 - 1  # player box right (pixels)
    top = y - size // 2  # player box top (pixels)
    bottom = y + size // 2 - 1  # player box bottom (pixels)

    return left, right, top, bottom


if __name__ == '__main__':
    login_server = Login()
    asyncio.run(login_server.run())
