/**
 * Parses a value to an enum. If it doesn't match it will return the default value.
 *
 * @param enumObj The enum object.
 * @param value The value to parse.
 * @param defaultValue The default enum value.
 * @returns The enum, or the default value.
 */
export default function parseEnumValue<
  T extends Record<string, string | number>
>(enumObj: T, value: unknown, defaultValue: T[keyof T]): T[keyof T] {
  const enumValues = Object.keys(enumObj)
    .filter((key) => isNaN(Number(key))) // exclude reverse-mapped numeric keys
    .map((key) => enumObj[key as keyof T]);

  return enumValues.includes(value as T[keyof T])
    ? (value as T[keyof T])
    : defaultValue;
}
