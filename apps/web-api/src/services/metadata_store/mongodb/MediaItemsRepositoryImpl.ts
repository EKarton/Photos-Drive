import { sum } from 'lodash';
import {
  Filter,
  Document as MongoDbDocument,
  ObjectId,
  Sort,
  WithId
} from 'mongodb';
import logger from '../../../utils/logger';
import { AlbumId, albumIdToString, convertStringToAlbumId } from '../Albums';
import {
  convertStringToMediaItemId,
  mediaIdToString,
  MediaItem,
  MediaItemId
} from '../MediaItems';
import {
  ListMediaItemsRequest,
  ListMediaItemsResponse,
  MediaItemNotFoundError,
  MediaItemsRepository,
  SortBy,
  SortByDirection,
  SortByField
} from '../MediaItemsRepository';
import { MongoDbClientsRepository } from './MongoDbClientsRepository';

/** Implementation of {@code MediaItemsRepository} */
export class MediaItemsRepositoryImpl implements MediaItemsRepository {
  private mongoDbRepository: MongoDbClientsRepository;

  constructor(mongoDbRepository: MongoDbClientsRepository) {
    this.mongoDbRepository = mongoDbRepository;
  }

  async getMediaItemById(
    id: MediaItemId,
    options?: { abortController?: AbortController }
  ): Promise<MediaItem> {
    const mongoDbClient = this.mongoDbRepository.getClientFromId(id.clientId);
    const rawDocs = await mongoDbClient
      .db('photos_drive')
      .collection('media_items')
      .findOne(
        { _id: new ObjectId(id.objectId) },
        { signal: options?.abortController?.signal }
      );

    if (rawDocs === null) {
      throw new MediaItemNotFoundError(id);
    }

    return this.convertMongoDbDocToMediaItemInstance(id, rawDocs);
  }

  async bulkGetMediaItemByIds(
    ids: MediaItemId[],
    options?: { abortController?: AbortController }
  ): Promise<MediaItem[]> {
    const clientIdsToObjectIds = new Map<string, string[]>();
    for (const id of ids) {
      if (!clientIdsToObjectIds.has(id.clientId)) {
        clientIdsToObjectIds.set(id.clientId, []);
      }
      clientIdsToObjectIds.get(id.clientId)!.push(id.objectId);
    }

    return (
      await Promise.all(
        Array.from(clientIdsToObjectIds.entries()).map(
          async ([clientId, objectIds]) => {
            const mongoDbClient =
              this.mongoDbRepository.getClientFromId(clientId);

            const rawDocs = await mongoDbClient
              .db('photos_drive')
              .collection('media_items')
              .find(
                { _id: { $in: objectIds.map((id) => new ObjectId(id)) } },
                { signal: options?.abortController?.signal }
              )
              .toArray();

            // Convert all docs for this client
            return rawDocs.map((doc) =>
              this.convertMongoDbDocToMediaItemInstance(
                { clientId, objectId: doc._id.toString() },
                doc
              )
            );
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
      this.mongoDbRepository.listClients().map(async ([_, mongoDbClient]) => {
        const numDocs = await mongoDbClient
          .db('photos_drive')
          .collection('media_items')
          .countDocuments(
            {
              album_id: `${albumId.clientId}:${albumId.objectId}`
            },
            { signal: options?.abortController?.signal }
          );

        return numDocs;
      })
    );

    return sum(counts);
  }

  async listMediaItems(
    req: ListMediaItemsRequest,
    options?: { abortController?: AbortController }
  ): Promise<ListMediaItemsResponse> {
    const clientIdToMongoClient = new Map(this.mongoDbRepository.listClients());
    const clientIdToMediaItemId = new Map(
      req.pageToken?.split(',').map((pageToken) => {
        const mediaItemId = convertStringToMediaItemId(pageToken);
        return [mediaItemId.clientId, mediaItemId];
      })
    );

    const overFetchSize = req.pageSize * 2;

    const mediaItems: MediaItem[][] = await Promise.all(
      Array.from(clientIdToMongoClient).map(async ([clientId, mongoClient]) => {
        const filterObj: Filter<MongoDbDocument> = {};

        if (req.albumId) {
          filterObj['album_id'] = albumIdToString(req.albumId);
        }

        const lastSeenMediaItemId = clientIdToMediaItemId.get(clientId);
        if (lastSeenMediaItemId) {
          const lastSeenMediaItemObjectId = new ObjectId(
            lastSeenMediaItemId.objectId
          );

          if (req.sortBy.field === SortByField.ID) {
            filterObj['_id'] =
              req.sortBy.direction === SortByDirection.ASCENDING
                ? { $gt: lastSeenMediaItemObjectId }
                : { $lt: lastSeenMediaItemObjectId };
          } else {
            const lastSeenMediaItem = await mongoClient
              .db('photos_drive')
              .collection('media_items')
              .findOne(
                { _id: lastSeenMediaItemObjectId },
                { signal: options?.abortController?.signal }
              );
            const lastSeenDateTaken: Date =
              lastSeenMediaItem!['date_taken'] ?? new Date(1970, 1, 1);

            filterObj['$or'] =
              req.sortBy.direction === SortByDirection.ASCENDING
                ? [
                    { date_taken: { $gt: lastSeenDateTaken } },
                    {
                      date_taken: lastSeenDateTaken,
                      _id: { $gt: lastSeenMediaItemObjectId }
                    }
                  ]
                : [
                    { date_taken: { $lt: lastSeenDateTaken } },
                    {
                      date_taken: lastSeenDateTaken,
                      _id: { $lt: lastSeenMediaItemObjectId }
                    }
                  ];
          }
        }

        const mongoSortDirection =
          req.sortBy.direction === SortByDirection.ASCENDING ? 1 : -1;

        let sortObj: Sort;
        if (req.sortBy.field === SortByField.ID) {
          sortObj = { _id: mongoSortDirection };
        } else {
          sortObj = {
            date_taken: mongoSortDirection,
            _id: mongoSortDirection
          };
        }

        logger.debug(`Filter object: ${JSON.stringify(filterObj)}`);
        logger.debug(`Sort object: ${JSON.stringify(sortObj)}`);
        logger.debug(`Limit size: ${req.pageSize}`);

        const rawDocs = await mongoClient
          .db('photos_drive')
          .collection('media_items')
          .find(filterObj, { signal: options?.abortController?.signal })
          .sort(sortObj)
          .limit(overFetchSize)
          .toArray();

        const mediaItems = rawDocs.map((rawDoc) => {
          const mediaItemId: MediaItemId = {
            clientId: clientId,
            objectId: rawDoc._id.toString()
          };
          return this.convertMongoDbDocToMediaItemInstance(mediaItemId, rawDoc);
        });

        return mediaItems;
      })
    );

    const sortedMediaItems = mediaItems
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

  private convertMongoDbDocToMediaItemInstance(
    id: MediaItemId,
    doc: WithId<MongoDbDocument>
  ): MediaItem {
    const mediaItem: MediaItem = {
      id,
      file_name: doc['file_name'],
      gphotos_client_id: doc['gphotos_client_id'],
      gphotos_media_item_id: doc['gphotos_media_item_id'],
      album_id: convertStringToAlbumId(doc['album_id']),
      width: doc['width'] || 0,
      height: doc['height'] || 0,
      date_taken: doc['date_taken'] || new Date(1970, 1, 1)
    };

    if (doc['location']) {
      mediaItem.location = {
        longitude: doc['location']['coordinates'][0],
        latitude: doc['location']['coordinates'][1]
      };
    }

    return mediaItem;
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
