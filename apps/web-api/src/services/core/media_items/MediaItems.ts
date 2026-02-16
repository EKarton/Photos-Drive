import { AlbumId } from '../albums/Albums';

/** Represents the ID of the media item in the database. */
export type MediaItemId = {
  /** The ID of the database client */
  clientId: string;

  /** The ID of the object stored in the database */
  objectId: string;
};

/** Converts a {@code MediaItemId} to a string. */
export function mediaIdToString(mediaId: MediaItemId): string {
  return `${mediaId.clientId}:${mediaId.objectId}`;
}

/** Converts a raw-value string from database to album ID. */
export function convertStringToMediaItemId(value: string): MediaItemId {
  const parts = value.split(':');
  if (parts.length == 2 && parts[0] && parts[1]) {
    return {
      clientId: parts[0],
      objectId: parts[1]
    };
  }

  throw new Error(`Cannot parse ${value} to media item ID`);
}

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

  /** The album ID that this media item belongs to. */
  album_id: AlbumId;

  /** The width of the media item. */
  width: number;

  /** The height of the media item. */
  height: number;

  /** The date and time that the media item was taken. */
  date_taken: Date;

  /** The mime type of the media item. */
  mime_type: string;
};

/** Represents a GPS location. */
export type GpsLocation = {
  /** Represents the latitude of a GPS location. */
  latitude: number;

  /** Represents the longitude of a GPS location. */
  longitude: number;
};
