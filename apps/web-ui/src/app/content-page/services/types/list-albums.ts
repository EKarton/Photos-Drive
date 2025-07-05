import { Album } from './album';

export interface ListAlbumsRequest {
  parentAlbumId?: string;
  pageSize?: number;
  pageToken?: string;
  sortBy?: ListAlbumsSortBy;
}

export interface ListAlbumsSortBy {
  field: ListAlbumsSortByFields;
  direction: ListAlbumsSortDirection;
}

export interface ListAlbumsResponse {
  albums: Album[];
  nextPageToken?: string;
}

export enum ListAlbumsSortByFields {
  ID = 'id',
}

export enum ListAlbumsSortDirection {
  ASCENDING = 'asc',
  DESCENDING = 'desc',
}
