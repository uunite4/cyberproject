import asyncio
import hashlib
import json
import random
import secrets
import sqlite3
import string
import os
import struct

import SETTINGS as S
from networking.wrappers.server_wrapper import QuicServer
from serverBorders.Player import check_collision_with_lava, check_collision_with_stone

#DB_PATH = r"C:\Users\USER\PycharmProjects\PythonProject\Cyber-Proj-main\loginServerBasics\game.db"
#DB_PATH = r"C:\Users\Itay\PycharmProjects\cyberproject\quic\game.db"
DB_PATH = r"game.db"


def player_info_update(key, x_position, y_position, health, team, direaction):
    with sqlite3.connect(DB_PATH, timeout=5) as conn:
        curser = conn.cursor()
        curser.execute("""UPDATE last_save SET x position = ?,y position = ?, health = ?, team = ?, direaction = ? WHERE token = ?""",(x_position, y_position, health, team, direaction,key))
        conn.commit()
        conn.close()
        print(f"Successfully updated stats for Player {key}")

class LoginServer:

    def __init__(self):
        self.server = QuicServer(
            ip=S.LOGIN_SERVER["ip"],
            port=S.LOGIN_SERVER["port"],
            cert_file="../networking/certificate/cert.pem",
            key_file="../networking/certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )

    def on_receive(self, connection_id: int, data: bytes):
        if (connection_id == self.loadbalancer_id):
            pass
        else:
            print("got client data")
            raw_data = data.decode()
            print(data)
            if not raw_data: return
            print("running login handle")
            handle_login_client(self, raw_data, connection_id)


    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    async def run(self):
        await self.server.start()
        print("Server started")
        await asyncio.Future()
        self.loadbalancer_id = await self.server.connect_to_server(
            ip=S.LOAD_BALANCER["ip"],
            port=S.LOAD_BALANCER["port"],
        )

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

    def player_inventory_upload(self, item1, item2, item3, item4, item5, item6, item7, item8, item9, item10, token):
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            # You must list every column you want to update
            cursor.execute("""UPDATE inventory 
                            SET item1 = ?, item2 = ?, item3 = ?, item4 = ?, item5 = ?,
                                item6 = ?, item7 = ?, item8 = ?, item9 = ?, item10 = ?
                            WHERE token = ?""",
                           (item1, item2, item3, item4, item5, item6, item7, item8, item9, item10, token))
            conn.commit()
            conn.close()
            print("invertory uploaded!")
    def player_info_update(self, token, x_position, y_position, health, team, direaction, item1, item2, item3, item4, item5, item6, item7, item8, item9, item10):
        self.player_inventory_upload(item1, item2, item3, item4, item5, item6, item7, item8, item9, item10, token)
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            curser = conn.cursor()
            curser.execute("""UPDATE last_save
                              SET x_position = ?,
                                  y_position = ?,
                                  health     = ?,
                                  team       = ?,
                                  direaction = ?
                              WHERE token = ?""", (x_position, y_position, health, team, direaction, token))

            conn.commit()
            conn.close()
            print(f"Successfully updated stats for Player {token}")

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

        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            # You MUST have a 'salt' column in your 'login' table
            cursor.execute("INSERT INTO login (username, password, salt, token) VALUES (?, ?, ?, ?)",
                           (username, pass_hash, salt, token))
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

    def handle_load_balancer(self, raw_data, connection_id):
        loginData = json.loads(raw_data)

        token = loginData["token"]
        x_position = loginData["x_position"]
        y_position = loginData["y_position"]
        health = loginData["health"]
        team = loginData["team"]
        direaction = loginData["direaction"]
        item1 = loginData["item1"]
        item2 = loginData["item2"]
        item3 = loginData["item3"]
        item4 = loginData["item4"]
        item5 = loginData["item5"]
        item6 = loginData["item6"]
        item7 = loginData["item7"]
        item8 = loginData["item8"]
        item9 = loginData["item9"]
        item10 = loginData["item10"]
        self.player_info_update(token, x_position, y_position, health, team, direaction,item1, item2, item3, item4, item5, item6, item7, item8, item9, item10)
        print("updated successfully!")
        response_packet = f"OK={token}={connection_id}"
        try:
            self.server.send(connection_id, response_packet.encode())
            print(f"Handled update info for {connection_id}. Response sent.")
        except Exception as e:
            print(f"Error handling request: {e}")

    def createStarterPack(self, token, x, y):
        self.player_info_update(token, x, y, 100, 1, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    def createResponsePacket(self, tkn, serverIndex):
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Find the user first to get THEIR specific salt
            cursor.execute("SELECT * FROM last_save WHERE token = ?", (tkn))
            user_row = cursor.fetchone()

            # Basics
            playerX = user_row["x_position"]
            playerY = user_row["y_position"]
            playerHealth = user_row["health"]
            playerInventory = []

            # Inventory
            for i in range(1, 11):
                itemslot = user_row["item" + str(i)]
                playerInventory.append(itemslot)

            i = 0
            while serverIndex is None:
                curServer = S.SERVERS[i]
                if (playerX > curServer["x"] and playerX < curServer["x"] + curServer["width"]):
                    serverIndex = i
                i += 1

            pk = struct.pack("!b16sbhhbbbbbbbbbbb", S.CMDS["LOGIN_BACK_TO_CLIENT"], tkn, serverIndex, playerX, playerY, playerHealth, *playerInventory)
            return pk

def handle_login_client(self, raw_data, connection_id):
   # still needs to make a new one also for the updating
   # in general make a new system that will be hashed with quic and will not be easy manupulated like the seperation with = sign
   global userToken
   global pk
   loginData = json.loads(raw_data)
   # loginData[0] = username, [1] = password, [2] = action (LOGIN/SIGNUP)

   username = loginData["username"]
   password = loginData["password"]  # not going to be ""
   action = loginData["action"]
   response_packet = ""

   if action == "LOGIN":
       print("login")
       print(username + " is username")
       print(password + " is password")
       print(action + " is action")
       userToken = self.handleLogin(username, password)
       print(userToken)

       if username == "":
           response_packet = "ERROR=ERROR: username is empty= try again"
       elif password == "":
           response_packet = "ERROR=ERROR: password is empty= try again"
       elif userToken == 404:
           response_packet = "ERROR=ERROR: with login=NO USER FOUND"
       else:
           pk = self.createResponsePacket(userToken, None)


   elif action == "SIGNUP":
       print("signup")
       print(username + " is username")
       print(password + " is password")
       print(action + " is action")
       userToken = self.handleSignup(username, password)
       print(userToken)
       if username == "":
           response_packet = "ERROR=ERROR: username is empty= try again"
       elif password == "":
           response_packet = "ERROR=ERROR: password is empty= try again"
       elif userToken == "ALREADY FOUND":
           response_packet = "ERROR=ERROR: with signup=User already found"
       else:
           # CREATE STARTER PACK
           x, y, serverI = get_random_position()
           self.createStarterPack(userToken, x, y)
           pk = self.createResponsePacket(userToken, serverI)

    rspk = self.createResponsePacket(userToken)
    # SEND TO LOAD BALANCER
   pk = struct.pack("!b16s", S.CMDS["LOGIN_TO_LB"], userToken)
   self.server.send(self.loadbalancer_id, pk)

def point_in_rect(px, py, rx, ry, w, h):
    return (
        rx <= px <= rx + w and
        ry <= py <= ry + h
    )

def get_random_position():
    # Choose a random server
    server_index = random.randint(0, S.SERVER_NUMBER - 1)
    server = S.SERVERS[server_index]

    left = server["x"]
    right = server["x"] + S.SERVER_WIDTH

    # Remove overlap zones
    if server_index > 0:
        left += S.OVERLAP_WIDTH

    if server_index < S.SERVER_NUMBER - 1:
        right -= S.OVERLAP_WIDTH

    while True:
        # Random position inside safe horizontal zone
        x = random.randint(left, right - 1)
        y = random.randint(0, S.MAP_HEIGHT - 1)
        if not check_collision_with_stone(x,y,S.PLAYER_SIZE) and not check_collision_with_lava(x,y,S.PLAYER_SIZE): #and collision with lava
            return x, y, server_index

if __name__ == '__main__':
    s = LoginServer()
    asyncio.run(s.run())
