#/usr/bin/env python3
import argparse


class Point:
    def __init__(self, row, col):
        """
        :type row: int
        :param col: vertical coord, from top to bottom, starting from 0
        :type col: int
        :param row: horizontal coord, from left to right, staring from 0
        """
        self._row = row
        self._col = col

    @property
    def row(self):
        return self._row

    @property
    def col(self):
        return self._col

    def __str__(self):
        return '({}, {})'.format(self.row + 1, self.col + 1)


class Cell:
    def __init__(self, point):
        """
        :type point: Point
        """
        self._point = point
        self.value = None
        self.candidates = 0
        self._mapping = '123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    @property
    def point(self):
        return self._point

    def __str__(self):
        if self.value is None:
            return '{}[{}]'.format(self.point, self.candidates)
        else:
            return '{}[{}]'.format(self.point, self.value)


class Board:
    def __init__(self, block_width, block_height):
        """
        :type block_width: int
        :type block_height: int
        """
        self._block_width = block_width
        self._block_height = block_height
        self._size = block_width * block_height
        self._cells = [Cell(Point(r, c)) for r in range(self._size) for c in range(self._size)]
        full_candidates = (1 << self._size) - 1
        for cell in self._cells:
            cell.candidates = full_candidates

    @property
    def block_width(self):
        return self._block_width

    @property
    def block_height(self):
        return self._block_height

    @property
    def size(self):
        return self._size

    def _to_index(self, row, col):
        return row * self.size + col

    def _to_row_col(self, index):
        return divmod(index, self.size)

    def __getitem__(self, row_col):
        """
        :type row_col: Point | tuple[int]
        :rtype: Cell
        """
        if isinstance(row_col, Point):
            row, col = row_col.row, row_col.col
        else:
            row, col = row_col
        return self._cells[self._to_index(row, col)]

    def to_str_simple(self):
        parts = []
        for row in range(self.size):
            for col in range(self.size):
                pass


def test():
    board = Board(2, 3)
    for row in range(board.size):
        for col in range(board.size):
            print(board[row, col], end='')
        print()


def main():
    parser = argparse.ArgumentParser(description='Deductive Sudoku Solver')

    args = parser.parse_args()
    # print(args)
    test()



if __name__ == '__main__':
    main()
