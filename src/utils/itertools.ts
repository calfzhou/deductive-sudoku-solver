import _ from 'lodash'

export type PruningReducer<TElem, TAccum> = (
  currElem: TElem,
  accumulation: TAccum,
  currIndex: number,
  array: TElem[]
) => [stop: boolean, accumulation?: TAccum]

const noPruning: PruningReducer<any, any> = () => [false]

/**
 * Iterate `r` length subsequences of elements from the input `iterable`.
 * combinations('ABCD', 2) --> AB AC AD BC BD CD
 * combinations(range(4), 3) --> 012 013 023 123
 * @param iterable
 * @param r
 * @param pruning The pruning reduce function. It must be greedy.
 * @returns
 */
export function* combinations<TElem, TAccum>(
  iterable: Iterable<TElem>,
  r: number,
  pruning: PruningReducer<TElem, TAccum> = noPruning
): Generator<TElem[]> {
  const pool = Array.from(iterable)
  const n = pool.length
  if (r <= 0 || r > n) {
    return
  }

  const indices = new Array<number>()
  const helper = function* (accumulation?: any): Generator<TElem[]> {
    if (indices.length === r) {
      yield indices.map(i => pool[i])
    } else {
      const last = _.last(indices) ?? -1
      for (let i = last + 1; i < n; ++i) {
        const [stop, new_accumulation] = pruning(pool[i], accumulation, i, pool)
        if (!stop) {
          indices.push(i)
          yield* helper(new_accumulation)
          indices.pop()
        }
      }
    }
  }

  yield* helper()
}

export function count<TElem>(iterable: Iterable<TElem>) {
  let n = 0
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  for (const _elem of iterable) {
    ++n
  }
  return n
}


export type PredicateFunc<TElem> = (elem: TElem, index: number) => boolean

export function* filter<TElem>(iterable: Iterable<TElem>, predicate: PredicateFunc<TElem> = Boolean): Generator<TElem> {
  let index = 0
  for (const elem of iterable) {
    if (predicate(elem, index)) {
      yield elem
    }
    ++index
  }
}
