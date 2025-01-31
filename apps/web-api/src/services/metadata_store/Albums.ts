import { MediaItemId } from './MediaItems';

/** Represents an album ID in the database. */
export type AlbumId = {
  /** The ID of the database client */
  clientId: string;

  /** The ID of the object stored in the database */
  objectId: string;
};

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

  /** A list of media item IDs in this album. */
  media_item_ids: MediaItemId[];
};
