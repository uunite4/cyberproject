from operator import truediv
import math
import pygame
import struct
import random
from settings import *
from map_data import *
from Entity import *


class PlayerData(Entity):
    def __init__(self, pid, x, y , dir1,group, gcd,fc,tc):
        super().__init__(x, y, dir1, pid, "player")
        self.health=100
        self.group = group
        self.color = (200, 50, 50)  # צבע ברירת מחדל, אפשר לקבל מהשרת
        self.healthBarx = 20
        self.healthBary = 20
        self.gun_cooldown = gcd
        self.weapons=['da','gu','h','s','i','b','la',0,0]
        self.current_weapon = 0
        self.attack = 0
        self.fartp=0
        self.f_cooldown = fc
        self.t_cooldown = tc
        self.speed_po = 0
        self.spat = 0
        self.invesebel = 0
        self.i_timer = 0
        self.ccw=0
        self.britmila = 0
        self.b_timer = 0
        self.la_cooldown = 0
        self.laser_event = 0
        self.outo_run = False

    def update_from_server(self, x, y, health, direction, attack, current_weapon, group,fartp,fcool,tcool,inv,wepons,cw,la):
        self.x = x
        self.y = y
        self.health = health
        if direction != 0:
            self.dir = direction
        self.attack = attack
        self.current_weapon = current_weapon
        self.group = group
        self.fartp = fartp
        self.f_cooldown = fcool
        self.t_cooldown = tcool
        self.invesebel = inv
        self.weapons=wepons
        self.ccw=cw
        self.laser_event = la

def handle_input():
    keys = pygame.key.get_pressed()
    dx = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
    dy = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
    outo = int(keys[pygame.K_r])
    pickup = int(keys[pygame.K_e])
    dspeed = int(keys[pygame.K_LSHIFT])
    shot = int(keys[pygame.K_SPACE])
    fart = int(keys[pygame.K_f])
    teleport = int(keys[pygame.K_q])
    #===
    if int(keys[pygame.K_1]):
        current_weapon=1
    elif int(keys[pygame.K_2]):
        current_weapon=2
    elif int(keys[pygame.K_2]):
        current_weapon=2
    elif int(keys[pygame.K_3]):
        current_weapon=3
    elif int(keys[pygame.K_4]):
        current_weapon=4
    elif int(keys[pygame.K_5]):
        current_weapon=5
    elif int(keys[pygame.K_6]):
        current_weapon = 6
    elif int(keys[pygame.K_7]):
        current_weapon=7
    elif int(keys[pygame.K_8]):
        current_weapon=8
    else: current_weapon=0
    #++++=
    if dx == 1:
        if dy == 1:
            dire = 2
        elif dy == 0:
            dire = 1
        elif dy ==-1:
            dire = 8
    elif dx == -1:
        if dy == 1:
            dire = 4
        elif dy == -1:
            dire = 6
        elif dy == 0:
            dire = 5
    elif dx == 0:
        if dy == 1:
            dire = 3
        elif dy == -1:
            dire = 7
        elif dy == 0:
            dire =0

    return dx,dy ,dspeed,dire ,shot ,current_weapon,pickup,fart,teleport,outo
def get_corners(x,y,size):
    left, right, top, bottom = get_sides(x,y,size)
    corners = [  # 4 corners
        (left, top),
        (right, top),
        (left, bottom),
        (right, bottom),
    ]

    return corners
def get_sides(x,y, size):
    left = x - size // 2  # player box left (pixels)
    right = x + size // 2 - 1  # player box right (pixels)
    top = y - size // 2  # player box top (pixels)
    bottom = y + size // 2 - 1  # player box bottom (pixels)

    return left,right,top,bottom
def check_collision_with_stone(self, next_x, next_y):  # True = blocked (stone/outside)
    corners = get_corners(next_x,next_y,PLAYER_SIZE)

    for px, py in corners:  # test each corner
        tile_x = int(px // TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= WIDTH or tile_y < 0 or tile_y >= HEIGHT:
            return True

        if MAP[tile_y][tile_x] == "S":
            return True
    return False
def check_collision_with_lava(self, next_x, next_y):    # True = blocked (stone/outside)
    corners = get_corners(next_x, next_y, PLAYER_SIZE)

    for px, py in corners:  # test each corner
        tile_x = int(px // TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= WIDTH or tile_y < 0 or tile_y >= HEIGHT:
            return True

        if MAP[tile_y][tile_x] == "L":
            return True
    return False
def check_bullet_hit(p,b):
    left, right, top, bottom = get_sides(p.x, p.y,PLAYER_SIZE)

    if left <= b.x <= right and top <= b.y <= bottom:
        return True
    return False
def check_fart_hit(p,f,low , high):
    corners = get_corners(p.x, p.y, PLAYER_SIZE)

    for cx, cy in corners:

        dx = cx - f.x
        dy = cy - f.y
        dist_sq = dx ** 2 + dy ** 2

        if dist_sq <= f.radius ** 2:

            angle = math.atan2(dy, dx)
            if angle < 0: angle += 2 * math.pi

            if low > high:
                if angle >= low or angle <= high: return True
            else:
                if low <= angle <= high: return True

    return False



    return True

def new_place():
    while True:
        px =random.randint(1,1000)#len(MAP)-1)
        py = random.randint(1,1000)#len(MAP[0])-1)
        if MAP[py][px] == "G":
            return px*TILE_SIZE,py*TILE_SIZE
        else:
            pass
def health_bar_update(health,screen):
    green1 =  (HEALTH_BAR_SIZE_X /100)*health
    red1= HEALTH_BAR_SIZE_X - green1
    pygame.draw.rect(screen, "green", (20, 20, green1, HEALTH_BAR_SIZE_Y))
    pygame.draw.rect(screen, "red", (20+green1, 20, red1, HEALTH_BAR_SIZE_Y))
def S_health_bar_update(health,screen,x,y):
    green1 =  (S_HEALTH_BAR_SIZE_X /100)*health
    red1= S_HEALTH_BAR_SIZE_X - green1
    #x=x%WINDOW_W
    #y=y%WINDOW_H
    pygame.draw.rect(screen, "green", (x, y-40, green1, S_HEALTH_BAR_SIZE_Y))
    pygame.draw.rect(screen, "red", (x+green1, y-40, red1, S_HEALTH_BAR_SIZE_Y))