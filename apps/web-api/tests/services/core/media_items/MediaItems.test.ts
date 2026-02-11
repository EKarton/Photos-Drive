import { convertStringToMediaItemId } from '../../../../src/services/core/media_items/MediaItems';

describe('convertStringToMediaItemId', () => {
  it('should parse a valid string into a MediaItemId object', () => {
    const input = 'abc123:def456';
    const expected = { clientId: 'abc123', objectId: 'def456' };

    expect(convertStringToMediaItemId(input)).toEqual(expected);
  });

  it('should throw an error if the string is missing ":"', () => {
    const input = 'abc123def456';
    expect(() => convertStringToMediaItemId(input)).toThrow(
      `Cannot parse ${input} to media item ID`
    );
  });

  it('should throw an error if the string has only one part', () => {
    const input = 'abc123:';
    expect(() => convertStringToMediaItemId(input)).toThrow(
      `Cannot parse ${input} to media item ID`
    );
  });

  it('should throw an error if the clientId is empty', () => {
    const input = ':def456';
    expect(() => convertStringToMediaItemId(input)).toThrow(
      `Cannot parse ${input} to media item ID`
    );
  });

  it('should throw an error if both clientId and objectId are empty', () => {
    const input = ':';
    expect(() => convertStringToMediaItemId(input)).toThrow(
      `Cannot parse ${input} to media item ID`
    );
  });

  it('should throw an error if there are more than 2 parts', () => {
    const input = 'abc:123:extra';
    expect(() => convertStringToMediaItemId(input)).toThrow(
      `Cannot parse ${input} to media item ID`
    );
  });
});
