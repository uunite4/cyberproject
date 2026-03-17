from Entity import Entity
import SETTINGS as S
import math
class Fart(Entity):
    def __init__(self, eid, x, y, dir, duration, radius=S.FART_RUADIOS):
        super().__init__(x, y, dir, 1, eid, "ability") #hp ddoesnt matter
        self.radius = radius
        self.duration = duration


def get_angle_from_dir(direction):
    back_dir_map = {1: 5, 2: 6, 3: 7, 4: 8, 5: 1, 6: 2, 7: 3, 8: 4}
    back_dir = back_dir_map.get(direction, direction)

    angles = {1: (1.75*math.pi,0.25*math.pi), 2: (0 * math.pi,0.5*math.pi), 3: (0.25 * math.pi,0.75*math.pi), 4: (0.5 * math.pi,1*math.pi),
              5: (0.75*math.pi,1.25*math.pi), 6: (1 * math.pi,1.5*math.pi), 7: (1.25 * math.pi,1.75*math.pi), 8: (1.5 * math.pi,2*math.pi)}
    return angles.get(back_dir, (0, 0))
