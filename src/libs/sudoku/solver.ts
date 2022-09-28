import _ from 'lodash'

import { HouseKind, Cell } from './grid'
import {
  DeduceRule,
  SolvingStep,
  StopSearchingError,
  GuessEvidence,
  ParadoxError,
  NakedEvidence,
  HiddenEvidence,
  LinkedEvidence,
} from './deduce-info'
import { combinations, filter } from '../../utils/itertools'
import Puzzle from './puzzle'
import ValueSet from './value-set'

export default class Solver {
  readonly maxLevels = new Map<DeduceRule, number>()
  lowerLevelFirst = true

  disableAllRules() {
    this.maxLevels.set(DeduceRule.Naked, 0)
    this.maxLevels.set(DeduceRule.Hidden, 0)
    this.maxLevels.set(DeduceRule.Linked, 0)
  }

  ruleEnabled(rule: DeduceRule, level: number): boolean {
    const maxLevel = this.maxLevels.get(rule) ?? -1
    return maxLevel < 0 || level <= maxLevel
  }

  *deduce(puzzle: Puzzle): Generator<SolvingStep> {
    while (!puzzle.fulfilled()) {
      let improved = false
      for (const step of this.deduceOneRound(puzzle)) {
        improved = true
        yield step
      }

      if (!improved) {
        break
      }
    }
  }

  *search(puzzle: Puzzle, solutions?: Puzzle[], maxCount = 1): Generator<SolvingStep> {
    solutions = solutions ?? new Array<Puzzle>()
    try {
      yield* this.guessSearch(1, puzzle, solutions, maxCount)
    } catch (err: unknown) {
      if (err instanceof StopSearchingError) {
        return
      } else {
        throw err
      }
    }
  }

  protected *guessSearch(level: number, puzzle: Puzzle, solutions: Puzzle[], maxCount: number): Generator<SolvingStep> {
    const cell = this.chooseGuessingCell(puzzle)
    if (cell === undefined) {
      return
    }

    const candidates = puzzle.candidates(cell)
    for (const value of candidates) {
      const clonedPuzzle = puzzle.clone()
      const removed = clonedPuzzle.candidates(cell).retain(value)
      const mutations = [{ cell, removed }]
      const evidence = new GuessEvidence(level, cell, candidates.asArray(), value)
      yield { evidence, mutations, puzzle: clonedPuzzle }

      try {
        yield* this.deduce(clonedPuzzle)
      } catch (err: unknown) {
        if (err instanceof ParadoxError) {
          yield { evidence: err.evidence, mutations: [], puzzle: clonedPuzzle }
          continue
        } else {
          throw err
        }
      }

      if (clonedPuzzle.fulfilled()) {
        solutions.push(clonedPuzzle)
        if (solutions.length >= maxCount) {
          throw new StopSearchingError()
        }
      } else {
        yield* this.guessSearch(level + 1, clonedPuzzle, solutions, maxCount)
      }
    }
  }

  protected chooseGuessingCell(puzzle: Puzzle): Cell | undefined {
    let selectedCell = undefined
    let minSize = puzzle.size + 1
    for (const cell of puzzle.grid.iterCells()) {
      const size = puzzle.candidates(cell).size
      if (size === 2) {
        return cell
      } else if (2 < size && size < minSize) {
        selectedCell = cell
        minSize = size
      }
    }
    return selectedCell
  }

  protected *deduceOneRound(puzzle: Puzzle): Generator<SolvingStep> {
    for (let level = 1; level < puzzle.size; ++level) {
      let improved = false

      if (this.ruleEnabled(DeduceRule.Naked, level)) {
        for (const step of this.nakedDeduce(level, puzzle)) {
          improved = true
          yield step
        }
      }

      if (this.ruleEnabled(DeduceRule.Hidden, level)) {
        for (const step of this.hiddenDeduce(level, puzzle)) {
          improved = true
          yield step
        }
      }

      if (level >= 2 && this.ruleEnabled(DeduceRule.Linked, level)) {
        for (const step of this.linkedDeduce(level, puzzle)) {
          improved = true
          yield step
        }
      }

      if (improved && this.lowerLevelFirst) {
        break
      }
    }
  }

  protected *nakedDeduce(level: number, puzzle: Puzzle): Generator<SolvingStep> {
    const grid = puzzle.grid

    // Traverse all `level`-length cell combinations of every house.
    for (const house of grid.iterHouses()) {
      // TODO: Apply pruning.
      for (const cells of combinations(grid.iterCells(house), level)) {
        // Get candidates union of the selected cells.
        const candidates = new ValueSet()
        cells.forEach(cell => candidates.merge(puzzle.candidates(cell)))

        // Compare number of cells to number of candidates (level).
        if (candidates.size < level) {
          const evidence = new NakedEvidence(level, house, cells, candidates.asArray())
          throw new ParadoxError(evidence)
        } else if (candidates.size > level) {
          continue
        }

        // For all houses containing all these cells, remove candidates from other cells.
        const commonHouses = grid.commonHousesOf(cells)
        const houseMutations = commonHouses.map(h => puzzle.removeCandidates(candidates, grid.iterCells(h, cells)))
        const mutations = _.flatten(houseMutations)
        if (mutations.length > 0) {
          const evidence = new NakedEvidence(level, house, cells, candidates.asArray())
          yield { evidence, mutations, puzzle }
        }
      }
    }
  }

  protected *hiddenDeduce(level: number, puzzle: Puzzle): Generator<SolvingStep> {
    const grid = puzzle.grid

    // Traverse all `level`-length value combinations of every house.
    for (const house of grid.iterHouses()) {
      for (const values of combinations(_.range(grid.size), level)) {
        // Get all cells containing any of the selected value.
        const cells = Array.from(filter(grid.iterCells(house), cell => puzzle.candidates(cell).containsAny(values)))

        // Compare number of values to number of cells (level).
        if (cells.length < level) {
          const evidence = new HiddenEvidence(level, house, values, cells)
          throw new ParadoxError(evidence)
        }

        // For other houses containing all these cells, remove candidates from other cells.
        const otherHouses = grid.commonHousesOf(cells, house.kind)
        const houseMutations = otherHouses.map(h => puzzle.removeCandidates(values, grid.iterCells(h, cells)))
        const mutations = _.flatten(houseMutations)

        // Remove other candidates from these cells.
        if (cells.length === level) {
          mutations.push(...puzzle.retainCandidates(values, cells))
        }

        if (mutations.length > 0) {
          const evidence = new HiddenEvidence(level, house, values, cells)
          yield { evidence, mutations, puzzle }
        }
      }
    }
  }

  protected *linkedDeduce(level: number, puzzle: Puzzle): Generator<SolvingStep> {
    const grid = puzzle.grid
    const houseKinds = [HouseKind.Row, HouseKind.Column]

    // Traverse all `level`-length house combinations for every candidate value.
    for (const value of _.range(grid.size)) {
      for (const kind of houseKinds) {
        const orthKind = grid.orthogonalKindOf(kind)
        if (orthKind === undefined) {
          continue
        }

        for (const indices of combinations(_.range(grid.size), level)) {
          // Get all orthogonal house indices where the value occurs.
          const orthIndices = new ValueSet()
          indices.forEach(index =>
            orthIndices.merge(
              _.range(grid.size).filter(orthIndex =>
                puzzle.candidates(grid.intersectCellOf(kind, index, orthIndex)).contains(value)
              )
            )
          )

          // Compare number of orthogonal houses to number of houses (level).
          if (orthIndices.size < level) {
            const evidence = new LinkedEvidence(level, value, kind, orthKind, indices, orthIndices.asArray())
            throw new ParadoxError(evidence)
          } else if (orthIndices.size > level) {
            continue
          }

          // Remove value from non-intersect cells of orthogonal houses.
          const houseMutations = orthIndices.asArray().map(orthIndex => {
            const cells = grid.iterCells(
              { kind: orthKind, index: orthIndex },
              indices.map(index => grid.intersectCellOf(kind, index, orthIndex))
            )
            return puzzle.removeCandidates(value, cells)
          })
          const mutations = _.flatten(houseMutations)
          if (mutations.length > 0) {
            const evidence = new LinkedEvidence(level, value, kind, orthKind, indices, orthIndices.asArray())
            yield { evidence, mutations, puzzle }
          }
        }
      }
    }
  }
}
