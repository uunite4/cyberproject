import math
import random

from pygame import Vector2

import client_settings as s
import map_data as m


class Player:
    def __init__(self, x=100, y=100, dir=3, health=100):
        self.x = x
        self.y = y
        self.dir = dir
        self.health = health
        self.att = 0
        self.weapon = 1
        self.weapons = s.BASIC_INV
        self.fartp = 0
        self.fart_timer = 0
        self.fart_ready = 1
        self.invisible = 0
        self.invis_timer = 0
        self.laser = 0
        self.laser_timer = 0
        self.brit = 0
        self.teleport = 1

        self.width = 40
        self.height = 40

        self.target = None
        self.idle = False

    # def move(self, xVel, yVel):
    #     self.x += xVel
    #     self.y += yVel

    def tp(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir

    def move_idle(self):

        inputs = {'d': 0, 'a': 0, 's': 0, 'w': 0}

        if self.target:
            dist = distance(self.x, self.y, self.target.x, self.target.y)
            if dist < 50:
                self.target = None

        while self.target is None:
            target = Vector2(0, 0)
            target.x = random.randint(self.x - 500, self.x + 500)
            target.y = random.randint(self.y - 500, self.y + 500)

            if in_view(self.x, self.y, target.x, target.y):
                self.target = Vector2(target.x, target.y)

        pos = Vector2(self.x, self.y)
        dire = (self.target - pos).normalize()
        inputs['w'] = 1 if dire.y < -0.5 else 0
        inputs['s'] = 1 if dire.y > 0.5 else 0
        inputs['a'] = 1 if dire.x < -0.5 else 0
        inputs['d'] = 1 if dire.x > 0.5 else 0

        return inputs


def check_collision_with_stone(next_x, next_y, size):  # True = blocked (stone/outside)
    corners = get_corners(next_x, next_y, size)

    for px, py in corners:  # test each corner
        tile_x = int(px // s.TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // s.TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= s.WIDTH or tile_y < 0 or tile_y >= s.HEIGHT:
            return True

        if m.MAP[tile_y][tile_x] == "T":
            return True
    return False


def check_collision_with_lava(next_x, next_y, size):  # True = lava
    corners = get_corners(next_x, next_y, size)

    for px, py in corners:  # test each corner
        tile_x = int(px // s.TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // s.TILE_SIZE)  # pixel -> tile row
        if tile_x < 0 or tile_x >= s.WIDTH or tile_y < 0 or tile_y >= s.HEIGHT:
            continue
        if m.MAP[tile_y][tile_x] == "L":
            return True
    return False


def get_corners(x, y, size):
    left, right, top, bottom = get_sides(x, y, size)
    corners = [  # 4 corners
        (left, top),
        (right, top),
        (left, bottom),
        (right, bottom),
    ]

    return corners


def get_sides(x, y, size):
    left = x - size // 2  # player box left (pixels)
    right = x + size // 2 - 1  # player box right (pixels)
    top = y - size // 2  # player box top (pixels)
    bottom = y + size // 2 - 1  # player box bottom (pixels)

    return left, right, top, bottom


def check_bullet_hit(p, b):
    left, right, top, bottom = get_sides(p["x"], p["y"], s.PLAYER_SIZE)

    if left <= b.x <= right and top <= b.y <= bottom:
        return True
    return False


def check_bullet_hitE(e, b):
    left, right, top, bottom = get_sides(e.x, e.y, s.MONSTERS[e.type]["size"])

    if left <= b.x <= right and top <= b.y <= bottom:
        return True
    return False


def check_fart_hit(p, f, low, high):
    corners = get_corners(p["x"], p["y"], s.PLAYER_SIZE)

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


def in_view(sx, sy, tx, ty):
    start = Vector2(sx, sy)
    target = Vector2(tx, ty)

    direction: Vector2 = Vector2(target) - Vector2(start)
    dist = direction.length()

    if dist == 0:
        return True

    direction = direction.normalize()

    step_size = s.TILE_SIZE / 2  # smaller = more accurate
    steps = int(dist / step_size)

    pos = Vector2(start)

    for _ in range(steps):
        if check_collision_with_stone(pos.x, pos.y, s.TILE_SIZE) or check_collision_with_lava(pos.x, pos.y,
                                                                                              s.TILE_SIZE):
            return False
        pos += direction * step_size

    return True


def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
