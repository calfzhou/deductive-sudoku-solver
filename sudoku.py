#/usr/bin/env python3
import argparse
import sys


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
        return f'({self.row + 1}, {self.col + 1})'


class Cell:
    def __init__(self, row, col, size):
        self._point = Point(row, col)
        self._value = None
        self._size = size
        self._candidates = (1 << size) - 1

    @property
    def point(self):
        return self._point

    @property
    def confirmed(self):
        return self._value is not None

    @property
    def value(self):
        if not self.confirmed:
            raise AttributeError('cell value is not confirmed')
        return self._value

    @property
    def candidates(self):
        # TODO: Can be refined.
        return [v for v in range(self._size) if self.is_possible(v)]

    @property
    def candidates_count(self):
        # TODO: Can be refined.
        return len(self.candidates)

    def is_possible(self, value):
        return bool(self._candidates & (1 << value))

    def __str__(self):
        if self.confirmed:
            return f'{self.point}{self._value}'
        else:
            return f'{self.point}[{self._candidates:x}]'


class Board:
    def __init__(self, block_width=3, block_height=3):
        """
        :type block_width: int
        :type block_height: int
        """
        self._block_width = block_width
        self._block_height = block_height
        self._size = block_width * block_height
        self._mapping = '123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self._cells = [Cell(r, c, self._size) for r in range(self._size) for c in range(self._size)]
        self._confirmed_count = 0

    @property
    def block_width(self):
        return self._block_width

    @property
    def block_height(self):
        return self._block_height

    @property
    def size(self):
        return self._size

    @property
    def blocks_per_row(self):
        return self._block_height

    @property
    def blocks_per_col(self):
        return self._block_width

    def mark(self, value):
        return self._mapping[value]

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

    def print_simple(self, output):
        for row in range(self.size):
            is_major_row = (row + 1) % self.block_height == 0
            for col in range(self.size):
                is_major_col = (col + 1) % self.block_width == 0
                cell = self[row, col]
                if cell.confirmed:
                    cell_text = self.mark(cell.value)
                else:
                    cell_text = ''.join(map(self.mark, cell.candidates))
                    cell_text = f'[{cell_text}]'

                if col == self.size - 1:
                    fence = ''
                elif is_major_col:
                    fence = '  '
                else:
                    fence = ' '

                print(f'{cell_text}{fence}', file=output, end='')

            print(file=output)
            if is_major_row and row < self.size - 1:
                print(file=output)

    def __print_board_line(self, output, major, cell_width=1):
        gap = '-' if major else ' '
        fence = '+'
        cell_line = gap.join('-' for _ in range(cell_width))
        board_line = f'{gap}{fence}{gap}'.join(cell_line for _ in range(self.size))
        print(f'{fence}{gap}{board_line}{gap}{fence}', file=output)

    def print_confirmed(self, output):
        self.__print_board_line(output, True)

        for row in range(self.size):
            is_major_row = (row + 1) % self.block_height == 0
            print('|', file=output, end='')
            for col in range(self.size):
                is_major_col = (col + 1) % self.block_width == 0
                cell = self[row, col]
                cell_text = self.mark(cell.value) if cell.confirmed else '?'
                fence = '|' if is_major_col else ':'
                print(f' {cell_text} {fence}', file=output, end='')

            print(file=output)
            self.__print_board_line(output, is_major_row)

    def print_with_candidates(self, output):
        self.__print_board_line(output, True, self.block_width)

        for row in range(self.size):
            is_major_row = (row + 1) % self.block_height == 0
            for sub_row in range(self.block_height):
                print('|', file=output, end='')
                for col in range(self.size):
                    is_major_col = (col + 1) % self.block_width == 0
                    cell = self[row, col]
                    for sub_col in range(self.block_width):
                        value = sub_row * self.block_width + sub_col
                        sub_cell_text = self.mark(value) if cell.is_possible(value) else ' '
                        print(f' {sub_cell_text}', file=output, end='')
                    print(' |' if is_major_col else ' :', file=output, end='')
                print(file=output)

            self.__print_board_line(output, is_major_row, self.block_width)


def test():
    board = Board(3, 2)
    board.print_simple(sys.stdout)
    board.print_confirmed(sys.stdout)
    board.print_with_candidates(sys.stdout)
    print('done.')


def main():
    parser = argparse.ArgumentParser(description='Deductive Sudoku Solver')

    args = parser.parse_args()
    # print(args)
    test()



if __name__ == '__main__':
    main()
