import fs from 'fs'

import Board from './board'
import { DeduceRule } from './deduce-info'
import Formatter from './formatter'
import * as itertools from '../../utils/itertools'
import Solver from './solver'

function loadPuzzleFile(filePath: string): string[] {
  const content = fs.readFileSync(filePath, 'utf8')
  return content.split(/\r?\n/)
}

type SolverCase = {
  naked?: number
  hidden?: number
  linked?: number
  solved?: boolean
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
  ['puzzles/d01.txt', [{ naked: -1, hidden: -1, linked: -1, solved: false }]],
  ['puzzles/d01.txt', [{ naked: -1, hidden: -1, linked: -1, solved: false }]],
]

const formatter = new Formatter()
const board = new Board()

describe.each(puzzles)('%s', (puzzlePath, cases) => {
  it.each(cases)('%o', options => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.maxLevels.set(DeduceRule.Naked, options.naked ?? 0)
    solver.maxLevels.set(DeduceRule.Hidden, options.hidden ?? 0)
    solver.maxLevels.set(DeduceRule.Linked, options.linked ?? 0)
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(options.solved ?? true)
  })
})
