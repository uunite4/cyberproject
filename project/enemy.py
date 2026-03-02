import pygame
import SETTINGS as S
from Player import *
from map import *
from Entity import *
from general_func import *
import time


class Enemy:
    def __init__(self,entity ,id , type,last_att):
        # entity
        self.entity = entity

        #other
        self.id =id
        self.health = S.MONSTERS[type]["health"]
        self.type = type
        self.last_att = time.time()


    # --- Methods ---
    def draw(self, surface):
        """Draws the player as a black rectangle centered on (x, y)."""
        rect_x = self.entity.x - self.size // 2
        rect_y = self.entity.y - self.size // 2
        pygame.draw.rect(surface, S.BLACK, (rect_x, rect_y, self.size, self.size))

        # Optional: Draw a circle for the attack radius
        # pygame.draw.circle(surface, (255, 0, 0), (self._x, self._y), self._att_radius, 1)

    def get_pos(self):
        return (self.entity.x, self.entity.y)

    def get_dmg(self):
        return S.MONSTERS[self.type]["damage"]

    def take_damage(self,damage): #returns true if dead and false if still alive
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            return True
        return False

    def Big_check(self,arr_id, arr_pos):#An array of pos numbers and another array of ids
        #the lists are ordered
        list_id_ip = []
        for i in arr_pos:
            dis = distance(i[0], i[1],self.entity.x,self.entity.y)

            if dis <= S.MONSTERS[self.type]["see_radius"]:
                list_id_ip.append(tuple[arr_id[i],arr_pos[i]])
            return order(list_id_ip)


    def small_check(self,arr_id,arr_pos):
        min_dis = distance(arr_pos[0][0],arr_pos[0][1],self.entity.x,self.entity.y)
        min_p = arr_id[0]
        for i in arr_pos:
            dis = distance(i[0], i[1],self.entity.x,self.entity.y)
            if dis < min_dis:
                min_dis = dis
                min_p =
        return min_dis,

    def check_att_redius(self,arr_pos_id):
        if (arr_pos_id== ""):
            return 0
        else:
            arr_att = []
            for i in arr_pos_id:
                dis = distance(i[0], i[1], self.entity.x, self.entity.y)
                if dis <= S.MONSTERS[self.type]["att_radius"]:
                    arr_att.append(arr_pos_id[i])
        return arr_att

    def to_attck(self, arr_att):#check if enemy should attck
        while True:
            if arr_att == "":
                pass# if there is no one in the attack radius keep walking eithout changes
            else:
                min_dis = distance(arr_att[0][0],arr_att[0][1],self.entity.x,self.entity.y)
                for i in arr_att:
                    dis = distance(i[0], i[1],self.entity.x,self.entity.y)
                    if dis < min_dis:
                        min_dis = dis
                attack(min_dis)#not real function - need attack function from idan

    def in_view(self,x,y):
        ex,ey = self.entity.x, self.entity.y
        dir, slope = vector(ex,ey,x,y)
        if dir==0:
            while (ey < y and slope==-1) or (ey > y and slope==1):
                if check_collision_with_stone(S.TILE_SIZE,ex,ey):
                    return False
                ey += slope*S.TILE_SIZE
            return True
        else:
            jump = jumps(S.TILE_SIZE, slope)
            while (ex < x and dir==-1) or (ex > x and dir==1):
                if check_collision_with_stone(S.TILE_SIZE, ex, ey):
                    return False
                ex += dir * jump
                ey += slope*dir*jump
            return True
