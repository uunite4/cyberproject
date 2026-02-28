
#from pygame.examples.grid import TILE_SIZE
MAP_W = 1920*40
MAP_H = 1080*40
WINDOW_W = 1280
WINDOW_H = 640
#=----=-=-=
FRAMERATE = 120
TILE_SIZE = 40
#-==-=-=playersettings
SPEED = 50
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