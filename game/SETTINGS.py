from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
from game.map_data import MAP

WIDTH = 1920
HEIGHT = 1080
MAP_WIDTH = 1920*40
MAP_HEIGHT = 1080*40
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
BROADCAST_INTERVAL = 0.01

PLAYER_VEL = 5
PLAYER_SIZE = 38
PLAYER_HEALTH =100

TILE_SIZE = 40
BUILDING_SIZE = 40

#Obgects
grass='sprites\\tiles\\grass.png'
stone='sprites\\tiles\\stone.png'
lava = 'sprites\\tiles\\lava.png'
tree ='sprites\\tiles\\tree.png'
pesel= 'sprites\\tiles\\statue.png'
marble = 'sprites\\tiles\\marble.png'
bitmikdash = 'sprites\\tiles\\statue.png'
ostone='sprites\\tiles\\blackstone.png'
poop = 'sprites\\inventory\\poop.png'
inventory1 = 'sprites\\inventory\\inventory.png'
select1 = 'sprites\\inventory\\select.png'
dagger = 'sprites\\weapons\\DAGGER-NORTH.png'
fart = 'sprites\\FARTS.png'
lazer = 'sprites\\weapons\\lazer.png'
gun = 'sprites\\weapons\\gun.png'
lcon1 = 'sprites\\weapons\\Icon1.png'
lcon5 = 'sprites\\weapons\\Icon5.png'
lcon28 = 'sprites\\weapons\\Icon28.png'
bolbol = 'sprites\\weapons\\bolbol.png'
scissors = 'sprites\\weapons\\scissors.png'

OVERLAP_WIDTH = 6000
SERVER_NUMBER = 4

GENERAL_OVERLAP = {
    "width" : OVERLAP_WIDTH,
    "color": (55, 53, 62)
}

# Calculate server width so total span = WINDOW_WIDTH
SERVER_WIDTH = (MAP_WIDTH + (SERVER_NUMBER - 1) * OVERLAP_WIDTH) // SERVER_NUMBER

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
}

ERRORSBYTES = {
    "ERROR: username is empty": 0x01,
    "ERROR: password is empty": 0x02,
    "ERROR: with signup": 0x03,
    "try again": 0x04,
    "ERROR: with login-server": 0x05,
    "User already found": 0x06,
    "NO USER FOUND": 0x07,
}
BYTESERRORS = {
    0x01: "ERROR: username is empty",
    0x02: "ERROR: password is empty",
    0x03: "ERROR: with signup",
    0x04: "try again",
    0x05: "ERROR: with login-server",
    0x06: "User already found",
    0x07: "NO USER FOUND",
}

LOAD_BALANCER = {
    "ip": "127.0.0.1",
    "port": 8050,
}

#HEALTH SPRITE SETTINGS
HEALTH_BAR_SIZE_X = 120
HEALTH_BAR_SIZE_Y = 30
S_HEALTH_BAR_SIZE_X = 40
S_HEALTH_BAR_SIZE_Y = 10

#bullet settings
BULLET_DISTANS =100
BULLET_SPEED = 15
BULLET_COOLDOWN = 10
BULLET_DAMEG = 10
BULLET_SIZE = 5

#fart settings
FART_RUADIOS=100
FART_TIME = 200
FART_COOLDOWN = 2000
FART_DAMEG = 0.3

#inventory
BASIC_INV = ['da',0,0,0,0,0,0,0]
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

#POTIONS
SPEED_POSSION_TIME = 500
INVESIBEL_TIME = 500

#LASER
LASER_TIME = 30
LASER_COOLDOWN = 200
LASER_DAMEG =20
LASER_DIS = 400

#BRIT-MILA
BRIT_TIMER = 3000


# LOGIN AREA
LOGIN_SERVER = {
    "ip": "127.0.0.1",
    "port": 7080
}

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

# DEBUG
login = True


#MONSTERS
MONSTERS = {
    "GOBLIN" : { #some sort of monster
        "health" : 50, #starter health
        "speed" : 2,
        "see_radius" : 400, #going to players in this range
        "att_radius" : 200, #attack players in this range
        "damage" : 20,
        "size" : 30, #of sprite
        "code" : 0,
    },
    "BEAR" : { #some sort of monster
        "health" : 70, #starter health
        "speed" : 1,
        "see_radius" : 400, #going to players in this range
        "att_radius" : 200, #attack players in this range
        "damage" : 30,
        "size" : 40, #of sprite
        "code" : 1,
    }
}
