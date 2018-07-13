import copy
import io
import typing

from .board import Area, AreaType, Board, Cell
from .number_set import NumberSet

class BoardData:
    _SHARED_ATTRS = ('_board',)

    def __init__(self, board: Board):
        self._board = board
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

    @classmethod
    def load(cls, puzzle_file: io.TextIOBase, board: Board) -> 'BoardData':
        def iter_puzzle_lines(file):
            for line in file:
                line = line.strip(' \r\n')
                if line != '':
                    yield line

        def iter_values(line):
            for mark in line:
                if mark != ' ':
                    yield board.lookup(mark)

        puzzle = cls(board)
        for row, line in zip(board.iter_areas(AreaType.ROW), iter_puzzle_lines(puzzle_file)):
            for cell, value in zip(row.iter_cells(), iter_values(line)):
                if value is not None:
                    puzzle.acknowledge_cell(cell, value)

        return puzzle

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in cls._SHARED_ATTRS:
                setattr(result, k, v)
            else:
                setattr(result, k, copy.deepcopy(v, memo))

        return result

    @property
    def board(self) -> Board:
        return self._board

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
        assert 0 <= number < self._board.size, f'number {number} out of range'
        index = (area.area_type.index * self._board.size + area.index) * self._board.size + number
        return self._hidden_confirm_levels[index]

    def confirm_hidden_level(self, area: Area, number: int, level: int):
        assert 0 <= number < self._board.size, f'number {number} out of range'
        index = (area.area_type.index * self._board.size + area.index) * self._board.size + number
        if level < self._hidden_confirm_levels[index]:
            self._hidden_confirm_levels[index] = level

    def get_linked_confirm_level(self, area: Area, number: int) -> int:
        index = (area.area_type.index * self._board.size + area.index) * self._board.size + number
        return self._linked_confirm_levels[index]

    def confirm_linked_level(self, area: Area, number: int, level: int):
        index = (area.area_type.index * self._board.size + area.index) * self._board.size + number
        if level < self._linked_confirm_levels[index]:
            self._linked_confirm_levels[index] = level

    def print(self, border: bool = False):
        if border:
            if self.solved():
                self.print_confirmed()
            else:
                self.print_with_candidates()
        else:
            self.print_simple()

    def print_simple(self):
        for row in self._board.iter_areas(AreaType.ROW):
            for cell in row.iter_cells():
                is_major_col = (cell.index_of_area(row) + 1) % self._board.block_width == 0
                if self.is_cell_confirmed(cell):
                    cell_text = self._board.mark(self.get_value(cell))
                else:
                    cell_text = ''.join(map(self._board.mark, self.get_candidates(cell)))
                    cell_text = f'[{cell_text}]'

                if cell.index_of_area(row) == self._board.size - 1:
                    fence = ''
                elif is_major_col:
                    fence = '  '
                else:
                    fence = ' '

                print(f'{cell_text}{fence}', end='')

            print()
            is_major_row = (row.index + 1) % self._board.block_height == 0
            if is_major_row and row.index < self._board.size - 1:
                print()

    def __print_board_line(self, major=True, cell_width=1):
        gap = '-' if major else ' '
        fence = '+'
        cell_line = gap.join('-' for _ in range(cell_width))
        board_line = f'{gap}{fence}{gap}'.join(cell_line for _ in range(self._board.size))
        print(f'{fence}{gap}{board_line}{gap}{fence}')

    def print_confirmed(self):
        self.__print_board_line(major=True)
        for row in self._board.iter_areas(AreaType.ROW):
            print('|', end='')
            for cell in row.iter_cells():
                cell_text = self._board.mark(self.get_value(cell)) if self.is_cell_confirmed(cell) else '?'
                is_major_col = (cell.index_of_area(row) + 1) % self._board.block_width == 0
                fence = '|' if is_major_col else ':'
                print(f' {cell_text} {fence}', end='')

            print()
            is_major_row = (row.index + 1) % self._board.block_height == 0
            self.__print_board_line(major=is_major_row)

    def print_with_candidates(self):
        self.__print_board_line(major=True, cell_width=self._board.block_width)
        for row in self._board.iter_areas(AreaType.ROW):
            for sub_row in range(self._board.block_height):
                print('|', end='')
                for cell in row.iter_cells():
                    for sub_col in range(self._board.block_width):
                        value = sub_row * self._board.block_width + sub_col
                        if value in self.get_candidates(cell):
                            sub_cell_text = self._board.mark(value)
                        else:
                            sub_cell_text = '*' if self.is_cell_confirmed(cell) else ' '
                        print(f' {sub_cell_text}', end='')

                    is_major_col = (cell.index_of_area(row) + 1) % self._board.block_width == 0
                    print(' |' if is_major_col else ' :', end='')
                print()

            is_major_row = (row.index + 1) % self._board.block_height == 0
            self.__print_board_line(major=is_major_row, cell_width=self._board.block_width)
