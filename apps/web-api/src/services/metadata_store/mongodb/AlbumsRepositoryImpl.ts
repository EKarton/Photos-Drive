import { Document as MongoDbDocument, ObjectId, WithId } from 'mongodb';
import { Album, AlbumId, convertStringToAlbumId } from '../Albums';
import { AlbumNotFoundError, AlbumsRepository } from '../AlbumsRepository';
import { MongoDbClientsRepository } from './MongoDbClientsRepository';

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
      })
    };
  }
}
