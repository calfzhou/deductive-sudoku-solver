import argparse
import distutils.util
import string
import sys

from . import name, __version__
from .board import Board
from .puzzle import BoardData
from .solver import DeduceMsgLevel, DeduceRule, SudokuSolver


def create_arg_parser() -> argparse.ArgumentParser:
    strtobool = lambda s: bool(distutils.util.strtobool(s))
    parser = argparse.ArgumentParser(prog=name, description='Deductive Sudoku Solver', allow_abbrev=False)
    parser.add_argument('--version', action='version', version=f'{name} {__version__}')
    parser.add_argument('puzzle_file', nargs='?',
                        help='a file contains the sudoku puzzle, see puzzles/*.txt for example'
                        ' (default: read from stdin)')

    board_group = parser.add_argument_group(
        'board arguments',
        description='The size (edge length) of the board is BLOCK_WIDTH * BLOCK_HEIGHT.')
    board_group.add_argument('--block-width', type=int, default=3,
                             help='how many columns a block contains (default: 3)')
    board_group.add_argument('--block-height', type=int, default=3,
                             help='how many rows a block contains (default: 3)')
    board_group.add_argument('--marks', default=f'123456789{string.ascii_uppercase}',
                             help='a string contains all marks for every cell value (default: "1..9A..Z")')

    rule_group = parser.add_argument_group('deduce rule arguments')
    rule_group.add_argument('--deduce', type=strtobool,
                            nargs='?', const=True, default=True, choices=[True, False],
                            help='whether enable deduce (set to `false` to disable all deduce rules,'
                            ' then enable specific rule by corresponding deduce level arguments) (default: true)')
    for rule in DeduceRule:
        rule_group.add_argument(f'--{rule}-deduce', type=int,
                                help=f'the max level of {rule} rule, use 0 for disable, -1 for no limit')
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
    solver = SudokuSolver()
    solver.lower_level_deduce_first = args.lower_level_first
    solver.guess_enabled = args.guess
    solver.max_solutions_count = args.max_solutions
    solver.deduce_msg_level = args.deduce_msg
    solver.guess_msg_level = args.guess_msg
    solver.board_border_enabled = args.better_print

    if not args.deduce:
        solver.disable_deduce()
    if args.naked_deduce is not None:
        solver.max_deduce_levels[DeduceRule.NAKED] = args.naked_deduce
    if args.hidden_deduce is not None:
        solver.max_deduce_levels[DeduceRule.HIDDEN] = args.hidden_deduce
    if args.linked_deduce is not None:
        solver.max_deduce_levels[DeduceRule.LINKED] = args.linked_deduce

    return solver


def create_board(args) -> Board:
    board = Board(block_width=args.block_width, block_height=args.block_height)
    board.mapping = args.marks
    return board


def load_puzzle(args) -> BoardData:
    board = Board(block_width=args.block_width, block_height=args.block_height)
    board.mapping = args.marks
    with (open(args.puzzle_file) if args.puzzle_file else sys.stdin) as f:
        puzzle = BoardData.load(f, board)
        return puzzle


def main():
    parser = create_arg_parser()
    args = parser.parse_args()
    # print(args)
    board_size = args.block_width * args.block_height
    if len(args.marks) < board_size:
        raise ValueError(f'each area of the board contains {board_size} cells,'
                         f' but only {len(args.marks)} marks provided')

    solver = create_solver(args)
    puzzle = load_puzzle(args)

    print('The puzzle is:')
    puzzle.print(args.better_print)

    status = solver.solve(puzzle)
    if puzzle.solved():
        print('Solved by deduction:')
        puzzle.print(args.better_print)
    elif status.solutions:
        print(f'Solved by guessing, find {len(status.solutions)} solutions:')
        for solution in status.solutions:
            solution.data.print(args.better_print)
            print()

        if status.interrupted:
            print('There might be more solutions not found.')
    else:
        print('Not solved, the final state is:')
        puzzle.print(args.better_print)

    # print(f'useless naked deduce: {status.useless_naked_deduce}')
    # print(f'useless hidden deduce: {status.useless_hidden_deduce}')
    # print(f'useless linked deduce: {status.useless_linked_deduce}')


if __name__ == '__main__':
    main()
