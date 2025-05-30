import { Document as MongoDbDocument, ObjectId, WithId } from 'mongodb';
import { Album, AlbumId, convertStringToAlbumId } from './Albums';
import { convertStringToMediaItemId } from './MediaItems';
import { MongoDbClientsRepository } from './MongoDbClientsRepository';

/** A class that stores the albums from the database. */
export interface AlbumsRepository {
  getAlbumById(id: AlbumId): Promise<Album>;
}

/** Implementation of {@code AlbumsRepository} */
export class AlbumsRepositoryImpl implements AlbumsRepository {
  private mongoDbRepository: MongoDbClientsRepository;

  constructor(mongoDbRepository: MongoDbClientsRepository) {
    this.mongoDbRepository = mongoDbRepository;
  }

  async getAlbumById(id: AlbumId): Promise<Album> {
    const mongoDbClient = this.mongoDbRepository.getClientFromId(id.clientId);
    const rawDocs = await mongoDbClient
      .db('sharded_google_photos')
      .collection('albums')
      .findOne({ _id: new ObjectId(id.objectId) });

    if (rawDocs === null) {
      throw new AlbumNotFoundError(id);
    }

    return this.convertMongoDbDocumentToAlbumInstance(id, rawDocs);
  }

  private convertMongoDbDocumentToAlbumInstance(
    id: AlbumId,
    doc: WithId<MongoDbDocument>
  ): Album {
    return {
      id: id,
      name: doc['name'],
      parent_album_id: doc['parent_album_id']
        ? convertStringToAlbumId(doc['parent_album_id'])
        : undefined,
      child_album_ids: doc['child_album_ids'].map((albumId: string) => {
        return convertStringToAlbumId(albumId);
      }),
      media_item_ids: doc['media_item_ids'].map((mediaItemId: string) => {
        return convertStringToMediaItemId(mediaItemId);
      })
    };
  }
}

/** Represents an error for when an album is not found. */
export class AlbumNotFoundError extends Error {
  constructor(albumId: AlbumId) {
    super(`Cannot find album with id ${albumId}`);
    this.name = 'AlbumNotFoundError';
  }
}
