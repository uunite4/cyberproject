import pygame
import struct
import random
from settings import *
from map_data import *


# ---------------------------------
# PlayerData - מחזיק את הנתונים האמיתיים מהשרת
# ---------------------------------
class PlayerData:
    def __init__(self, pid, x, y , dir1,group, gcd):
        self.id = pid
        self.x = x
        self.y = y
        self.group = group
        self.health = PLAYER_HEALTH  # אפשר להוסיף עוד שדות בעתיד
        self.color = (200, 50, 50)  # צבע ברירת מחדל, אפשר לקבל מהשרת
        self.healthBarx = 20
        self.healthBary = 20
        self.dir = dir1
        self.gun_cooldown = gcd
        self.current_weapon = 1
        self.attack = 0

    def update_from_server(self, x, y, health, direction, attack, current_weapon):
        self.x = x
        self.y = y
        self.health = health
        if direction != 0:
            self.dir = direction
        self.attack = attack
        self.current_weapon = current_weapon

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
def check_collision_with_stone(self, next_x, next_y):  # True = blocked (stone/outside)
    left = next_x - PLAYER_SIZE // 2  # player box left (pixels)
    right = next_x + PLAYER_SIZE // 2 - 1  # player box right (pixels)
    top = next_y - PLAYER_SIZE // 2  # player box top (pixels)
    bottom = next_y + PLAYER_SIZE // 2 - 1  # player box bottom (pixels)

    corners = [  # 4 corners
        (left, top),
        (right, top),
        (left, bottom),
        (right, bottom),
    ]

    for px, py in corners:  # test each corner
        tile_x = int(px // TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= WIDTH or tile_y < 0 or tile_y >= HEIGHT:
            return True

        if MAP[tile_y][tile_x] == "x":
            return True
    return False
def check_collision_with_lava(self, next_x, next_y):    # True = blocked (stone/outside)
    left = next_x - PLAYER_SIZE // 2  # player box left (pixels)
    right = next_x + PLAYER_SIZE // 2 - 1  # player box right (pixels)
    top = next_y - PLAYER_SIZE // 2  # player box top (pixels)
    bottom = next_y + PLAYER_SIZE // 2 - 1  # player box bottom (pixels)

    corners = [  # 4 corners
        (left, top),
        (right, top),
        (left, bottom),
        (right, bottom),
    ]

    for px, py in corners:  # test each corner
        tile_x = int(px // TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= WIDTH or tile_y < 0 or tile_y >= HEIGHT:
            return True

        if MAP[tile_y][tile_x] == "b":
            return True
    return False
def check_bullet_hit(p,b):
    left = p.x #- PLAYER_SIZE // 2  # player box left (pixels)
    right = p.x + PLAYER_SIZE   # player box right (pixels)
    top = p.y #- PLAYER_SIZE // 2  # player box top (pixels)
    bottom = p.y + PLAYER_SIZE // 2 - 1  # player box bottom (pixels)

    corners = [  # 4 corners
        (left, top),
        (right, top),
        (left, bottom),
        (right, bottom),
    ]

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
def check_player_collision(current_player, next_x, next_y, clients):
    for other_sock, other_data in clients.items():
        other_p = other_data["player"]
        if other_p.id == current_player.id:
            continue  # אל תבדוק התנגשות של השחקן עם עצמו

        if (abs(next_x - other_p.x) < PLAYER_SIZE and
            abs(next_y - other_p.y) < PLAYER_SIZE):
            return True
    return False
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