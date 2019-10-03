import pygame
from pygame.locals import *
from Tile import Tile


class App:
    def __init__(self):
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.gray = (211, 211, 211)
        self.running = True
        self.screen = None
        self.size = self.weight, self.height = 512, 512

    def on_init(self):
        pygame.init()
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.running = True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            print("Exiting App")
            self.running = False

    def on_loop(self):
        pass

    def on_render(self):
        self.screen.fill(self.gray)
        self.create_board()
        pygame.display.update()

    def on_cleanup(self):
        pygame.quit()

    def draw_tile(self, tile: Tile, x, y) -> Tile:
        width = tile.get_width()
        length = tile.get_length()
        color = tile.get_color()
        pygame.draw.rect(self.screen, color, (x, y, width, length))

    def create_board(self):
        for x in range(8):
            for y in range(8):
                if (x + y) % 2 == 0:
                    white_tile = Tile(self.white, x, y)
                    self.draw_tile(white_tile, x * 64, y * 64)
                else:
                    black_tile = Tile(self.black, x, y)
                    self.draw_tile(black_tile, x * 64, y * 64)

    def on_execute(self):
        print("Starting App")
        if self.on_init() == False:
            self.running = False

        while self.running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup
