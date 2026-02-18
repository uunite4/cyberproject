import pygame
import struct
import random
from settings import *
from map_data import *



class Bullet:
    def __init__(self, pid, x, y , dir1,dise,pi):
        self.id = pid
        self.player_id = pi
        self.x = x
        self.y = y
        self.dir = dir1
        self.dis = dise  # אפשר להוסיף עוד שדות בעתיד
          # צבע ברירת מחדל, אפשר לקבל מהשרת


    def update_bullet(self):
        if self.dis >= 0:
            if self.dir == 1:
                dx =  1
                dy = 0
            elif self.dir == 2:
                dx = 1
                dy = 1
            elif self.dir == 3:
                dx = 0
                dy = 1
            elif self.dir == 4:
                dx = -1
                dy = 1
            elif self.dir == 5:
                dx = -1
                dy = 0
            elif self.dir == 6:
                dx =  -1
                dy = -1
            elif self.dir == 7:
                dx = 0
                dy = -1
            elif self.dir == 8:
                dx = 1
                dy = -1

            self.x += dx * BULLET_SPEED
            self.y += dy * BULLET_SPEED
            self.dis -= 1
            return False
        else: return True
    def update_from_server_bull(self,bx,by):
        self.x = bx
        self.y = by

def get_next_bullet_id(bullets):
    used_ids = {b.id for b in bullets}
    current_id = 0
    while current_id in used_ids:
        current_id += 1
    return current_id