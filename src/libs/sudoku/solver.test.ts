import fs from 'fs'

import Board from './board'
import { DeduceRule } from './deduce-info'
import Formatter from './formatter'
import * as itertools from '../../utils/itertools'
import Puzzle from './puzzle'
import Solver from './solver'

function loadPuzzleFile(filePath: string): string[] {
  const content = fs.readFileSync(filePath, 'utf8')
  return content.split(/\r?\n/)
}

type SolverCase = {
  naked?: number
  hidden?: number
  linked?: number
  allRules?: number
  solved?: boolean
  search?: number
  solutions?: number
}

const puzzles: Array<[string, SolverCase[]]> = [
  ['puzzles/a01.txt', [{ naked: 1 }, { hidden: 4 }]],
  ['puzzles/b01.txt', [{ naked: 3 }, { hidden: 1, naked: 1 }, { hidden: 5 }]],
  ['puzzles/b02.txt', [{ naked: 5 }, { hidden: 2, naked: 1 }, { hidden: 6 }]],
  ['puzzles/b03.txt', [{ naked: 3 }, { hidden: 4 }]],
  [
    'puzzles/c01.txt',
    [
      { naked: -1, hidden: -1, solved: false },
      { linked: 2, naked: 2 },
      { linked: 2, hidden: 1, naked: 1 },
      { linked: 2, hidden: 6 },
    ],
  ],
  [
    'puzzles/c02.txt',
    [
      { naked: -1, hidden: -1, solved: false },
      { linked: 2, naked: 2 },
      { linked: 2, hidden: 1, naked: 1 },
      { linked: 2, hidden: 6 },
    ],
  ],
  [
    'puzzles/c03.txt',
    [
      { naked: -1, hidden: -1, solved: false },
      { linked: 3, naked: 5, hidden: 1 },
      { linked: 3, hidden: 4, naked: 1 },
      { linked: 3, hidden: 6 },
    ],
  ],
  ['puzzles/d01.txt', [{ allRules: -1, search: 2, solutions: 1 }]],
  ['puzzles/d01.txt', [{ allRules: -1, search: 2, solutions: 1 }]],
  ['puzzles/x01.txt', [{ allRules: -1, search: 2, solutions: 1 }]],
  ['puzzles/y01.txt', [{ allRules: -1, search: 2, solutions: 2 }]],
]

const formatter = new Formatter()
const board = new Board()

describe.each(puzzles)('%s', (puzzlePath, cases) => {
  it.each(cases)('%o', options => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.maxLevels.set(DeduceRule.Naked, options.naked ?? options.allRules ?? 0)
    solver.maxLevels.set(DeduceRule.Hidden, options.hidden ?? options.allRules ?? 0)
    solver.maxLevels.set(DeduceRule.Linked, options.linked ?? options.allRules ?? 0)
    itertools.count(solver.deduce(puzzle))

    const expectedSolved = options.solved ?? ((options.search ?? 0) === 0)
    expect(puzzle.solved()).toBe(expectedSolved)

    const solutions = new Array<Puzzle>()
    if ((options.search ?? 0) > 0) {
      itertools.count(solver.search(puzzle, solutions, options.search ?? 0))
    }
    expect(solutions).toHaveLength(options.solutions ?? 0)
  })
})
