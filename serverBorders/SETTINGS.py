from pathlib import Path
import pygame
BASE_DIR = Path(__file__).resolve().parent

MAP_WIDTH = 192*40
MAP_HEIGHT = 108*40
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
BROADCAST_INTERVAL = 0.01

PLAYER_VEL = 5
PLAYER_SIZE = 38
PLAYER_HEALTH =100

TILE_SIZE = 40
BUILDING_SIZE = 40
WIDTH = 192
HEIGHT = 108
#Obgects
grass='sprites\grass.png'
stone='sprites\stone.png'
lava = 'sprites\lava.png'
tree ='sprites\\tree.png'
pesel= 'sprites\\statue.png'
marble = 'sprites\marble.png'
bitmikdash = 'sprites\statue.png'
ostone='sprites\\blackstone.png'
poop = 'sprites\poop.png'
inventory1 = 'sprites\inventory.png'
select1 = 'sprites\select.png'
dagger = 'sprites\DAGGER-NORTH.png'
fart = 'sprites\FARTS.png'

OVERLAP_WIDTH = 600
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
FART_TIME=200
FART_COOLDOWN = 2000
FART_DAMEG = 0.3

#inventory
INVENTORI = ['gu','da','h','s','i','b','la']
