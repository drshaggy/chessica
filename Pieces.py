# Model

from abc import *


class Piece(ABC):
    def __init__(self, piece_id):
        self.current_tile = ''
        self.piece_id = piece_id
        if self.piece_id <= 16:
            self.color = 'white'
        else:
            self.color = 'black'
        self.image_path = 'resources/' + self.color + '_' + self.name + '.png'

    @abstractmethod
    def move(self):
        pass

    def get_image_path(self):
        return self.image_path

    def set_current_tile(self, current_tile):
        self.current_tile = current_tile

    def get_current_tile(self):
        return self.current_tile


class Pawn(Piece):
    def __init__(self, piece_id):
        self.name = 'pawn'
        self.points = 1
        super().__init__(piece_id)

    def move(self):
        # todo move logic here
        pass


class Bishop(Piece):
    def __init__(self, piece_id):
        self.name = 'bishop'
        self.points = 3
        super().__init__(piece_id)

    def move(self):
        # todo move logic here
        pass


class Knight(Piece):
    def __init__(self, piece_id):
        self.name = 'knight'
        self.points = 3
        super().__init__(piece_id)

    def move(self):
        # todo move logic here
        pass


class Rook(Piece):
    def __init__(self, piece_id):
        self.name = 'rook'
        self.points = 5
        super().__init__(piece_id)

    def move(self):
        # todo move logic here
        pass


class Queen(Piece):
    def __init__(self, piece_id):
        self.name = 'queen'
        self.points = 9
        super().__init__(piece_id)

    def move(self):
        # todo move logic here
        pass


class King(Piece):
    def __init__(self, piece_id):
        self.name = 'king'
        self.points = 100000000
        super().__init__(piece_id)

    def move(self):
        # todo move logic here
        pass