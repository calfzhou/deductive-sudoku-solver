import _ from 'lodash'

import ValueSet from './value-set'

describe('create value set', () => {
  test('with a number', () => {
    expect(new ValueSet(3).asArray()).toEqual([3])
  })

  test('with an array of numbers', () => {
    expect(new ValueSet([1, 3, 5]).asArray()).toEqual([1, 3, 5])
  })

  test('to empty', () => {
    expect(new ValueSet().asArray()).toEqual([])
  })

  test('with the capacity', () => {
    expect(new ValueSet(undefined, 9).asArray()).toEqual(_.range(9))
  })
})

describe('a value set', () => {
  it('is iterable', () => {
    const valueSet = new ValueSet([1, 3, 5])
    const result = new Array<number>()
    for (const value of valueSet) {
      result.push(value)
    }
    expect(result).toEqual([1, 3, 5])
  })
})

describe('modify value set', () => {
  test('merges a number', () => {
    const valueSet = new ValueSet([1, 3, 5])
    expect(valueSet.merge(4)).toEqual([4])
    expect(valueSet.asArray()).toEqual([1, 3, 5, 4])
  })

  test('merges an exists number', () => {
    const valueSet = new ValueSet([1, 3, 5])
    expect(valueSet.merge(3)).toEqual([])
    expect(valueSet.asArray()).toEqual([1, 3, 5])
  })

  test('merges an array of numbers', () => {
    const valueSet = new ValueSet([1, 3, 5])
    expect(valueSet.merge([3, 4, 5, 6])).toEqual([4, 6])
    expect(valueSet.asArray()).toEqual([1, 3, 5, 4, 6])
  })

  test('removes a number', () => {
    const valueSet = new ValueSet([1, 3, 5])
    expect(valueSet.remove(3)).toEqual([3])
    expect(valueSet.asArray()).toEqual([1, 5])
  })

  test('removes a not exists number', () => {
    const valueSet = new ValueSet([1, 3, 5])
    expect(valueSet.remove(4)).toEqual([])
    expect(valueSet.asArray()).toEqual([1, 3, 5])
  })

  test('removes an array of numbers', () => {
    const valueSet = new ValueSet([1, 3, 5])
    expect(valueSet.remove([3, 4, 5, 6])).toEqual([3, 5])
    expect(valueSet.asArray()).toEqual([1])
  })

  test('retains a number', () => {
    const valueSet = new ValueSet([1, 3, 5])
    expect(valueSet.retain(3)).toEqual([1, 5])
    expect(valueSet.asArray()).toEqual([3])
  })

  test('retains a not exists number', () => {
    const valueSet = new ValueSet([1, 3, 5])
    expect(valueSet.retain(4)).toEqual([1, 3, 5])
    expect(valueSet.asArray()).toEqual([])
  })

  test('retains an array of numbers', () => {
    const valueSet = new ValueSet([1, 3, 5])
    expect(valueSet.retain([3, 4, 5, 6])).toEqual([1])
    expect(valueSet.asArray()).toEqual([3, 5])
  })
})
