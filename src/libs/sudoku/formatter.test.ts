import Formatter from './formatter'

describe('formatter splits line to columns', () => {
  test('single-char normal', () => {
    const formatter = new Formatter()
    // @ts-ignore
    const cols = formatter.splitMarkers('2*8**6**7')
    expect(Array.from(cols)).toEqual(Array.from('2*8**6**7'))
  })

  test('single-char with squares', () => {
    const formatter = new Formatter()
    // @ts-ignore
    const cols = formatter.splitMarkers('5***[8 9][]**[^3]7')
    expect(Array.from(cols)).toEqual([
      '5', '*', '*', '*', '[8 9]', '[]', '*', '*', '[^3]', '7'
    ])
  })
})
