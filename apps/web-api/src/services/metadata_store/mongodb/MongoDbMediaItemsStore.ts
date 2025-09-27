import {
  Collection,
  Filter,
  MongoClient,
  Document as MongoDbDocument,
  ObjectId,
  Sort
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
  MediaItemsStore,
  SampleMediaItemsRequest,
  SampleMediaItemsResponse,
  SortByDirection,
  SortByField
} from '../MediaItemsStore';

/** Implementation of {@code MediaItemsRepository} */
export class MongoDbMediaItemsStore implements MediaItemsStore {
  private clientId: string;
  private collection: Collection;

  constructor(
    clientId: string,
    mongoClient: MongoClient,
    dbName: string = 'photos_drive',
    collectionName: string = 'media_items'
  ) {
    this.clientId = clientId;
    this.collection = mongoClient.db(dbName).collection(collectionName);
  }

  getClientId(): string {
    return this.clientId;
  }

  async getMediaItemById(
    id: MediaItemId,
    options?: { abortController?: AbortController }
  ): Promise<MediaItem> {
    const rawDocs = await this.collection.findOne(
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
    const rawDocs = await this.collection
      .find(
        { _id: { $in: ids.map((id) => new ObjectId(id.objectId)) } },
        { signal: options?.abortController?.signal }
      )
      .toArray();

    // Convert all docs for this client
    return rawDocs.map((doc) =>
      this.convertMongoDbDocToMediaItemInstance(
        { clientId: this.getClientId(), objectId: doc._id.toString() },
        doc
      )
    );
  }

  async getNumMediaItemsInAlbum(
    albumId: AlbumId,
    options?: { abortController?: AbortController }
  ): Promise<number> {
    const numDocs = await this.collection.countDocuments(
      {
        album_id: `${albumId.clientId}:${albumId.objectId}`
      },
      { signal: options?.abortController?.signal }
    );

    return numDocs;
  }

  async listMediaItems(
    req: ListMediaItemsRequest,
    options?: { abortController?: AbortController }
  ): Promise<ListMediaItemsResponse> {
    const lastMediaItemId = req.pageToken
      ? convertStringToMediaItemId(req.pageToken)
      : undefined;

    const filterObj: Filter<MongoDbDocument> = {};

    if (req.albumId) {
      filterObj['album_id'] = albumIdToString(req.albumId);
    }
    if (req.earliestDateTaken || req.latestDateTaken) {
      filterObj['date_taken'] = {};
      if (req.earliestDateTaken) {
        filterObj['date_taken']['$gte'] = req.earliestDateTaken;
      }
      if (req.latestDateTaken) {
        filterObj['date_taken']['$lte'] = req.latestDateTaken;
      }
    }
    if (req.withinLocation) {
      filterObj['location'] = {
        $near: {
          $geometry: {
            type: 'Point',
            coordinates: [
              req.withinLocation.longitude,
              req.withinLocation.latitude
            ]
          },
          $maxDistance: req.withinLocation.range
        }
      };
    }

    if (lastMediaItemId) {
      const lastSeenMediaItemObjectId = new ObjectId(lastMediaItemId.objectId);

      if (req.sortBy.field === SortByField.ID) {
        filterObj['_id'] =
          req.sortBy.direction === SortByDirection.ASCENDING
            ? { $gt: lastSeenMediaItemObjectId }
            : { $lt: lastSeenMediaItemObjectId };
      } else {
        const lastSeenMediaItem = await this.collection.findOne(
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

    const rawDocs = await this.collection
      .find(filterObj, { signal: options?.abortController?.signal })
      .sort(sortObj)
      .limit(req.pageSize)
      .toArray();

    const mediaItems = rawDocs.map((rawDoc) => {
      const mediaItemId: MediaItemId = {
        clientId: this.getClientId(),
        objectId: rawDoc._id.toString()
      };
      return this.convertMongoDbDocToMediaItemInstance(mediaItemId, rawDoc);
    });

    const nextMediaItemId =
      mediaItems.length > 0 ? mediaItems[mediaItems.length - 1].id : undefined;

    return {
      mediaItems,
      nextPageToken: nextMediaItemId
        ? mediaIdToString(nextMediaItemId)
        : undefined
    };
  }

  async sampleMediaItems(
    req: SampleMediaItemsRequest,
    options?: { abortController?: AbortController }
  ): Promise<SampleMediaItemsResponse> {
    const filterObj: Filter<MongoDbDocument> = {};

    if (req.albumId) {
      filterObj['album_id'] = albumIdToString(req.albumId);
    }
    if (req.earliestDateTaken || req.latestDateTaken) {
      filterObj['date_taken'] = {};
      if (req.earliestDateTaken) {
        filterObj['date_taken']['$gte'] = req.earliestDateTaken;
      }
      if (req.latestDateTaken) {
        filterObj['date_taken']['$lte'] = req.latestDateTaken;
      }
    }
    if (req.withinLocation) {
      filterObj['location'] = {
        $near: {
          $geometry: {
            type: 'Point',
            coordinates: [
              req.withinLocation.longitude,
              req.withinLocation.latitude
            ]
          },
          $maxDistance: req.withinLocation.range
        }
      };
    }

    logger.debug(`Sample filter object: ${JSON.stringify(filterObj)}`);
    logger.debug(`Sample size: ${req.pageSize}`);

    const pipeline = [
      { $match: filterObj },
      { $sample: { size: req.pageSize } }
    ];

    const rawDocs = await this.collection
      .aggregate(pipeline, { signal: options?.abortController?.signal })
      .toArray();

    const mediaItems = rawDocs.map((rawDoc) => {
      const mediaItemId: MediaItemId = {
        clientId: this.getClientId(),
        objectId: rawDoc._id.toString()
      };
      return this.convertMongoDbDocToMediaItemInstance(mediaItemId, rawDoc);
    });

    return { mediaItems };
  }

  private convertMongoDbDocToMediaItemInstance(
    id: MediaItemId,
    doc: MongoDbDocument
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
