import asyncio
import hashlib
import json
import secrets
import sqlite3
import string
import os

from login.loginServer import player_info_update
from wrappers.server_wrapper import QuicServer

#DB_PATH = r"C:\Users\USER\PycharmProjects\PythonProject\Cyber-Proj-main\loginServerBasics\game.db"
#DB_PATH = r"C:\Users\Itay\PycharmProjects\cyberproject\quic\game.db"
DB_PATH = r"C:\Users\USER\PycharmProjects\cyberproject\quic\game.db"


class LoginServer:

    def __init__(self):
        self.server = QuicServer(
            ip="127.0.0.1",
            port=8080,
            cert_file="../certificate/cert.pem",
            key_file="../certificate/key.pem",
            on_receive=self.on_receive,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        )

    def on_receive(self, connection_id: int, data: bytes):

        raw_data = data.decode()
        if not raw_data: return
        #if connection_id == self.loadbalancer_id:
            #self.handle_load_balancer(self, raw_data, connection_id)

        #else:
        handle_login_client(self, raw_data, connection_id)

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    async def run(self):
        await self.server.start()
        print("Server started")

        #loadbalancer_id = await self.server.connect_to_server()

        try:
            await asyncio.Future()

        except asyncio.CancelledError:
            print("Server shutting down...")

        finally:
            await self.server.stop()
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

def handle_login_client(self, raw_data, connection_id):
       # still needs to make a new one also for the updating
       # in general make a new system that will be hashed with quic and will not be easy manupulated like the seperation with = sign
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
               game_server_ip = self.sendTokenToLB(userToken)
               response_packet = f"OK={userToken}={game_server_ip}"


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
               game_server_ip = self.sendTokenToLB(userToken)
               response_packet = f"OK={userToken}={game_server_ip}"

       # Send response and CLOSE this specific client connection

       print(response_packet)

       try:
           self.server.send(connection_id, response_packet.encode())
           print(f"Handled {action} for {username}. Response sent.")
       except Exception as e:
           print(f"Error handling request: {e}")



if __name__ == '__main__':
    s = LoginServer()
    asyncio.run(s.run())
