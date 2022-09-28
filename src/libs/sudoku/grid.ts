export const enum HouseKind {
  Row = 'row',
  Column = 'column',
  Box = 'box',
}

export type Cell = {
  readonly row: number
  readonly col: number
}

export type House = {
  readonly kind: HouseKind
  readonly index: number
}

export default class Grid {
  readonly size: number
  readonly cellCount: number

  constructor(public readonly boxHeight = 3, public readonly boxWidth = 3) {
    this.size = boxHeight * boxWidth
    this.cellCount = this.size * this.size
  }

  indexOf(cell: Cell): number {
    return this.size * cell.row + cell.col
  }

  boxIndexOf(cell: Cell): number {
    return this.boxHeight * Math.floor(cell.row / this.boxHeight) + Math.floor(cell.col / this.boxWidth)
  }

  houseOf(cell: Cell, kind: HouseKind): House {
    switch (kind) {
      case HouseKind.Row:
        return { kind, index: cell.row }
      case HouseKind.Column:
        return { kind, index: cell.col }
      case HouseKind.Box:
        return { kind, index: this.boxIndexOf(cell) }
    }
  }

  orthogonalKindOf(kind: HouseKind): HouseKind | undefined {
    switch (kind) {
      case HouseKind.Row:
        return HouseKind.Column
      case HouseKind.Column:
        return HouseKind.Row
    }
  }

  intersectCellOf(kind: HouseKind, index: number, orthIndex: number): Cell {
    switch (kind) {
      case HouseKind.Row:
        return { row: index, col: orthIndex }
      case HouseKind.Column:
        return { row: orthIndex, col: index }
      default:
        throw new Error(`Cannot intersect ${kind} with any other house kind.`)
    }
  }

  *iterCells(house?: House, excludes?: readonly Cell[]): Generator<Cell> {
    let minRow = 0,
      minCol = 0,
      maxRow = this.size - 1,
      maxCol = this.size - 1
    switch (house?.kind) {
      case HouseKind.Row:
        minRow = maxRow = house.index
        break
      case HouseKind.Column:
        minCol = maxCol = house.index
        break
      case HouseKind.Box:
        minRow = this.boxHeight * Math.floor(house.index / this.boxHeight)
        minCol = this.boxWidth * (house.index % this.boxHeight)
        maxRow = minRow + this.boxHeight - 1
        maxCol = minCol + this.boxWidth - 1
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

  *iterHouses(kind?: HouseKind): Generator<House> {
    const kinds = kind === undefined ? [HouseKind.Row, HouseKind.Column, HouseKind.Box] : [kind]
    for (kind of kinds) {
      for (let index = 0; index < this.size; ++index) {
        yield { kind, index }
      }
    }
  }

  // *iterSurroundedHouses(cell: Cell): Generator<House> {
  //   const kinds = [HouseKind.Row, HouseKind.Column, HouseKind.Box]
  //   for (const kind of kinds) {
  //     yield this.houseOf(cell, kind)
  //   }
  // }

  commonHousesOf(cells: readonly Cell[], exclude?: HouseKind): House[] {
    const houses = new Array<House>()

    const { row, col } = cells[0]
    if (exclude !== HouseKind.Row && cells.every(cell => cell.row === row)) {
      houses.push({ kind: HouseKind.Row, index: row })
    }
    if (exclude !== HouseKind.Column && cells.every(cell => cell.col === col)) {
      houses.push({ kind: HouseKind.Column, index: col })
    }

    const index = this.boxIndexOf(cells[0])
    if (exclude !== HouseKind.Box && cells.every(cell => this.boxIndexOf(cell) === index)) {
      houses.push({ kind: HouseKind.Box, index })
    }

    return houses
  }
}
