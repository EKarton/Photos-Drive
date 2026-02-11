import { sum } from 'lodash';
import {
  Album,
  AlbumId,
  albumIdToString,
  convertStringToAlbumId
} from './Albums';
import {
  AlbumsStore,
  ListAlbumsRequest,
  ListAlbumsResponse,
  SortBy,
  SortByDirection,
  SortByField
} from './BaseAlbumsStore';

/** Implementation of {@code AlbumsRepository} */
export class DistributedAlbumsStore implements AlbumsStore {
  private repos: AlbumsStore[];
  private clientIdToRepo: Map<string, AlbumsStore>;

  constructor(repos: AlbumsStore[]) {
    this.repos = repos;
    this.clientIdToRepo = new Map();

    for (const repo of repos) {
      this.clientIdToRepo.set(repo.getClientId(), repo);
    }
  }

  getClientId(): string {
    throw new Error('Cannot get client ID from this repo');
  }

  async getAlbumById(
    id: AlbumId,
    options?: { abortController?: AbortController }
  ): Promise<Album> {
    return this.clientIdToRepo.get(id.clientId)!.getAlbumById(id, options);
  }

  async getNumAlbumsInAlbum(
    id: AlbumId,
    options?: { abortController?: AbortController }
  ): Promise<number> {
    const counts = await Promise.all(
      this.repos.map((repo) => repo.getNumAlbumsInAlbum(id, options))
    );

    return sum(counts);
  }

  async listAlbums(
    req: ListAlbumsRequest,
    options?: { abortController?: AbortController }
  ): Promise<ListAlbumsResponse> {
    const clientIdToAlbumId = new Map(
      req.pageToken?.split(',').map((pageToken) => {
        const albumId = convertStringToAlbumId(pageToken);
        return [albumId.clientId, albumId];
      })
    );
    const overFetchSize = req.pageSize * 2;

    const responses = await Promise.all(
      this.repos.map((repo) => {
        const lastAlbumId = clientIdToAlbumId.get(repo.getClientId());
        const newRequest: ListAlbumsRequest = {
          ...req,
          pageSize: overFetchSize,
          pageToken: lastAlbumId ? albumIdToString(lastAlbumId) : undefined
        };
        return repo.listAlbums(newRequest, options);
      })
    );

    const sortedAlbums = responses
      .map((res) => res.albums)
      .flat()
      .sort((a: Album, b: Album) => {
        return sortAlbum(a, b, req.sortBy);
      })
      .slice(0, req.pageSize);

    const clientIdToLastAlbumId = new Map<string, AlbumId>();
    for (let i = sortedAlbums.length - 1; i >= 0; i--) {
      const album = sortedAlbums.at(i);
      const clientId = album!.id.clientId;

      if (!clientIdToLastAlbumId.has(clientId)) {
        clientIdToLastAlbumId.set(clientId, album!.id);
      }
    }

    for (const [clientId, albumId] of clientIdToAlbumId) {
      if (!clientIdToLastAlbumId.has(clientId)) {
        clientIdToLastAlbumId.set(clientId, albumId);
      }
    }

    const nextPageToken =
      Array.from(clientIdToLastAlbumId.values())
        .map(albumIdToString)
        .join(',') || undefined;

    return {
      albums: sortedAlbums,
      nextPageToken: sortedAlbums.length > 0 ? nextPageToken : undefined
    };
  }
}

/** Returns -1 if a should go before b; else 1 based on {@code SortBy} */
export function sortAlbum(a: Album, b: Album, sortBy: SortBy): number {
  switch (sortBy.field) {
    case SortByField.ID:
      if (sortBy.direction === SortByDirection.ASCENDING) {
        return albumIdToString(a.id) < albumIdToString(b.id) ? -1 : 1;
      } else {
        return albumIdToString(a.id) > albumIdToString(b.id) ? -1 : 1;
      }
    case SortByField.NAME:
      if (sortBy.direction === SortByDirection.ASCENDING) {
        return a.name < b.name ? -1 : 1;
      } else {
        return a.name > b.name ? -1 : 1;
      }
  }
}
