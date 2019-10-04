# Model

from numpy import *
from Pieces import *


class Board:
    def __init__(self, is_white_perspective):
        self.pieces = {}
        self.is_white_perspective = is_white_perspective
        self.board_matrix = None
        # Creates tile dictionary for locations
        self.tiles = {}
        self.ranks = [1, 2, 3, 4, 5, 6, 7, 8]
        self.ranks.reverse()
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.files.reverse()
        for x in range(8):
            for y in range(8):
                self.tiles[self.files[x]+str(self.ranks[y])] = (x*64, y*64)

    def generate_pieces(self, color):
        if color == 'white':
            modifier = 0
            player_rank = 1
            pawn_rank = 2
        else:
            modifier = 16
            player_rank = 8
            pawn_rank = 7
        for x in range(1, 9):
            self.pieces[x + modifier] = Pawn(x + modifier)
            self.pieces[x + modifier].set_current_tile(self.files[x-1]+str(pawn_rank))
        for x in range(2):
            self.pieces[9 + x + modifier] = Bishop(9 + x + modifier)
            self.pieces[9 + x + modifier].set_current_tile(
                self.files[5 - 3*x] + str(player_rank))
        for x in range(2):
            self.pieces[11 + x + modifier] = Knight(11 + x + modifier)
            self.pieces[11 + x + modifier].set_current_tile(
                self.files[6-5*x] + str(player_rank))
        for x in range(2):
            self.pieces[13 + x + modifier] = Rook(13 + x + modifier)
            self.pieces[13 + x + modifier].set_current_tile(
                self.files[7-7*x] + str(player_rank))
        self.pieces[15 + modifier] = Queen(15 + modifier)
        self.pieces[15 + modifier].set_current_tile(
            self.files[3] + str(player_rank))
        self.pieces[16 + modifier] = King(16 + modifier)
        self.pieces[16 + modifier].set_current_tile(
            self.files[4] + str(player_rank))

    def on_init(self):
        white_matrix = array([[29, 27, 25, 31, 32, 26, 28, 30],
                              [17, 18, 19, 20, 21, 22, 23, 24],
                              [0, 0, 0, 0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0, 0, 0, 0],
                              [1, 2, 3, 4, 5, 6, 7, 8],
                              [13, 11, 9, 15, 16, 10, 12, 14]])
        if self.is_white_perspective:
            self.board_matrix = white_matrix
        else:
            self.board_matrix = flip(flip(white_matrix, 0), 1)

    def get_board_matrix(self):
        return self.board_matrix
