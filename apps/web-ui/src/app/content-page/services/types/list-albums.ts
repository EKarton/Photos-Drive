import { Album } from './album';
import {
  ListAlbumsSortByFields,
  ListAlbumsSortDirection,
} from './list-media-items';

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
  nextPageToken: string;
}
