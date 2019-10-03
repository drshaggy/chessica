import pygame
from pygame.locals import *
from Tile import Tile


class App:
    def __init__(self):
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.running = True
        self.screen = None
        self.size = self.weight, self.height = 1000, 1000

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
        pygame.draw.rect(self.screen, self.white, (0, 936, 64, 64))
        pygame.display.update()


    def on_cleanup(self):
        pygame.quit()

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
