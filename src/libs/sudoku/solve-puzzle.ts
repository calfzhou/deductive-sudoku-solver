import fs from 'fs'

import { program, Option } from 'commander'
import _ from 'lodash'
import pluralize from 'pluralize'

import Board from './board'
import { DeduceRule, GuessEvidence } from './deduce-info'
import Formatter from './formatter'
import Puzzle from './puzzle'
import Solver from './solver'

function loadPuzzleFile(filePath: string): string[] {
  const content = fs.readFileSync(filePath, 'utf8')
  return content.split(/\r?\n/)
}

enum StepMsgLevel {
  None,
  Evidence,
  Mutations,
  Puzzle,
}

type StepMsgLevelStrings = keyof typeof StepMsgLevel

program
  .argument('<puzzle-file>', 'a file contains sudoku puzzle, read from stdin if not provided')
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
    new Option('--markers <string>', 'all markers for every candidate value')
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
    new Option('--search [count]', 'search (at most `count`) solutions when not solved by deduction')
      .default(0)
      .preset(1)
      .argParser(_.parseInt)
  )
  .addOption(
    new Option('--show-steps [level]', 'show solving steps')
      .default('none')
      .preset('mutations')
      .choices(['none', 'evidence', 'mutations', 'puzzle'])
  )
  .addOption(new Option('--better-print', 'print intermediate puzzle with borders').default(false))
  .addOption(new Option('--no-better-print', 'print intermediate puzzle without borders'))
  .action((puzzlePath, options) => {
    // console.log('puzzlePath', puzzlePath)
    // console.log('options', options)

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
        solver.maxLevels.set(rule, level)
      }
    }
    solver.lowerLevelFirst = options.lowerLevelFirst

    const board = new Board(options.blockHeight, options.blockWidth)
    const formatter = new Formatter(options.markers)
    const puzzle = formatter.parsePuzzle(loadPuzzleFile(puzzlePath), board)
    console.log(formatter.formatPuzzle(puzzle))

    const stepMsgLevel = StepMsgLevel[_.upperFirst(_.camelCase(options.showSteps)) as StepMsgLevelStrings]
    for (const step of solver.deduce(puzzle)) {
      if (stepMsgLevel >= StepMsgLevel.Evidence) {
        console.log(formatter.formatSolvingStep(step, stepMsgLevel >= StepMsgLevel.Mutations))
        if (stepMsgLevel >= StepMsgLevel.Puzzle) {
          console.log(formatter.formatPuzzle(step.puzzle, options.betterPrint))
        }
      }
    }

    if (puzzle.solved()) {
      console.log('The puzzle is solved by deduction:')
      console.log(formatter.formatPuzzle(puzzle))
      return
    }

    console.log('The puzzle is NOT solved by deduction, current result is:')
    console.log(formatter.formatPuzzle(puzzle, options.betterPrint))

    if (options.search > 0) {
      const solutions = new Array<Puzzle>()
      let guessLevel = 0
      for (const step of solver.search(puzzle, solutions, options.search)) {
        if (stepMsgLevel >= StepMsgLevel.Evidence) {
          if (step.evidence instanceof GuessEvidence) {
            guessLevel = step.evidence.level - 1
          }

          console.log(formatter.formatSolvingStep(step, stepMsgLevel >= StepMsgLevel.Mutations, guessLevel))
          if (stepMsgLevel >= StepMsgLevel.Puzzle && step.mutations.length > 0) {
            console.log(formatter.formatPuzzle(step.puzzle, options.betterPrint))
          }

          if (step.evidence instanceof GuessEvidence) {
            guessLevel = step.evidence.level
          }
        }
      }

      console.log(`Find ${pluralize('solution', solutions.length, true)} by brute search.`)
      for (const [index, solution] of solutions.entries()) {
        console.log(`Solutions #${index + 1}:`)
        console.log(formatter.formatPuzzle(solution))
      }
    }
  })

program.parse()
