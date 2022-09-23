import _ from 'lodash'

import Board, { Cell } from './board'
import ValueSet, { ValuesParam } from './value-set'

export type Variation = {
  readonly cell: Cell
  readonly removed: number[]
}

export default class Puzzle {
  // `data` holds all cells' candidate numbers.
  data: readonly ValueSet[]

  constructor(public readonly board: Board, data?: readonly ValueSet[]) {
    if (data === undefined) {
      this.data = _.times(board.cellCount, () => new ValueSet(undefined, board.size))
    } else {
      this.data = data
    }
  }

  get size(): number {
    return this.board.size
  }

  clone() {
    return new Puzzle(this.board, _.cloneDeep(this.data))
  }

  candidates(cell: Cell): ValueSet {
    const index = this.board.indexOf(cell)
    return this.data[index]
  }

  /**
   * Checks if the puzzle is fulfilled, i.e. all cells have one and only one candidate.
   * @returns true if fulfilled.
   */
  fulfilled() : boolean {
    return this.data.every(candidates => candidates.size === 1)
  }

  /**
   * Checks if the puzzle contains paradox, no matter it is fulfilled or not.
   * Only checks primary paradox, i.e. two cells in one area have the same single candidate.
   * @returns true if contains paradox.
   */
  paradoxical(): boolean {
    for (const area of this.board.iterAreas()) {
      const knownValues = new Set<number>()
      for (const cell of this.board.iterCells(area)) {
        const candidates = this.candidates(cell)
        if (candidates.size === 0) {
          return true
        } else if (candidates.size > 1) {
          continue
        }

        const value = candidates.peek()
        if (knownValues.has(value)) {
          return true
        }

        knownValues.add(value)
      }
    }

    return false
  }

  /**
   * Checks if the puzzle is solved, i.e. fulfilled and no paradox.
   * @returns true if solved.
   */
  solved(): boolean {
    return this.fulfilled() && !this.paradoxical()
  }

  /**
   * Retains `candidates` from all `cells`' candidate sets.
   * @param candidates
   * @param cells
   * @returns A list of happened variations, i.e. changed cell with removed candidates.
   */
  retainCandidates(candidates: ValuesParam, cells: Iterable<Cell>): Variation[] {
    const variations = new Array<Variation>()
    for (const cell of cells) {
      const removed = this.candidates(cell).retain(candidates)
      if (removed.length > 0) {
        variations.push({ cell, removed })
      }
    }
    return variations
  }

  /**
   * Removes `candidates` from all `cells`' candidate sets.
   * @param candidates
   * @param cells
   * @returns A list of happened variations, i.e. changed cell with removed candidates.
   */
  removeCandidates(candidates: ValuesParam, cells: Iterable<Cell>): Variation[] {
    const variations = new Array<Variation>()
    for (const cell of cells) {
      const removed = this.candidates(cell).remove(candidates)
      if (removed.length > 0) {
        variations.push({ cell, removed })
      }
    }
    return variations
  }
}
