import _ from 'lodash'

import Grid, { Cell } from './grid'
import ValueSet, { ValuesParam } from './value-set'

export type Variation = {
  readonly cell: Cell
  readonly removed: number[]
}

export default class Puzzle {
  // `data` holds all cells' candidate numbers.
  data: readonly ValueSet[]

  constructor(public readonly grid: Grid, data?: readonly ValueSet[]) {
    if (data === undefined) {
      this.data = _.times(grid.cellCount, () => new ValueSet(undefined, grid.size))
    } else {
      this.data = data
    }
  }

  get size(): number {
    return this.grid.size
  }

  clone() {
    return new Puzzle(this.grid, _.cloneDeep(this.data))
  }

  candidates(cell: Cell): ValueSet {
    const index = this.grid.indexOf(cell)
    return this.data[index]
  }

  /**
   * Checks if the puzzle is fulfilled, i.e. all cells have one and only one candidate.
   * @returns true if fulfilled.
   */
  fulfilled(): boolean {
    return this.data.every(candidates => candidates.size === 1)
  }

  /**
   * Checks if the puzzle contains paradox, no matter it is fulfilled or not.
   * Only checks primary paradox, i.e. two cells in one house have the same single candidate.
   * @returns true if contains paradox.
   */
  paradoxical(): boolean {
    for (const house of this.grid.iterHouses()) {
      const knownValues = new Set<number>()
      for (const cell of this.grid.iterCells(house)) {
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
