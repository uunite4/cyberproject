

# Dagger.py
import time
from game.SETTINGS import PLAYER_SIZE,MONSTERS


class Dagger:
    def __init__(self):
        self.damage = 15
        self.reach = 40
        self.width = 36
        self.cooldown = 0.3
        self.last_attack = {}   # attacker_id -> last time
    # --------------------
    # Cooldown
    # --------------------
    def ready(self, attacker_id):
        now = time.time()
        last = self.last_attack.get(attacker_id, 0)
        return now - last >= self.cooldown

    def trigger_cooldown(self, attacker_id):
        self.last_attack[attacker_id] = time.time()


    # --------------------
    # Direction
    # --------------------
    def dir_vector(self, d):
        if d == 1:   return 1, 0      # east
        if d == 2:   return 1, 1      # south-east
        if d == 3:   return 0, 1      # south
        if d == 4:   return -1, 1     # south-west
        if d == 5:   return -1, 0     # west
        if d == 6:   return -1, -1    # north-west
        if d == 7:   return 0, -1     # north
        if d == 8:   return 1, -1     # north-east
        return 0, 1


    # --------------------
    # Hitbox
    # --------------------
    def build_hitbox(self, attacker):
        dx, dy = self.dir_vector(attacker["dir"])

        # normalize diagonal
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        fx = attacker["x"] + dx * self.reach
        fy = attacker["y"] + dy * self.reach

        half = self.width // 2

        return (
            fx - half,
            fy - half,
            fx + half,
            fy + half
        )

    # --------------------
    # Apply damage
    # --------------------
    def damage_player(self, target):
        target.health -= self.damage
        if target.health <= 0:
            target.health = 0


    def respawn_if_dead(self, target, new_place):
        if target.health <= 0:
            target.x, target.y = new_place()
            target.health = 100


    # --------------------
    # MAIN ATTACK FUNCTION
    # --------------------


