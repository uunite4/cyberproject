
import pygame
import struct
import random

from pygame import Vector2

from settings import *
from map_data import *
from Entity import *

# ---------------------------------
# PlayerData - מחזיק את הנתונים האמיתיים מהשרת
# ---------------------------------
class PlayerData(Entity):
    def __init__(self, pid, x, y , dir1,group, gcd):
        super().__init__(x, y, dir1, PLAYER_HEALTH, pid, "player")
        self.group = group
        self.color = (200, 50, 50)  # צבע ברירת מחדל, אפשר לקבל מהשרת
        self.healthBarx = 20
        self.healthBary = 20
        self.gun_cooldown = gcd
        self.current_weapon = 1
        self.attack = 0
        self.target = None
        self.idle = False

    def update_from_server(self, x, y, health, direction, attack, current_weapon, group):

        if self.idle:

            while self.target is None:

                target = Vector2(0, 0)
                ex = int(self.x)
                ey = int(self.y)
                target.x = random.randint(ex - 200, ex + 200)
                target.y = random.randint(ey - 200, ey + 200)

                from general_func import in_view
                if in_view(self.x, self.y, target.x, target.y):
                    self.target = Vector2(target.x, target.y)

            from general_func import distance
            dist = distance(self.x, self.y, self.target.x, self.target.y)
            if dist < 20:
                self.target = None

            pos = Vector2(self.x, self.y)
            dire = (self.target - pos).normalize() * 5
            self.x += dire.x
            self.y += dire.y

        else:
            self.x = x
            self.y = y

        self.health = health
        if direction != 0:
            self.dir = direction
        self.attack = attack
        self.current_weapon = current_weapon
        self.group = group

def handle_input():
    keys = pygame.key.get_pressed()
    dx = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
    dy = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
    dspeed = int(keys[pygame.K_LSHIFT])
    shot = int(keys[pygame.K_SPACE])
    if int(keys[pygame.K_1]):
        current_weapon=1
    elif int(keys[pygame.K_2]):
        current_weapon=2
    else: current_weapon=0
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

    return dx,dy ,dspeed,dire ,shot ,current_weapon

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

def check_collision_with_stone(next_x, next_y, size):  # True = blocked (stone/outside)
    corners = get_corners(next_x,next_y,size)

    for px, py in corners:  # test each corner
        tile_x = int(px // TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= WIDTH or tile_y < 0 or tile_y >= HEIGHT:
            return True

        if MAP[tile_y][tile_x] == "x":
            return True
    return False
def check_collision_with_lava(next_x, next_y, size):    # True = blocked (stone/outside)
    corners = get_corners(next_x, next_y, size)

    for px, py in corners:  # test each corner
        tile_x = int(px // TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= WIDTH or tile_y < 0 or tile_y >= HEIGHT:
            return True

        if MAP[tile_y][tile_x] == "b":
            return True
    return False
def check_bullet_hit(p,b):
    left, right, top, bottom = get_sides(p.x, p.y,PLAYER_SIZE)

    if left <= b.x <= right and top <= b.y <= bottom:
        return True
    return False


def new_place():
    while True:
        px =random.randint(1,WIDTH)
        py = random.randint(1,HEIGHT)
        if MAP[py][px] == " ":
            return px*40,py*40
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
