import pygame
from pygame.locals import *


class Tile:
    def __init__(self, color, file, rank):
        self.width = 64
        self.length = 64
        self.color = color
        self.rank = rank
        self.file = file

    def get_width(self):
        return self.width

    def get_length(self):
        return self.length

    def get_color(self):
        return self.color

    def get_file(self):
        return self.file

    def get_rank(self):
        return self.rank

