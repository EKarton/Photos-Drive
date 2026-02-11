import { sum } from 'lodash';
import { AlbumId, albumIdToString } from '../albums/Albums';
import {
  ListMediaItemsRequest,
  ListMediaItemsResponse,
  MediaItemsStore,
  SampleMediaItemsRequest,
  SampleMediaItemsResponse,
  SortBy,
  SortByDirection,
  SortByField
} from './BaseMediaItemsStore';
import {
  convertStringToMediaItemId,
  mediaIdToString,
  MediaItem,
  MediaItemId
} from './MediaItems';

/** Implementation of {@code MediaItemsRepository} for multiple media item repos */
export class DistributedMediaItemsStore implements MediaItemsStore {
  private repos: MediaItemsStore[];
  private clientIdToRepo: Map<string, MediaItemsStore>;

  constructor(repos: MediaItemsStore[]) {
    this.repos = repos;
    this.clientIdToRepo = new Map();

    for (const repo of repos) {
      this.clientIdToRepo.set(repo.getClientId(), repo);
    }
  }

  getClientId(): string {
    throw new Error('Cannot get client ID from this repo');
  }

  async getMediaItemById(
    id: MediaItemId,
    options?: { abortController?: AbortController }
  ): Promise<MediaItem> {
    const repo = this.clientIdToRepo.get(id.clientId);
    return repo!.getMediaItemById(id, options);
  }

  async bulkGetMediaItemByIds(
    ids: MediaItemId[],
    options?: { abortController?: AbortController }
  ): Promise<MediaItem[]> {
    const clientIdsToMediaItemIds = new Map<string, MediaItemId[]>();
    for (const id of ids) {
      if (!clientIdsToMediaItemIds.has(id.clientId)) {
        clientIdsToMediaItemIds.set(id.clientId, []);
      }
      clientIdsToMediaItemIds.get(id.clientId)!.push(id);
    }

    return (
      await Promise.all(
        Array.from(clientIdsToMediaItemIds.entries()).map(
          ([clientId, mediaItemIds]) => {
            return this.clientIdToRepo
              .get(clientId)!
              .bulkGetMediaItemByIds(mediaItemIds, options);
          }
        )
      )
    ).flat();
  }

  async getNumMediaItemsInAlbum(
    albumId: AlbumId,
    options?: { abortController?: AbortController }
  ): Promise<number> {
    const counts = await Promise.all(
      this.repos.map((repo) => repo.getNumMediaItemsInAlbum(albumId, options))
    );

    return sum(counts);
  }

  async listMediaItems(
    req: ListMediaItemsRequest,
    options?: { abortController?: AbortController }
  ): Promise<ListMediaItemsResponse> {
    const clientIdToMediaItemId = new Map(
      req.pageToken?.split(',').map((pageToken) => {
        const mediaItemId = convertStringToMediaItemId(pageToken);
        return [mediaItemId.clientId, mediaItemId];
      })
    );

    const overFetchSize = req.pageSize * 2;

    const responses: ListMediaItemsResponse[] = await Promise.all(
      this.repos.map((repo) => {
        const lastMediaItemId = clientIdToMediaItemId.get(repo.getClientId());
        const newRequest: ListMediaItemsRequest = {
          ...req,
          pageSize: overFetchSize,
          pageToken: lastMediaItemId
            ? mediaIdToString(lastMediaItemId)
            : undefined
        };
        return repo.listMediaItems(newRequest, options);
      })
    );

    const sortedMediaItems = responses
      .map((res) => res.mediaItems)
      .flat()
      .sort((a: MediaItem, b: MediaItem) => {
        return sortMediaItem(a, b, req.sortBy);
      })
      .slice(0, req.pageSize);

    const clientIdToLastMediaItemId = new Map<string, MediaItemId>();
    for (let i = sortedMediaItems.length - 1; i >= 0; i--) {
      const album = sortedMediaItems.at(i);
      const clientId = album!.id.clientId;

      if (!clientIdToLastMediaItemId.has(clientId)) {
        clientIdToLastMediaItemId.set(clientId, album!.id);
      }
    }

    for (const [clientId, albumId] of clientIdToMediaItemId) {
      if (!clientIdToLastMediaItemId.has(clientId)) {
        clientIdToLastMediaItemId.set(clientId, albumId);
      }
    }

    const nextPageToken =
      Array.from(clientIdToLastMediaItemId.values())
        .map(albumIdToString)
        .join(',') || undefined;

    return {
      mediaItems: sortedMediaItems,
      nextPageToken: sortedMediaItems.length > 0 ? nextPageToken : undefined
    };
  }

  async sampleMediaItems(
    req: SampleMediaItemsRequest,
    options?: { abortController?: AbortController }
  ): Promise<SampleMediaItemsResponse> {
    const responses = await Promise.all(
      this.repos.map((repo) => repo.sampleMediaItems(req, options))
    );

    return {
      mediaItems: responses
        .map((res) => res.mediaItems)
        .flat()
        .slice(0, req.pageSize)
    };
  }
}

/** Returns -1 if a should go before b; else 1 based on {@code SortBy} */
export function sortMediaItem(
  a: MediaItem,
  b: MediaItem,
  sortBy: SortBy
): number {
  switch (sortBy.field) {
    case SortByField.ID: {
      const aId = mediaIdToString(a.id);
      const bId = mediaIdToString(b.id);

      if (sortBy.direction === SortByDirection.ASCENDING) {
        return aId < bId ? -1 : 1;
      } else {
        return aId > bId ? -1 : 1;
      }
    }
    case SortByField.DATE_TAKEN: {
      const aTime = a.date_taken.getTime();
      const bTime = b.date_taken.getTime();

      if (sortBy.direction === SortByDirection.ASCENDING) {
        return aTime < bTime ? -1 : 1;
      } else {
        return aTime > bTime ? -1 : 1;
      }
    }
  }
}
