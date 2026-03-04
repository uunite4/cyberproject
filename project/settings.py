
#from pygame.examples.grid import TILE_SIZE
MAP_W = 192*40
MAP_H = 108*40
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
WIDTH = 192
HEIGHT = 108
#Obgects
grass='grass.png'
stone='stone.png'
lava = 'lava.png'
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

MONSTERS = {
    "GOBLIN" : { #some sort of monster
        "health" : 200, #starter health
        "speed" : 3,
        "see_radius" : 5, #going to players in this range
        "att_radius" : 3, #attack players in this range
        "damage" : 20,
        "size" : 30, #of sprite
    }
}
#BLOCK_MAP = [
#    '666666666666',
#    '444557755444',
#    '333333333333',
#    '222222222222',
#    '111111111111',
#    '            ',
#    '            ',
#    '            ',#  '            ']

#COLOR_LEGEND = {
#    '1': 'blue',
#    '2': 'green',
#    '3': 'red',
#    '4': 'orange',
 #   '5': 'purple',
#    '6': 'bronce',
#    '7': 'grey',
#}

#GAP_SIZE = 2
#BLOCK_HEIGHT = WINDOW_HEIGHT / len(BLOCK_MAP) - GAP_SIZE
#BLOCK_WIDTH = WINDOW_WIDTH / len(BLOCK_MAP[0]) - GAP_SIZE
#TOP_OFFSET = WINDOW_HEIGHT // 30

#UPGRADES = ['speed', 'laser', 'heart', 'size']