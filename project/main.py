import pygame
from SETTINGS import S
from Player import *
from map import *
from enemy import Enemy
from Entity import *
from general_func import *



def draw_enemy(screen, enemys, cam_x, cam_y, ENEMY_SPRITES, DEFAULT_SPRITE):
    for eid, e in enemys.items():
        ex = int(e.x - cam_x - S.ENEMY_SIZE // 2)
        ey = int(e.y - cam_y - S.ENEMY_SIZE // 2)

        sprite = ENEMY_SPRITES.get(e.dir, DEFAULT_SPRITE)

        screen.blit(sprite, (ex, ey))
        if getattr(e, "attack", 0) == 1:
            # (Insert the dagger drawing logic here)
            pass


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
        arr_id_fromserver,arr_pos_fromserver = ""#need to get  from server params
        for eid, enemy in enemies.items():
            # 2. Ask the enemy: "Who do you see?"
            visible_players = enemy.Big_check(arr_id_fromserver, arr_pos_fromserver)

            if visible_players:
                target_id, (tx, ty) = visible_players[0]  # Target the closest player
                dist = distance(enemy.entity.x, enemy.entity.y, tx, ty)

                if dist > S.MONSTERS[enemy.type]["att_radius"]:
                    #movment
                    pass
                else:
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


        screen.fill(S.BLACK)
        draw_map()
        pygame.display.flip()
        clock.tick(10)
    pygame.quit()


if __name__ == "__main__":
    main()