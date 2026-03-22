LOGIN_SERVER = {
    "ip": "127.0.0.1",
    "port": 7080
}

LOAD_BALANCER = {
    "ip": "127.0.0.1",
    "port": 8050,
}

MAP_WIDTH = 1920 * 40

OVERLAP_WIDTH = 6000
SERVER_NUMBER = 4
SERVER_WIDTH = (MAP_WIDTH + (SERVER_NUMBER - 1) * OVERLAP_WIDTH) // SERVER_NUMBER

SERVER_STEP = SERVER_WIDTH - OVERLAP_WIDTH
BASE_IP = "127.0.0.1"
BASE_PORT = 9000

SERVERS = [
    {
        "x": i * SERVER_STEP,
        "ip": BASE_IP,
        "port": BASE_PORT + i,
        "width": SERVER_WIDTH,
    }
    for i in range(SERVER_NUMBER)
]

WIDTH = 1920
HEIGHT = 1080

MAP_WIDTH = 1920 * 40
MAP_HEIGHT = 1080 * 40

TILE_SIZE = 40
PLAYER_SIZE = 38

ERRORSBYTES = {
    "ERROR: username is empty": 0x01,
    "ERROR: password is empty": 0x02,
    "ERROR: with signup": 0x03,
    "try again": 0x04,
    "ERROR: with loginserver": 0x05,
    "User already found": 0x06,
    "NO USER FOUND": 0x07,
}

CMDS = {
    "INIT_POS": 0x01,
    "MOVE": 0x02,
    "OVERLAP": 0x03,
    "SWITCH_SERVER": 0x04,
    "POS_DONT_RESPOND": 0x05,
    "INIT_LB": 0x06,
    "LB_ADDING_PLAYER": 0x07,
    "RENDER": 0x08,
    "DAMAGE": 0x09,
    "RESPAWN": 0x0A,
    "ATTACK": 0x0B,
    "OUT_OF_OVERLAP": 0x0C,
    "REMOVE_ME": 0x0D,
    "HP_DONT_RESPOND": 0x0E,
    "CHANGE_WEAPON": 0x0F,
    "ADD_ME": 0x10,
    "FART": 0x11,
    "HELLO": 0x12,
    "LOGIN_TO_LB": 0x13,
    "CLIENT_DATA": 0x14,
    "DELETE_ITEM": 0x15,
    "FART_READY": 0x16,
    "PICKUP_ITEM": 0x17,
    "ADD_ITEM": 0x18,
    "TRANSFER_P": 0x19,
    "HELLO_FROM_LB": 0x1A,
    "INVIS": 0x1B,
    "LASER": 0x1C,
    "BRIT": 0x1D,
    "FARTING": 0x1E,
    "ERROR": 0x1F,
    "PLAYER_LEFT": 0x20,
    "TELEPORT_READY": 0x21,
    "TELEPORT": 0x22,
}

BASIC_INV = ['da', 'gu', 0, 0, 0, 0, 0, 0]
INVENTORY_SIZE = len(BASIC_INV)
