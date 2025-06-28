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

  async getMediaItemById(id: MediaItemId): Promise<MediaItem> {
    const mongoDbClient = this.mongoDbRepository.getClientFromId(id.clientId);
    const rawDocs = await mongoDbClient
      .db('photos_drive')
      .collection('media_items')
      .findOne({ _id: new ObjectId(id.objectId) });

    if (rawDocs === null) {
      throw new MediaItemNotFoundError(id);
    }

    return this.convertMongoDbDocToMediaItemInstance(id, rawDocs);
  }

  async getNumMediaItemsInAlbum(albumId: AlbumId): Promise<number> {
    const counts = await Promise.all(
      this.mongoDbRepository.listClients().map(async ([_, mongoDbClient]) => {
        const numDocs = await mongoDbClient
          .db('photos_drive')
          .collection('media_items')
          .countDocuments({
            album_id: `${albumId.clientId}:${albumId.objectId}`
          });

        return numDocs;
      })
    );

    return sum(counts);
  }

  async listMediaItems(
    req: ListMediaItemsRequest
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
          if (req.sortBy.field === SortByField.ID) {
            filterObj['_id'] =
              req.sortBy.direction === SortByDirection.ASCENDING
                ? { $gt: new ObjectId(lastSeenMediaItemId.objectId) }
                : { $lt: new ObjectId(lastSeenMediaItemId.objectId) };
          }
        }

        const sortObj: Sort = {};
        const mongoSortDirection =
          req.sortBy.direction === SortByDirection.ASCENDING ? 1 : -1;

        if (req.sortBy.field === SortByField.ID) {
          sortObj['_id'] = mongoSortDirection;
        }

        logger.debug(`Filter object: ${JSON.stringify(filterObj)}`);
        logger.debug(`Sort object: ${JSON.stringify(sortObj)}`);
        logger.debug(`Limit size: ${req.pageSize}`);

        const rawDocs = await mongoClient
          .db('photos_drive')
          .collection('media_items')
          .find(filterObj)
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
    case SortByField.ID:
      if (sortBy.direction === SortByDirection.ASCENDING) {
        return mediaIdToString(a.id) < mediaIdToString(b.id) ? -1 : 1;
      } else {
        return mediaIdToString(a.id) > mediaIdToString(b.id) ? -1 : 1;
      }
  }
}
