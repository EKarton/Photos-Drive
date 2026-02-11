import { albumIdToString } from '../../services/metadata_store/Albums';
import {
  mediaIdToString,
  MediaItem
} from '../../services/metadata_store/MediaItems';

/** Serializes a media item to a JSON object */
export function serializeMediaItem(mediaItem: MediaItem): object {
  return {
    id: mediaIdToString(mediaItem.id),
    fileName: mediaItem.file_name,
    location: mediaItem.location,
    gPhotosMediaItemId: `${mediaItem.gphotos_client_id}:${mediaItem.gphotos_media_item_id}`,
    albumId: albumIdToString(mediaItem.album_id),
    width: mediaItem.width,
    height: mediaItem.height,
    dateTaken: mediaItem.date_taken.toISOString()
  };
}
