
export const enum AreaKind {
  Row = 'row',
  Column = 'column',
  Block = 'block',
}

export interface Cell {
  readonly row: number
  readonly col: number
}

export interface Area {
  readonly kind: AreaKind
  readonly index: number
}

export default class Board {
  readonly size: number
  readonly cellCount: number

  constructor(public readonly blockHeight = 3, public readonly blockWidth = 3) {
    this.size = blockHeight * blockWidth
    this.cellCount = this.size * this.size
  }

  indexOf(cell: Cell): number {
    return this.size * cell.row + cell.col
  }

  blockIndexOf(cell: Cell): number {
    return this.blockHeight * Math.floor(cell.row / this.blockHeight)
      + Math.floor(cell.col / this.blockWidth)
  }

  areaOf(cell: Cell, kind: AreaKind): Area {
    switch (kind) {
      case AreaKind.Row:
        return { kind, index: cell.row }
      case AreaKind.Column:
        return { kind, index: cell.col }
      case AreaKind.Block:
        return { kind, index: this.blockIndexOf(cell) }
    }
  }

  intersectCellOf(kind: AreaKind, index: number, orthIndex: number): Cell {
    switch (kind) {
      case AreaKind.Row:
        return { row: index, col: orthIndex }
      case AreaKind.Column:
        return { row: orthIndex, col: index }
      default:
        throw new Error(`Cannot intersect ${kind} with any other area kind.`)
    }
  }

  *iterCells(area?: Area, excludes?: Cell[]): Generator<Cell> {
    let minRow = 0, minCol = 0, maxRow = this.size - 1, maxCol = this.size - 1
    switch (area?.kind) {
      case AreaKind.Row:
        minRow = maxRow = area.index
        break
      case AreaKind.Column:
        minCol = maxCol = area.index
        break
      case AreaKind.Block:
        minRow = this.blockHeight * Math.floor(area.index / this.blockHeight)
        minCol = this.blockWidth * (area.index % this.blockHeight)
        maxRow = minRow + this.blockHeight - 1
        maxCol = minCol + this.blockWidth - 1
        break
    }

    const blacklist = new Set((excludes ?? []).map(cell => this.indexOf(cell)))

    for (let row = minRow; row <= maxRow; ++row) {
      for (let col = minCol; col <= maxCol; ++col) {
        const cell = { row, col }
        if (!blacklist.has(this.indexOf(cell))) {
          yield cell
        }
      }
    }
  }

  *iterAreas(kind?: AreaKind): Generator<Area> {
    const kinds = (kind === undefined) ? [AreaKind.Row, AreaKind.Column, AreaKind.Block] : [kind]
    for (kind of kinds) {
      for (let index = 0; index < this.size; ++index) {
        yield { kind, index }
      }
    }
  }

  // *iterSurroundedAreas(cell: Cell): Generator<Area> {
  //   const kinds = [AreaKind.Row, AreaKind.Column, AreaKind.Block]
  //   for (const kind of kinds) {
  //     yield this.areaOf(cell, kind)
  //   }
  // }

  commonAreasOf(cells: Cell[], exclude?: AreaKind): Area[] {
    const areas = new Array<Area>()

    const { row, col } = cells[0]
    if (exclude !== AreaKind.Row && cells.every(cell => cell.row === row)) {
      areas.push({ kind: AreaKind.Row, index: row })
    }
    if (exclude !== AreaKind.Column && cells.every(cell => cell.col === col)) {
      areas.push({ kind: AreaKind.Column, index: col })
    }

    const index = this.blockIndexOf(cells[0])
    if (exclude !== AreaKind.Block && cells.every(cell => this.blockIndexOf(cell) === index)) {
      areas.push({ kind: AreaKind.Block, index })
    }

    return areas
  }
}
