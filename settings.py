
#from pygame.examples.grid import TILE_SIZE
MAP_W = 1920*40
MAP_H = 1080*40
WINDOW_W = 1280
WINDOW_H = 640
#=----=-=-=
FRAMERATE = 120
TILE_SIZE = 40
#-==-=-=playersettings
SPEED = 5
PLAYER_SIZE = 40
PLAYER_HEALTH =100
#=======cmd
CMD_JUMP    = 0x03
CMD_JOIN    = 0x01
CMD_INPUT   = 0x02
CMD_STATE   = 0x10
CMD_WELCOME = 0x11
#-=-=-=-=--=serverinfo
HOST = "0.0.0.0"
PORT = 5000
SERVER_IP = "127.0.0.1"
#=-=-=-=-=-=-BROADCAST
BROADCAST_HZ = 30
BROADCAST_DT = 1.0 / BROADCAST_HZ
#-=-=-=-=-=--MAP
BUILDING_SIZE = 40
WIDTH = 1920
HEIGHT = 1080
#Obgects
grass='imges\grass.png'
stone='imges\stone.png'
lava = 'imges\lava.png'
tree ='imges\\tree.png'
pesel= 'imges\statue.png'
marble = 'imges\marble.png'
bitmikdash = 'imges\statue.png'
ostone='imges\\blackstone.png'
poop = 'poop.png'
inventory1 = 'inventory.png'
select1 = 'select.png'
lazer = 'wepons\\lazer.png'
gun = 'wepons\\gun.png'
lcon1 = 'wepons\\Icon1.png'
lcon5 = 'wepons\\Icon5.png'
lcon28 = 'wepons\\Icon28.png'
bolbol = 'wepons\\bolbol.png'
scissors = 'wepons\\scissors.png'
#===========
HEALTH_BAR_SIZE_X = 120
HEALTH_BAR_SIZE_Y = 30
S_HEALTH_BAR_SIZE_X = 40
S_HEALTH_BAR_SIZE_Y = 10
#==================
BULLET_DISTANS =100
BULLET_SPEED = 15
BULLET_COOLDOWN = 10
BULLET_DAMEG = 10
BULLET_SIZE = 5
#+=====
FART_RUADIOS=100
FART_TIME=200
FART_COOLDOWN = 2000
FART_DAMEG = 0.3
#-------
BRIT_TIMER = 200
#
TELEPORT_RANGE = 200
TELEPORT_COOLDOWN = 1000
#=====-=-=-=
INVENTORI = ['da',0,0,0,0,0,0,0,0]
#--------=-=
SPEED_POSSION_TIME = 500
INVESIBEL_TIME = 500
BRIT_TIMER = 3000
#=========
LASER_TIME = 30
LASER_COOLDOWN = 200
LASER_DAMEG =20
LASER_DIS = 400