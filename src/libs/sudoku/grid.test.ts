import Grid, { HouseKind, Cell } from './grid'

function buildCells(minRow: number, maxRow: number, minCol: number, maxCol: number): Cell[] {
  const cells = new Array<Cell>()
  for (let row = minRow; row <= maxRow; row++) {
    for (let col = minCol; col <= maxCol; col++) {
      cells.push({ row, col })
    }
  }
  return cells
}

describe('a 3x4 box grid', () => {
  const grid = new Grid(3, 4)

  test('calcs size', () => {
    expect(grid.size).toEqual(12)
    expect(grid.cellCount).toEqual(144)
  })

  test("calcs cell's surrounded house", () => {
    expect(grid.houseOf({ row: 0, col: 0 }, HouseKind.Row).index).toEqual(0)
    expect(grid.houseOf({ row: 0, col: 7 }, HouseKind.Row).index).toEqual(0)
    expect(grid.houseOf({ row: 5, col: 0 }, HouseKind.Row).index).toEqual(5)
    expect(grid.houseOf({ row: 5, col: 7 }, HouseKind.Row).index).toEqual(5)

    expect(grid.houseOf({ row: 0, col: 0 }, HouseKind.Column).index).toEqual(0)
    expect(grid.houseOf({ row: 0, col: 7 }, HouseKind.Column).index).toEqual(7)
    expect(grid.houseOf({ row: 5, col: 0 }, HouseKind.Column).index).toEqual(0)
    expect(grid.houseOf({ row: 5, col: 7 }, HouseKind.Column).index).toEqual(7)

    expect(grid.houseOf({ row: 0, col: 0 }, HouseKind.Box).index).toEqual(0)
    expect(grid.houseOf({ row: 0, col: 7 }, HouseKind.Box).index).toEqual(1)
    expect(grid.houseOf({ row: 5, col: 0 }, HouseKind.Box).index).toEqual(3)
    expect(grid.houseOf({ row: 5, col: 7 }, HouseKind.Box).index).toEqual(4)
  })

  // test("iters cell's surrounded houses", () => {
  //   expect(Array.from(grid.iterSurroundedHouses({ row: 0, col: 0 }))).toEqual([
  //     { kind: HouseKind.Row, index: 0 }, { kind: HouseKind.Column, index: 0 }, { kind: HouseKind.Box, index: 0 },
  //   ])
  //   expect(Array.from(grid.iterSurroundedHouses({ row: 0, col: 7 }))).toEqual([
  //     { kind: HouseKind.Row, index: 0 }, { kind: HouseKind.Column, index: 7 }, { kind: HouseKind.Box, index: 1 },
  //   ])
  //   expect(Array.from(grid.iterSurroundedHouses({ row: 5, col: 0 }))).toEqual([
  //     { kind: HouseKind.Row, index: 5 }, { kind: HouseKind.Column, index: 0 }, { kind: HouseKind.Box, index: 3 },
  //   ])
  //   expect(Array.from(grid.iterSurroundedHouses({ row: 5, col: 7 }))).toEqual([
  //     { kind: HouseKind.Row, index: 5 }, { kind: HouseKind.Column, index: 7 }, { kind: HouseKind.Box, index: 4 },
  //   ])
  // })

  test('iters all cells', () => {
    expect(Array.from(grid.iterCells())).toEqual(buildCells(0, 11, 0, 11))
  })

  test('iters row cells', () => {
    expect(Array.from(grid.iterCells({ kind: HouseKind.Row, index: 0 }))).toEqual(buildCells(0, 0, 0, 11))
    expect(Array.from(grid.iterCells({ kind: HouseKind.Row, index: 11 }))).toEqual(buildCells(11, 11, 0, 11))
  })

  test('iters column cells', () => {
    expect(Array.from(grid.iterCells({ kind: HouseKind.Column, index: 0 }))).toEqual(buildCells(0, 11, 0, 0))
    expect(Array.from(grid.iterCells({ kind: HouseKind.Column, index: 11 }))).toEqual(buildCells(0, 11, 11, 11))
  })

  test('iters box cells', () => {
    expect(Array.from(grid.iterCells({ kind: HouseKind.Box, index: 0 }))).toEqual(buildCells(0, 2, 0, 3))
    expect(Array.from(grid.iterCells({ kind: HouseKind.Box, index: 1 }))).toEqual(buildCells(0, 2, 4, 7))
    expect(Array.from(grid.iterCells({ kind: HouseKind.Box, index: 2 }))).toEqual(buildCells(0, 2, 8, 11))
    expect(Array.from(grid.iterCells({ kind: HouseKind.Box, index: 3 }))).toEqual(buildCells(3, 5, 0, 3))
    expect(Array.from(grid.iterCells({ kind: HouseKind.Box, index: 6 }))).toEqual(buildCells(6, 8, 0, 3))
    expect(Array.from(grid.iterCells({ kind: HouseKind.Box, index: 9 }))).toEqual(buildCells(9, 11, 0, 3))
    expect(Array.from(grid.iterCells({ kind: HouseKind.Box, index: 10 }))).toEqual(buildCells(9, 11, 4, 7))
  })

  test('iters houses', () => {
    const houses = []
    for (let index = 0; index < grid.size; ++index) {
      houses.push({ kind: HouseKind.Row, index })
    }
    for (let index = 0; index < grid.size; ++index) {
      houses.push({ kind: HouseKind.Column, index })
    }
    for (let index = 0; index < grid.size; ++index) {
      houses.push({ kind: HouseKind.Box, index })
    }
    expect(Array.from(grid.iterHouses())).toEqual(houses)
  })
})
