import { Album, AlbumId } from './Albums';

/** A class that stores the albums from the database. */
export interface AlbumsRepository {
  getAlbumById(id: AlbumId): Promise<Album>;
}

/** Represents an error for when an album is not found. */
export class AlbumNotFoundError extends Error {
  constructor(albumId: AlbumId) {
    super(`Cannot find album with id ${albumId}`);
    this.name = 'AlbumNotFoundError';
  }
}
