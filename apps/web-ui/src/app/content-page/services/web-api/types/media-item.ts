export interface RawMediaItem {
  id: string;
  fileName: string;
  hashCode: string;
  location?: GpsLocation;
  gPhotosMediaItemId: string;
  width: number;
  height: number;
  dateTaken: string;
}

export type RawMediaItemDetailsApiResponse = RawMediaItem;

export interface MediaItem {
  id: string;
  fileName: string;
  hashCode: string;
  location?: GpsLocation;
  gPhotosMediaItemId: string;
  width: number;
  height: number;
  dateTaken: Date;
}

export type MediaItemDetailsApiResponse = MediaItem;

export interface GpsLocation {
  latitude: number;
  longitude: number;
}
