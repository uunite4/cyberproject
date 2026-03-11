import pygame

class Player:
    def __init__(self, x=100, y=100, dir=3):
        self.x = x
        self.y = y
        self.dir = dir

        self.width = 40
        self.height = 40

    # def move(self, xVel, yVel):
    #     self.x += xVel
    #     self.y += yVel

    def tp(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir

    def draw(self, screen):
        playerRect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (190, 190, 190), playerRect)

