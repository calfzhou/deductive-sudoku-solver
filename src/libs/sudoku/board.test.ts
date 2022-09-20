import Board, { AreaKind, Cell } from './board'

function buildCells(minRow: number, maxRow: number, minCol: number, maxCol: number): Cell[] {
  const cells = new Array<Cell>()
  for (let row = minRow; row <= maxRow; row++) {
    for (let col = minCol; col <= maxCol; col++) {
      cells.push({ row, col })
    }
  }
  return cells
}

describe('a 3x4 block board', () => {
  const board = new Board(3, 4)

  test('calcs size', () => {
    expect(board.size).toEqual(12)
    expect(board.cellCount).toEqual(144)
  })

  test("calcs cell's surrounded area", () => {
    expect(board.areaOf({ row: 0, col: 0 }, AreaKind.Row).index).toEqual(0)
    expect(board.areaOf({ row: 0, col: 7 }, AreaKind.Row).index).toEqual(0)
    expect(board.areaOf({ row: 5, col: 0 }, AreaKind.Row).index).toEqual(5)
    expect(board.areaOf({ row: 5, col: 7 }, AreaKind.Row).index).toEqual(5)

    expect(board.areaOf({ row: 0, col: 0 }, AreaKind.Column).index).toEqual(0)
    expect(board.areaOf({ row: 0, col: 7 }, AreaKind.Column).index).toEqual(7)
    expect(board.areaOf({ row: 5, col: 0 }, AreaKind.Column).index).toEqual(0)
    expect(board.areaOf({ row: 5, col: 7 }, AreaKind.Column).index).toEqual(7)

    expect(board.areaOf({ row: 0, col: 0 }, AreaKind.Block).index).toEqual(0)
    expect(board.areaOf({ row: 0, col: 7 }, AreaKind.Block).index).toEqual(1)
    expect(board.areaOf({ row: 5, col: 0 }, AreaKind.Block).index).toEqual(3)
    expect(board.areaOf({ row: 5, col: 7 }, AreaKind.Block).index).toEqual(4)
  })

  // test("iters cell's surrounded areas", () => {
  //   expect(Array.from(board.iterSurroundedAreas({ row: 0, col: 0 }))).toEqual([
  //     { kind: AreaKind.Row, index: 0 }, { kind: AreaKind.Column, index: 0 }, { kind: AreaKind.Block, index: 0 },
  //   ])
  //   expect(Array.from(board.iterSurroundedAreas({ row: 0, col: 7 }))).toEqual([
  //     { kind: AreaKind.Row, index: 0 }, { kind: AreaKind.Column, index: 7 }, { kind: AreaKind.Block, index: 1 },
  //   ])
  //   expect(Array.from(board.iterSurroundedAreas({ row: 5, col: 0 }))).toEqual([
  //     { kind: AreaKind.Row, index: 5 }, { kind: AreaKind.Column, index: 0 }, { kind: AreaKind.Block, index: 3 },
  //   ])
  //   expect(Array.from(board.iterSurroundedAreas({ row: 5, col: 7 }))).toEqual([
  //     { kind: AreaKind.Row, index: 5 }, { kind: AreaKind.Column, index: 7 }, { kind: AreaKind.Block, index: 4 },
  //   ])
  // })

  test('iters all cells', () => {
    expect(Array.from(board.iterCells())).toEqual(buildCells(0, 11, 0, 11))
  })

  test('iters row cells', () => {
    expect(Array.from(board.iterCells({ kind: AreaKind.Row, index: 0 }))).toEqual(buildCells(0, 0, 0, 11))
    expect(Array.from(board.iterCells({ kind: AreaKind.Row, index: 11 }))).toEqual(buildCells(11, 11, 0, 11))
  })

  test('iters column cells', () => {
    expect(Array.from(board.iterCells({ kind: AreaKind.Column, index: 0 }))).toEqual(buildCells(0, 11, 0, 0))
    expect(Array.from(board.iterCells({ kind: AreaKind.Column, index: 11 }))).toEqual(buildCells(0, 11, 11, 11))
  })

  test('iters block cells', () => {
    expect(Array.from(board.iterCells({ kind: AreaKind.Block, index: 0 }))).toEqual(buildCells(0, 2, 0, 3))
    expect(Array.from(board.iterCells({ kind: AreaKind.Block, index: 1 }))).toEqual(buildCells(0, 2, 4, 7))
    expect(Array.from(board.iterCells({ kind: AreaKind.Block, index: 2 }))).toEqual(buildCells(0, 2, 8, 11))
    expect(Array.from(board.iterCells({ kind: AreaKind.Block, index: 3 }))).toEqual(buildCells(3, 5, 0, 3))
    expect(Array.from(board.iterCells({ kind: AreaKind.Block, index: 6 }))).toEqual(buildCells(6, 8, 0, 3))
    expect(Array.from(board.iterCells({ kind: AreaKind.Block, index: 9 }))).toEqual(buildCells(9, 11, 0, 3))
    expect(Array.from(board.iterCells({ kind: AreaKind.Block, index: 10 }))).toEqual(buildCells(9, 11, 4, 7))
  })

  test('iters areas', () => {
    const areas = []
    for (let index = 0; index < board.size; ++index) {
      areas.push({ kind: AreaKind.Row, index })
    }
    for (let index = 0; index < board.size; ++index) {
      areas.push({ kind: AreaKind.Column, index })
    }
    for (let index = 0; index < board.size; ++index) {
      areas.push({ kind: AreaKind.Block, index })
    }
    expect(Array.from(board.iterAreas())).toEqual(areas)
  })
})
