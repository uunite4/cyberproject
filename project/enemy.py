import pygame
import SETTINGS as S
from Player import *
from map import *
from Entity import *
from general_func import *
import time


class enemyData:
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

    def Big_check(self,arr_id, arr_pos):#An array of numbers and another array
        #the lists are ordered
        for i in arr_pos:
            dis = distance(i[0], i[1],self.entity.x,self.entity.y)
            list_id_ip = []
            if dis <= S.MONSTERS[self.type]["see_radius"]:
                list_id_ip.append(tuple[arr_id[i],arr_pos[i]])
            return order(list_id_ip)


    def small_check(self,arr_id,arr_pos):
        min_dis = distance(arr_pos[0][0],arr_pos[0][1],self.entity.x,self.entity.y)
        for i in arr_pos:
            dis = distance(i[0], i[1],self.entity.x,self.entity.y)
            if dis < min_dis:
                min_dis = dis
        return min_dis