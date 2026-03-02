import pygame
import random
from settings import *
from map_data import *

class Entity:
    def __init__(self, x, y, dir, health, id, type):
        self.id = id
        self.x = x
        self.y = y
        self.dir = dir
        self.health = health
        self.type = type
