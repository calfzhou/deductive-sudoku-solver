import enum
import itertools
import string
import typing

from .number_set import NumberSet


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
        self.name: str
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
