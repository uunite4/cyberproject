import socket
import secrets
import string
import sqlite3

# --- CONFIGURATION ---
LOGIN_SERVER_IP = "127.0.0.1"
LOGIN_SERVER_PORT = 8080
DB_PATH = r"C:\Users\USER\PycharmProjects\PythonProject\Cyber-Proj-main\loginServerBasics\game.db"


def player_info_update(key, x_position, y_position, health, team, direaction):
    with sqlite3.connect(DB_PATH, timeout=5) as conn:
        curser = conn.cursor()
        curser.execute("""UPDATE last save SET x position = ?,y position = ?, health = ?, team = ?, direaction = ? WHERE key = ?""",(x_position, y_position, health, team, direaction,key))
        conn.commit()
        conn.close()
        print(f"Successfully updated stats for Player {key}")

def get_unique_token():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    while True:
        # 1. Generate a potential token
        new_token = generateToken()

        # 2. Ask the DB if anyone is already using it
        cursor.execute("SELECT 1 FROM login WHERE token = ?", (new_token,))
        exists = cursor.fetchone()

        # 3. If 'exists' is None, the token is unique!
        if not exists:
            conn.close()
            return new_token

        # If it's NOT None, the loop runs again to try a different token
def generateToken(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def initialize():
    loginSocket = socket.socket()
    # Allow the OS to reuse the port immediately after a restart (prevents "Address already in use")
    loginSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    loginSocket.bind((LOGIN_SERVER_IP, LOGIN_SERVER_PORT))
    loginSocket.listen(5)  # Listen for up to 5 queued connections
    print(f"Server started on {LOGIN_SERVER_IP}:{LOGIN_SERVER_PORT}")
    return loginSocket


def handleLogin(username, password):
    with sqlite3.connect(DB_PATH, timeout=5) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT token FROM login WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        return user['token'] if user else 404


def handleSignup(username, password):
    if handleLogin(username, password) != 404:
        return "ALREADY FOUND"

    token = get_unique_token()
    try:
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO login (username, password, token) VALUES (?, ?, ?)",
                           (username, password, token))
            # Optional: cursor.execute("INSERT INTO PlayerData...")
            conn.commit()
            return token
    except sqlite3.IntegrityError:
        return "ALREADY FOUND"


def sendTokenToLB(token):
    return "38.97.84.242"  # Mock IP for game server


def main():
    loginSocket = initialize()

    # --- THE INFINITE LOOP ---
    # This keeps the server alive for player after player
    while True:
        try:
            print("\nWaiting for a new client...")
            (clientSocket, clientAddress) = loginSocket.accept()
            print(f"Client connected from {clientAddress}")

            # Receive the data
            raw_data = clientSocket.recv(1024).decode()
            if not raw_data: continue  # Skip if empty

            loginData = raw_data.split("=")
            # loginData[0] = username, [1] = password, [2] = action (LOGIN/SIGNUP)

            username = loginData[0]
            password = loginData[1]
            action = loginData[2]           #not going to be ""

            response_packet = ""


            if action == "LOGIN":
                print("login")
                print(username + " is username")
                print(password + " is password")
                print(action + " is action")
                userToken = handleLogin(username, password)
                print(userToken)

                if username == "":
                    response_packet = "ERROR=ERROR: username is empty= try again"
                elif password == "":
                    response_packet = "ERROR=ERROR: password is empty= try again"
                elif userToken == 404:
                    response_packet = "ERROR=ERROR: with login=NO USER FOUND"
                else:
                    gameServerIP = sendTokenToLB(userToken)
                    response_packet = f"OK={userToken}={gameServerIP}"

            elif action == "SIGNUP":
                print("signup")
                print(username + " is username")
                print(password + " is password")
                print(action + " is action")
                userToken = handleSignup(username, password)
                print(userToken)
                if username == "":
                    response_packet = "ERROR=ERROR: username is empty= try again"
                elif password == "":
                    response_packet = "ERROR=ERROR: password is empty= try again"
                elif userToken == "ALREADY FOUND":
                    response_packet = "ERROR=ERROR: with signup=User already found"
                else:
                    gameServerIP = sendTokenToLB(userToken)
                    response_packet = f"OK={userToken}={gameServerIP}"

            # Send response and CLOSE this specific client connection

            print(response_packet)
            clientSocket.send(response_packet.encode())
            clientSocket.close()
            print(f"Handled {action} for {username}. Response sent.")

        except Exception as e:
            print(f"Error handling request: {e}")


if __name__ == "__main__":
    main()