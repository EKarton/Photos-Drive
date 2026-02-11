import {
  Collection,
  Filter,
  MongoClient,
  Document as MongoDbDocument,
  ObjectId,
  Sort,
  WithId
} from 'mongodb';
import logger from '../../../utils/logger';
import {
  Album,
  AlbumId,
  albumIdToString,
  convertStringToAlbumId
} from './Albums';
import {
  AlbumNotFoundError,
  AlbumsStore,
  ListAlbumsRequest,
  ListAlbumsResponse,
  SortByDirection,
  SortByField
} from './BaseAlbumsStore';

/** MongoDB implementation of {@code AlbumsRepository} */
export class MongoDbAlbumsStore implements AlbumsStore {
  private clientId: string;
  private collection: Collection;

  constructor(
    clientId: string,
    mongoClient: MongoClient,
    dbName: string = 'photos_drive',
    collectionName: string = 'albums'
  ) {
    this.clientId = clientId;
    this.collection = mongoClient.db(dbName).collection(collectionName);
  }

  getClientId(): string {
    return this.clientId;
  }

  async getAlbumById(
    id: AlbumId,
    options?: { abortController?: AbortController }
  ): Promise<Album> {
    const rawDocs = await this.collection.findOne(
      { _id: new ObjectId(id.objectId) },
      { signal: options?.abortController?.signal }
    );

    if (rawDocs === null) {
      throw new AlbumNotFoundError(id);
    }

    return this.convertMongoDbDocumentToAlbumInstance(id, rawDocs);
  }

  async getNumAlbumsInAlbum(
    id: AlbumId,
    options?: { abortController?: AbortController }
  ): Promise<number> {
    return this.collection.countDocuments(
      {
        parent_album_id: albumIdToString(id)
      },
      { signal: options?.abortController?.signal }
    );
  }

  async listAlbums(
    req: ListAlbumsRequest,
    options?: { abortController?: AbortController }
  ): Promise<ListAlbumsResponse> {
    const lastSeenAlbumId = req.pageToken
      ? convertStringToAlbumId(req.pageToken)
      : undefined;

    logger.debug(`List Albums Request: ${req}`);
    const filterObj: Filter<MongoDbDocument> = {};

    if (req.parentAlbumId) {
      filterObj['parent_album_id'] = albumIdToString(req.parentAlbumId);
    }

    if (lastSeenAlbumId) {
      const lastSeenAlbumObjectId = new ObjectId(lastSeenAlbumId.objectId);

      if (req.sortBy.field === SortByField.ID) {
        filterObj['_id'] =
          req.sortBy.direction === SortByDirection.ASCENDING
            ? { $gt: lastSeenAlbumObjectId }
            : { $lt: lastSeenAlbumObjectId };
      } else if (req.sortBy.field === SortByField.NAME) {
        const lastSeenAlbum = await this.collection.findOne(
          { _id: lastSeenAlbumObjectId },
          { signal: options?.abortController?.signal }
        );
        const lastSeenAlbumName = lastSeenAlbum!['name'];

        filterObj['$or'] =
          req.sortBy.direction === SortByDirection.ASCENDING
            ? [
                { name: { $gt: lastSeenAlbumName } },
                {
                  name: lastSeenAlbumName,
                  _id: { $gt: lastSeenAlbumObjectId }
                }
              ]
            : [
                { name: { $lt: lastSeenAlbumName } },
                {
                  name: lastSeenAlbumName,
                  _id: { $lt: lastSeenAlbumObjectId }
                }
              ];
      }
    }

    const mongoSortDirection =
      req.sortBy.direction === SortByDirection.ASCENDING ? 1 : -1;

    let sortObj: Sort;
    if (req.sortBy.field === SortByField.ID) {
      sortObj = {
        _id: mongoSortDirection
      };
    } else {
      sortObj = {
        name: mongoSortDirection,
        _id: mongoSortDirection
      };
    }

    logger.debug(`Filter object: ${JSON.stringify(filterObj)}`);
    logger.debug(`Sort object: ${JSON.stringify(sortObj)}`);
    logger.debug(`Limit size: ${req.pageSize}`);

    const rawDocs = await this.collection
      .find(filterObj, {
        collation: { locale: 'en', strength: 1 },
        signal: options?.abortController?.signal
      })
      .sort(sortObj)
      .limit(req.pageSize)
      .toArray();

    const albums = rawDocs.map((rawDoc) => {
      const albumId: AlbumId = {
        clientId: this.getClientId(),
        objectId: rawDoc._id.toString()
      };
      return this.convertMongoDbDocumentToAlbumInstance(albumId, rawDoc);
    });

    logger.debug(`Num albums: ${albums.length}`);

    const nextAlbumId =
      albums.length > 0 ? albums[albums.length - 1].id : undefined;

    return {
      albums,
      nextPageToken: nextAlbumId ? albumIdToString(nextAlbumId) : undefined
    };
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
        : undefined
    };
  }
}
