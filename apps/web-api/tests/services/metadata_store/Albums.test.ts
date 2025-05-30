import { convertStringToAlbumId } from '../../../src/services/metadata_store/Albums';

describe('convertStringToAlbumId', () => {
  it('should parse a valid string into an AlbumId object', () => {
    const input = 'clientX:albumY';
    const expected = { clientId: 'clientX', objectId: 'albumY' };

    expect(convertStringToAlbumId(input)).toEqual(expected);
  });

  it('should throw an error if the string is missing ":"', () => {
    const input = 'clientXalbumY';
    expect(() => convertStringToAlbumId(input)).toThrow(
      `Cannot parse ${input} to album ID`
    );
  });

  it('should throw an error if objectId is empty', () => {
    const input = 'clientX:';
    expect(() => convertStringToAlbumId(input)).toThrow(
      `Cannot parse ${input} to album ID`
    );
  });

  it('should throw an error if clientId is empty', () => {
    const input = ':albumY';
    expect(() => convertStringToAlbumId(input)).toThrow(
      `Cannot parse ${input} to album ID`
    );
  });

  it('should throw an error if both clientId and objectId are empty', () => {
    const input = ':';
    expect(() => convertStringToAlbumId(input)).toThrow(
      `Cannot parse ${input} to album ID`
    );
  });

  it('should throw an error if there are more than two parts', () => {
    const input = 'clientX:albumY:extra';
    expect(() => convertStringToAlbumId(input)).toThrow(
      `Cannot parse ${input} to album ID`
    );
  });
});
