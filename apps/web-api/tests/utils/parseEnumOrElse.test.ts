import parseEnumElse from '../../src/utils/parseEnumOrElse';

enum TestStringEnum {
  FOO = 'foo',
  BAR = 'bar'
}

enum TestNumberEnum {
  ONE = 1,
  TWO = 2
}

describe('parseEnumValueOrElse', () => {
  describe('string enum', () => {
    it('returns the correct enum value when matched', () => {
      expect(parseEnumElse(TestStringEnum, 'foo', TestStringEnum.BAR)).toBe(
        TestStringEnum.FOO
      );
      expect(parseEnumElse(TestStringEnum, 'bar', TestStringEnum.FOO)).toBe(
        TestStringEnum.BAR
      );
    });

    it('returns the default when value does not match', () => {
      expect(parseEnumElse(TestStringEnum, 'baz', TestStringEnum.FOO)).toBe(
        TestStringEnum.FOO
      );
      expect(parseEnumElse(TestStringEnum, 123, TestStringEnum.FOO)).toBe(
        TestStringEnum.FOO
      );
      expect(parseEnumElse(TestStringEnum, undefined, TestStringEnum.FOO)).toBe(
        TestStringEnum.FOO
      );
      expect(parseEnumElse(TestStringEnum, null, TestStringEnum.FOO)).toBe(
        TestStringEnum.FOO
      );
    });
  });

  describe('number enum', () => {
    it('returns the correct enum value when matched', () => {
      expect(parseEnumElse(TestNumberEnum, 1, TestNumberEnum.TWO)).toBe(
        TestNumberEnum.ONE
      );
      expect(parseEnumElse(TestNumberEnum, 2, TestNumberEnum.ONE)).toBe(
        TestNumberEnum.TWO
      );
    });

    it('returns the default when value does not match', () => {
      expect(parseEnumElse(TestNumberEnum, 3, TestNumberEnum.ONE)).toBe(
        TestNumberEnum.ONE
      );
      expect(parseEnumElse(TestNumberEnum, '1', TestNumberEnum.ONE)).toBe(
        TestNumberEnum.ONE
      );
      expect(parseEnumElse(TestNumberEnum, undefined, TestNumberEnum.ONE)).toBe(
        TestNumberEnum.ONE
      );
    });
  });

  describe('mixed values', () => {
    enum MixedEnum {
      STRING = 'stringValue',
      NUMBER = 100
    }

    it('handles mixed value enums correctly', () => {
      expect(parseEnumElse(MixedEnum, 'stringValue', MixedEnum.NUMBER)).toBe(
        MixedEnum.STRING
      );
      expect(parseEnumElse(MixedEnum, 100, MixedEnum.STRING)).toBe(
        MixedEnum.NUMBER
      );
      expect(parseEnumElse(MixedEnum, 'nonexistent', MixedEnum.NUMBER)).toBe(
        MixedEnum.NUMBER
      );
    });
  });
});
