import pygame
from settings import *
from Player import *
from map import *
from enemy import Enemy
from Entity import *
from general_func import *
import random
import time


def draw_enemy(screen, enemys, cam_x, cam_y, ENEMY_SPRITES, DEFAULT_SPRITE):
    for eid, e in enemys.items():
        ex = int(e.entity.x - cam_x - ENEMY_SIZE // 2)
        ey = int(e.entity.y - cam_y - ENEMY_SIZE // 2)

        sprite = ENEMY_SPRITES.get(e.entity.dir, DEFAULT_SPRITE)

        screen.blit(sprite, (ex, ey))
        if getattr(e, "attack", 0) == 1:
            # (Insert the dagger drawing logic here)
            pass


def vec_to_dir(dx, dy):
    """
    Converts a direction vector (dx, dy) into one of 8 direction codes.

    Direction mapping:
        1 = East
        2 = South-East
        3 = South
        4 = South-West
        5 = West
        6 = North-West
        7 = North
        8 = North-East


    """

    # vertical movement (no horizontal movement)
    if dx == 0:

        # Moving down
        if dy < 0:
            return 3  # South

        # Moving up
        else:
            return 7  # North


    # Moving  right (East side)
    elif dx > 0:

        if dy < 0.41 and dy > -0.41:
            return 1  # East

        elif dy >= 0.41 and dy <= 2.41:
            return 8  # North-East

        elif dy <= -0.41 and dy >= -2.41:
            return 2  # South-East

        elif dy < -2.41:
            return 3  # South

        else:
            return 7  # North


    # Moving left (West side)
    else:

        if dy < 0.41 and dy > -0.41:
            return 5  # West

        elif dy <= -0.41 and dy >= -2.41:
            return 6  # North-West

        elif dy >= 0.41 and dy <= 2.41:
            return 4  # South-West

        elif dy < -2.41:
            return 7  # North

        else:
            return 3  # South

def enemy_att(enemy,tx,ty):
    now = time.time()

    if now - enemy.last_att >= enemy.shoot_cooldown:
        enemy.last_att = now
        enemy.attack = 1

        dx, dy = vector(enemy.entity.x, enemy.entity.y, tx, ty)
        speed = S.MONSTERS[enemy.type]["bullet_speed"]
        vx = dx * speed
        vy = dy * speed
        # ---- CREATE BULLET ----
        bullet_id = "hdjsd"
        bullets[bullet_id] = Bullet(#from idan code
            bullet_id,
            enemy.entity.x,
            enemy.entity.y,
            0,
            vx,
            vy
        )
def main():
    pygame.init()

    enemies = {}
    skeleton_id = "skelly_01"

    # Arguments: x, y, dir, health, id, type
    base_data = Entity(500, 400, 2, 100, skeleton_id, "enemy")
    enemies[skeleton_id] = Enemy(base_data, skeleton_id, "skeleton")
    clock = pygame.time.Clock()
    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        arr_id_fromserver = ["15345","68745","32458"]#need to get  from server params
        arr_pos_fromserver = [[44,67],[457,369],[116,456]]#need to get  from server params
        for eid, enemy in enemies.items():
            # 2. Ask the enemy: "Who do you see?"
            visible_players = enemy.Big_check(arr_id_fromserver, arr_pos_fromserver)

            if visible_players:
                target_id, (tx, ty) = visible_players[0]  # Target the closest player
                dist = distance(enemy.entity.x, enemy.entity.y, tx, ty)

                if dist > MONSTERS[enemy.type]["att_radius"]:
                    #movment
                    enemy_att(enemy, tx, ty)# update bullet list
                else:
                    enemy.attack = 0
                    if random.random() < 0.03:  # 3% chance to change mind
                        enemy.entity.dir = random.randint(0, 3)

                    w_speed = 1  # Walking speed is usually slower than chasing
                    if enemy.entity.dir == 0:
                        enemy.entity.y -= w_speed
                    elif enemy.entity.dir == 3:
                        enemy.entity.y += w_speed
                    elif enemy.entity.dir == 2:
                        enemy.entity.x -= w_speed
                    elif enemy.entity.dir == 1:
                        enemy.entity.x += w_speed


        screen.fill(BLACK)
        #draw_map()
        #draw_frame(screen, enemies, bullets, WIDTH, HEIGHT, SPRITES1, DEFAULT_SPRITE1, SPRITES2, DEFAULT_SPRITE2,
        #           DAGGERS, DEFAULT_DAGGER)

        pygame.display.flip()
        clock.tick(10)
    pygame.quit()


if __name__ == "__main__":
    main()