#/usr/bin/env python3
import argparse
import string
import sys
import typing
from enum import Enum, Flag, auto


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

    def __hash__(self):
        return hash((self._row, self._col))

    def __eq__(self, other):
        if isinstance(other, Coord):
            return self._row == other._row and self._col == other._col
        else:
            return False

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

    def walk(self, excludes: typing.Container[Coord] = None) -> typing.Generator[Coord]:
        """Walk through all coords within the area, excluding the one given by `excludes`."""
        excludes = excludes or set()
        for row in range(self.row_start, self.row_end):
            for col in range(self.col_start, self.col_end):
                coord = Coord(row, col)
                if coord not in excludes:
                    yield coord

    def __contains__(self, coord: Coord):
        return self.row_start <= coord.row < self.row_end and self.col_start <= coord.col < self.col_end


class CandidateSet:
    def __init__(self, size: int = 0):
        self._size = size
        self._data = self._mask(size) - 1

    @staticmethod
    def _mask(value: int) -> int:
        return 1 << value

    @staticmethod
    def _retrieve_data(candidates) -> int:
        if isinstance(candidates, CandidateSet):
            return candidates._data
        elif isinstance(candidates, int):
            return CandidateSet._mask(candidates)
        else:
            raise TypeError(f'cannot retrieve data from type {type(candidates)}')

    def set(self, candidates: typing.Union['CandidateSet', int]) -> bool:
        """Returns True if candidates changed."""
        data = self._data
        self._data = self._retrieve_data(candidates)
        return data != self._data

    def retain(self, candidates: typing.Union['CandidateSet', int]) -> bool:
        """Returns True if candidates changed."""
        data = self._data
        self._data &= self._retrieve_data(candidates)
        return data != self._data

    def add(self, candidates: typing.Union['CandidateSet', int]) -> bool:
        """Returns True if candidates changed."""
        data = self._data
        self._data |= self._retrieve_data(candidates)
        return data != self._data

    def remove(self, candidates: typing.Union['CandidateSet', int]) -> bool:
        """Returns True if candidates changed."""
        data = self._data
        self &= ~self._retrieve_data(candidates)
        return data != self._data

    def peek(self) -> int:
        """Returns a possible candidate value."""
        value = self._data.bit_length() - 1
        return value if value >= 0 else None

    def copy(self):
        new = CandidateSet(self._size)
        new._data = self._data
        return new

    def __len__(self):
        return bin(self._data).count('1')

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
        self.retain(other)
        return self

    def __and__(self, other):
        new = self.copy()
        new &= other
        return new

    def __ior__(self, other):
        self.add(other)
        return self

    def __or__(self, other):
        new = self.copy()
        new |= other
        return new

    def __isub__(self, other):
        self.remove(other)
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
# 只有board可以操作cell。
class Board:
    def __init__(self, block_width: int = 3, block_height: int = 3):
        self._block_width = block_width
        self._block_height = block_height
        self._size = block_width * block_height
        self._mapping = f'123456789{string.ascii_uppercase}'
        self._cells = [Cell(r, c, self._size) for r in range(self._size) for c in range(self._size)]
        self._confirmed_count = 0

    def acknowledge_cell(self, coord: Coord, value: int):
        """Remove cell's candidates except the given one.
        Confirmed cell cannot be acknowledged to different value.
        Will NOT confirm the cell.
        """
        if value is None:
            raise ValueError('cannot acknowledge None to a cell')

        cell = self._get_cell(coord)
        if cell.confirmed and cell.value != value:
            raise ValueError('cannot acknowledge different value to a confirmed cell')

        cell.candidates.retain(value)

    def confirm_cell(self, coord: Coord):
        """Confirm cell's single candidate.
        Will FAIL if the cell doesn't have candidate, or has more than two candidates.
        Will NOT update other cells' candidates.
        """
        cell = self._get_cell(coord)
        if cell.confirmed:
            return

        if len(cell.candidates) != 1:
            raise ValueError('cannot confirm a cell with 0 candidate or 2+ candidates')

        cell.value = cell.candidates.peek()
        self._confirmed_count += 1

    def retain_candidates(self, candidates: CandidateSet, coords: typing.Iterable[Coord]) -> bool:
        """Returns True if candidates changed."""
        modified = False
        coord: Coord
        for coord in coords:
            cell = self._get_cell(coord)
            modified = cell.candidates.retain(candidates) or modified

        return modified

    def remove_candidates(self, candidates: CandidateSet, coords: typing.Iterable[Coord]) -> bool:
        """Returns True if candidates changed."""
        modified = False
        coord: Coord
        for coord in coords:
            cell = self._get_cell(coord)
            modified = cell.candidates.remove(candidates) or modified

        return modified

    def is_cell_confirmed(self, coord: Coord) -> bool:
        cell = self._get_cell(coord)
        return cell.confirmed

    def get_cell_candidates_count(self, coord: Coord) -> int:
        cell = self._get_cell(coord)
        return len(cell.candidates)

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

    def get_common_area(self, coords: typing.Iterable[Coord], area_type: AreaType) -> Area:
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

    def _to_row_col(self, index: int) -> typing.Tuple[int, int]:
        assert 0 <= index < self._size * self._size, f'index {index} out of range'
        return divmod(index, self._size)

    def _validate_coord(self, coord):
        if not (0 <= coord.row < self._size and 0 <= coord.col < self._size):
            raise ValueError(f'coord {coord} out of range')

    def _get_cell(self, coord: Coord) -> Cell:
        if isinstance(coord, (tuple, list)):
            coord = Coord(*coord)

        self._validate_coord(coord)
        return self._cells[self._to_index(coord.row, coord.col)]

    def __getitem__(self, coord: Coord) -> Cell:
        return self._get_cell(coord)

    def print_simple(self, output):
        for row in range(self._size):
            is_major_row = (row + 1) % self.block_height == 0
            for col in range(self._size):
                is_major_col = (col + 1) % self.block_width == 0
                cell: Cell = self._get_cell((row, col))
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
                cell: Cell = self._get_cell((row, col))
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
                    cell = self._get_cell((row, col))
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


class ParadoxError(Exception):
    pass


class SudokuSolver:
    def __init__(self):
        pass

    def solve(self, board: Board):
        self._deduce(board)
        # deduce
        # if not ok: guess
        #
        # deduce:
        #   do:
        #     apply rules
        #   while has progress
        #
        # guess:
        #   choose a cell
        #   for each possibility:
        #     assume
        #     deduce
        #     if failed: roll back, continue
        #     if not ok: guess
        #     if ok: return
        pass

    def _deduce(self, board: Board):
        # Check if is already done here?
        improved = False
        improved = self._primary_deduce() or improved

    def _primary_deduce(self) -> bool:
        # for each coord, if no candidate, error; if 2+ candidates, pass.
        # confirm cell
        # for each area type: retain area exclude cell
        pass


def test():
    board = Board(3, 3)
    board.acknowledge_cell((1, 2), 1)
    board.acknowledge_cell((2, 5), 7)
    board.acknowledge_cell((4, 3), 4)
    board.confirm_cell((4, 3))
    board.print_simple(sys.stdout)
    board.print_confirmed(sys.stdout)
    board.print_with_candidates(sys.stdout)

    solver = SudokuSolver()
    solver.solve(board)
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
