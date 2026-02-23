from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
PLAYER_VEL = 10
PLAYER_SIZE = 40

OVERLAP_WIDTH = 100
SERVER_NUMBER = 3

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
        "port": BASE_PORT + i
    }
    for i in range(SERVER_NUMBER)
]

OVERLAPS = [
    {"x": i * SERVER_STEP}
    for i in range(1, SERVER_NUMBER)
]

# SERVERS_WIDTH = WINDOW_WIDTH // 2 + OVERLAP["width"] // 2
#
# SERVER1 = {
#     "width": SERVERS_WIDTH,
#     "color": (173, 28, 28),
#     "x": 0,
#     "ip": "127.0.0.1",
#     "port": 8081
# }
#
# SERVER2 = {
#     "width": SERVERS_WIDTH,
#     "color": (28, 28, 176),
#     "x": WINDOW_WIDTH // 2 - OVERLAP["width"] // 2,
#     "ip": "127.0.0.1",
#     "port": 8082
# }
#
CMDS = {
    "INIT_POS": 0x01,
    "MOVE": 0x02,
    "OVERLAP": 0x03,
    "SWITCH_SERVER": 0x04,
    "POS_DONT_RESPOND": 0x05,
}