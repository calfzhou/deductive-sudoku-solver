#/usr/bin/env python3
import argparse
import copy
import itertools
import string
import typing
from enum import Enum, auto


class NumberSet:
    def __init__(self, size: int = 0):
        self._size = size
        self._data = self._mask(size) - 1

    @staticmethod
    def _mask(value: int) -> int:
        return 1 << value

    @classmethod
    def _retrieve_data(cls, numbers) -> int:
        if isinstance(numbers, cls):
            return numbers._data
        elif isinstance(numbers, int):
            return cls._mask(numbers)
        elif isinstance(numbers, typing.Iterable):
            data = 0
            for number in numbers:
                data |= cls._mask(number)
            return data
        else:
            raise TypeError(f'cannot retrieve data from type {type(numbers)}')

    def set(self, numbers: typing.Union['NumberSet', int, typing.Iterable[int]]) -> bool:
        """Returns True if numbers changed."""
        data = self._data
        self._data = self._retrieve_data(numbers)
        return data != self._data

    def retain(self, numbers: typing.Union['NumberSet', int, typing.Iterable[int]]) -> bool:
        """Returns True if numbers changed."""
        data = self._data
        self._data &= self._retrieve_data(numbers)
        return data != self._data

    def add(self, numbers: typing.Union['NumberSet', int, typing.Iterable[int]]) -> bool:
        """Returns True if numbers changed."""
        data = self._data
        self._data |= self._retrieve_data(numbers)
        return data != self._data

    def remove(self, numbers: typing.Union['NumberSet', int, typing.Iterable[int]]) -> bool:
        """Returns True if numbers changed."""
        data = self._data
        self._data &= ~self._retrieve_data(numbers)
        return data != self._data

    def peek(self) -> int:
        """Returns an available number."""
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


class AreaType(Enum):
    ROW = auto()
    COLUMN = auto()
    BLOCK = auto()

    def orthogonal_type(self):
        if self == type(self).ROW:
            return type(self).COLUMN
        elif self == type(self).COLUMN:
            return type(self).ROW
        else:
            raise ValueError(f'there is no orthogonal area type of {self}')


class Cell:
    def __init__(self, row: int, col: int, board: 'Board'):
        assert 0 <= row < board.size, f'cell row {row} out of range'
        assert 0 <= col < board.size, f'cell col {col} out of range'
        self._row = row
        self._col = col
        self._index = board.size * row + col
        row_in_block = row % board.block_height
        col_in_block = col % board.block_width
        block_index = board.block_width * row_in_block + col_in_block
        # Cell index inside surrounding area.
        self._index_of_areas = {
            AreaType.ROW: col,
            AreaType.COLUMN: row,
            AreaType.BLOCK: block_index,
        }
        self._areas: typing.Dict[AreaType, 'Area'] = {}

    @property
    def row(self) -> int:
        return self._row

    @property
    def col(self) -> int:
        return self._col

    @property
    def index(self) -> int:
        return self._index

    def index_of_area(self, area_or_type: typing.Union[AreaType, 'Area']) -> int:
        if isinstance(area_or_type, Area):
            return self._index_of_areas[area_or_type.area_type]
        elif isinstance(area_or_type, AreaType):
            return self._index_of_areas[area_or_type]
        else:
            raise TypeError(f'Unsupported type: "{type(area_or_type)}"')

    def get_area(self, area_type: AreaType) -> 'Area':
        return self._areas[area_type]

    def iter_areas(self) -> typing.Iterator['Area']:
        return self._areas.values()

    def __repr__(self):
        return f'({self._row + 1},{self._col + 1})'


class Area:
    def __init__(self, area_type: AreaType, index: int, board: 'Board'):
        assert 0 <= index < board.size, f'area index {index} out of range'
        self._area_type = area_type
        self._index = index
        self._cells: typing.List[Cell] = []

    @property
    def area_type(self) -> AreaType:
        return self._area_type

    @property
    def index(self) -> int:
        return self._index

    @property
    def first_row(self) -> int:
        return self._cells[0].row

    @property
    def first_col(self) -> int:
        return self._cells[0].col

    @property
    def last_row(self) -> int:
        return self._cells[-1].row

    @property
    def last_col(self) -> int:
        return self._cells[-1].col

    def get_cell(self, index_of_area: int) -> Cell:
        return self._cells[index_of_area]

    def iter_cells(self, excludes: typing.Iterable = None) -> typing.Iterator[Cell]:
        positions = NumberSet(0)
        for item in excludes or []:
            if isinstance(item, Cell):
                positions.add(item.index_of_area(self._area_type))
            elif isinstance(item, Area):
                positions.add(item.index)
            elif isinstance(item, int):
                positions.add(item)
            else:
                raise TypeError(f'Unsupported item type of excludes "{type(item)}"')

        for cell in self._cells:
            if cell.index_of_area(self._area_type) not in positions:
                yield cell

    def __repr__(self):
        if self._cells:
            return f'{self._area_type.name} {self._cells[0]}-{self._cells[-1]}'
        else:
            return f'{self._area_type.name}-{self._index + 1}'


class Board:
    def __init__(self, block_width: int = 3, block_height: int = 3):
        self._block_width = block_width
        self._block_height = block_height
        self._size = block_width * block_height
        self._mapping: str = f'123456789{string.ascii_uppercase}'

        self._cells = [Cell(r, c, self) for r, c in itertools.product(range(self._size), repeat=2)]
        # self._areas = [Area(t, i, self) for t, i in itertools.product(AreaType, range(self._size))]
        self._areas: typing.Dict[AreaType, typing.List[Area]] = {}
        for t in AreaType:
            self._areas[t] = [Area(t, i, self) for i in range(self._size)]
        self._connect_area_and_cell()

    @property
    def block_width(self) -> int:
        return self._block_width

    @property
    def block_height(self) -> int:
        return self._block_height

    @property
    def blocks_per_row(self) -> int:
        return self._block_height

    @property
    def blocks_per_col(self) -> int:
        return self._block_width

    @property
    def size(self) -> int:
        return self._size

    def mark(self, value: int) -> str:
        return self._mapping[value]

    def iter_cells(self) -> typing.Iterator[Cell]:
        return iter(self._cells)

    def get_area(self, area_type: AreaType, index: int) -> Area:
        return self._areas[area_type][index]

    def iter_areas(self, area_type: AreaType = None) -> typing.Iterator[Area]:
        if area_type is None:
            return itertools.chain(*self._areas.values())
        else:
            return iter(self._areas[area_type])

    def get_common_area(self, cells: typing.Iterable[Cell], area_type: AreaType) -> Area:
        cell_iter = iter(cells)
        cell = next(cell_iter, None)
        if cell is None:
            return None

        area = cell.get_area(area_type)
        for cell in cell_iter:
            if cell.get_area(area_type) != area:
                return None

        return area

    def iter_common_areas(self, cells: typing.Iterable[Cell]) -> typing.Iterator[Area]:
        for area_type in AreaType:
            area = self.get_common_area(cells, area_type)
            if area is not None:
                yield area

    def iter_numbers(self) -> typing.Iterator[int]:
        return range(self._size)

    def _connect_area_and_cell(self):
        cell: Cell
        for cell in self._cells:
            # Each cell belongs to 3 areas, one for each type.
            area_index_mapping = {
                AreaType.ROW: cell.row,
                AreaType.COLUMN: cell.col,
                AreaType.BLOCK: self.blocks_per_row * (cell.row // self._block_height) + (cell.col // self._block_width),
            }
            for area_type in AreaType:
                area_index = area_index_mapping[area_type]
                area = self._areas[area_type][area_index]
                area._cells.append(cell)
                cell._areas[area_type] = area


class ParadoxError(Exception):
    pass


class DeduceFinished(Exception):
    pass


class StopGuessing(Exception):
    pass


class BoardData:
    def __init__(self, board: Board):
        # Every cell's confirmed value.
        self._cell_values: typing.List[int] = [None for _ in board.iter_cells()]
        self._confirmed_count = 0

        # Every cell's candidate set.
        self._cell_candidates = [NumberSet(board.size) for _ in board.iter_cells()]

        # Every (area, cell)'s naked confirm level.

        # Every (area, number)'s hidden confirm level.

    def solved(self) -> bool:
        return self._confirmed_count == len(self._cell_values)

    def get_value(self, cell: Cell) -> int:
        return self._cell_values[cell.index]

    def _set_value(self, cell: Cell, value: int):
        self._cell_values[cell.index] = value

    def get_candidates(self, cell: Cell) -> NumberSet:
        return self._cell_candidates[cell.index]

    def is_cell_confirmed(self, cell: Cell) -> bool:
        return self.get_value(cell) is not None

    def get_positions(self, area: Area, number: int) -> NumberSet:
        positions = NumberSet(0)
        for cell in area.iter_cells():
            if number in self.get_candidates(cell):
                positions.add(cell.index_of_area(area))

        return positions

    def acknowledge_cell(self, cell: Cell, value: int):
        """Remove cell's candidates except the given one.
        Confirmed cell cannot be acknowledged to different value.
        Will NOT confirm the cell.
        """
        if value is None:
            raise ValueError('cannot acknowledge None to a cell')

        if self.is_cell_confirmed(cell) and self.get_value(cell) != value:
            raise ValueError('cannot acknowledge different value to a confirmed cell')

        self.get_candidates(cell).retain(value)

    def confirm_cell(self, cell: Cell):
        """Confirm cell's single candidate.
        Will FAIL if the cell doesn't have candidate, or has more than two candidates.
        Will NOT update other cells' candidates.
        """
        if self.is_cell_confirmed(cell):
            return

        candidates = self.get_candidates(cell)
        if len(candidates) != 1:
            raise ValueError('cannot confirm a cell with 0 or 2+ candidates')

        value = candidates.peek()
        self._set_value(cell, value)
        self._confirmed_count += 1

    def retain_candidates(self, candidates: NumberSet, cells: typing.Iterable[Cell]) -> bool:
        """Returns True if candidates changed."""
        modified = False
        cell: Cell
        for cell in cells:
            modified = self.get_candidates(cell).retain(candidates) or modified

        return modified

    def remove_candidates(self, candidates: NumberSet, cells: typing.Iterable[Cell]) -> bool:
        """Returns True if candidates changed."""
        modified = False
        cell: Cell
        for cell in cells:
            modified = self.get_candidates(cell).remove(candidates) or modified

        return modified

    def print_simple(self, board: Board):
        for row in board.iter_areas(AreaType.ROW):
            for cell in row.iter_cells():
                is_major_col = (cell.index_of_area(row) + 1) % board.block_width == 0
                if self.is_cell_confirmed(cell):
                    cell_text = board.mark(cell.value)
                else:
                    cell_text = ''.join(map(board.mark, self.get_candidates(cell)))
                    cell_text = f'[{cell_text}]'

                if cell.index_of_area(row) == board.size - 1:
                    fence = ''
                elif is_major_col:
                    fence = '  '
                else:
                    fence = ' '

                print(f'{cell_text}{fence}', end='')

            print()
            is_major_row = (row.index + 1) % board.block_height == 0
            if is_major_row and row.index < board.size - 1:
                print()

    def __print_board_line(self, board: Board, major=True, cell_width=1):
        gap = '-' if major else ' '
        fence = '+'
        cell_line = gap.join('-' for _ in range(cell_width))
        board_line = f'{gap}{fence}{gap}'.join(cell_line for _ in range(board.size))
        print(f'{fence}{gap}{board_line}{gap}{fence}')

    def print_confirmed(self, board: Board):
        self.__print_board_line(board, major=True)
        for row in board.iter_areas(AreaType.ROW):
            print('|', end='')
            for cell in row.iter_cells():
                cell_text = board.mark(self.get_value(cell)) if self.is_cell_confirmed(cell) else '?'
                is_major_col = (cell.index_of_area(row) + 1) % board.block_width == 0
                fence = '|' if is_major_col else ':'
                print(f' {cell_text} {fence}', end='')

            print()
            is_major_row = (row.index + 1) % board.block_height == 0
            self.__print_board_line(board, major=is_major_row)

    def print_with_candidates(self, board: Board):
        self.__print_board_line(board, major=True, cell_width=board.block_width)
        for row in board.iter_areas(AreaType.ROW):
            for sub_row in range(board.block_height):
                print('|', end='')
                for cell in row.iter_cells():
                    for sub_col in range(board.block_width):
                        value = sub_row * board.block_width + sub_col
                        if value in self.get_candidates(cell):
                            sub_cell_text = board.mark(value)
                        else:
                            sub_cell_text = '*' if self.is_cell_confirmed(cell) else ' '
                        print(f' {sub_cell_text}', end='')

                    is_major_col = (cell.index_of_area(row) + 1) % board.block_width == 0
                    print(' |' if is_major_col else ' :', end='')
                print()

            is_major_row = (row.index + 1) % board.block_height == 0
            self.__print_board_line(board, major=is_major_row, cell_width=board.block_width)


class SolvingStatus:
    def __init__(self, board_size: int):
        self.guess_depth = 0
        self.solutions: typing.List[BoardData] = []
        self.interrupted = False

        self.useless_naked_deduce = [0] * board_size
        self.useless_hidden_deduce = [0] * board_size
        self.useless_linked_deduce = [0] * board_size

    def print(self, *args, **kwargs):
        if self.guess_depth == 0:
            print(*args, **kwargs)
        else:
            print('', '  ' * (self.guess_depth - 1), *args, **kwargs)


class SudokuSolver:
    def __init__(self, board: Board):
        self._board = board

        self.naked_deduce_enabled = True
        self.max_naked_deduce_level = board.size - 1

        self.hidden_deduce_enabled = True
        self.max_hidden_deduce_level = board.size - 1

        self.linked_deduce_enabled = True
        self.max_linked_deduce_level = board.size - 1

        self.lower_level_deduce_first = False

        self.guess_enabled = False
        self.max_solutions_count = 1

    def solve(self, puzzle: BoardData) -> SolvingStatus:
        status = SolvingStatus(self._board.size)
        self._deduce(puzzle, status)
        if not puzzle.solved() and self.guess_enabled:
            puzzle.print_with_candidates(self._board)
            self._guess(puzzle, status)

        return status

    def _deduce(self, puzzle: BoardData, status: SolvingStatus):
        finished = False
        try:
            while not (puzzle.solved() or finished):
                finished = not self._deduce_one_round(puzzle, status)
        except DeduceFinished:
            pass

    def _deduce_one_round(self, puzzle: BoardData, status: SolvingStatus) -> bool:
        improved = False
        improved = self._primary_check(puzzle, status) or improved
        if improved and self.lower_level_deduce_first:
            return improved

        for level in range(1, self._board.size):
            if self.naked_deduce_enabled and 2 <= level <= self.max_naked_deduce_level:
                improved = self._naked_deduce(level, puzzle, status) or improved

            if self.hidden_deduce_enabled and 1 <= level <= self.max_hidden_deduce_level:
                improved = self._hidden_deduce(level, puzzle, status) or improved

            if self.linked_deduce_enabled and 2 <= level <= self.max_linked_deduce_level:
                improved = self._linked_deduce(level, True, puzzle, status) or improved
                improved = self._linked_deduce(level, False, puzzle, status) or improved

            if improved and self.lower_level_deduce_first:
                return improved

        return improved

    def _guess(self, puzzle: BoardData, status: SolvingStatus):
        cell = self._choose_guessing_cell(puzzle)
        if cell is None:
            return

        for value in puzzle.get_candidates(cell):
            temp_puzzle = copy.deepcopy(puzzle)
            temp_puzzle.acknowledge_cell(cell, value)
            status.print(f'[Guess] assume cell {cell} is "{self._board.mark(value)}"')
            status.guess_level += 1
            try:
                self._deduce(temp_puzzle, status)
            except ParadoxError as err:
                status.print('[Guess Failed]', err)
            else:
                if temp_puzzle.solved():
                    status.solutions.append(temp_puzzle)
                    status.print('[Solution] find a solution')
                    temp_puzzle.print_simple()
                    if len(status.solutions) >= self.max_solutions_count:
                        raise StopGuessing
                else:
                    self._guess(temp_puzzle, status)
            finally:
                status.guess_depth -= 1

    def _choose_guessing_cell(self, puzzle: BoardData) -> Cell:
        cell_for_guessing = None
        min_candidates_count = self._board.size + 1
        for cell in self._board.iter_cells():
            if puzzle.is_cell_confirmed(cell):
                continue

            candidates_count = len(puzzle.get_candidates(cell))
            if candidates_count == 2:
                return cell

            if candidates_count < min_candidates_count:
                cell_for_guessing = cell
                min_candidates_count = candidates_count

        return cell_for_guessing

    def _primary_check(self, puzzle: BoardData, status: SolvingStatus) -> bool:
        improved = False
        for cell in self._board.iter_cells():
            if puzzle.is_cell_confirmed(cell):
                continue

            candidates = puzzle.get_candidates(cell)
            if len(candidates) == 0:
                raise ParadoxError(f'cell {cell} has no candidate')
            elif len(candidates) > 1:
                continue

            # len(candidates) = 1
            puzzle.confirm_cell(cell)
            for cell_area in cell.iter_areas():
                result = puzzle.remove_candidates(candidates, cell_area.iter_cells(excludes=[cell]))
                improved = result or improved

            status.print(f'[Primary Check] cell {cell} is confirmed to be "{self._board.mark(candidates.peek())}"')
            if puzzle.solved():
                raise DeduceFinished

        return improved

    def _naked_deduce(self, level: int, puzzle: BoardData, status: SolvingStatus):
        improved = False
        for area in self._board.iter_areas():
            # filter area cells
            all_cells = []
            for cell in area.iter_cells():
                if puzzle.is_cell_confirmed(cell):
                    continue
                if len(puzzle.get_candidates(cell)) > level:
                    continue

                # TODO: Check confirm level.

                all_cells.append(cell)

            # for each L-combinations
            for cells in itertools.combinations(all_cells, level):
                # check candidates union
                candidates = NumberSet(0)
                for cell in cells:
                    candidates.add(puzzle.get_candidates(cell))

                if len(candidates) < level:
                    raise ParadoxError(f'TODO: Naked level {level} impossible.')
                elif len(candidates) > level:
                    continue

                # get containing areas.
                # remove candidates from other cells.
                result = False
                for cell_area in self._board.iter_common_areas(cells):
                    result = puzzle.remove_candidates(candidates, cell_area.iter_cells(excludes=cells)) or result

                improved = result or improved
                if result:
                    status.print(f'[Naked Deduce] area {area} cells {cells} TODO')
                    # TODO: update area-cell confirm level.
                else:
                    status.useless_naked_deduce[level] += 1
                #     status.print(f'[Naked Deduce] redundant area {area} cells {cells}')

        return improved

    def _hidden_deduce(self, level: int, puzzle: BoardData, status: SolvingStatus):
        improved = False
        for area in self._board.iter_areas():
            # filter area numbers
            all_numbers = []
            for number in self._board.iter_numbers():
                if len(puzzle.get_positions(area, number)) > level:
                    # TODO: 应该是可以部分参与。
                    continue

                all_numbers.append(number)

            # for each L-combinations
            for numbers in itertools.combinations(all_numbers, level):
                # check positions union
                positions = NumberSet(0)
                for number in numbers:
                    positions.add(puzzle.get_positions(area, number))

                if len(positions) < level:
                    raise ParadoxError(f'TODO: Hidden level {level} impossible.')
                # elif len(positions) > level:
                #     continue

                result = False
                cells = []
                for index in positions:
                    cells.append(area.get_cell(index))

                for cell_area in self._board.iter_common_areas(cells):
                    if cell_area == area:
                        if len(positions) == level:
                            result = puzzle.retain_candidates(numbers, cells) or result
                    else:
                        result = puzzle.remove_candidates(numbers, cell_area.iter_cells(excludes=cells)) or result

                improved = result or improved
                if result:
                    status.print(f'[Hidden Deduce] area {area} numbers {numbers} TODO')
                else:
                    status.useless_hidden_deduce[level] += 1
                #     status.print(f'[Hidden Deduce] redundant area {area} numbers {numbers}')

        return improved

    def _linked_deduce(self, level: int, row_first: bool, puzzle: BoardData, status: SolvingStatus):
        area_type = AreaType.ROW if row_first else AreaType.COLUMN
        improved = False
        for number in self._board.iter_numbers():
            # filter number rows/cols
            all_areas = []
            for area in self._board.iter_areas(area_type):
                if len(puzzle.get_positions(area, number)) > level:
                    continue

                all_areas.append(area)

            # for each L-combinations
            for areas in itertools.combinations(all_areas, level):
                positions = NumberSet(0)
                for area in areas:
                    positions.add(puzzle.get_positions(area, number))

                if len(positions) < level:
                    raise ParadoxError(f'TODO: Linked level {level} impossible.')
                elif len(positions) > level:
                    continue

                result = False
                # TODO: 取这些positions对应的cols/rows
                # for each of them, remove candidates(number, col/row - row/col交点)
                for position in positions:
                    orthogonal_area = self._board.get_area(area_type.orthogonal_type(), position)
                    result = puzzle.remove_candidates(number, orthogonal_area.iter_cells(excludes=areas)) or result

                if result:
                    status.print(f'[Linked Deduce] number {number} areas {areas} TODO')
                else:
                    status.useless_linked_deduce[level] += 1

        return improved


def test(args):
    board = Board(block_width=3, block_height=3)
    puzzle = BoardData(board)

    def iter_puzzle_lines(file):
        for line in file:
            line = line.strip(' \r\n')
            if line != '':
                yield line

    def iter_values(line):
        for mark in line:
            if mark == ' ':
                continue

            value = board._mapping.find(mark)
            yield value if value >= 0 else None

    with open(args.puzzle_file) as f:
        row: Area
        line: str
        for row, line in zip(board.iter_areas(AreaType.ROW), iter_puzzle_lines(f)):
            cell: Cell
            value: int
            for cell, value in zip(row.iter_cells(), iter_values(line)):
                if value is not None:
                    puzzle.acknowledge_cell(cell, value)

    puzzle.print_simple(board)
    puzzle.print_confirmed(board)
    puzzle.print_with_candidates(board)

    solver = SudokuSolver(board)
    status = solver.solve(puzzle)
    puzzle.print_confirmed(board)

    if solver.naked_deduce_enabled:
        print(f'useless naked deduce: {status.useless_naked_deduce}')
    if solver.hidden_deduce_enabled:
        print(f'useless hidden deduce: {status.useless_hidden_deduce}')
    if solver.linked_deduce_enabled:
        print(f'useless linked deduce: {status.useless_linked_deduce}')


def main():
    parser = argparse.ArgumentParser(description='Deductive Sudoku Solver')

    puzzle_group = parser.add_argument_group('puzzle arguments')
    puzzle_group.add_argument('--block-width', type=int, default=3,
                              help='how many columns a block contains (default: 3)')
    puzzle_group.add_argument('--block-height', type=int, default=3,
                              help='how many rows a block contains (default: 3)')
    puzzle_group.add_argument('--mapping',
                              help='')
    puzzle_group.add_argument('-f', '--puzzle-file',
                              help='puzzle file')

    rule_group = parser.add_argument_group('deduce rule arguments')
    for rule in ('naked', 'hidden', 'linked'):
        rule_group.add_argument(f'--max-{rule}-deduce-level', type=int)

    rule_group.add_argument('--disable-lower-level-first', action='store_true')
    rule_group.add_argument('--disable-deduce', action='store_true')
    rule_group.add_argument('--disable-guess', action='store_true')

    output_group = parser.add_argument_group('output arguments')
    output_group.add_argument('--foo')

    # args = parser.parse_args()
    args = parser.parse_args(['-f', 'old/005que.txt'])
    print(args)
    test(args)


if __name__ == '__main__':
    main()
