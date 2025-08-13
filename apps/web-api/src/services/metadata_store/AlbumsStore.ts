import { Album, AlbumId } from './Albums';

/** List of possible fields to sort by for {@code AlbumsStore.listAlbumsRequest} */
export enum SortByField {
  ID = 'id',
  NAME = 'name'
}

/** List of possible sort directions for {@code AlbumsStore.listAlbumsRequest} */
export enum SortByDirection {
  ASCENDING = 'asc',
  DESCENDING = 'desc'
}

/** Sort definition for {@code AlbumsStore.listAlbumsRequest} */
export interface SortBy {
  field: SortByField;
  direction: SortByDirection;
}

/** Request params for {@code AlbumsStore.listAlbums} */
export interface ListAlbumsRequest {
  parentAlbumId?: AlbumId;
  pageSize: number;
  pageToken?: string;
  sortBy: SortBy;
}

/** Response for {@code AlbumsStore.listAlbums} */
export type ListAlbumsResponse = {
  albums: Album[];
  nextPageToken?: string;
};

/** A class that stores the albums from the database. */
export interface AlbumsStore {
  getClientId(): string;

  getAlbumById(
    id: AlbumId,
    options?: { abortController?: AbortController }
  ): Promise<Album>;

  getNumAlbumsInAlbum(
    id: AlbumId,
    options?: { abortController?: AbortController }
  ): Promise<number>;

  listAlbums(
    req: ListAlbumsRequest,
    options?: { abortController?: AbortController }
  ): Promise<ListAlbumsResponse>;
}

/** Represents an error for when an album is not found. */
export class AlbumNotFoundError extends Error {
  constructor(albumId: AlbumId) {
    super(`Cannot find album with id ${albumId}`);
    this.name = 'AlbumNotFoundError';
  }
}
