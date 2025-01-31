/** Represents the ID of the media item in the database. */
export type MediaItemId = {
  /** The ID of the database client */
  clientId: string;

  /** The ID of the object stored in the database */
  objectId: string;
};

/** Represents a media item in the database */
export type MediaItem = {
  /** The ID of the media item. */
  id: MediaItemId;

  /** The file name of the media item. */
  file_name: string;

  /** The hash code of the media item. */
  hash_code?: string;

  /** The GPS location of the media item. */
  location?: GpsLocation;

  /** The ID of the Google Photos account that its stored on. */
  gphotos_client_id: string;

  /** The ID of the media item that is stored in Google Photos. */
  gphotos_media_item_id: string;
};

/** Represents a GPS location. */
export type GpsLocation = {
  /** Represents the latitude of a GPS location. */
  latitude: number;

  /** Represents the longitude of a GPS location. */
  longitude: number;
};
