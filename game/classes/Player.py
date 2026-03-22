import math
import random

from pygame import Vector2

import SETTINGS as S
import map_data as M


class Player:
    def __init__(self, x=100, y=100, dir=3, health=100):
        self.x = x
        self.y = y
        self.dir = dir
        self.health = health
        self.att = 0
        self.weapon = 1
        self.weapons = S.BASIC_INV
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
        self.server_num = None

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
            from game.general_func import distance
            dist = distance(self.x, self.y, self.target.x, self.target.y)
            if dist < 50:
                self.target = None

        while self.target is None:
            target = Vector2(0, 0)
            target.x = random.randint(self.x - 500, self.x + 500)
            target.y = random.randint(self.y - 500, self.y + 500)

            if check_overlap_side(self.server_num, target.x):
                self.target = None

            from game.general_func import in_view
            if in_view(self.x, self.y, target.x, target.y):
                self.target = Vector2(target.x, target.y)

        pos = Vector2(self.x, self.y)
        dire = (self.target - pos).normalize()
        inputs['w'] = 1 if dire.y < -0.5 else 0
        inputs['s'] = 1 if dire.y > 0.5 else 0
        inputs['a'] = 1 if dire.x < -0.5 else 0
        inputs['d'] = 1 if dire.x > 0.5 else 0

        return inputs


def check_overlap_side(server_num, x):
    """
    Checks if a given x-coordinate falls within an overlap region
    for a specific server and returns the side.

    Args:
        server_num (int): The index of the server (0 to SERVER_NUMBER - 1).
        x (float/int): The x-coordinate to check.

    Returns:
        str or bool: "left" if in the left overlap, "right" if in the right overlap,
                     or False if not in any overlap.
    """

    # 1. Check the LEFT overlap (shared with the previous server)
    if server_num > 0:
        left_overlap_start = server_num * S.SERVER_STEP
        left_overlap_end = left_overlap_start + S.OVERLAP_WIDTH

        if left_overlap_start <= x <= left_overlap_end:
            return "left"

    # 2. Check the RIGHT overlap (shared with the next server)
    if server_num < S.SERVER_NUMBER - 1:
        right_overlap_start = (server_num + 1) * S.SERVER_STEP
        right_overlap_end = right_overlap_start + S.OVERLAP_WIDTH

        if right_overlap_start <= x <= right_overlap_end:
            return "right"

    # Not in any overlap zone for this specific server
    return False


def check_collision_with_stone(next_x, next_y, size):  # True = blocked (stone/outside)
    corners = get_corners(next_x, next_y, size)

    for px, py in corners:  # test each corner
        tile_x = int(px // S.TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // S.TILE_SIZE)  # pixel -> tile row

        if tile_x < 0 or tile_x >= S.WIDTH or tile_y < 0 or tile_y >= S.HEIGHT:
            return True

        if M.MAP[tile_y][tile_x] == "x":
            return True
    return False


def check_collision_with_lava(next_x, next_y, size):  # True = lava
    corners = get_corners(next_x, next_y, size)

    for px, py in corners:  # test each corner
        tile_x = int(px // S.TILE_SIZE)  # pixel -> tile col
        tile_y = int(py // S.TILE_SIZE)  # pixel -> tile row
        if tile_x < 0 or tile_x >= S.WIDTH or tile_y < 0 or tile_y >= S.HEIGHT:
            continue
        if M.MAP[tile_y][tile_x] == "b":
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
    left, right, top, bottom = get_sides(p["x"], p["y"], S.PLAYER_SIZE)

    if left <= b.x <= right and top <= b.y <= bottom:
        return True
    return False


def check_bullet_hitE(e, b):
    left, right, top, bottom = get_sides(e.x, e.y, S.MONSTERS[e.type]["size"])

    if left <= b.x <= right and top <= b.y <= bottom:
        return True
    return False


def check_fart_hit(p, f, low, high):
    corners = get_corners(p["x"], p["y"], S.PLAYER_SIZE)

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
