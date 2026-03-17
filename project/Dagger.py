

# Dagger.py
import time
from settings import PLAYER_SIZE


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
        dx, dy = self.dir_vector(attacker.dir)

        # normalize diagonal
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        fx = attacker.x + dx * self.reach
        fy = attacker.y + dy * self.reach

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
    def attack(self, attacker, clients,enemies, new_place):

        if not self.ready(attacker.id):
            return

        self.trigger_cooldown(attacker.id)

        hitbox = self.build_hitbox(attacker)

        for data in clients.values():
            target = data["player"]

            if target.id == attacker.id:
                continue
            if target.group == attacker.group:
                continue
            if target.health <= 0:
                continue

            target_box = player_rect(target)

            if rects_overlap(hitbox, target_box):
                self.damage_player(target)
                self.respawn_if_dead(target, new_place)



def rects_overlap(a, b):
    # a,b: (left, top, right, bottom)
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

def player_rect(p):
    half = PLAYER_SIZE // 2
    # player is centered at (p.x, p.y)
    return (p.x - half, p.y - half, p.x + half - 1, p.y + half - 1)