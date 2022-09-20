import _ from 'lodash'

import { AreaKind } from './board'
import { combinations, filter } from '../../utils/itertools'
import Puzzle from './puzzle'
import ValueSet from './value-set'
import Formatter from './formatter'
import { format } from 'node:path/win32'

export const enum DeduceRule {
  Naked = 'naked',
  Hidden = 'hidden',
  Linked = 'linked',
}

interface SolvingStep {
  readonly rule: DeduceRule
  readonly level: number
}

export class ParadoxError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ParadoxError'
  }
}

class SolvingStatus {}

class Solver {
  readonly maxLevels = {
    [DeduceRule.Naked]: -1,
    [DeduceRule.Hidden]: -1,
    [DeduceRule.Linked]: -1,
  }
  lowerLevelFirst = true

  disableAllRules() {
    this.maxLevels[DeduceRule.Naked] = 0
    this.maxLevels[DeduceRule.Hidden] = 0
    this.maxLevels[DeduceRule.Linked] = 0
  }

  ruleEnabled(rule: DeduceRule, level: number): boolean {
    const maxLevel = this.maxLevels[rule]
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
    const board = puzzle.board
    const rule = DeduceRule.Naked

    // Traverse all `level`-length cell combinations of every area.
    for (const area of board.iterAreas()) {
      // TODO: Apply pruning.
      for (const cells of combinations(board.iterCells(area), level)) {
        // Get candidates union of the selected cells.
        const candidates = new ValueSet()
        cells.forEach(cell => candidates.merge(puzzle.candidates(cell)))

        // Compare number of cells to number of candidates (level).
        if (candidates.size < level) {
          // TODO: Paradox.
          console.log('paradox', rule, level, area, cells)
          throw new ParadoxError(rule)
        } else if (candidates.size > level) {
          continue
        }

        // Remove candidates from other cells of the current area.
        const mutations = puzzle.removeCandidates(candidates, board.iterCells(area, cells))
        if (mutations.length > 0) {
          // console.log(rule, level, area, cells, mutations)
          yield { rule, level }
        }
      }
    }
  }

  protected *hiddenDeduce(level: number, puzzle: Puzzle): Generator<SolvingStep> {
    const board = puzzle.board
    const rule = DeduceRule.Hidden

    // Traverse all `level`-length value combinations of every area.
    for (const area of board.iterAreas()) {
      for (const values of combinations(_.range(board.size), level)) {
        // Get all cells containing any of the selected value.
        const cells = Array.from(filter(board.iterCells(area), cell => puzzle.candidates(cell).containsAny(values)))

        // Compare number of values to number of cells (level).
        if (cells.length < level) {
          console.log('paradox', rule, level, area, cells)
          throw new ParadoxError(rule)
        }

        // For other areas which contain all these cells, remove candidates from other cells.
        const mutations = _.concat(...board.commonAreasOf(cells, area.kind).map(
          area => puzzle.removeCandidates(values, board.iterCells(area, cells))))

        // Remove other candidates from these cells.
        if (cells.length === level) {
          mutations.push(...puzzle.retainCandidates(values, cells))
        }

        if (mutations.length > 0) {
          // console.log(rule, level, area, cells, mutations)
          yield { rule, level }
        }
      }
    }
  }

  protected *linkedDeduce(level: number, puzzle: Puzzle): Generator<SolvingStep> {
    const board = puzzle.board
    const rule = DeduceRule.Linked
    const areaKinds = [[AreaKind.Row, AreaKind.Column], [AreaKind.Column, AreaKind.Row]]

    // Traverse all `level`-length area combinations for every candidate value.
    for (const value of _.range(board.size)) {
      for (const [areaKind, orthAreaKind] of areaKinds) {
        for (const indices of combinations(_.range(board.size), level)) {
          // Get all orthogonal area indices where the value occurs.
          const orthIndices = new ValueSet()
          indices.forEach(index => orthIndices.merge(_.range(board.size).filter(
            orthIndex => puzzle.candidates(board.intersectCellOf(areaKind, index, orthIndex)).contains(value)
          )))

          // Compare number of orthogonal areas to number of areas (level).
          if (orthIndices.size < level) {
            console.log('paradox', rule, level, value, areaKind, indices)
            throw new ParadoxError(rule)
          } else if (orthIndices.size > level) {
            continue
          }

          // Remove value from non-intersect cells of orthogonal areas.
          const mutations = _.concat(...orthIndices.asArray().map(orthIndex => {
            const cells = board.iterCells(
              { kind: orthAreaKind, index: orthIndex },
              indices.map(index => board.intersectCellOf(areaKind, index, orthIndex))
            )
            return puzzle.removeCandidates(value, cells)
          }))
          if (mutations.length > 0) {
            // console.log(rule, level, value, areaKind, indices, orthIndices.asArray(), mutations)
            yield { rule, level }
          }
        }
      }
    }
  }
}

export default Solver
