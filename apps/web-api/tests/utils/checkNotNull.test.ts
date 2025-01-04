import checkNotNull from '../../src/utils/checkNotNull'

describe('checkNotNull', () => {
  it('should throw an error given null', () => {
    const item: string | null = null

    expect(() => checkNotNull(item)).toThrow('Item is null')
  })

  it('should throw an error given undefined', () => {
    const item: string | undefined = undefined

    expect(() => checkNotNull(item)).toThrow('Item is null')
  })

  it('should return the item given not null and not undefined', () => {
    const item: string | undefined = 'Item'

    expect(checkNotNull(item)).toEqual('Item')
  })
})
