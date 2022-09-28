import _ from 'lodash'
import pluralize from 'pluralize'

import Grid, { Cell } from './grid'
import { GuessEvidence, HiddenEvidence, LinkedEvidence, NakedEvidence, SolvingStep } from './deduce-info'
import ValueSet, { ValuesParam } from './value-set'
import Puzzle from './puzzle'

export default class Formatter {
  readonly markers: readonly string[]
  readonly mapping = new Map<string, number>()
  readonly maxLength: number
  readonly multiChar: boolean

  static readonly defaultMarkers = _.range(1, 37).map(i => (i % 36).toString(36).toUpperCase())

  constructor(markers?: string | readonly string[]) {
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
    if (values.length === 0) {
      return '[]'
    }

    const sep = this.multiChar ? ' ' : ''

    if (capacity !== undefined) {
      if (values.length === capacity) {
        return '*'
      } else if (values.length >= capacity / 2 + 1) {
        const text = new ValueSet(undefined, capacity)
          .retain(values)
          .map(v => this.markers[v])
          .join(sep)
        return `[^${text}]`
      }
    }

    const text = values.map(v => this.markers[v]).join(sep)
    return values.length > 1 ? `[${text}]` : text
  }

  formatPuzzle(puzzle: Puzzle, border = false): string {
    return border ? this.formatPuzzleWithBorder(puzzle) : this.formatPuzzleSimple(puzzle)
  }

  protected formatPuzzleSimple(puzzle: Puzzle): string {
    const grid = puzzle.grid
    const rowPieces = _.times(grid.size, () => new Array<string>())

    let prevMaxWidth = 0
    for (const col of _.range(grid.size)) {
      let maxWidth = 0
      for (const row of _.range(grid.size)) {
        const pieces = rowPieces[row]

        const prevWidth = _.last(pieces)?.length ?? 0
        if (prevMaxWidth > prevWidth) {
          pieces.push(' '.repeat(prevMaxWidth - prevWidth))
        }

        if (col > 0 && col % grid.boxWidth === 0) {
          pieces.push(' ')
        }

        const candidates = puzzle.candidates({ row, col })
        const text = this.formatValues(candidates, grid.size)
        pieces.push(text)
        maxWidth = Math.max(maxWidth, text.length)
      }
      prevMaxWidth = Math.max(maxWidth, this.maxLength + 1)
    }

    const lines = new Array<string>()
    for (const row of _.range(grid.size)) {
      if (row > 0 && row % grid.boxHeight === 0) {
        lines.push('')
      }
      lines.push(rowPieces[row].join(''))
    }

    return lines.join('\n')
  }

  protected formatPuzzleWithBorder(puzzle: Puzzle): string {
    const grid = puzzle.grid
    const lines = new Array<string>()

    for (const row of _.range(grid.size)) {
      lines.push(this.formatBorderLine(grid, row % grid.boxHeight === 0))
      for (const subRow of _.range(grid.boxHeight)) {
        const pieces = new Array<string>()
        for (const col of _.range(grid.size)) {
          pieces.push(col % grid.boxWidth === 0 ? '|' : ':')
          const candidates = puzzle.candidates({ row, col })
          for (const subCol of _.range(grid.boxWidth)) {
            const value = grid.boxWidth * subRow + subCol
            if (candidates.contains(value)) {
              pieces.push(this.markers[value].padStart(this.maxLength))
            } else {
              pieces.push(' ')
            }
          }
        }
        pieces.push('|')
        lines.push(pieces.join(' '))
      }
    }

    lines.push(this.formatBorderLine(grid, true))
    return lines.join('\n')
  }

  protected formatBorderLine(grid: Grid, major = true): string {
    const gap = major ? '-' : ' '
    const fence = '+'
    const cellLine = _.times(grid.boxWidth * this.maxLength, _.constant('-')).join(gap)
    const gridLine = _.times(grid.size, _.constant(cellLine)).join(`${gap}${fence}${gap}`)
    return `${fence}${gap}${gridLine}${gap}${fence}`
  }

  formatSolvingStep(step: SolvingStep, showMutations = true, indent = 0): string {
    const formatCells = (cells: readonly Cell[], inclusive = true) => {
      return [
        pluralize('cell', cells.length, inclusive),
        cells.length > 1 ? ' [' : ' ',
        cells.map(cell => `r${cell.row + 1}c${cell.col + 1}`).join(', '),
        cells.length > 1 ? ']' : '',
      ].join('')
    }
    const formatValues = (values: readonly number[], word = 'value', inclusive = true) => {
      return [
        pluralize(word, values.length, inclusive),
        values.length > 1 ? ' [' : ' ',
        values.map(value => `'${this.markers[value]}'`).join(', '),
        values.length > 1 ? ']' : '',
      ].join('')
    }
    const formatIndices = (indices: readonly number[], word = 'index', inclusive = true) => {
      return [
        pluralize(word, indices.length, inclusive),
        indices.length > 1 ? ' [' : ' ',
        indices.map(index => index + 1).join(', '),
        indices.length > 1 ? ']' : '',
      ].join('')
    }

    const lines = new Array<string>()

    const evidence = step.evidence
    const paradoxical = step.mutations.length === 0

    let pieces = new Array<string>()
    pieces.push('> '.repeat(indent))
    paradoxical && pieces.push('[paradox] ')
    pieces.push(`[${evidence.rule}@${evidence.level}]`)
    if (evidence instanceof NakedEvidence) {
      pieces.push(' ')
      pieces.push(formatCells(evidence.cells, false))
      pieces.push(' have ')
      pieces.push(formatValues(evidence.values, 'candidate'))
    } else if (evidence instanceof HiddenEvidence) {
      pieces.push(` [${evidence.house.kind} ${evidence.house.index + 1}] `)
      pieces.push(formatValues(evidence.values, 'value', false))
      pieces.push(' appear in ')
      pieces.push(formatCells(evidence.cells))
    } else if (evidence instanceof LinkedEvidence) {
      pieces.push(` [candidate '${this.markers[evidence.value]}'] from `)
      pieces.push(formatIndices(evidence.indices, evidence.kind, false))
      pieces.push(' appear in ')
      pieces.push(formatIndices(evidence.orthIndices, evidence.orthKind))
    } else if (evidence instanceof GuessEvidence) {
      pieces.push(` [cell r${evidence.cell.row + 1}c${evidence.cell.col + 1}] has `)
      pieces.push(formatValues(evidence.candidates, 'value'))
      pieces.push(`, choose '${this.markers[evidence.value]}'`)
    }

    let stepPrefix = ' '
    if (step.mutations.length !== 1 || !showMutations) {
      lines.push(pieces.join(''))
      pieces = new Array<string>()
      stepPrefix = '  '.repeat(indent + 1)
    }

    if (showMutations) {
      for (const { cell, removed } of step.mutations) {
        pieces.push(stepPrefix)
        pieces.push(`=> cell r${cell.row + 1}c${cell.col + 1} remove `)
        pieces.push(formatValues(removed, 'candidates', false))
        lines.push(pieces.join(''))
        pieces = new Array<string>()
      }
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

  parsePuzzle(lines: Iterable<string>, grid: Grid): Puzzle {
    if (grid.size > this.markers.length) {
      throw new Error(`The grid is too big for this formatter (${grid.size} > ${this.markers.length}).`)
    }

    const puzzle = new Puzzle(grid)

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

        if (++col >= grid.size) {
          break
        }
      }

      if (++row >= grid.size) {
        break
      }
    }

    return puzzle
  }
}
