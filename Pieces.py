from abc import *


class Piece(ABC):
    def __init__(self, color):
        self.color = color
        self.points = 0
        self.image = ''

    @abstractmethod
    def move(self):
        pass


class Rook(Piece):
    def __init__(self, color):
        super().__init__(self)
        self.points = 5
        self.image = 'resources/'+color+'_rook.png'

    def move(self):
        # Todo add movement logic here
        pass

