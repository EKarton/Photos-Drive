export default function checkNotNull<T>(item: T | null | undefined): T {
  if (item === null) {
    throw new Error('Item is null')
  }

  if (item === undefined) {
    throw new Error('Item is null')
  }

  return item
}
