#!/usr/bin/env python3
import argparse
import copy
import distutils.util
import enum
import itertools
import string
import sys
import typing


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

    def __repr__(self):
        return ', '.join(str(n) for n in self)


class AreaType(enum.Enum):
    ROW = 0
    COLUMN = 1
    BLOCK = 2

    def __init__(self, index):
        self._index = index

    @property
    def index(self):
        return self._index

    def orthogonal_type(self) -> 'AreaType':
        if self is self.ROW:
            return self.COLUMN
        elif self is self.COLUMN:
            return self.ROW
        else:
            raise ValueError(f'{self} has no orthogonal type')

    def __str__(self):
        return self.name.lower()


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
        self._board = board
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
        return f'{self._area_type.name.lower()} {self._index + 1}'

    def __str__(self):
        if self._area_type == AreaType.BLOCK:
            r, c = divmod(self._index, self._board.blocks_per_row)
            return f'({r + 1},{c + 1})'
        else:
            return f'{self._index + 1}'


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

    @property
    def mapping(self) -> str:
        return self._mapping

    @mapping.setter
    def mapping(self, value):
        self._mapping = value

    def mark(self, number: int) -> str:
        return self._mapping[number]

    def lookup(self, mark: str) -> int:
        number = self._mapping.find(mark)
        return number if number >= 0 else None

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
        self._board_size = board.size
        self._acknowledged_cells = NumberSet(0)

        # Every cell's confirmed value.
        self._cell_values = [None] * board.size * board.size
        self._confirmed_count = 0

        # Every cell's candidate set.
        self._cell_candidates = [NumberSet(board.size) for _ in board.iter_cells()]

        # Every (area, cell)'s naked confirm level.
        self._naked_confirm_levels = [board.size] * len(AreaType) * board.size * board.size

        # Every (area, number)'s hidden confirm level.
        self._hidden_confirm_levels = [board.size] * len(AreaType) * board.size * board.size

        # Every (row/col, number)'s linked confirm level.
        self._linked_confirm_levels = [board.size] * len(AreaType) * board.size * board.size

    @property
    def board_size(self):
        return self._board_size

    def solved(self) -> bool:
        return self._confirmed_count == len(self._cell_values)

    def is_cell_acknowledged(self, cell: Cell) -> bool:
        return cell.index in self._acknowledged_cells

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
        self._acknowledged_cells.add(cell.index)

    def get_value(self, cell: Cell) -> int:
        return self._cell_values[cell.index]

    def _set_value(self, cell: Cell, value: int):
        self._cell_values[cell.index] = value

    def is_cell_confirmed(self, cell: Cell) -> bool:
        return self.get_value(cell) is not None

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

    def get_candidates(self, cell: Cell) -> NumberSet:
        return self._cell_candidates[cell.index]

    def get_positions(self, area: Area, number: int) -> NumberSet:
        positions = NumberSet(0)
        for cell in area.iter_cells():
            if number in self.get_candidates(cell):
                positions.add(cell.index_of_area(area))

        return positions

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

    def get_naked_confirm_level(self, area: Area, cell: Cell) -> int:
        index = cell.index * len(AreaType) + area.area_type.index
        return self._naked_confirm_levels[index]

    def confirm_naked_level(self, area: Area, cell: Cell, level: int):
        index = cell.index * len(AreaType) + area.area_type.index
        if level < self._naked_confirm_levels[index]:
            self._naked_confirm_levels[index] = level

    def get_hidden_confirm_level(self, area: Area, number: int) -> int:
        assert 0 <= number < self._board_size, f'number {number} out of range'
        index = (area.area_type.index * self._board_size + area.index) * self._board_size + number
        return self._hidden_confirm_levels[index]

    def confirm_hidden_level(self, area: Area, number: int, level: int):
        assert 0 <= number < self._board_size, f'number {number} out of range'
        index = (area.area_type.index * self._board_size + area.index) * self._board_size + number
        if level < self._hidden_confirm_levels[index]:
            self._hidden_confirm_levels[index] = level

    def get_linked_confirm_level(self, area: Area, number: int) -> int:
        index = (area.area_type.index * self._board_size + area.index) * self._board_size + number
        return self._linked_confirm_levels[index]

    def confirm_linked_level(self, area: Area, number: int, level: int):
        index = (area.area_type.index * self._board_size + area.index) * self._board_size + number
        if level < self._linked_confirm_levels[index]:
            self._linked_confirm_levels[index] = level

    def print(self, board: Board, border: bool = False):
        if border:
            if self.solved():
                self.print_confirmed(board)
            else:
                self.print_with_candidates(board)
        else:
            self.print_simple(board)

    def print_simple(self, board: Board):
        for row in board.iter_areas(AreaType.ROW):
            for cell in row.iter_cells():
                is_major_col = (cell.index_of_area(row) + 1) % board.block_width == 0
                if self.is_cell_confirmed(cell):
                    cell_text = board.mark(self.get_value(cell))
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


class GuessDecision(typing.NamedTuple):
    cell: int
    value: int


class GuessedSolution(typing.NamedTuple):
    guesses: typing.List[GuessDecision]
    data: BoardData


class DeduceMsgLevel(enum.IntEnum):
    NONE = enum.auto()
    GUESS = enum.auto()
    DEDUCE = enum.auto()
    BOARD = enum.auto()

    def __str__(self):
        return self.name.lower()

    @classmethod
    def parse(cls, name):
        return cls[name.upper()]


class SolvingStatus:
    def __init__(self, puzzle: BoardData):
        self.puzzle = puzzle
        self.guesses: typing.List[GuessDecision] = []
        self.solutions: typing.List[GuessedSolution] = []
        self.interrupted = False

        self.useless_naked_deduce = [0] * puzzle.board_size
        self.useless_hidden_deduce = [0] * puzzle.board_size
        self.useless_linked_deduce = [0] * puzzle.board_size

    @property
    def guessing(self) -> bool:
        return bool(self.guesses)

    @property
    def guess_depth(self) -> int:
        return len(self.guesses)


class SudokuSolver:
    def __init__(self, board: Board):
        self._board = board

        self.naked_deduce_enabled = True
        self.max_naked_deduce_level = board.size - 1

        self.hidden_deduce_enabled = True
        self.max_hidden_deduce_level = board.size - 1

        self.linked_deduce_enabled = True
        self.max_linked_deduce_level = board.size - 1

        self.lower_level_deduce_first = True

        self.guess_enabled = True
        self.max_solutions_count = 10

        self.deduce_msg_level = DeduceMsgLevel.DEDUCE
        self.guess_msg_level = DeduceMsgLevel.DEDUCE
        self.board_border_enabled = True

    @property
    def board(self):
        return self._board

    def solve(self, puzzle: BoardData) -> SolvingStatus:
        status = SolvingStatus(puzzle)
        self._deduce(status)
        if not puzzle.solved() and self.guess_enabled:
            print('Deduce finished but not solved the puzzle, try guessing.')
            # puzzle.print(self._board, self.board_border_enabled)
            try:
                self._guess(status)
            except StopGuessing:
                pass

        return status

    def _deduce(self, status: SolvingStatus):
        finished = False
        try:
            while not (status.puzzle.solved() or finished):
                finished = not self._deduce_one_round(status)
        except DeduceFinished:
            pass

    def _deduce_one_round(self, status: SolvingStatus) -> bool:
        improved = False
        improved = self._primary_check(status) or improved
        if improved and self.lower_level_deduce_first:
            return improved

        for level in range(1, self._board.size):
            if self.naked_deduce_enabled and 2 <= level <= self.max_naked_deduce_level:
                improved = self._naked_deduce(level, status) or improved

            if self.hidden_deduce_enabled and 1 <= level <= self.max_hidden_deduce_level:
                improved = self._hidden_deduce(level, status) or improved

            if self.linked_deduce_enabled and 2 <= level <= self.max_linked_deduce_level:
                improved = self._linked_deduce(level, AreaType.ROW, status) or improved
                improved = self._linked_deduce(level, AreaType.COLUMN, status) or improved

            if improved and self.lower_level_deduce_first:
                return improved

        return improved

    def _guess(self, status: SolvingStatus):
        orig_puzzle = status.puzzle
        cell = self._choose_guessing_cell(orig_puzzle)
        if cell is None:
            return

        for value in orig_puzzle.get_candidates(cell):
            status.puzzle = copy.deepcopy(orig_puzzle)
            status.puzzle.acknowledge_cell(cell, value)
            self._show_guess_msg(status, cell, value)
            status.guesses.append(GuessDecision(cell.index, value))
            try:
                self._deduce(status)
            except ParadoxError:
                pass
            else:
                if status.puzzle.solved():
                    self._show_guess_success_msg(status)
                    solution = GuessedSolution(copy.deepcopy(status.guesses), status.puzzle)
                    status.solutions.append(solution)
                    if len(status.solutions) >= self.max_solutions_count:
                        status.interrupted = True
                        raise StopGuessing
                else:
                    self._guess(status)
            finally:
                status.guesses.pop()

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

    def _primary_check(self, status: SolvingStatus) -> bool:
        puzzle = status.puzzle
        improved = False
        for cell in self._board.iter_cells():
            if puzzle.is_cell_confirmed(cell):
                continue

            candidates = puzzle.get_candidates(cell)
            if len(candidates) == 0:
                self._show_primary_check_msg(status, cell, None)
                raise ParadoxError
            elif len(candidates) > 1:
                continue

            # len(candidates) = 1
            result = False
            for cell_area in cell.iter_areas():
                result = puzzle.remove_candidates(candidates, cell_area.iter_cells(excludes=[cell])) or result
                puzzle.confirm_naked_level(cell_area, cell, 1)
                puzzle.confirm_hidden_level(cell_area, candidates.peek(), 1)

            improved = result or improved
            if result:
                self._show_primary_check_msg(status, cell, candidates.peek(),
                                             acknowledged=puzzle.is_cell_acknowledged(cell))

            puzzle.confirm_cell(cell)
            if puzzle.solved():
                raise DeduceFinished

        return improved

    def _naked_deduce(self, level: int, status: SolvingStatus):
        puzzle = status.puzzle
        def is_useful(cell: Cell) -> bool:
            # if puzzle.is_cell_confirmed(cell):
            #     return False
            if puzzle.get_naked_confirm_level(area, cell) <= level:
                return False
            if len(puzzle.get_candidates(cell)) > level:
                return False
            return True

        improved = False
        for area in self._board.iter_areas():
            # for each L-combinations
            all_cells = [cell for cell in area.iter_cells() if is_useful(cell)]
            for cells in itertools.combinations(all_cells, level):
                if not all(map(is_useful, cells)):
                    continue

                # check candidates union
                candidates = NumberSet(0)
                for cell in cells:
                    candidates.add(puzzle.get_candidates(cell))

                if len(candidates) < level:
                    self._show_naked_deduce_msg(status, area, cells, candidates)
                    raise ParadoxError
                elif len(candidates) > level:
                    continue

                # get containing areas.
                # remove candidates from other cells.
                result = False
                for cell_area in self._board.iter_common_areas(cells):
                    result = puzzle.remove_candidates(candidates, cell_area.iter_cells(excludes=cells)) or result
                    for cell in cells:
                        puzzle.confirm_naked_level(cell_area, cell, level)
                    for number in candidates:
                        puzzle.confirm_hidden_level(cell_area, number, level)

                improved = result or improved
                if result:
                    self._show_naked_deduce_msg(status, area, cells, candidates)
                else:
                    status.useless_naked_deduce[level] += 1

                if len(cells) == 1:
                    puzzle.confirm_cell(cells[0])
                    if puzzle.solved():
                        raise DeduceFinished

        return improved

    def _hidden_deduce(self, level: int, status: SolvingStatus):
        puzzle = status.puzzle
        level_ex = max(level, self._board.block_width, self._board.block_height)
        def is_useful(number: int) -> bool:
            if puzzle.get_hidden_confirm_level(area, number) <= level:
                return False
            if len(puzzle.get_positions(area, number)) > level_ex:
                return False
            return True

        improved = False
        for area in self._board.iter_areas():
            # for each L-combinations
            all_numbers = [number for number in self._board.iter_numbers() if is_useful(number)]
            for numbers in itertools.combinations(all_numbers, level):
                if not all(map(is_useful, numbers)):
                    continue

                # check positions union
                positions = NumberSet(0)
                for number in numbers:
                    positions.add(puzzle.get_positions(area, number))

                cells = [area.get_cell(index) for index in positions]
                if len(positions) < level:
                    self._show_hidden_deduce_msg(status, area, numbers, cells)
                    raise ParadoxError
                elif len(positions) > level_ex:
                    continue
                elif area.area_type == AreaType.ROW and len(positions) > max(level, self._board.block_width):
                    continue
                elif area.area_type == AreaType.COLUMN and len(positions) > max(level, self._board.block_height):
                    continue

                result = False
                for cell_area in self._board.iter_common_areas(cells):
                    if cell_area == area:
                        if len(cells) == level:
                            result = puzzle.retain_candidates(numbers, cells) or result
                    else:
                        result = puzzle.remove_candidates(numbers, cell_area.iter_cells(excludes=cells)) or result

                    if len(cells) == level:
                        for number in numbers:
                            puzzle.confirm_hidden_level(cell_area, number, level)
                        for cell in cells:
                            puzzle.confirm_naked_level(cell_area, cell, level)
                    # else:
                    #     for number in numbers:
                    #         puzzle.confirm_hidden_level(cell_area, number, len(cells))

                improved = result or improved
                if result:
                    self._show_hidden_deduce_msg(status, area, numbers, cells)
                elif len(cells) == level:
                    status.useless_hidden_deduce[level] += 1

                if len(cells) == 1:
                    puzzle.confirm_cell(cells[0])
                    if puzzle.solved():
                        raise DeduceFinished

        return improved

    def _linked_deduce(self, level: int, area_type: AreaType, status: SolvingStatus):
        puzzle = status.puzzle
        def is_useful(area: Area) -> bool:
            if puzzle.get_linked_confirm_level(area, number) <= level:
                return False
            if len(puzzle.get_positions(area, number)) > level:
                return False
            return True

        orth_area_type = area_type.orthogonal_type()
        improved = False
        for number in self._board.iter_numbers():
            # for each L-combinations
            all_areas = [area for area in self._board.iter_areas(area_type) if is_useful(area)]
            for areas in itertools.combinations(all_areas, level):
                if not all(map(is_useful, areas)):
                    continue

                positions = NumberSet(0)
                for area in areas:
                    positions.add(puzzle.get_positions(area, number))

                if len(positions) < level:
                    self._show_linked_deduce_msg(status, number, area_type, areas, positions)
                    raise ParadoxError
                elif len(positions) > level:
                    continue

                result = False
                # for each of them, remove candidates(number, col/row - row/col交点)
                for position in positions:
                    orthogonal_area = self._board.get_area(orth_area_type, position)
                    result = puzzle.remove_candidates(number, orthogonal_area.iter_cells(excludes=areas)) or result
                    puzzle.confirm_linked_level(orthogonal_area, number, level)

                for area in areas:
                    puzzle.confirm_linked_level(area, number, level)

                if result:
                    self._show_linked_deduce_msg(status, number, area_type, areas, positions)
                else:
                    status.useless_linked_deduce[level] += 1

        return improved

    def _get_msg_indent(self, status: SolvingStatus) -> str:
        return '  ' * status.guess_depth

    def _get_msg_level(self, status: SolvingStatus) -> DeduceMsgLevel:
        return self.guess_msg_level if status.guessing else self.deduce_msg_level

    def _show_primary_check_msg(self, status: SolvingStatus, cell: Cell, value: int, acknowledged: bool = False):
        msg_level = self._get_msg_level(status)
        if msg_level < DeduceMsgLevel.DEDUCE:
            return

        if acknowledged and msg_level < DeduceMsgLevel.BOARD:
            return

        indent = self._get_msg_indent(status)
        if value is None:
            print(f'{indent}[Paradox @ Primary Check] cell {cell} has no candidate')
        else:
            value_text = self._board.mark(value)
            print(f'{indent}[Primary Check] cell {cell} has single candidate "{value_text}"')

        if msg_level < DeduceMsgLevel.BOARD:
            return

        status.puzzle.print(self._board, self.board_border_enabled)

    def _show_naked_deduce_msg(self, status: SolvingStatus, area: Area,
                               cells: typing.Iterable[Cell], candidates: typing.Iterable[int]):
        msg_level = self._get_msg_level(status)
        if msg_level < DeduceMsgLevel.DEDUCE:
            return

        indent = self._get_msg_indent(status)
        level = len(cells)
        cells_text = ', '.join(f'{cell}' for cell in cells)
        candidates_text = ', '.join(f'"{self._board.mark(number)}"' for number in candidates)
        if len(candidates) < level:
            print(f'{indent}[Paradox @ Naked Deduce L{level}] in {area.area_type} {area},'
                  f' cells [{cells_text}] have only {len(candidates)} candidates [{candidates_text}]')
        else:
            print(f'{indent}[Naked Deduce L{level}] in {area.area_type} {area},'
                  f' cells [{cells_text}] have exactly {level} candidates [{candidates_text}]')

        if msg_level < DeduceMsgLevel.BOARD:
            return

        status.puzzle.print(self._board, self.board_border_enabled)

    def _show_hidden_deduce_msg(self, status: SolvingStatus, area: Area,
                                numbers: typing.Iterable[int], cells: typing.Iterable[Cell]):
        msg_level = self._get_msg_level(status)
        if msg_level < DeduceMsgLevel.DEDUCE:
            return

        indent = self._get_msg_indent(status)
        level = len(numbers)
        exactly = 'exactly ' if len(cells) == level else ''
        numbers_text = ', '.join(f'"{self._board.mark(number)}"' for number in numbers)
        cells_text = ', '.join(f'{cell}' for cell in cells)
        if len(cells) < level:
            print(f'{indent}[Paradox @ Hidden Deduce L{level}] in {area.area_type} {area},'
                  f' numbers [{numbers_text}] appear in only {len(cells)} cells [{cells_text}]')
        else:
            print(f'{indent}[Hidden Deduce L{level}] in {area.area_type} {area},'
                  f' numbers [{numbers_text}] appear in {exactly}{len(cells)} cells [{cells_text}]')

        if msg_level < DeduceMsgLevel.BOARD:
            return

        status.puzzle.print(self._board, self.board_border_enabled)

    def _show_linked_deduce_msg(self, status: SolvingStatus, number: int, area_type: AreaType,
                                areas: typing.Iterable[Area], positions: typing.Iterable[int]):
        msg_level = self._get_msg_level(status)
        if msg_level < DeduceMsgLevel.DEDUCE:
            return

        indent = self._get_msg_indent(status)
        level = len(areas)
        number_text = self._board.mark(number)
        orth_area_type = area_type.orthogonal_type()
        areas_text = ', '.join(f'{area}' for area in areas)
        orth_areas_text = ', '.join(f'{position + 1}' for position in positions)
        if len(positions) < level:
            print(f'{indent}[Paradox @ Linked Deduce L{level}] number "{number_text}" in {area_type}s [{areas_text}],'
                  f' appear in only {len(positions)} {orth_area_type}s [{orth_areas_text}]')
        else:
            print(f'{indent}[Linked Deduce L{level}] number "{number_text}" in {area_type}s [{areas_text}],'
                  f' appear in exactly {level} {orth_area_type}s [{orth_areas_text}]')

        if msg_level < DeduceMsgLevel.BOARD:
            return

        status.puzzle.print(self._board, self.board_border_enabled)

    def _show_guess_msg(self, status: SolvingStatus, cell: Cell, value: int):
        msg_level = self.guess_msg_level
        if msg_level < DeduceMsgLevel.GUESS:
            return

        indent = self._get_msg_indent(status)
        level = status.guess_depth + 1
        value_text = self._board.mark(value)
        print(f'{indent}[Guess L{level}] assume cell {cell} value is "{value_text}"')

    def _show_guess_success_msg(self, status: SolvingStatus):
        msg_level = self.guess_msg_level
        if msg_level < DeduceMsgLevel.GUESS:
            return

        indent = self._get_msg_indent(status)
        print(f'{indent}[Guess Success] find a solution')


def create_arg_parser() -> argparse.ArgumentParser:
    strtobool = lambda s: bool(distutils.util.strtobool(s))
    parser = argparse.ArgumentParser(description='Deductive Sudoku Solver', allow_abbrev=False)
    parser.add_argument('puzzle_file', nargs='?',
                        help='a file contains a sudoku puzzle, see puzzles/*.txt for example.'
                        ' If omitted, read puzzle from stdin.')

    board_group = parser.add_argument_group(
        'board arguments',
        description='The size (edge length) of the board is BLOCK_WIDTH * BLOCK_HEIGHT.')
    board_group.add_argument('--block-width', type=int, default=3,
                             help='how many columns a block contains (default: 3)')
    board_group.add_argument('--block-height', type=int, default=3,
                             help='how many rows a block contains (default: 3)')
    board_group.add_argument('--cell-values', default=f'123456789{string.ascii_uppercase}',
                             help='a string contains all marks for every cell value (default: "1..9A..Z")')

    rule_group = parser.add_argument_group('deduce rule arguments')
    rule_group.add_argument('--deduce', type=strtobool,
                            nargs='?', const=True, default=True, choices=[True, False],
                            help='whether enable deduce (set to `false` to disable all deduce rules,'
                            ' then enable specific rule by corresponding deduce level arguments) (default: true)')
    for rule in ('naked', 'hidden', 'linked'):
        rule_group.add_argument(f'--{rule}-deduce', type=int,
                                help=f'the max level of {rule} rule, use 0 to disable it')
    rule_group.add_argument('--lower-level-first', type=strtobool,
                            nargs='?', const=True, default=True, choices=[True, False],
                            help='whether always prefer lower level deduce if possible,'
                            ' can decrease the number of deduce steps and increase deduce speed'
                            ' (default: true)')
    rule_group.add_argument('--guess', type=strtobool,
                            nargs='?', const=True, default=True, choices=[True, False],
                            help='whether enable guess when then puzzle cannot be solved by deducing (default: true)')
    rule_group.add_argument('--max-solutions', type=int, default=2,
                            help='when solving by guessing, stop guessing when the given number of solutions'
                            ' are found (default: 2)')

    output_group = parser.add_argument_group(
        'output arguments',
        description='Message levels: none - no message will be print; guess - only print guess operation;'
        ' deduce - print deduce message; board - print board data after each deduce step.')
    output_group.add_argument('--deduce-msg', type=DeduceMsgLevel.parse,
                              choices=[DeduceMsgLevel.NONE, DeduceMsgLevel.DEDUCE, DeduceMsgLevel.BOARD],
                              default=DeduceMsgLevel.DEDUCE,
                              help='deduce message level (default: deduce)')
    output_group.add_argument('--guess-msg', type=DeduceMsgLevel.parse,
                              choices=list(DeduceMsgLevel), default=DeduceMsgLevel.GUESS,
                              help='guess message level (default: guess)')
    output_group.add_argument('--better-print', type=strtobool,
                             nargs='?', const=True, default=True, choices=[True, False],
                             help='print puzzle in board format (with cell border) instead of plain format (default: true)')

    return parser


def create_solver(args) -> SudokuSolver:
    board = Board(block_width=args.block_width, block_height=args.block_height)
    board.mapping = args.cell_values

    solver = SudokuSolver(board)
    solver.lower_level_deduce_first = args.lower_level_first
    solver.guess_enabled = args.guess
    solver.max_solutions_count = args.max_solutions
    solver.deduce_msg_level = args.deduce_msg
    solver.guess_msg_level = args.guess_msg
    solver.board_border_enabled = args.better_print

    if not args.deduce:
        solver.naked_deduce_enabled = False
        solver.hidden_deduce_enabled = False
        solver.linked_deduce_enabled = False

    if args.naked_deduce == 0:
        solver.naked_deduce_enabled = False
    elif args.naked_deduce is not None:
        solver.naked_deduce_enabled = True
        solver.max_naked_deduce_level = args.naked_deduce

    if args.hidden_deduce == 0:
        solver.hidden_deduce_enabled = False
    elif args.hidden_deduce is not None:
        solver.hidden_deduce_enabled = True
        solver.max_hidden_deduce_level = args.hidden_deduce

    if args.linked_deduce == 0:
        solver.linked_deduce_enabled = False
    elif args.linked_deduce is not None:
        solver.linked_deduce_enabled = True
        solver.max_linked_deduce_level = args.linked_deduce

    return solver


def load_puzzle(args, board: Board) -> BoardData:
    def iter_puzzle_lines(file):
        for line in file:
            line = line.strip(' \r\n')
            if line != '':
                yield line

    def iter_values(line):
        for mark in line:
            if mark == ' ':
                continue

            yield board.lookup(mark)

    puzzle = BoardData(board)
    with (open(args.puzzle_file) if args.puzzle_file else sys.stdin) as f:
        row: Area
        line: str
        for row, line in zip(board.iter_areas(AreaType.ROW), iter_puzzle_lines(f)):
            cell: Cell
            value: int
            for cell, value in zip(row.iter_cells(), iter_values(line)):
                if value is not None:
                    puzzle.acknowledge_cell(cell, value)

    return puzzle


def main():
    parser = create_arg_parser()
    args = parser.parse_args()
    # print(args)
    board_size = args.block_width * args.block_height
    if len(args.cell_values) < board_size:
        raise ValueError(f'each area of the board contains {board_size} cells,'
                         f' but only {len(args.cell_values)} values provided')

    solver = create_solver(args)
    board = solver.board
    puzzle = load_puzzle(args, board)

    print('The puzzle is:')
    puzzle.print(board, args.better_print)

    status = solver.solve(puzzle)
    if puzzle.solved():
        print('Solved by deduction:')
        puzzle.print(board, args.better_print)
    elif status.solutions:
        print(f'Solved by guessing, find {len(status.solutions)} solutions:')
        for solution in status.solutions:
            solution.data.print(board, args.better_print)
            print()

        if status.interrupted:
            print('There might be more solutions not found.')
    else:
        print('Not solved.')

    # if solver.naked_deduce_enabled:
    #     print(f'useless naked deduce: {status.useless_naked_deduce}')
    # if solver.hidden_deduce_enabled:
    #     print(f'useless hidden deduce: {status.useless_hidden_deduce}')
    # if solver.linked_deduce_enabled:
    #     print(f'useless linked deduce: {status.useless_linked_deduce}')


if __name__ == '__main__':
    main()
