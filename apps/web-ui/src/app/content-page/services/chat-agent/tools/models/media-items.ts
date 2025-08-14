import { z } from 'zod';

import { MediaItem } from '../../../web-api/types/media-item';

// --- GPS Location Model ---
export const GpsLocationModelSchema = z.object({
  latitude: z.number().describe('Latitude in degrees'),
  longitude: z.number().describe('Longitude in degrees'),
});

export type GpsLocationModel = z.infer<typeof GpsLocationModelSchema>;

// --- Media Item Model ---
export const MediaItemModelSchema = z.object({
  id: z.string().describe('ID of this media item'),
  file_name: z.string().describe('File name of the media item'),
  location: GpsLocationModelSchema.optional().describe(
    'GPS location if available',
  ),
  gphotos_media_item_id: z.string().describe('Google Photos media item ID'),
  width: z.number().describe('Width of image/video in pixels'),
  height: z.number().describe('Height of image/video in pixels'),
  date_taken: z.string().describe('Timestamp when the image/video was taken'),
});

// Converts the internal location object
export function domainToGpsLocation(loc?: {
  latitude: number;
  longitude: number;
}): GpsLocationModel | undefined {
  return loc
    ? {
        latitude: loc.latitude,
        longitude: loc.longitude,
      }
    : undefined;
}

// Converts your domain MediaItem into our Tool output schema type
export function domainToToolMediaItem(item: MediaItem): MediaItemModel {
  return {
    id: item.id,
    file_name: item.fileName,
    location: domainToGpsLocation(item.location),
    gphotos_media_item_id: item.gPhotosMediaItemId,
    width: item.width,
    height: item.height,
    date_taken:
      item.dateTaken instanceof Date
        ? item.dateTaken.toISOString()
        : new Date(item.dateTaken).toISOString(),
  };
}

export type MediaItemModel = z.infer<typeof MediaItemModelSchema>;
