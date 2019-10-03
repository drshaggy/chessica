import pygame
from pygame.locals import *
from Tile import Tile
from Board_Logic import *
from Pieces import *


class App:
    def __init__(self):
        self.white = (255, 229, 204)
        self.black = (102, 51, 0)
        self.gray = (211, 211, 211)
        self.running = True
        self.screen = None
        self.size = self.weight, self.height = 512, 512
        self.tile_values = {0: 'blank',
                            1: 'white_pawn',
                            2: 'black_pawn',
                            3: 'white_bishop',
                            4: 'black_bishop',
                            5: 'white_knight',
                            6: 'black_knight',
                            7: 'white_rook',
                            8:'black_rook',
                            9: 'white_queen',
                            10: 'black_queen',
                            11: 'white_king',
                            12: 'black_king'}

    def on_init(self):
        # Initialize gui
        pygame.init()
        pygame.display.set_caption('Chessica')
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.running = True

        # Initialize board logic
        board = Board(True)
        board.on_init()
        self.board_matrix = board.get_board_matrix()

    def on_event(self, event):
        if event.type == pygame.QUIT:
            print("Exiting App")
            self.running = False

    def on_loop(self):
        pass

    def on_render(self):
        self.screen.fill(self.gray)
        self.create_board()
        rook = Rook('white')
        self.draw_pieces(self.board_matrix)
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

    def draw_pieces(self, board_matrix):
        for x in range(8):
            for y in range(8):
                piece_id = board_matrix[y, x]
                if piece_id == 0:
                    pass
                else:
                    self.draw_piece('resources/' + self.tile_values[piece_id] + '.png',
                                x * 64, y * 64)

    def draw_piece(self, piece, x, y):
        img = pygame.image.load(piece)
        img_rect = img.get_rect()
        self.screen.blit(img, (x, y))
