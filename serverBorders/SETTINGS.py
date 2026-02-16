from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
CERT = str(BASE_DIR.parent / "auth" / "cert.pem")
KEY = str(BASE_DIR.parent / "auth" / "key.pem")
PLAYER_VEL = 3

OVERLAP_WIDTH = 300

OVERLAP = {
    "width" : OVERLAP_WIDTH,
    "color": (28, 173, 28),
    "x": WINDOW_WIDTH // 2 - OVERLAP_WIDTH // 2
}

SERVERS_WIDTH = WINDOW_WIDTH // 2 + OVERLAP["width"] // 2

SERVER1 = {
    "width": SERVERS_WIDTH,
    "color": (173, 28, 28),
    "x": 0,
    "ip": "127.0.0.1",
    "port": 8081
}

SERVER2 = {
    "width": SERVERS_WIDTH,
    "color": (28, 28, 176),
    "x": WINDOW_WIDTH // 2 - OVERLAP["width"] // 2,
    "ip": "127.0.0.1",
    "port": 8082
}

CMDS = {
    "INIT_POS": 0x01,
    "MOVE": 0x02,
    "MOVE+OVERLAP": 0x03,
    "MOVE+SWITCH_SERVER": 0x03,
}
