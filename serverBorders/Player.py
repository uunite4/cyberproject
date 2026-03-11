import pygame
import SETTINGS as S

class Player:
    def __init__(self, x=100, y=100, dir=3, health=100):
        self.x = x
        self.y = y
        self.dir = dir
        self.health = health

        self.width = 40
        self.height = 40

    # def move(self, xVel, yVel):
    #     self.x += xVel
    #     self.y += yVel

    def tp(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir

