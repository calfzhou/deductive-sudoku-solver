#/usr/bin/env python3
import argparse
import string
import sys
from enum import Enum, Flag, auto
from typing import List, Tuple


class AreaType(Enum):
    ROW = auto()
    COLUMN = auto()
    BLOCK = auto()


class OperationRange(Flag):
    CELLS = auto()
    GIVEN_AREA = auto()
    OTHER_AREAS = auto()
    AREAS = GIVEN_AREA | OTHER_AREAS
    ALL = CELLS | AREAS


class Coord:
    def __init__(self, row: int, col: int):
        self._row = row
        self._col = col

    @property
    def row(self) -> int:
        return self._row

    @property
    def col(self) -> int:
        return self._col

    def __str__(self):
        return f'({self._row + 1}, {self.col + 1})'


class Area:
    def __init__(self, start: Coord, end: Coord):
        self._start = start
        self._end = end

    @property
    def row_start(self) -> int:
        return self._start.row

    @property
    def row_end(self) -> int:
        return self._end.row

    @property
    def col_start(self) -> int:
        return self._start.col

    @property
    def col_end(self) -> int:
        return self._end.col

    def __contains__(self, coord: Coord):
        return self.row_start <= coord.row < self.row_end and self.col_start <= coord.col < self.col_end


class CandidateSet:
    def __init__(self, size: int = 0):
        self._size = size
        self._data = self._mask(size) - 1

    @staticmethod
    def _mask(value: int) -> int:
        return 1 << value

    def set(self, value: int):
        self._data = self._mask(value)

    def retain(self, value: int):
        self._data &= self._mask(value)

    def add(self, value: int):
        self._data |= self._mask(value)

    def remove(self, value: int):
        self &= ~self._mask(value)

    def first(self) -> int:
        for value in self:
            return value

        return None

    def copy(self):
        new = CandidateSet(self._size)
        new._data = self._data
        return new

    def __len__(self):
        # TODO: Can be refined.
        return len([v for v in self])

    def __contains__(self, value: int):
        return bool(self._data & self._mask(value))

    def __iter__(self):
        data = self._data
        value = 0
        while data > 0:
            if (data & 1) == 1:
                yield value

            data >>= 1
            value += 1

    def __iand__(self, other):
        if isinstance(other, CandidateSet):
            self._data &= other._data
        # elif isinstance(other, int):
        #     self._data &= self._mask(other)
        else:
            raise TypeError(f'cannot &= with {type(other)}')

        return self

    def __and__(self, other):
        new = self.copy()
        new &= other
        return new

    def __ior__(self, other):
        if isinstance(other, CandidateSet):
            self._data |= other._data
        # elif isinstance(other, int):
        #     self._data |= self._mask(other)
        else:
            raise TypeError(f'cannot |= with {type(other)}')

        return self

    def __or__(self, other):
        new = self.copy()
        new |= other
        return new

    def __isub__(self, other):
        if isinstance(other, CandidateSet):
            self._data &= ~other._data
        # elif isinstance(other, int):
        #     self._data &= ~self._mask(other)
        else:
            raise TypeError(f'cannot -= with {type(other)}')

        return self

    def __sub__(self, other):
        new = self.copy()
        new -= other
        return new


class Cell:
    def __init__(self, row: int, col: int, size: int):
        self._coord = Coord(row, col)
        self._value: int = None
        self._candidates = CandidateSet(size)

    @property
    def coord(self) -> Coord:
        return self._coord

    @property
    def confirmed(self) -> bool:
        return self._value is not None

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int):
        self._value = value
        if value is not None:
            self._candidates.set(value)

    @property
    def candidates(self) -> CandidateSet:
        return self._candidates

    def is_possible(self, value: int) -> bool:
        return value in self._candidates

    def intersection_candidates(self, candidates: CandidateSet):
        self._candidates &= candidates

    def difference_candidates(self, candidates: CandidateSet):
        self._candidates -= candidates

    def __str__(self):
        if self.confirmed:
            return f'{self._coord}{self._value}'
        else:
            return f'{self._coord}[{self._candidates}]'


# Cell 不做逻辑检查，直接接受指令并操作。
# Board 做单个cell的逻辑检查，但不做cell之间的逻辑判定。
class Board:
    def __init__(self, block_width: int = 3, block_height: int = 3):
        self._block_width = block_width
        self._block_height = block_height
        self._size = block_width * block_height
        self._mapping = f'123456789{string.ascii_uppercase}'
        self._cells : List[Cell] = [Cell(r, c, self._size) for r in range(self._size) for c in range(self._size)]
        self._confirmed_count = 0

    def acknowledge_cell_value(self, coord: Coord, value: int):
        """Remove cell's candidates except the given one.
        Confirmed cell cannot be acknowledged to different value.
        Will NOT confirm the cell.
        """
        if value is None:
            raise ValueError('cannot acknowledge None to a cell')

        cell: Cell = self[coord]
        if cell.confirmed and cell.value != value:
            raise ValueError('cannot acknowledge different value to a confirmed cell')

        cell.candidates.retain(value)

    def confirm_cell(self, coord: Coord):
        """Confirm cell's single candidate.
        Will FAIL if the cell has no candidate, or more than two candidates.
        Will NOT update other cells' candidates.
        """
        cell: Cell = self[coord]
        if cell.confirmed:
            return

        if len(cell.candidates) != 1:
            raise ValueError('cannot confirm a cell with 0 candidate or 2+ candidates')

        cell.value = cell.candidates.first()
        self._confirmed_count += 1

    @property
    def block_width(self) -> int:
        return self._block_width

    @property
    def block_height(self) -> int:
        return self._block_height

    @property
    def size(self) -> int:
        return self._size

    @property
    def blocks_per_row(self) -> int:
        return self._block_height

    @property
    def blocks_per_col(self) -> int:
        return self._block_width

    def get_area(self, coord: Coord, area_type: AreaType) -> Area:
        start: Coord
        end: Coord
        if area_type == area_type.ROW:
            start = Coord(coord.row, 0)
            end = Coord(coord.row + 1, self._size)
        elif area_type == area_type.COLUMN:
            start = Coord(0, coord.col)
            end = Coord(self._size, coord.col + 1)
        elif area_type == area_type.BLOCK:
            start = Coord(coord.row // self._block_height * self._block_height,
                          coord.col // self._block_width * self._block_width)
            end = Coord(start.row + self._block_height, start.col + self._block_width)
        else:
            assert False, f'invalid area type {area_type}'

        return Area(start, end)

    def get_common_area(self, coords: List[Coord], area_type: AreaType) -> Area:
        coord_iter = iter(coords)
        coord = next(coord_iter, None)
        if coord is None:
            return None

        area = self.get_area(coord, area_type)
        for coord in coord_iter:
            if coord not in area:
                return None

        return area

    def mark(self, value: int) -> str:
        return self._mapping[value]

    def _to_index(self, row: int, col: int) -> int:
        assert 0 <= row < self._size, f'row {row} out of range'
        assert 0 <= col < self._size, f'col {col} out of range'
        return row * self._size + col

    def _to_row_col(self, index: int) -> Tuple[int, int]:
        assert 0 <= index < self._size * self._size, f'index {index} out of range'
        return divmod(index, self._size)

    def _validate_coord(self, coord):
        if not (0 <= coord.row < self._size and 0 <= coord.col < self._size):
            raise ValueError(f'coord {coord} out of range')

    def __getitem__(self, coord: Coord) -> Cell:
        if isinstance(coord, (tuple, list)):
            coord = Coord(*coord)

        self._validate_coord(coord)
        return self._cells[self._to_index(coord.row, coord.col)]

    def print_simple(self, output):
        for row in range(self._size):
            is_major_row = (row + 1) % self.block_height == 0
            for col in range(self._size):
                is_major_col = (col + 1) % self.block_width == 0
                cell = self[row, col]
                if cell.confirmed:
                    cell_text = self.mark(cell.value)
                else:
                    cell_text = ''.join(map(self.mark, cell.candidates))
                    cell_text = f'[{cell_text}]'

                if col == self._size - 1:
                    fence = ''
                elif is_major_col:
                    fence = '  '
                else:
                    fence = ' '

                print(f'{cell_text}{fence}', file=output, end='')

            print(file=output)
            if is_major_row and row < self._size - 1:
                print(file=output)

    def __print_board_line(self, output, major, cell_width=1):
        gap = '-' if major else ' '
        fence = '+'
        cell_line = gap.join('-' for _ in range(cell_width))
        board_line = f'{gap}{fence}{gap}'.join(cell_line for _ in range(self.size))
        print(f'{fence}{gap}{board_line}{gap}{fence}', file=output)

    def print_confirmed(self, output):
        self.__print_board_line(output, True)

        for row in range(self._size):
            is_major_row = (row + 1) % self.block_height == 0
            print('|', file=output, end='')
            for col in range(self._size):
                is_major_col = (col + 1) % self.block_width == 0
                cell = self[row, col]
                cell_text = self.mark(cell.value) if cell.confirmed else '?'
                fence = '|' if is_major_col else ':'
                print(f' {cell_text} {fence}', file=output, end='')

            print(file=output)
            self.__print_board_line(output, is_major_row)

    def print_with_candidates(self, output):
        self.__print_board_line(output, True, self.block_width)

        for row in range(self._size):
            is_major_row = (row + 1) % self.block_height == 0
            for sub_row in range(self.block_height):
                print('|', file=output, end='')
                for col in range(self._size):
                    is_major_col = (col + 1) % self.block_width == 0
                    cell = self[row, col]
                    for sub_col in range(self.block_width):
                        value = sub_row * self.block_width + sub_col
                        if cell.is_possible(value):
                            sub_cell_text = self.mark(value)
                        else:
                            sub_cell_text = '*' if cell.confirmed else ' '
                        print(f' {sub_cell_text}', file=output, end='')
                    print(' |' if is_major_col else ' :', file=output, end='')
                print(file=output)

            self.__print_board_line(output, is_major_row, self.block_width)


def test():
    board = Board(3, 3)
    board.acknowledge_cell_value((1, 2), 1)
    board.acknowledge_cell_value((2, 5), 7)
    board.acknowledge_cell_value((4, 3), 6)
    board.confirm_cell((4, 3))
    board.print_simple(sys.stdout)
    board.print_confirmed(sys.stdout)
    board.print_with_candidates(sys.stdout)
    print('done.')


def main():
    parser = argparse.ArgumentParser(description='Deductive Sudoku Solver')

    # parser.add_argument('-w', '--block-width', type=int, default=3,
    #                     help='')

    args = parser.parse_args()
    # print(args)
    test()



if __name__ == '__main__':
    main()
