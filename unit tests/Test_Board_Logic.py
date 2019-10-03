import unittest
import numpy
from Board_Logic import *


class MyTestCase(unittest.TestCase):
    def test_on_init(self):
        expected = array([[7, 5, 3, 11, 9, 3, 5, 7],
                          [1, 1, 1, 1, 1, 1, 1, 1],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0, 0, 0, 0],
                          [2, 2, 2, 2, 2, 2, 2, 2],
                          [8, 6, 4, 12, 10, 4, 6, 8]])
        board = Board(False)
        board.on_init()
        result = board.board_matrix
        numpy.testing.assert_array_equal(result, expected)


if __name__ == '__main__':
    unittest.main()
