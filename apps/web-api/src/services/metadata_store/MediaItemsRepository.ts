import { AlbumId } from './Albums';
import { MediaItem, MediaItemId } from './MediaItems';

/** List of possible fields to sort by for {@code ListMediaItemsRequest} */
export enum SortByField {
  ID = 'id',
  DATE_TAKEN = 'date-taken'
}

/** List of possible sort directions for {@code ListMediaItemsRequest} */
export enum SortByDirection {
  ASCENDING = 'asc',
  DESCENDING = 'desc'
}

/** Sort definition for {@code ListMediaItemsRequest} */
export interface SortBy {
  field: SortByField;
  direction: SortByDirection;
}

/** Request params for {@code MediaItemsRepository.listMediaItems} */
export interface ListMediaItemsRequest {
  albumId?: AlbumId;
  pageSize: number;
  pageToken?: string;
  sortBy: SortBy;
}

/** Response for {@code MediaItemsRepository.listMediaItems} */
export type ListMediaItemsResponse = {
  mediaItems: MediaItem[];
  nextPageToken?: string;
};

/** A class that stores the media items from the database. */
export interface MediaItemsRepository {
  getMediaItemById(
    id: MediaItemId,
    options?: { abortController?: AbortController }
  ): Promise<MediaItem>;

  bulkGetMediaItemByIds(
    ids: MediaItemId[],
    options?: { abortController?: AbortController }
  ): Promise<MediaItem[]>;

  getNumMediaItemsInAlbum(
    albumId: AlbumId,
    options?: { abortController?: AbortController }
  ): Promise<number>;

  listMediaItems(
    req: ListMediaItemsRequest,
    options?: { abortController?: AbortController }
  ): Promise<ListMediaItemsResponse>;
}

/** Represents an error for when an album is not found. */
export class MediaItemNotFoundError extends Error {
  constructor(mediaItemId: MediaItemId) {
    super(`Cannot find media item with id ${mediaItemId}`);
    this.name = 'MediaItemNotFoundError';
  }
}
