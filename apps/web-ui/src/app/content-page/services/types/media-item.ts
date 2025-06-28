export type MediaItemDetailsApiResponse = MediaItem;

export interface MediaItem {
  id: string;
  fileName: string;
  hashCode: string;
  location?: MediaItemLocation;
  gPhotosMediaItemId: string;
  width: number;
  height: number;
  dateTaken: Date;
}

export interface MediaItemLocation {
  latitude: number;
  longitude: number;
}

export type RawMediaItemDetailsApiResponse = RawMediaItem;

export interface RawMediaItem {
  id: string;
  fileName: string;
  hashCode: string;
  location?: MediaItemLocation;
  gPhotosMediaItemId: string;
  width: number;
  height: number;
  dateTaken: string;
}
