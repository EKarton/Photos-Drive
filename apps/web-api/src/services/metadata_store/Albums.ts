/** Represents an album ID in the database. */
export type AlbumId = {
  /** The ID of the database client */
  clientId: string;

  /** The ID of the object stored in the database */
  objectId: string;
};

/** Converts a raw-value string from database to album ID. */
export function convertStringToAlbumId(value: string): AlbumId {
  const parts = value.split(':');
  if (parts.length == 2 && parts[0] && parts[1]) {
    return {
      clientId: parts[0],
      objectId: parts[1]
    };
  }

  throw new Error(`Cannot parse ${value} to album ID`);
}

/** Represents an album in the database. */
export type Album = {
  /** The album ID */
  id: AlbumId;

  /** The name of the album. */
  name: string;

  /** The parent album ID, if it exists. */
  parent_album_id?: AlbumId;

  /** The child album IDs. */
  child_album_ids: AlbumId[];
};
