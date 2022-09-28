import { House, Cell, HouseKind } from './grid'
import Puzzle, { Variation } from './puzzle'

export const enum DeduceRule {
  Naked = 'naked',
  Hidden = 'hidden',
  Linked = 'linked',
  Guess = 'guess',
}

export abstract class DeduceEvidence {
  constructor(public readonly rule: DeduceRule, public readonly level: number) {}
}

export class NakedEvidence extends DeduceEvidence {
  constructor(
    level: number,
    public readonly house: House,
    public readonly cells: readonly Cell[],
    public readonly values: readonly number[]
  ) {
    super(DeduceRule.Naked, level)
  }
}

export class HiddenEvidence extends DeduceEvidence {
  constructor(
    level: number,
    public readonly house: House,
    public readonly values: readonly number[],
    public readonly cells: readonly Cell[]
  ) {
    super(DeduceRule.Hidden, level)
  }
}

export class LinkedEvidence extends DeduceEvidence {
  constructor(
    level: number,
    public readonly value: number,
    public readonly kind: HouseKind,
    public readonly orthKind: HouseKind,
    public readonly indices: readonly number[],
    public readonly orthIndices: readonly number[]
  ) {
    super(DeduceRule.Linked, level)
  }
}

export class GuessEvidence extends DeduceEvidence {
  constructor(
    level: number,
    public readonly cell: Cell,
    public readonly candidates: readonly number[],
    public readonly value: number
  ) {
    super(DeduceRule.Guess, level)
  }
}

export class ParadoxError extends Error {
  constructor(public readonly evidence: DeduceEvidence) {
    super(`Paradox found by rule ${evidence.rule}@${evidence.level}.`)
    this.name = 'ParadoxError'
  }
}

export class StopSearchingError extends Error {
  constructor() {
    super('Stop searching.')
    this.name = 'StopSearchingError'
  }
}

export type SolvingStep = {
  readonly evidence: DeduceEvidence
  readonly mutations: readonly Variation[]
  readonly puzzle: Puzzle
}
