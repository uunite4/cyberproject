import pygame
from SETTINGS import S
from Player import *
from map import *
from Entity import *

class enemyData:
    def __init__(self,entity ,pid , type,last_att):
        # entity
        self.entity = entity

        #other
        self.id =id
        self.type = type
        self.last_att = last_att

    def set_health(self, value):
        # Clamping logic still works here
        if value < 0: value = 0
        self._health = value

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



    def Big_check(self,arr_id, arr_pos):#An array of numbers and another array
        #the lists are ordered
        for i in arr_pos:
            dis = distance(i[0], i[1],self.entity.x,self.entity.y)
            if dis <= see_radius:
                list_id_ip.append(tuple(arr_id[i],arr_pos[i]))
            return order(list_id_ip)
