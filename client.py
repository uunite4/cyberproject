import socket

USERNAME_INPUT = ""
PASSWORD_INPUT = ""
STATE_CONNECTION = ""
LOGIN_SERVER_IP = "127.0.0.1"
LOGIN_SERVER_PORT = 8080

def getInput():
    global USERNAME_INPUT, PASSWORD_INPUT, STATE_CONNECTION
    USERNAME_INPUT = input("Username: ")
    PASSWORD_INPUT = input("Password: ")
    if (input("New User? ") == "Y"):
        STATE_CONNECTION = "SIGNUP"
    else:
        STATE_CONNECTION = "LOGIN"

def SendLoginInfo():
    clientSocket = socket.socket()
    clientSocket.connect((LOGIN_SERVER_IP, LOGIN_SERVER_PORT))
    # BUILD PACKET
    pk = USERNAME_INPUT + "=" + PASSWORD_INPUT + "=" + STATE_CONNECTION
    clientSocket.send(pk.encode())
    return clientSocket

def getResponse(clientSocket):
    res = clientSocket.recv(1024).decode()
    return res.split("=")

def main():
    getInput()
    clientSocket = SendLoginInfo()
    resArry = getResponse(clientSocket)
    if (resArry[0] == "OK"):
        print("Token: " + resArry[1] +"\nGame Server IP: " + resArry[2])
    else:
        # WE GOT AN ERROR
        print(resArry[1])
    clientSocket.close()

if __name__ == "__main__":
    main()