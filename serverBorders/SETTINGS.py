from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
PLAYER_VEL = 10
PLAYER_SIZE = 40
BROADCAST_INTERVAL = 0.01

OVERLAP_WIDTH = 60
SERVER_NUMBER = 4

GENERAL_OVERLAP = {
    "width" : OVERLAP_WIDTH,
    "color": (55, 53, 62)
}

# Calculate server width so total span = WINDOW_WIDTH
SERVER_WIDTH = (WINDOW_WIDTH + (SERVER_NUMBER - 1) * OVERLAP_WIDTH) // SERVER_NUMBER

GENERAL_SERVER = {
    "width" : SERVER_WIDTH,
    "color": (68, 68, 78),
}

# Distance between the left side of each server
SERVER_STEP = SERVER_WIDTH - OVERLAP_WIDTH
BASE_IP = "127.0.0.1"
BASE_PORT = 8081

SERVERS = [
    {
        "x": i * SERVER_STEP,
        "ip": BASE_IP,
        "port": BASE_PORT + i,
        "width": SERVER_WIDTH,
    }
    for i in range(SERVER_NUMBER)
]

OVERLAPS = [
    {"x": i * SERVER_STEP}
    for i in range(1, SERVER_NUMBER)
]

CMDS = {
    "INIT_POS": 0x01,
    "MOVE": 0x02,
    "OVERLAP": 0x03,
    "SWITCH_SERVER": 0x04,
    "POS_DONT_RESPOND": 0x05,
    "INIT_LB": 0x06,
    "LB_ADDING_PLAYER": 0x07,
    "RENDER": 0x08
}

LOAD_BALANCER = {
    "ip": "127.0.0.1",
    "port": 8050,
}