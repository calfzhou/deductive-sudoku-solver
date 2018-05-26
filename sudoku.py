#/usr/bin/env python3
import argparse
import copy
import itertools
import string
import sys
import typing
from enum import Enum, Flag, auto


class AreaType(Enum):
    ROW = auto()
    COLUMN = auto()
    BLOCK = auto()


class Coord:
    def __init__(self, row: int, col: int):
        self._row = row
        self._col = col

    def __copy__(self):
        # This class is immutable.
        return self

    def __deepcopy(self, memo):
        # This class is immutable.
        return self

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
    def __init__(self, left_top: Coord, right_bottom: Coord):
        self._left_top = left_top
        self._right_bottom = right_bottom

    def __copy__(self):
        # This class is immutable.
        return self

    def __deepcopy(self, memo):
        # This class is immutable.
        return self

    @property
    def first_row(self) -> int:
        return self._left_top.row

    @property
    def last_row(self) -> int:
        return self._right_bottom.row

    @property
    def first_col(self) -> int:
        return self._left_top.col

    @property
    def last_col(self) -> int:
        return self._right_bottom.col

    @property
    def row_range(self) -> typing.Iterator[int]:
        return range(self.first_row, self.last_row + 1)

    @property
    def col_range(self) -> typing.Iterator[int]:
        return range(self.first_col, self.last_col + 1)

    def iter_coords(self, excludes: typing.Container[Coord] = None) -> typing.Iterator[Coord]:
        """Iterate all coords within the area, excluding the one given by `excludes`."""
        excludes = excludes or set()
        for row, col in itertools.product(self.row_range, self.col_range):
            coord = Coord(row, col)
            if coord not in excludes:
                yield coord

    def __contains__(self, coord: Coord):
        return self.first_row <= coord.row <= self.last_row and self.first_col <= coord.col <= self.last_col


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
        self._data &= ~self._retrieve_data(candidates)
        return data != self._data

    def peek(self) -> int:
        """Returns a possible candidate value."""
        value = self._data.bit_length() - 1
        return value if value >= 0 else None

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
        new = copy.copy(self)
        new &= other
        return new

    def __ior__(self, other):
        self.add(other)
        return self

    def __or__(self, other):
        new = copy.copy(self)
        new |= other
        return new

    def __isub__(self, other):
        self.remove(other)
        return self

    def __sub__(self, other):
        new = copy.copy(self)
        new -= other
        return new


class Cell:
    def __init__(self, coord: Coord, size: int):
        self._coord = coord
        self._value: int = None
        self._candidates = CandidateSet(size)

    @property
    def coord(self) -> Coord:
        return self._coord

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

    def __str__(self):
        if self.confirmed():
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
        self._mapping: str = f'123456789{string.ascii_uppercase}'
        self._cells = [Cell(coord, self._size) for coord in self.iter_coords()]
        self._confirmed_count = 0

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
    def cells_count(self) -> int:
        return len(self._cells)

    @property
    def blocks_per_row(self) -> int:
        return self._block_height

    @property
    def blocks_per_col(self) -> int:
        return self._block_width

    def mark(self, value: int) -> str:
        return self._mapping[value]

    def iter_coords(self) -> typing.Iterator[Coord]:
        for row, col in itertools.product(range(self._size), repeat=2):
            yield Coord(row, col)

    def iter_row_areas(self) -> typing.Iterator[Area]:
        for row in range(self._size):
            yield Area(Coord(row, 0), Coord(row, self._size - 1))

    def iter_col_areas(self) -> typing.Iterator[Area]:
        for col in range(self._size):
            yield Area(Coord(0, col), Coord(self._size - 1, col))

    def iter_block_areas(self) -> typing.Iterator[Area]:
        pass

    def solved(self) -> bool:
        return self._confirmed_count == self.cells_count

    def get_area(self, coord: Coord, area_type: AreaType) -> Area:
        start: Coord
        end: Coord
        if area_type == area_type.ROW:
            start = Coord(coord.row, 0)
            end = Coord(coord.row, self._size - 1)
        elif area_type == area_type.COLUMN:
            start = Coord(0, coord.col)
            end = Coord(self._size - 1, coord.col)
        elif area_type == area_type.BLOCK:
            start = Coord(coord.row // self._block_height * self._block_height,
                          coord.col // self._block_width * self._block_width)
            end = Coord(start.row + self._block_height - 1, start.col + self._block_width - 1)
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

    def acknowledge_cell(self, coord: Coord, value: int):
        """Remove cell's candidates except the given one.
        Confirmed cell cannot be acknowledged to different value.
        Will NOT confirm the cell.
        """
        if value is None:
            raise ValueError('cannot acknowledge None to a cell')

        cell = self._get_cell(coord)
        if cell.confirmed() and cell.value != value:
            raise ValueError('cannot acknowledge different value to a confirmed cell')

        cell.candidates.retain(value)

    def confirm_cell(self, coord: Coord):
        """Confirm cell's single candidate.
        Will FAIL if the cell doesn't have candidate, or has more than two candidates.
        Will NOT update other cells' candidates.
        """
        cell = self._get_cell(coord)
        if cell.confirmed():
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
        return cell.confirmed()

    def get_cell_candidates_count(self, coord: Coord) -> int:
        cell = self._get_cell(coord)
        return len(cell.candidates)

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

    def print_simple(self, output=sys.stdout):
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

    def __print_board_line(self, output=sys.stdout, major=True, cell_width=1):
        gap = '-' if major else ' '
        fence = '+'
        cell_line = gap.join('-' for _ in range(cell_width))
        board_line = f'{gap}{fence}{gap}'.join(cell_line for _ in range(self.size))
        print(f'{fence}{gap}{board_line}{gap}{fence}', file=output)

    def print_confirmed(self, output=sys.stdout):
        self.__print_board_line(output, True)
        for row in range(self._size):
            is_major_row = (row + 1) % self.block_height == 0
            print('|', file=output, end='')
            for col in range(self._size):
                is_major_col = (col + 1) % self.block_width == 0
                cell: Cell = self._get_cell((row, col))
                cell_text = self.mark(cell.value) if cell.confirmed() else '?'
                fence = '|' if is_major_col else ':'
                print(f' {cell_text} {fence}', file=output, end='')

            print(file=output)
            self.__print_board_line(output, is_major_row)

    def print_with_candidates(self, output=sys.stdout):
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
                            sub_cell_text = '*' if cell.confirmed() else ' '
                        print(f' {sub_cell_text}', file=output, end='')
                    print(' |' if is_major_col else ' :', file=output, end='')
                print(file=output)

            self.__print_board_line(output, is_major_row, self.block_width)


class ParadoxError(Exception):
    pass


class SolvingStatus:
    def __init__(self):
        self.guess_level = 0
        self.solutions: typing.List[Board] = []
        self.interrupted = False

    def print(self, *args, **kwargs):
        if self.guess_level == 0:
            print(*args, **kwargs)
        else:
            print('', '  ' * (self.guess_level - 1), *args, **kwargs)


class SudokuSolver:
    def __init__(self):
        pass

    def solve(self, board: Board) -> SolvingStatus:
        status = SolvingStatus()
        self._deduce(board, status)
        if not board.solved():
            # board.print_with_candidates(sys.stdout)
            self._guess(board, status)

        return status

    @staticmethod
    def _msg_indent(level) -> str:
        return '  ' * level

    def _deduce(self, board: Board, status: SolvingStatus):
        finished = False
        while not finished:
            improved = False
            improved = self._primary_check(board, status) or improved
            # Apply other rules.
            finished = not improved

    def _guess(self, board: Board, status: SolvingStatus):
        coord = self._choose_guessing_coord(board)
        if coord is None:
            return

        cell = board[coord]
        for value in cell.candidates:
            temp_board = copy.deepcopy(board)
            temp_board.acknowledge_cell(cell.coord, value)
            status.print(f'[Guess] assume cell {cell.coord} is "{board.mark(value)}"')
            status.guess_level += 1
            try:
                self._deduce(temp_board, status)
            except ParadoxError as err:
                status.print('[Guess Failed]', err)
            else:
                if temp_board.solved():
                    status.solutions.append(temp_board)
                    status.print('[Solution] find a solution')
                    temp_board.print_simple(sys.stdout)
                else:
                    self._guess(temp_board, status)
            finally:
                status.guess_level -= 1

    def _choose_guessing_coord(self, board: Board) -> Coord:
        coord_for_guessing = None
        min_candidates = board.size + 1
        for coord in board.iter_coords():
            cell: Cell = board[coord]
            if cell.confirmed():
                continue

            if len(cell.candidates) < min_candidates:
                coord_for_guessing = coord
                min_candidates = len(cell.candidates)

        return coord_for_guessing

    def _primary_check(self, board: Board, status: SolvingStatus) -> bool:
        improved = False
        for coord in board.iter_coords():
            cell: Cell = board[coord]
            if cell.confirmed():
                continue

            candidates_count = len(cell.candidates)
            if candidates_count > 1:
                continue
            elif candidates_count == 0:
                raise ParadoxError(f'cell {coord} has no candidate')

            # candidates_count = 1
            board.confirm_cell(coord)
            for area_type in AreaType:
                area = board.get_area(coord, area_type)
                result = board.remove_candidates(cell.candidates, area.iter_coords(excludes={coord}))
                improved = result or improved
            status.print(f'[Primary Check] cell {coord} is confirmed to be "{board.mark(cell.value)}"')

        return improved


def test(args):
    board = Board(3, 3)
    with open(args.puzzle_file) as f:
        for row, line in enumerate(f):
            if row == board.size:
                break

            for col, char in enumerate(line):
                value = board._mapping.find(char)
                if value >= 0:
                    board.acknowledge_cell((row, col), value)

    # board.print_simple(sys.stdout)
    # board.print_confirmed(sys.stdout)
    # board.print_with_candidates(sys.stdout)

    solver = SudokuSolver()
    status = solver.solve(board)
    # board.print_confirmed(sys.stdout)
    # board.print_simple(sys.stdout)
    # board.print_with_candidates(sys.stdout)
    if board.solved():
        print('puzzle is solved without guess')
    elif status.solutions:
        print(f'find {len(status.solutions)} solutions by guessing')
        if status.interrupted:
            print('there might be more solutions')
    else:
        print('puzzle is unsolvable')
    # board.print_confirmed(sys.stdout)


def main():
    parser = argparse.ArgumentParser(description='Deductive Sudoku Solver')

    puzzle_group = parser.add_argument_group('board arguments')
    puzzle_group.add_argument('-w', '--block-width', type=int, default=3,
                              help='how many columns a block contains (default: 3)')
    puzzle_group.add_argument('--block-height', type=int, default=3,
                              help='how many rows a block contains (default: 3)')
    puzzle_group.add_argument('--mapping',
                              help='')
    puzzle_group.add_argument('-f', '--puzzle-file',
                              help='puzzle file')

    args = parser.parse_args(['-f', 'old/002que.txt'])
    print(args)
    test(args)



if __name__ == '__main__':
    main()
