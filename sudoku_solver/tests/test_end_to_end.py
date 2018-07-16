import json
import unittest
from os import path

import ddt

from sudoku_solver.__main__ import create_arg_parser, create_board, create_solver, load_puzzle
from sudoku_solver.solver import DeduceMsgLevel


@ddt.ddt
class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arg_parser = create_arg_parser()

    @ddt.file_data('data/end-to-end-cases.json')
    def test(self, **case_info):
        # print(case_info)
        cmd_args = case_info['cmd_line'].split(' ')
        args = self.arg_parser.parse_args(cmd_args)
        solver = create_solver(args)
        solver.deduce_msg_level = DeduceMsgLevel.NONE
        solver.guess_msg_level = DeduceMsgLevel.NONE
        puzzle = load_puzzle(args)

        status = solver.solve(puzzle)

        expected_solved = case_info['solved']
        self.assertIs(puzzle.solved(), expected_solved)

        if 'solutions_count' in case_info:
            expected_solutions_count = case_info['solutions_count']
            self.assertEqual(len(status.solutions), expected_solutions_count)

        if 'interrupted' in case_info:
            expected_interrupted = case_info['interrupted']
            self.assertIs(status.interrupted, expected_interrupted)


if __name__ == '__main__':
    unittest.main()
