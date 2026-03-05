import pygame

import Player
import settings as S
from Player import *
import Player
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

    def Big_check(self, arr_id, arr_pos):  # An array of pos numbers and another array of ids
        list_dis = []
        list_id = []
        list_pos = []
        for i in range(len(arr_pos)):
            dis = distance(arr_pos[i][0], arr_pos[i][1], self.entity.x, self.entity.y)

            if dis <= S.MONSTERS[self.type]["see_radius"]:
                list_id.append(arr_id[i])
                list_pos.append(arr_pos[i])
                list_dis.append(dis)
        arr_idn, arr_posn = order(list_dis, list_id, list_pos)
        return arr_idn, arr_posn


    def small_check(self,arr_id,arr_pos):
        min_dis = distance(arr_pos[0][0],arr_pos[0][1],self.entity.x,self.entity.y)
        min_p = arr_id[0]
        for i in range(len(arr_pos)):
            dis = distance(arr_pos[i][0], arr_pos[i][1],self.entity.x,self.entity.y)
            if dis < min_dis:
                min_dis = dis
                min_p = arr_id[i]
        return min_p

    def get_target(self,arr_id, arr_pos):
        if not arr_pos:
            while True:
                target = rand_pos(s.MONSTERS[self.type]["att_radius"],self)
                if in_view(self.entity.x,self.entity.y,target[0],target[1]):
                    return target[0],target[1],None
                #calculate the square of the attack radius
                #find a random spot in it
                #check if the enemy see it
        else:
            for i in arr_pos:
                dis = distance(arr_pos[i][0],arr_pos[i][1],self.entity.x,self.entity.y)
                if dis <= s.MONSTERS[self.type]["att_radius"]:
                    return arr_pos[i][0],arr_pos[i][1], arr_id[i]
                elif dis <= s.MONSTERS[self.type]["see_radius"]:
                    return arr_pos[i][0],arr_pos[i][1], None
            while True:
                target = rand_pos(s.MONSTERS[self.type]["att_radius"], self)
                if in_view(self.entity.x, self.entity.y, target[0], target[1]):
                    return target[0], target[1], None
                # calculate the square of the attack radius
                # find a random spot in it
                # check if the enemy see it

