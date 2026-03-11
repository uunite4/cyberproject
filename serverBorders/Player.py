import pygame
import SETTINGS as S
import map_data as M

class Player:
    def __init__(self, x=100, y=100, dir=3, health=100):
        self.x = x
        self.y = y
        self.dir = dir
        self.health = health

        self.width = 40
        self.height = 40

    # def move(self, xVel, yVel):
    #     self.x += xVel
    #     self.y += yVel

    def tp(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir

def check_collision_with_stone(next_x, next_y, size):  # True = blocked (stone/outside)
    corners = get_corners(next_x,next_y,size)

    for px, py in corners:  # test each corner
        tile_x = int(px // S.TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // S.TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= S.WIDTH or tile_y < 0 or tile_y >= S.HEIGHT:
            return True

        if M.MAP[tile_y][tile_x] == "x":
            return True
    return False

def check_collision_with_lava(next_x, next_y, size):  # True = lava
    corners = get_corners(next_x,next_y,size)

    for px, py in corners:  # test each corner
        tile_x = int(px // S.TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // S.TILE_SIZE)  # pixel -> tile row

        if M.MAP[tile_y][tile_x] == "b":
            return True
    return False

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
