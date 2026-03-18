
from serverBorders.general_func import *
import time
import serverBorders.SETTINGS as s


class Enemy:
    def __init__(self,entity ,id , type):
        # entity
        self.entity = entity

        #other
        self.id =id
        self.health = S.MONSTERS[type]["health"]
        self.type = type
        self.last_att = time.time()
        self.entity.group = 0


    # --- Methods ---

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
            dis = distance(arr_pos[i][0], arr_pos[i][1],self.entity.x,self.entity.y)

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

    def get_target(self, arr_id, arr_pos, memory):
        for i, pos in enumerate(arr_pos):
            dis = distance(pos[0], pos[1], self.entity.x, self.entity.y)

            # Check if this player is within attack radius and in view
            if in_view(self.entity.x, self.entity.y, pos[0], pos[1]):
                if dis <= s.MONSTERS[self.type]["att_radius"]:
                    return pos[0], pos[1], arr_id[i]
                else:
                    # In view but too far? Return the pos but no ID (target to walk towards)
                    return pos[0], pos[1], None

        if memory[0]:
            tx, ty = memory
            dis = distance(self.entity.x, self.entity.y, tx, ty)

            # If we are more than 25 pixels away, keep this target
            if dis > 25:
                return tx, ty, None
        # If no players are found/visible, pick a random spot to wander
        while True:
            target = rand_pos(s.MONSTERS[self.type]["see_radius"], self)
            if in_view(self.entity.x, self.entity.y, target[0], target[1]):
                return target[0], target[1], None

    def update_from_server_enemy(self,entity, id, type):
        # entity
        self.entity = entity

        # other
        self.id = id
        self.health = S.MONSTERS[type]["health"]
        self.type = type
        self.last_att = time.time()


