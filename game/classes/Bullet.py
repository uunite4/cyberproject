

import game_settings as S
from classes.Entity import *
from classes.Player import check_collision_with_stone


class Bullet(Entity):
    def __init__(self, bid, x, y , dir1, dis, pi):
        super().__init__(x, y, dir1, dis, bid, "bullet")
        self.player_id = pi


    def update_bullet(self):
        dx = 0
        dy = 0
        if self.health >= 0:
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

            self.x += dx * S.BULLET_SPEED
            self.y += dy * S.BULLET_SPEED
            self.health -= 1
            if check_collision_with_stone(self.x, self.y, S.BULLET_SIZE):
                return True
            else:
                return False
        else:
            return True
    def update_from_server_bull(self,bx,by):
        self.x = bx
        self.y = by

def get_next_bullet_id(bullets):
    used_ids = {b.id for b in bullets}
    current_id = 0
    while current_id in used_ids:
        current_id += 1
    return current_id
