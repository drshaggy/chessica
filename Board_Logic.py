from numpy import *


class Board:
    def __init__(self, is_white_perspective):
        self.is_white_perspective = is_white_perspective
        self.tile_values = {'blank': 0,
                            'white_pawn': 1,
                            'black_pawn': 2,
                            'white_bishop': 3,
                            'black_bishop': 4,
                            'white_knight': 5,
                            'black_knight': 6,
                            'white_rook': 7,
                            'black_rook': 8,
                            'white_queen': 9,
                            'black_queen': 10,
                            'white_king': 11,
                            'black_king': 12}

    def on_init(self):
        white_matrix = array([[8, 6, 4, 10, 12, 4, 6, 8],
                              [2, 2, 2, 2, 2, 2, 2, 2],
                              [0, 0, 0, 0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0, 0, 0, 0],
                              [1, 1, 1, 1, 1, 1, 1, 1],
                              [7, 5, 3, 9, 11, 3, 5, 7]])
        if self.is_white_perspective:
            self.board_matrix = white_matrix
        else:
            self.board_matrix = flip(flip(white_matrix, 0), 1)

    def get_board_matrix(self):
        return self.board_matrix
