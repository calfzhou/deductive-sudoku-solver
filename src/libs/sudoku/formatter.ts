import _ from 'lodash'

import Board from './board'
import ValueSet, { ValuesParam } from './value-set'
import Puzzle from './puzzle'

class Formatter {
  readonly markers: string[]
  readonly mapping = new Map<string, number>()
  readonly maxLength: number
  readonly multiChar: boolean

  static readonly defaultMarkers = _.range(1, 36).map(i => i.toString(36).toUpperCase())

  constructor(markers?: string | string[]) {
    if (markers === undefined) {
      markers = Formatter.defaultMarkers
    } else if (typeof markers === 'string') {
      markers = Array.from(markers)
    }

    this.markers = markers
    for (const [index, marker] of markers.entries()) {
      if (this.mapping.has(marker)) {
        throw new Error(`Found duplicate marker: '${marker}'.`)
      }
      this.mapping.set(marker, index)
    }

    this.maxLength = _.max(_.map(this.markers, 'length')) ?? 1
    this.multiChar = this.maxLength > 1
  }

  formatValues(values: ValuesParam, capacity?: number): string {
    values = ValueSet.normalizeValues(values)
    const sep = this.multiChar ? ' ' : ''

    if (capacity !== undefined) {
      if (values.length === capacity) {
        return '*'
      } else if (values.length > capacity / 2) {
        const text = new ValueSet(undefined, capacity).retain(values).map(v => this.markers[v]).join(sep)
        return `[^${text}]`
      }
    }

    const text = values.map(v => this.markers[v]).join(sep)
    return (values.length === 1) ? text : `[${text}]`
  }

  formatPuzzle(puzzle: Puzzle): string {
    const board = puzzle.board
    const lines = new Array<string>()
    for (const row of _.range(board.size)) {
      if (row > 0 && row % board.blockHeight === 0) {
        lines.push('')
      }
      const pieces = new Array<string>()
      for (const col of _.range(board.size)) {
        if (col > 0 && col % board.blockWidth === 0) {
          pieces.push(' ')
        }
        const candidates = puzzle.candidates({ row, col })
        pieces.push(this.formatValues(candidates, board.size))
      }
      lines.push(pieces.join(this.multiChar ? ' ' : ''))
    }
    return lines.join('\n')
  }

  protected *splitMarkers(line: string): Generator<string> {
    for (const piece of line.split(/(\[[^\]]*\])/)) {
      if (piece === undefined || piece === '') {
        continue
      } else if (piece[0] === '[') {
        yield piece
      } else {
        const cols = this.multiChar ? piece.split(' ') : Array.from(piece)
        for (const col of cols) {
          if (col === undefined || col === ' ') {
            continue
          } else {
            yield col
          }
        }
      }
    }
  }

  protected lookup(marker: string): number {
    const index = this.mapping.get(marker)
    if (index === undefined) {
      throw new Error(`Unknown marker '${marker}'.`)
    } else {
      return index
    }
  }

  parsePuzzle(lines: Iterable<string>, board: Board): Puzzle {
    if (board.size > this.markers.length) {
      throw new Error(`The board is too big for this formatter (${board.size} > ${this.markers.length}).`)
    }

    const puzzle = new Puzzle(board)

    let row = 0
    for (const line of lines) {
      if (line === '') {
        continue
      }

      let col = 0
      for (const piece of this.splitMarkers(line)) {
        if (piece === '*') {
          // Do nothing.
        } else if (piece[0] === '[') {
          const text = piece.slice(piece[1] === '^' ? 2 : 1, -1)
          const markers = Array.from(this.splitMarkers(text))
          const numbers = _.map(markers, marker => this.lookup(marker))
          if (piece[1] === '^') {
            puzzle.candidates({ row, col }).remove(numbers)
          } else {
            puzzle.candidates({ row, col }).retain(numbers)
          }
        } else {
          puzzle.candidates({ row, col }).retain(this.lookup(piece))
        }

        if (++col >= board.size) {
          break
        }
      }

      if (++row >= board.size) {
        break
      }
    }

    return puzzle
  }
}

export default Formatter
