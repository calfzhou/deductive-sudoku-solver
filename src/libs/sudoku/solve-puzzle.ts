import { program, Option } from 'commander'
import fs from 'fs'
import _ from 'lodash'

import Board from './board'
import Formatter from './formatter'
import * as itertools from '../../utils/itertools'
import Solver, { DeduceRule } from './solver'

function loadPuzzleFile(filePath: string): string[] {
  const content = fs.readFileSync(filePath, 'utf8')
  return content.split(/\r?\n/)
}

program
  .argument('[puzzle-file]', 'a file contains sudoku puzzle, read from stdin if not provided')
  .addOption(
    new Option('--block-height <number>', 'how many rows a block contains')
      .default(3)
      .argParser(_.parseInt)
)
  .addOption(
    new Option('--block-width <number>', 'how many columns a block contains')
      .default(3)
      .argParser(_.parseInt)
  )
  .addOption(
    new Option('--marks <string>', 'all marks for every cell value')
      .default(Formatter.defaultMarkers.join(''))
  )
  .addOption(new Option('--deduce', 'enable deduce').default(true))
  .addOption(new Option('--no-deduce', 'set all deduce rule max level to 0'))
  .addOption(
    new Option('--naked [level]', 'max level of naked rule, -1 for unlimited')
      .preset(-1)
      .argParser(_.parseInt)
  )
  .addOption(
    new Option('--hidden [level]', 'max level of hidden rule, -1 for unlimited')
      .preset(-1)
      .argParser(_.parseInt)
  )
  .addOption(
    new Option('--linked [level]', 'max level of linked rule, -1 for unlimited')
      .preset(-1)
      .argParser(_.parseInt)
  )
  .addOption(new Option('--lower-level-first', 'prefer lower level deduce').default(true))
  .addOption(new Option('--no-lower-level-first', 'use any level deduce when possible'))
  .addOption(
    new Option('--guess [number]', 'enable guessing (stop when find the given number of solutions)')
      .default(false)
      .preset(2)
      .argParser(_.parseInt)
  )
  .addOption(new Option('--no-guess', 'disable guessing'))
  .action((puzzlePath, options) => {
    console.log('puzzlePath', puzzlePath)
    console.log('options', options)

    const board = new Board(options.blockHeight, options.blockWidth)
    const formatter = new Formatter(options.markers)
    const solver = new Solver()

    if (!options.deduce) {
      solver.disableAllRules()
    }
    const maxLevels: Array<[DeduceRule, number]> = [
      [DeduceRule.Naked, options.naked],
      [DeduceRule.Hidden, options.hidden],
      [DeduceRule.Linked, options.linked],
    ]
    for (const [rule, level] of maxLevels) {
      if (level !== undefined) {
        solver.maxLevels[rule] = level
      }
    }
    solver.lowerLevelFirst = options.lowerLevelFirst

    console.log(board)
    console.log(solver)

    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    console.log(formatter.formatPuzzle(puzzle))

    const stepCount = itertools.count(solver.deduce(puzzle))
    console.log(`Deduced ${stepCount} steps, the puzzle is ${puzzle.solved() ? '' : 'NOT '}solved.`)
    console.log(formatter.formatPuzzle(puzzle))
  })

program.parse()
