import socket
import userDBController as db
import secrets
import string
import sqlite3

LOGIN_SERVER_IP = "127.0.0.1"
LOGIN_SERVER_PORT = 8080
DB_PATH = r"C:\Users\USER\PycharmProjects\PythonProject\Cyber-Proj-main\game.db"


def generateToken(length=16):
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for i in range(length))
    return token

def intialize():
    loginSocket = socket.socket()
    loginSocket.bind((LOGIN_SERVER_IP, LOGIN_SERVER_PORT))
    loginSocket.listen()
    return loginSocket

def recieveData(loginSocket):
    (client_socket, client_address) = loginSocket.accept()
    print("Client connected")

    loginData = client_socket.recv(1024).decode()
    return loginData.split("="), client_socket, client_address


def handleLogin(loginData):
    # We unpack the tuple (username, password) into two variables
    username, password = loginData[0], loginData[1]

    # Open the connection to our 'smart file' (the database)
    conn = sqlite3.connect(DB_PATH)

    # This tells the librarian: "Bring me results as Dictionaries, not just lists"
    # This allows us to use user['token'] instead of user[0]
    conn.row_factory = sqlite3.Row

    # Create the Librarian (Cursor) who will do the work
    cursor = conn.cursor()

    # THE COMMAND: Look for a row where BOTH username AND password match.
    # The '?' are placeholders to prevent hackers from deleting our DB (SQL Injection)
    cursor.execute("SELECT token FROM login WHERE username = ? AND password = ?", (username, password))

    # We ask the cursor to give us the ONE result he found
    user = cursor.fetchone()

    # Always close the connection so the file isn't 'locked'
    conn.close()

    if user:
        # If the user exists, return their stored token
        return user['token']
    else:
        # If no user was found, return our error code
        return 404


def handleSignup(loginData):
    username, password = loginData[0], loginData[1]

    # Re-use our check function. If handleLogin doesn't return 404, the user exists!
    if handleLogin(loginData) != 404:
        return "ALREADY FOUND"

    # Create a fresh, unique token for this new user
    token = generateToken()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Insert into the 'login' table
        cursor.execute("INSERT INTO login (username, password, token) VALUES (?, ?, ?)",
                       (username, password, token))

        # This is magic: it gets the 'ID' number SQLite just created for this user
        #last_id = cursor.lastrowid

        # 2. Use that SAME ID to create a 'save file' in the PlayerData table
        # This 'links' the two tables together!
        # and also it is a comment until we need it and have a playerData table
        #cursor.execute("INSERT INTO PlayerData (user_id, level, gold) VALUES (?, ?, ?)",
                       #(last_id, 1, 100))

        # Nothing is saved to the file until you COMMIT.
        # This is like clicking 'Save' in a Word document.
        conn.commit()
        return token

    except sqlite3.IntegrityError:
        # If the 'Unique' constraint on 'username' fails, it jumps here
        return "ALREADY FOUND"
    finally:
        # This runs NO MATTER WHAT (even if there was an error) to close the file
        conn.close()

def sendTokenToLB(token):
    # WE ACTUALLY NEED A CONNECTION HERE BUT BECAUSE
    # WE DONT HAVE A LOAD BALANCER I'M JUST GOING TO RETURN
    # A MADE-UP IP THAT IS SUPPOSE TO BE THE IP OF THE GAME SERVER.
    return "38.97.84.242"


def main():
    loginSocket = intialize()
    loginData, clientSocket, clientAddress = recieveData(loginSocket)
    global userToken
    if (loginData[2] == "LOGIN"):                                   # LOGIN
        userToken = handleLogin(loginData)
        if (userToken == 404):
            pk = "ERROR=ERROR: NO USER FOUND"
            clientSocket.send(pk.encode())
            clientSocket.close()
            return
    else:                                                           # SIGNUP
        userToken = handleSignup(loginData)
        if (userToken == "ALREADY FOUND"):
            pk = "ERROR=ERROR: USER ALREADY FOUND"
            clientSocket.send(pk.encode())
            clientSocket.close()
            return

    # NOW WE GOT THE TOKEN (WHETHER WE CREATED A NEW USER OR JUST AUTHENTICATED THEM)
    gameServerIP = sendTokenToLB(userToken)
    pk = "OK=" + userToken + "=" + gameServerIP
    clientSocket.send(pk.encode())
    clientSocket.close()

if __name__ == "__main__":
    main()