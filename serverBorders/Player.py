import pygame

class Player:
    def __init__(self, x=100, y=100):
        self.x = x
        self.y = y

        self.width = 40
        self.height = 40

    def move(self, xVel, yVel):
        self.x += xVel
        self.y += yVel

    def draw(self, screen):
        playerRect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (190, 190, 190), playerRect)