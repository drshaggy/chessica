import pygame
from pygame.locals import *

class Tile:
    def __init__(self):
        self.width = 64
        self.length = 64

    def draw(self, screen, x, y, color):
        pygame.draw.rect()