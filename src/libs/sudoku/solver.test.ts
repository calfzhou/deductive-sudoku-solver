import fs from 'fs'

import Board from './board'
import Formatter from './formatter'
import * as itertools from '../../utils/itertools'
import Solver, { DeduceRule } from './solver'

function loadPuzzleFile(filePath: string): string[] {
  const content = fs.readFileSync(filePath, 'utf8')
  return content.split(/\r?\n/)
}

const formatter = new Formatter()
const board = new Board()

describe('puzzle a01', () => {
  const puzzlePath = 'puzzles/a01.txt'

  it('can be solved by primary deduce (naked@1)', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Naked] = 1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by hidden@4', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Hidden] = 4
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })
})

describe('puzzle b01', () => {
  const puzzlePath = 'puzzles/b01.txt'

  it('can be solved by naked@3', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Naked] = 3
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by hidden@1 + primary', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Hidden] = 1
    solver.maxLevels[DeduceRule.Naked] = 1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by hidden@5', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Hidden] = 5
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })
})

describe('puzzle b02', () => {
  const puzzlePath = 'puzzles/b02.txt'

  it('can be solved by naked@5', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Naked] = 5
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by hidden@2 + primary', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Hidden] = 2
    solver.maxLevels[DeduceRule.Naked] = 1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by hidden@6', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Hidden] = 6
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })
})

describe('puzzle b03', () => {
  const puzzlePath = 'puzzles/b03.txt'

  it('can be solved by naked@3', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Naked] = 3
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by hidden@4', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Hidden] = 4
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })
})

describe('puzzle c01', () => {
  const puzzlePath = 'puzzles/c01.txt'

  it('can NOT be solved by naked and hidden', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Naked] = -1
    solver.maxLevels[DeduceRule.Hidden] = -1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(false)
  })

  it('can be solved by linked@2 + naked@2', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Linked] = 2
    solver.maxLevels[DeduceRule.Naked] = 2
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by linked@2 + hidden@1 + primary', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Linked] = 2
    solver.maxLevels[DeduceRule.Hidden] = 1
    solver.maxLevels[DeduceRule.Naked] = 1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by linked@2 + hidden@6', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Linked] = 2
    solver.maxLevels[DeduceRule.Hidden] = 6
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })
})

describe('puzzle c02', () => {
  const puzzlePath = 'puzzles/c02.txt'

  it('can NOT be solved by naked and hidden', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Naked] = -1
    solver.maxLevels[DeduceRule.Hidden] = -1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(false)
  })

  it('can be solved by linked@2 + naked@2', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Linked] = 2
    solver.maxLevels[DeduceRule.Naked] = 2
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by linked@2 + hidden@1 + primary', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Linked] = 2
    solver.maxLevels[DeduceRule.Hidden] = 1
    solver.maxLevels[DeduceRule.Naked] = 1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by linked@2 + hidden@6', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Linked] = 2
    solver.maxLevels[DeduceRule.Hidden] = 6
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })
})

describe('puzzle c03', () => {
  const puzzlePath = 'puzzles/c03.txt'

  it('can NOT be solved by naked and hidden', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Naked] = -1
    solver.maxLevels[DeduceRule.Hidden] = -1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(false)
  })

  it('can be solved by linked@3 + naked@5 + hidden@1', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Linked] = 3
    solver.maxLevels[DeduceRule.Naked] = 5
    solver.maxLevels[DeduceRule.Hidden] = 1
    itertools.count(solver.deduce(puzzle))
    // console.log(puzzle.data.map((c, i) => `puzzle._cell_candidates[${i}].retain([${c.asArray()}])`).join('\n'))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by linked@3 + hidden@4 + primary', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Linked] = 3
    solver.maxLevels[DeduceRule.Hidden] = 4
    solver.maxLevels[DeduceRule.Naked] = 1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })

  it('can be solved by linked@3 + hidden@6', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Linked] = 3
    solver.maxLevels[DeduceRule.Hidden] = 6
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(true)
  })
})

describe('puzzle d01', () => {
  const puzzlePath = 'puzzles/d01.txt'

  it('can NOT be solved by naked and hidden and linked', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Naked] = -1
    solver.maxLevels[DeduceRule.Hidden] = -1
    solver.maxLevels[DeduceRule.Linked] = -1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(false)
  })
})

describe('puzzle d02', () => {
  const puzzlePath = 'puzzles/d02.txt'

  it('can NOT be solved by naked and hidden and linked', () => {
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    const solver = new Solver()
    solver.disableAllRules()
    solver.maxLevels[DeduceRule.Naked] = -1
    solver.maxLevels[DeduceRule.Hidden] = -1
    solver.maxLevels[DeduceRule.Linked] = -1
    itertools.count(solver.deduce(puzzle))
    expect(puzzle.solved()).toBe(false)
  })
})
