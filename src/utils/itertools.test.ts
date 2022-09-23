import _ from 'lodash'

import { combinations, PruningReducer } from './itertools'

describe('combinations', () => {
  test('(ABCD, 2)', () => {
    expect(Array.from(combinations('ABCD', 2))).toEqual([
      ['A', 'B'],
      ['A', 'C'],
      ['A', 'D'],
      ['B', 'C'],
      ['B', 'D'],
      ['C', 'D'],
    ])
  })

  test('(4, 3)', () => {
    expect(Array.from(combinations(_.range(4), 3))).toEqual([
      [0, 1, 2],
      [0, 1, 3],
      [0, 2, 3],
      [1, 2, 3],
    ])
  })

  test('pruning everything', () => {
    const pruning: PruningReducer<unknown, unknown> = () => [true]
    expect(Array.from(combinations(_.range(4), 3, pruning))).toHaveLength(0)
  })

  test('pruning odd numbers', () => {
    const pruning: PruningReducer<number, unknown> = currElem => [currElem % 2 === 1]
    const odds = _.range(1, 10, 2)

    const result = Array.from(combinations(_.range(10), 3, pruning))
    result.forEach(selection => {
      expect(selection).toHaveLength(3)
      expect(selection).toEqual(expect.not.arrayContaining(odds))
    })
    expect(result).toHaveLength(10)
  })

  test('pruning if sum > 10', () => {
    const pruning: PruningReducer<number, number> = (currELem, accumulation?) => {
      accumulation = accumulation ?? 0
      accumulation += currELem
      return [accumulation > 10, accumulation]
    }

    const result = Array.from(combinations(_.range(10), 3, pruning))
    result.forEach(selection => {
      expect(selection).toHaveLength(3)
      expect(_.sum(selection)).toBeLessThanOrEqual(10)
    })
    expect(result).toHaveLength(31)
  })
})
