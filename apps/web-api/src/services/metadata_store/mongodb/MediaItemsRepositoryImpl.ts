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

    const pages: ListMediaItemsResponse[] = await Promise.all(
      Array.from(clientIdToMongoClient).map(async ([clientId, mongoClient]) => {
        logger.debug(`Album ID: ${albumIdToString(req.albumId)}`);
        const filterObj: Filter<MongoDbDocument> = {
          album_id: albumIdToString(req.albumId)
        };

        const lastSeenId = clientIdToPageToken.get(clientId);
        if (lastSeenId) {
          if (req.sortBy.field === SortByField.ID) {
            filterObj['_id'] =
              req.sortBy.direction === SortByDirection.ASCENDING
                ? { $gt: lastSeenId }
                : { $lt: lastSeenId };
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
          .db('sharded_google_photos')
          .collection('media_items')
          .find(filterObj)
          .sort(sortObj)
          .limit(req.pageSize)
          .toArray();

        const mediaItems = rawDocs.map((rawDoc) => {
          const mediaItemId: MediaItemId = {
            clientId: clientId,
            objectId: rawDoc._id.toString()
          };
          return this.convertMongoDbDocToMediaItemInstance(mediaItemId, rawDoc);
        });

        logger.debug(`Num MediaItems: ${mediaItems.length}`);

        return {
          mediaItems,
          nextPageToken:
            mediaItems.length > 0
              ? mediaIdToString(mediaItems[mediaItems.length - 1].id)
              : undefined
        };
      })
    );

    const sortedMediaItems = pages
      .map((page) => page.mediaItems)
      .flat()
      .sort((a: MediaItem, b: MediaItem) => {
        return sortMediaItem(a, b, req.sortBy);
      });

    return {
      mediaItems: sortedMediaItems,
      nextPageToken:
        pages
          .map((page) => page.nextPageToken)
          .filter((nextToken) => nextToken)
          .join(',') || undefined
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
