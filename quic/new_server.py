import asyncio
import hashlib
import json
import secrets
import sqlite3
import string

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
        if connection_id == self.loadbalancer_id:
            self.handle_load_balancer(self, raw_data)

        else:
            handle_login_client()

    def on_connect(self, connection_id: int):
        print(f"{connection_id} connected")

    def on_disconnect(self, connection_id: int):
        print(f"{connection_id} disconnected")

    async def run(self):
        await self.server.start()
        print("Server started")

        loadbalancer_id = await self.server.connect_to_server()

        try:
            await asyncio.Future()

        except asyncio.CancelledError:
            print("Server shutting down...")

        finally:
            await self.server.stop()
            print("Server shut down")

    def hash_password(self, password):
        # Returns a fixed-length string 'fingerprint' of the password
        return hashlib.sha256(password.encode()).hexdigest()

    def player_info_update(self, key, x_position, y_position, health, team, direaction):
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            curser = conn.cursor()
            curser.execute("""UPDATE last_save
                              SET x position = ?,
                                  y position = ?,
                                  health     = ?,
                                  team       = ?,
                                  direaction = ?
                              WHERE token = ?""", (x_position, y_position, health, team, direaction, key))
            conn.commit()
            conn.close()
            print(f"Successfully updated stats for Player {key}")

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

    def handleSignup(self, username, password):
        if self.handleLogin(username, password) != 404:
            return "ALREADY FOUND"

        token = self.get_unique_token()
        pass_hash = self.hash_password(password)
        try:
            with sqlite3.connect(DB_PATH, timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO login (username, password, token) VALUES (?, ?, ?)",
                               (username, pass_hash, token))
                # Optional: cursor.execute("INSERT INTO PlayerData...")
                conn.commit()
                return token
        except sqlite3.IntegrityError:
            return "ALREADY FOUND"

    def handleLogin(self, username, password):
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            pass_hash = self.hash_password(password)
            cursor.execute("SELECT token FROM login WHERE username = ? AND password = ?", (username, pass_hash))
            user = cursor.fetchone()
            return user['token'] if user else 404

    def generateToken(self, length=16):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def handle_load_balancer(self, raw_data):
        loginData = json.loads(raw_data)

        key = loginData["key"]
        x_position = loginData["x_position"]
        y_position = loginData["y_position"]
        health = loginData["health"]
        team = loginData["team"]
        direaction = loginData["direaction"]
        self.player_info_update(key, x_position, y_position, health, team, direaction)
        print("updated successfully!")


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
               gameServerIP = self.sendTokenToLB(userToken)
               response_packet = f"OK={userToken}={gameServerIP}"

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
               gameServerIP = self.sendTokenToLB(userToken)
               response_packet = f"OK={userToken}={gameServerIP}"

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
