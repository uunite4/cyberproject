import pygame
from SETTINGS import S
from Player import *
from map import *
from enemy import *

def main():
    pygame.init()

    clock = pygame.time.Clock()
    enemy = enemyData(pid=1, x=640, y=320, p_type="fighter", speed = 3, see_radius=5, att_radius= 7) # enemy
    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill(S.BLACK)
        draw_map()
        enemy.draw(screen)
        pygame.display.flip()
        clock.tick(10)
    pygame.quit()


if __name__ == "__main__":
    main()