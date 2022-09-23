import _ from 'lodash'

export type ValuesParam = number | readonly number[] | ValueSet

export default class ValueSet {
  protected values: number[]

  constructor(values?: ValuesParam, capacity?: number) {
    if (values !== undefined) {
      this.values = Array.from(ValueSet.normalizeValues(values))
    } else if (capacity !== undefined) {
      this.values = _.range(capacity)
    } else {
      this.values = new Array<number>()
    }
  }

  get size(): number {
    return this.values.length
  }

  peek(): number {
    return this.values[0]
  }

  [Symbol.iterator]() {
    return this.values.values()
  }

  asArray(): number[] {
    return this.values
  }

  static normalizeValues(values: ValuesParam): readonly number[] {
    if (typeof values === 'number') {
      return [values]
    } else if (values instanceof ValueSet) {
      return values.values
    } /* ReadonlyArray<number> */ else {
      return values
    }
  }

  contains(value: number): boolean {
    return _.includes(this.values, value)
  }

  containsAny(values: ValuesParam): boolean {
    values = ValueSet.normalizeValues(values)
    return values.some(value => this.contains(value))
  }

  containsAll(values: ValuesParam): boolean {
    values = ValueSet.normalizeValues(values)
    return values.every(value => this.contains(value))
  }

  /**
   * Merges given values, i.e. this ∪= values.
   * @param values
   * @returns An array of added values, i.e. values - this.
   */
  merge(values: ValuesParam): number[] {
    values = ValueSet.normalizeValues(values)
    const added = _.difference(values, this.values)
    if (added.length > 0) {
      this.values = _.union(this.values, added)
    }
    return added
  }

  /**
   * Removes given values, i.e. this -= values.
   * @param values
   * @returns An array of removed values, i.e. this ∩ values.
   */
  remove(values: ValuesParam): number[] {
    values = ValueSet.normalizeValues(values)
    const removed = _.intersection(this.values, values)
    if (removed.length > 0) {
      _.pullAll(this.values, removed)
    }
    return removed
  }

  /**
   * Keeps given values only, removes all other values, i.e. this ∩= values.
   * @param values
   * @returns An array of removed values, i.e. this - values.
   */
  retain(values: ValuesParam): number[] {
    // Keep the given values only, remove all other values.
    // Returns removed values.
    values = ValueSet.normalizeValues(values)
    const removed = _.difference(this.values, values)
    if (removed.length > 0) {
      _.pullAll(this.values, removed)
    }
    return removed
  }
}
