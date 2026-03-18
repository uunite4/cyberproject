from game.classes.Entity import *

class DroppedWeapon(Entity):
    def __init__(self, item_id, x, y, weapon_type):
        super().__init__(x, y, 0, 1, item_id, "dropped_weapon")
        self.weapon_type = weapon_type