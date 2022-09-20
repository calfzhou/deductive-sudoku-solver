import copy
import enum
import itertools
import typing

from .board import Area, AreaType, Board, Cell
from .number_set import NumberSet
from .puzzle import BoardData

class ParadoxError(Exception):
    pass


class DeduceFinished(Exception):
    pass


class StopGuessing(Exception):
    pass


class GuessDecision(typing.NamedTuple):
    cell: int
    value: int


class GuessedSolution(typing.NamedTuple):
    guesses: typing.List[GuessDecision]
    data: BoardData


class DeduceRule(enum.Enum):
    NAKED = enum.auto()
    HIDDEN = enum.auto()
    LINKED = enum.auto()

    def __str__(self):
        self.name: str
        return self.name.lower()


class DeduceMsgLevel(enum.IntEnum):
    NONE = enum.auto()
    GUESS = enum.auto()
    DEDUCE = enum.auto()
    BOARD = enum.auto()

    def __str__(self):
        self.name: str
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

        self.useless_naked_deduce = [0] * puzzle.board.size
        self.useless_hidden_deduce = [0] * puzzle.board.size
        self.useless_linked_deduce = [0] * puzzle.board.size

    @property
    def board(self) -> Board:
        return self.puzzle.board

    @property
    def guessing(self) -> bool:
        return bool(self.guesses)

    @property
    def guess_depth(self) -> int:
        return len(self.guesses)


class SudokuSolver:
    def __init__(self):
        self.max_deduce_levels = {rule: -1 for rule in DeduceRule}
        self.lower_level_deduce_first = True

        self.guess_enabled = True
        self.max_solutions_count = 10

        self.deduce_msg_level = DeduceMsgLevel.DEDUCE
        self.guess_msg_level = DeduceMsgLevel.DEDUCE
        self.board_border_enabled = True

    def solve(self, puzzle: BoardData) -> SolvingStatus:
        status = SolvingStatus(puzzle)
        self._deduce(status)
        if not puzzle.solved() and self.guess_enabled:
            if self.deduce_msg_level > DeduceMsgLevel.NONE:
                print('Deduce finished but not solved the puzzle, try guessing.')

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

    def disable_deduce(self):
        for rule in self.max_deduce_levels:
            self.max_deduce_levels[rule] = 0

    def _get_rule_max_level(self, rule: DeduceRule, puzzle: BoardData) -> int:
        max_level = self.max_deduce_levels[rule]
        if max_level == 0:
            return 0
        elif max_level == -1:
            return puzzle.board.size
        else:
            return max_level

    def _deduce_one_round(self, status: SolvingStatus) -> bool:
        puzzle = status.puzzle
        improved = False
        improved = self._primary_check(status) or improved
        if improved and self.lower_level_deduce_first:
            return improved

        for level in range(1, status.board.size):
            if 2 <= level <= self._get_rule_max_level(DeduceRule.NAKED, puzzle):
                improved = self._naked_deduce(level, status) or improved

            if 1 <= level <= self._get_rule_max_level(DeduceRule.HIDDEN, puzzle):
                improved = self._hidden_deduce(level, status) or improved

            if 2 <= level <= self._get_rule_max_level(DeduceRule.LINKED, puzzle):
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
        min_candidates_count = puzzle.board.size + 1
        for cell in puzzle.board.iter_cells():
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
        for cell in puzzle.board.iter_cells():
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
        for area in puzzle.board.iter_areas():
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
                for cell_area in puzzle.board.iter_common_areas(cells):
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
        level_ex = max(level, puzzle.board.block_width, puzzle.board.block_height)
        def is_useful(number: int) -> bool:
            if puzzle.get_hidden_confirm_level(area, number) <= level:
                return False
            if len(puzzle.get_positions(area, number)) > level_ex:
                return False
            return True

        improved = False
        for area in puzzle.board.iter_areas():
            # for each L-combinations
            all_numbers = [number for number in puzzle.board.iter_numbers() if is_useful(number)]
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
                elif area.area_type == AreaType.ROW and len(positions) > max(level, puzzle.board.block_width):
                    continue
                elif area.area_type == AreaType.COLUMN and len(positions) > max(level, puzzle.board.block_height):
                    continue

                result = False
                for cell_area in puzzle.board.iter_common_areas(cells):
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
            if puzzle.get_linked_confirm_level(area, number) < level:
                return False
            if len(puzzle.get_positions(area, number)) > level:
                return False
            return True

        orth_area_type = area_type.orthogonal_type()
        improved = False
        for number in puzzle.board.iter_numbers():
            # for each L-combinations
            all_areas = [area for area in puzzle.board.iter_areas(area_type) if is_useful(area)]
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
                    orthogonal_area = puzzle.board.get_area(orth_area_type, position)
                    result = puzzle.remove_candidates(number, orthogonal_area.iter_cells(excludes=areas)) or result
                    puzzle.confirm_linked_level(orthogonal_area, number, level)

                for area in areas:
                    puzzle.confirm_linked_level(area, number, level)

                improved = result or improved
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
            value_text = status.board.mark(value)
            print(f'{indent}[Primary Check] cell {cell} has single candidate "{value_text}"')

        if msg_level < DeduceMsgLevel.BOARD:
            return

        status.puzzle.print(self.board_border_enabled)

    def _show_naked_deduce_msg(self, status: SolvingStatus, area: Area,
                               cells: typing.Iterable[Cell], candidates: typing.Iterable[int]):
        msg_level = self._get_msg_level(status)
        if msg_level < DeduceMsgLevel.DEDUCE:
            return

        indent = self._get_msg_indent(status)
        level = len(cells)
        cells_text = ', '.join(f'{cell}' for cell in cells)
        candidates_text = ', '.join(f'"{status.board.mark(number)}"' for number in candidates)
        if len(candidates) < level:
            print(f'{indent}[Paradox @ Naked Deduce L{level}] in {area.area_type} {area},'
                  f' cells [{cells_text}] have only {len(candidates)} candidates [{candidates_text}]')
        else:
            print(f'{indent}[Naked Deduce L{level}] in {area.area_type} {area},'
                  f' cells [{cells_text}] have exactly {level} candidates [{candidates_text}]')

        if msg_level < DeduceMsgLevel.BOARD:
            return

        status.puzzle.print(self.board_border_enabled)

    def _show_hidden_deduce_msg(self, status: SolvingStatus, area: Area,
                                numbers: typing.Iterable[int], cells: typing.Iterable[Cell]):
        msg_level = self._get_msg_level(status)
        if msg_level < DeduceMsgLevel.DEDUCE:
            return

        indent = self._get_msg_indent(status)
        level = len(numbers)
        exactly = 'exactly ' if len(cells) == level else ''
        numbers_text = ', '.join(f'"{status.board.mark(number)}"' for number in numbers)
        cells_text = ', '.join(f'{cell}' for cell in cells)
        if len(cells) < level:
            print(f'{indent}[Paradox @ Hidden Deduce L{level}] in {area.area_type} {area},'
                  f' numbers [{numbers_text}] appear in only {len(cells)} cells [{cells_text}]')
        else:
            print(f'{indent}[Hidden Deduce L{level}] in {area.area_type} {area},'
                  f' numbers [{numbers_text}] appear in {exactly}{len(cells)} cells [{cells_text}]')

        if msg_level < DeduceMsgLevel.BOARD:
            return

        status.puzzle.print(self.board_border_enabled)

    def _show_linked_deduce_msg(self, status: SolvingStatus, number: int, area_type: AreaType,
                                areas: typing.Iterable[Area], positions: typing.Iterable[int]):
        msg_level = self._get_msg_level(status)
        if msg_level < DeduceMsgLevel.DEDUCE:
            return

        indent = self._get_msg_indent(status)
        level = len(areas)
        number_text = status.board.mark(number)
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

        status.puzzle.print(self.board_border_enabled)

    def _show_guess_msg(self, status: SolvingStatus, cell: Cell, value: int):
        msg_level = self.guess_msg_level
        if msg_level < DeduceMsgLevel.GUESS:
            return

        indent = self._get_msg_indent(status)
        level = status.guess_depth + 1
        value_text = status.board.mark(value)
        print(f'{indent}[Guess L{level}] assume cell {cell} value is "{value_text}"')

    def _show_guess_success_msg(self, status: SolvingStatus):
        msg_level = self.guess_msg_level
        if msg_level < DeduceMsgLevel.GUESS:
            return

        indent = self._get_msg_indent(status)
        print(f'{indent}[Guess Success] find a solution')
