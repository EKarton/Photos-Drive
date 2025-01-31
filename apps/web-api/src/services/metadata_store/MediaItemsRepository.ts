import { Document as MongoDbDocument, ObjectId, WithId } from 'mongodb';
import { MediaItem, MediaItemId } from './MediaItems';
import { MongoDbClientsRepository } from './MongoDbClientsRepository';

/** A class that stores the media items from the database. */
export interface MediaItemsRepository {
  getMediaItemById(id: MediaItemId): Promise<MediaItem>;
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

  private convertMongoDbDocToMediaItemInstance(
    id: MediaItemId,
    doc: WithId<MongoDbDocument>
  ): MediaItem {
    const mediaItem: MediaItem = {
      id,
      file_name: doc['file_name'],
      gphotos_client_id: doc['gphotos_client_id'],
      gphotos_media_item_id: doc['gphotos_media_item_id']
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
