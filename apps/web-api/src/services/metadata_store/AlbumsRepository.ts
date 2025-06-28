import { Album, AlbumId } from './Albums';

/** List of possible fields to sort by for {@code ListAlbumsRequest} */
export enum SortByField {
  ID = 'id'
}

/** List of possible sort directions for {@code ListAlbumsRequest} */
export enum SortByDirection {
  ASCENDING = 'asc',
  DESCENDING = 'desc'
}

/** Sort definition for {@code ListAlbumsRequest} */
export interface SortBy {
  field: SortByField;
  direction: SortByDirection;
}

/** Request params for {@code AlbumsRepository.listAlbums} */
export interface ListAlbumsRequest {
  parentAlbumId?: AlbumId;
  pageSize: number;
  pageToken?: string;
  sortBy: SortBy;
}

/** Response for {@code AlbumsRepository.listAlbums} */
export type ListAlbumsResponse = {
  albums: Album[];
  nextPageToken?: string;
};

/** A class that stores the albums from the database. */
export interface AlbumsRepository {
  getAlbumById(id: AlbumId): Promise<Album>;
  getNumAlbumsInAlbum(id: AlbumId): Promise<number>;
  listAlbums(req: ListAlbumsRequest): Promise<ListAlbumsResponse>;
}

/** Represents an error for when an album is not found. */
export class AlbumNotFoundError extends Error {
  constructor(albumId: AlbumId) {
    super(`Cannot find album with id ${albumId}`);
    this.name = 'AlbumNotFoundError';
  }
}
