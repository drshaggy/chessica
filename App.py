# View

import pygame
from Tile import Tile
from Board_Logic import *
from Pieces import *
from Player import *
from math import *


class App:
    def __init__(self):
        self.white = (255, 229, 204)
        self.black = (102, 51, 0)
        self.gray = (211, 211, 211)
        self.running = True
        self.screen = None
        self.size = self.weight, self.height = 512, 512
        self.board_matrix = None
        self.tile_values = {0: 'blank',
                            1: 'white_pawn',
                            2: 'black_pawn',
                            3: 'white_bishop',
                            4: 'black_bishop',
                            5: 'white_knight',
                            6: 'black_knight',
                            7: 'white_rook',
                            8: 'black_rook',
                            9: 'white_queen',
                            10: 'black_queen',
                            11: 'white_king',
                            12: 'black_king'}
        self.board = Board(True)
        self.player1 = Player(True)

    def on_init(self):
        # Initialize gui
        pygame.init()
        pygame.display.set_caption('Player2')
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.running = True

        # Initialize board logic
        self.board.on_init()
        self.board.generate_pieces('white')
        self.board.generate_pieces('black')

    def on_event(self, event):
        if event.type == pygame.QUIT:
            print("Exiting App")
            self.running = False

    def on_loop(self):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if click[0] == 1:  # If left mouse button is pressed
            selected_tile = self.find_tile(mouse[0], mouse[1])
            print(selected_tile)
            selected = pygame.image.load('resources/selected.png').convert()
            alpha = 64
            selected.set_alpha(alpha)
            tiles = self.board.tiles
            loc = tiles[selected_tile]
            self.screen.blit(selected, loc)
            pygame.display.update()


    def on_render(self):
        self.screen.fill(self.gray)
        self.generate_board()
        self.draw_pieces()
        pygame.display.update()

    def on_cleanup(self):
        pygame.quit()

    def draw_tile(self, tile: Tile, x, y) -> Tile:
        width = tile.get_width()
        length = tile.get_length()
        color = tile.get_color()
        pygame.draw.rect(self.screen, color, (x, y, width, length))

    def generate_board(self):
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

    def draw_pieces(self):
        for x in range(8):
            for y in range(8):
                piece_id = self.board.board_matrix[y, x]
                if piece_id == 0:
                    pass
                else:
                    self.draw_piece(self.board.pieces[piece_id])

    def draw_piece(self, piece: Piece) -> Piece:
        # tell pygame to draw a piece on the screen
        dim = self.board.tiles[piece.current_tile]
        image_path = piece.get_image_path()
        img = pygame.image.load(image_path)
        self.screen.blit(img, dim)

    def find_tile(self, x, y):
        tile_x = floor(x/64)
        tile_y = floor(y/64)
        files = self.board.files
        ranks = self.board.ranks_rev
        st = files[tile_x]
        r = str(ranks[tile_y])
        return st + r


