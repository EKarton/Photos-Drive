import {
  Filter,
  Document as MongoDbDocument,
  ObjectId,
  Sort,
  WithId
} from 'mongodb';
import logger from '../../utils/logger';
import { AlbumId, albumIdToString, convertStringToAlbumId } from './Albums';
import {
  convertStringToMediaItemId,
  MediaItem,
  MediaItemId
} from './MediaItems';
import { MongoDbClientsRepository } from './MongoDbClientsRepository';

/** List of possible fields to sort by for {@code ListMediaItemsRequest} */
export enum SortByField {
  ID = 'id'
}

/** List of possible sort directions for {@code ListMediaItemsRequest} */
export enum SortByDirection {
  ASCENDING = 'asc',
  DESCENDING = 'desc'
}

/** Sort definition for {@code ListMediaItemsRequest} */
export interface SortBy {
  field: SortByField;
  direction: SortByDirection;
}

/** Request params for {@code MediaItemsRepository.listMediaItems} */
export interface ListMediaItemsRequest {
  albumId: AlbumId;
  pageSize: number;
  pageToken: string;
  sortBy?: SortBy;
}

/** Response for {@code MediaItemsRepository.listMediaItems} */
export type ListMediaItemsResponse = {
  mediaItems: MediaItem[];
  nextPageToken?: string;
};

/** A class that stores the media items from the database. */
export interface MediaItemsRepository {
  getMediaItemById(id: MediaItemId): Promise<MediaItem>;
  getMediaItemsInAlbum(albumId: AlbumId): Promise<MediaItem[]>;
  listMediaItemsInAlbum(
    req: ListMediaItemsRequest
  ): Promise<ListMediaItemsResponse>;
}

/** Implementation of {@code MediaItemsRepository} */
export class MediaItemsRepositoryImpl implements MediaItemsRepository {
  private mongoDbRepository: MongoDbClientsRepository;

  constructor(mongoDbRepository: MongoDbClientsRepository) {
    this.mongoDbRepository = mongoDbRepository;
  }

  async getMediaItemById(id: MediaItemId): Promise<MediaItem> {
    const mongoDbClient = this.mongoDbRepository.getClientFromId(id.clientId);
    const rawDocs = await mongoDbClient
      .db('sharded_google_photos')
      .collection('media_items')
      .findOne({ _id: new ObjectId(id.objectId) });

    if (rawDocs === null) {
      throw new MediaItemNotFoundError(id);
    }

    return this.convertMongoDbDocToMediaItemInstance(id, rawDocs);
  }

  async getMediaItemsInAlbum(albumId: AlbumId): Promise<MediaItem[]> {
    const items = await Promise.all(
      this.mongoDbRepository
        .listClients()
        .map(async ([clientId, mongoDbClient]) => {
          const rawDocs = await mongoDbClient
            .db('sharded_google_photos')
            .collection('media_items')
            .find({ album_id: `${albumId.clientId}:${albumId.objectId}` })
            .toArray();

          return rawDocs.map((rawDoc) => {
            const mediaItemId: MediaItemId = {
              clientId: clientId,
              objectId: rawDoc['_id'].toString()
            };
            return this.convertMongoDbDocToMediaItemInstance(
              mediaItemId,
              rawDoc
            );
          });
        })
    );

    return items.flat();
  }

  async listMediaItemsInAlbum(
    req: ListMediaItemsRequest
  ): Promise<ListMediaItemsResponse> {
    const clientIdToMongoClient = new Map(this.mongoDbRepository.listClients());
    const clientIdToPageToken = new Map(
      req.pageToken?.split(',').map((pageToken) => {
        const mediaItemId = convertStringToMediaItemId(pageToken);
        return [mediaItemId.clientId, new ObjectId(mediaItemId.objectId)];
      })
    );

    const clientIdToNextPageToken = new Map<string, string>();
    const totalMediaItems: MediaItem[] = [];

    for (const [clientId, mongoClient] of clientIdToMongoClient) {
      logger.debug(`Album ID: ${albumIdToString(req.albumId)}`);
      const filterObj: Filter<MongoDbDocument> = {
        album_id: albumIdToString(req.albumId)
      };
      if (clientIdToPageToken.has(clientId)) {
        filterObj['_id'] = {
          $gt: clientIdToPageToken.get(clientId)
        };
      }

      const sortObj: Sort = {};
      if (req.sortBy) {
        const mongoSortDirection =
          req.sortBy.direction === SortByDirection.ASCENDING ? 1 : -1;

        switch (req.sortBy.field) {
          case SortByField.ID: {
            sortObj['_id'] = mongoSortDirection;
            break;
          }
          default:
            throw Error(`Unhandled sortBy field: ${req.sortBy.field}`);
        }
      }

      logger.debug(`Filter object: ${JSON.stringify(filterObj)}`);
      logger.debug(`Sort object: ${JSON.stringify(sortObj)}`);
      logger.debug(`Limit size: ${req.pageSize}`);

      const rawDocs = await mongoClient
        .db('sharded_google_photos')
        .collection('media_items')
        .find(filterObj)
        .sort(sortObj)
        .limit(req.pageSize)
        .toArray();

      logger.debug('I am here');

      const mediaItems = rawDocs.map((rawDoc) => {
        const mediaItemId: MediaItemId = {
          clientId: clientId,
          objectId: rawDoc._id.toString()
        };
        return this.convertMongoDbDocToMediaItemInstance(mediaItemId, rawDoc);
      });

      logger.debug(`MediaItems: ${mediaItems}`);

      if (mediaItems.length > 0) {
        totalMediaItems.push(...mediaItems);
        clientIdToNextPageToken.set(
          clientId,
          mediaItems[mediaItems.length - 1].id.objectId
        );
      }
    }

    const sortedMediaItems = totalMediaItems.sort(
      (a: MediaItem, b: MediaItem) => {
        if (req.sortBy === undefined) {
          return 0;
        }
        switch (req.sortBy.field) {
          case SortByField.ID:
            if (req.sortBy.direction === SortByDirection.ASCENDING) {
              return a.id < b.id ? -1 : 1;
            } else {
              return a.id > b.id ? -1 : 1;
            }
          default:
            throw Error(`Unhandled sortBy field: ${req.sortBy.field}`);
        }
      }
    );

    const nextPageToken = Array.from(clientIdToNextPageToken)
      .map(([key, value]) => `${key}:${value}`)
      .join(',');

    return {
      mediaItems: sortedMediaItems,
      nextPageToken: nextPageToken.length > 0 ? nextPageToken : undefined
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
      album_id: convertStringToAlbumId(doc['album_id'])
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

/** Represents an error for when an album is not found. */
export class MediaItemNotFoundError extends Error {
  constructor(mediaItemId: MediaItemId) {
    super(`Cannot find media item with id ${mediaItemId}`);
    this.name = 'MediaItemNotFoundError';
  }
}
