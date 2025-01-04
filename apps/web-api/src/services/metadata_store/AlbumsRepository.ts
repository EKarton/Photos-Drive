import { Document as MongoDbDocument, ObjectId, WithId } from 'mongodb'
import { Album, AlbumId } from './Albums'
import { MongoDbClientsRepository } from './MongoDbClientsRepository'

/** A class that stores the albums from the database. */
export interface AlbumsRepository {
  getAlbumById(id: AlbumId): Promise<Album>
}

/** Implementation of {@code AlbumsRepository} */
export class AlbumsRepositoryImpl implements AlbumsRepository {
  private mongoDbRepository: MongoDbClientsRepository

  constructor(mongoDbRepository: MongoDbClientsRepository) {
    this.mongoDbRepository = mongoDbRepository
  }

  async getAlbumById(id: AlbumId): Promise<Album> {
    const mongoDbClient = this.mongoDbRepository.getClientFromId(id.clientId)
    const rawDocs = await mongoDbClient
      .db('sharded_google_photos')
      .collection('albums')
      .findOne({ _id: new ObjectId(id.objectId) })

    if (rawDocs === null) {
      throw new AlbumNotFoundError(id)
    }

    return this.convertMongoDbDocumentToAlbumInstance(id, rawDocs)
  }

  private convertMongoDbDocumentToAlbumInstance(
    id: AlbumId,
    doc: WithId<MongoDbDocument>
  ): Album {
    return {
      id: id,
      name: doc['name'],
      parent_album_id: this.convertMongoDbObjectId(doc['parent_album_id']),
      child_album_ids: doc['child_album_ids'].map((albumId: string) => {
        return this.convertMongoDbObjectId(albumId)
      }),
      media_item_ids: doc['media_item_ids'].map((mediaItemId: string) => {
        return this.convertMongoDbObjectId(mediaItemId)
      })
    }
  }

  private convertMongoDbObjectId(rawType?: string): AlbumId | undefined {
    const parts = rawType?.split(':') || []
    if (parts.length == 2 && parts[0] && parts[1]) {
      return {
        clientId: parts[0],
        objectId: parts[1]
      }
    }

    return undefined
  }
}

/** Represents an error for when an album is not found. */
export class AlbumNotFoundError extends Error {
  constructor(albumId: AlbumId) {
    super(`Cannot find album with id ${albumId}`)
    this.name = 'AlbumNotFoundError'
  }
}
