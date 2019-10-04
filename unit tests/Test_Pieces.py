import unittest
from Pieces import *


class MyTestCase(unittest.TestCase):
    def test_rook_construction(self):
        rook = Rook(13)
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
