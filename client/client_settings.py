import json
import os
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


CONFIG_PATH = resource_path("config.json")


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


config = load_config()

LOGIN_SERVER = config["login_server"]

CHAT_SERVER_IP = config["chat_server"]["ip"]
CHAT_SERVER_PORT = config["chat_server"]["port"]

SERVERS_ADDRESSES = config["servers"]

WIDTH = 1920
HEIGHT = 1080
MAP_WIDTH = 1920 * 40
MAP_HEIGHT = 1080 * 40
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
BROADCAST_INTERVAL = 0.01

PLAYER_VEL = 5
PLAYER_SIZE = 38
PLAYER_HEALTH = 100

TILE_SIZE = 40
BUILDING_SIZE = 40

# Obgects
grass = resource_path('sprites\\tiles\\grass.png')
stone = resource_path('sprites\\tiles\\stone.png')
lava = resource_path('sprites\\tiles\\lava.png')
tree = resource_path('sprites\\tiles\\tree.png')
pesel = resource_path('sprites\\tiles\\statue.png')
marble = resource_path('sprites\\tiles\\marble.png')
bitmikdash = resource_path('sprites\\tiles\\statue.png')
ostone = resource_path('sprites\\tiles\\blackstone.png')
log = resource_path('sprites\\obstacles\\log.png')
tree_1 = resource_path('sprites\\obstacles\\tree_1.png')
tree_2 = resource_path('sprites\\obstacles\\tree_2.png')
poop = resource_path('sprites\\inventory\\poop.png')
inventory1 = resource_path('sprites\\inventory\\inventory.png')
select1 = resource_path('sprites\\inventory\\select.png')
dagger = resource_path('sprites\\weapons\\DAGGER-NORTH.png')
fart = resource_path('sprites\\FARTS.png')
lazer = resource_path('sprites\\weapons\\lazer.png')
gun = resource_path('sprites\\weapons\\gun.png')
lcon1 = resource_path('sprites\\weapons\\Icon1.png')
lcon5 = resource_path('sprites\\weapons\\Icon5.png')
lcon28 = resource_path('sprites\\weapons\\Icon28.png')
bolbol = resource_path('sprites\\weapons\\bolbol.png')
scissors = resource_path('sprites\\weapons\\scissors.png')

OVERLAP_WIDTH = 6000
SERVER_NUMBER = 4

# Calculate server width so total span = WINDOW_WIDTH
SERVER_WIDTH = (MAP_WIDTH + (SERVER_NUMBER - 1) * OVERLAP_WIDTH) // SERVER_NUMBER

# Distance between the left side of each server
SERVER_STEP = SERVER_WIDTH - OVERLAP_WIDTH

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

BYTESERRORS = {
    0x01: "ERROR: username is empty",
    0x02: "ERROR: password is empty",
    0x03: "ERROR: with signup",
    0x04: "try again",
    0x05: "ERROR: with loginserver",
    0x06: "User already found",
    0x07: "NO USER FOUND",
}

# HEALTH SPRITE SETTINGS
HEALTH_BAR_SIZE_X = 120
HEALTH_BAR_SIZE_Y = 30
S_HEALTH_BAR_SIZE_X = 40
S_HEALTH_BAR_SIZE_Y = 10

# bullet settings
BULLET_DISTANS = 100
BULLET_SPEED = 10
BULLET_COOLDOWN = 10
BULLET_DAMEG = 10
BULLET_SIZE = 5

# fart settings
FART_RUADIOS = 100
FART_TIME = 200
FART_COOLDOWN = 2000
FART_DAMEG = 0.3

# teleport settings
TELEPORT_RANGE = 200
TELEPORT_COOLDOWN = 1000

# inventory
BASIC_INV = ['da', 'gu', 0, 0, 0, 0, 0, 0]
INVENTORY_SIZE = len(BASIC_INV)

INVENTORY_MAP = {
    0: 0,
    1: "da",
    2: "gu",
    3: "h",
    4: "s",
    5: "i",
    6: "b",
    7: "la"
}

# POTIONS
SPEED_POSSION_TIME = 500
INVESIBEL_TIME = 500

# LASER
LASER_TIME = 30
LASER_COOLDOWN = 200
LASER_DAMEG = 20
LASER_DIS = 400

# BRIT-MILA
BRIT_TIMER = 3000

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

# DEBUG
login = True

# MONSTERS
MONSTERS = {
    "GOBLIN": {  # some sort of monster
        "health": 50,  # starter health
        "speed": 2,
        "see_radius": 400,  # going to players in this range
        "att_radius": 200,  # attack players in this range
        "damage": BULLET_DAMEG,
        "size": 30,  # of sprite
        "code": 0,
        "type": "ranged",
    },
    "BEAR": {  # some sort of monster
        "health": 70,  # starter health
        "speed": 1,
        "see_radius": 400,  # going to players in this range
        "att_radius": 25,  # attack players in this range
        "damage": BULLET_DAMEG * 2,
        "size": 40,  # of sprite
        "code": 1,
        "type": "melee",
    }
}

ENEMY_COOLDOWN = 0.5

CHAT_WIDTH: int = 480
CHAT_HEIGHT: int = 540

CHAT_MAX_INPUT_WIDTH = CHAT_WIDTH - 100
CHAT_BG_COLOR = (30, 30, 30)
CHAT_TEXT_COLOR = (220, 220, 220)
CHAT_INPUT_BG = (50, 50, 50)
CHAT_USERNAME_COLOR = (100, 200, 255)

CHAT_MESSAGE_AMOUNT: int = 15
CHAT_SERVER_SEND_FPS: int = 10
