import { MediaItem, RawMediaItem } from './media-item';

export interface ListMediaItemsRequest {
  albumId?: string;
  pageSize?: number;
  pageToken?: string;
  sortBy?: ListMediaItemsSortBy;
}

export interface ListMediaItemsSortBy {
  field: ListMediaItemsSortByFields;
  direction: ListMediaItemsSortDirection;
}

export enum ListMediaItemsSortByFields {
  ID = 'id',
}

export enum ListMediaItemsSortDirection {
  ASCENDING = 'asc',
  DESCENDING = 'desc',
}

export interface RawListMediaItemsResponse {
  mediaItems: RawMediaItem[];
  nextPageToken?: string;
}

export interface ListMediaItemsResponse {
  mediaItems: MediaItem[];
  nextPageToken?: string;
}

export enum ListAlbumsSortByFields {
  ID = 'id',
}

export enum ListAlbumsSortDirection {
  ASCENDING = 'asc',
  DESCENDING = 'desc',
}
