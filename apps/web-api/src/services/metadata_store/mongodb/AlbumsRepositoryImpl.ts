import { sum } from 'lodash';
import {
  Filter,
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
} from '../Albums';
import {
  AlbumNotFoundError,
  AlbumsRepository,
  ListAlbumsRequest,
  ListAlbumsResponse,
  SortBy,
  SortByDirection,
  SortByField
} from '../AlbumsRepository';
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
      .db('photos_drive')
      .collection('albums')
      .findOne({ _id: new ObjectId(id.objectId) });

    if (rawDocs === null) {
      throw new AlbumNotFoundError(id);
    }

    return this.convertMongoDbDocumentToAlbumInstance(id, rawDocs);
  }

  async getNumAlbumsInAlbum(id: AlbumId): Promise<number> {
    const counts = await Promise.all(
      this.mongoDbRepository.listClients().map(async ([_, mongoDbClient]) => {
        const numDocs = await mongoDbClient
          .db('photos_drive')
          .collection('albums')
          .countDocuments({
            parent_album_id: albumIdToString(id)
          });

        return numDocs;
      })
    );

    return sum(counts);
  }

  async listAlbums(req: ListAlbumsRequest): Promise<ListAlbumsResponse> {
    const clientIdToMongoClient = new Map(this.mongoDbRepository.listClients());
    const clientIdToAlbumId = new Map(
      req.pageToken?.split(',').map((pageToken) => {
        const albumId = convertStringToAlbumId(pageToken);
        return [albumId.clientId, albumId];
      })
    );
    const overFetchSize = req.pageSize * 2;

    const albums: Album[][] = await Promise.all(
      Array.from(clientIdToMongoClient).map(async ([clientId, mongoClient]) => {
        logger.debug(`List Albums Request: ${req}`);
        const filterObj: Filter<MongoDbDocument> = {};

        if (req.parentAlbumId) {
          filterObj['parent_album_id'] = albumIdToString(req.parentAlbumId);
        }

        const lastSeenAlbumId = clientIdToAlbumId.get(clientId)?.objectId;
        if (lastSeenAlbumId) {
          const lastSeenAlbumObjectId = new ObjectId(lastSeenAlbumId);

          if (req.sortBy.field === SortByField.ID) {
            filterObj['_id'] =
              req.sortBy.direction === SortByDirection.ASCENDING
                ? { $gt: lastSeenAlbumObjectId }
                : { $lt: lastSeenAlbumObjectId };
          } else if (req.sortBy.field === SortByField.NAME) {
            const lastSeenAlbum = await mongoClient
              .db('photos_drive')
              .collection('albums')
              .findOne({ _id: lastSeenAlbumObjectId });
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

        const sortObj: Sort = {};
        const mongoSortDirection =
          req.sortBy.direction === SortByDirection.ASCENDING ? 1 : -1;

        if (req.sortBy.field === SortByField.ID) {
          sortObj['_id'] = mongoSortDirection;
        } else if (req.sortBy.field === SortByField.NAME) {
          sortObj['name'] = mongoSortDirection;
          sortObj['_id'] = mongoSortDirection;
        }

        logger.debug(`Filter object: ${JSON.stringify(filterObj)}`);
        logger.debug(`Sort object: ${JSON.stringify(sortObj)}`);
        logger.debug(`Limit size: ${req.pageSize}`);

        const rawDocs = await mongoClient
          .db('photos_drive')
          .collection('albums')
          .find(filterObj, { collation: { locale: 'en', strength: 1 } })
          .sort(sortObj)
          .limit(overFetchSize)
          .toArray();

        const albums = rawDocs.map((rawDoc) => {
          const albumId: AlbumId = {
            clientId: clientId,
            objectId: rawDoc._id.toString()
          };
          return this.convertMongoDbDocumentToAlbumInstance(albumId, rawDoc);
        });

        logger.debug(`Num albums: ${albums.length}`);

        return albums;
      })
    );

    const sortedAlbums = albums
      .flat()
      .sort((a: Album, b: Album) => {
        return sortAlbum(a, b, req.sortBy);
      })
      .slice(0, req.pageSize);

    const clientIdToLastAlbumId = new Map<string, AlbumId>();
    for (let i = sortedAlbums.length - 1; i >= 0; i--) {
      const album = sortedAlbums.at(i);
      const clientId = album!.id.clientId;

      if (!clientIdToLastAlbumId.has(clientId)) {
        clientIdToLastAlbumId.set(clientId, album!.id);
      }
    }

    for (const [clientId, albumId] of clientIdToAlbumId) {
      if (!clientIdToLastAlbumId.has(clientId)) {
        clientIdToLastAlbumId.set(clientId, albumId);
      }
    }

    const nextPageToken =
      Array.from(clientIdToLastAlbumId.values())
        .map(albumIdToString)
        .join(',') || undefined;

    return {
      albums: sortedAlbums,
      nextPageToken: sortedAlbums.length > 0 ? nextPageToken : undefined
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

/** Returns -1 if a should go before b; else 1 based on {@code SortBy} */
export function sortAlbum(a: Album, b: Album, sortBy: SortBy): number {
  switch (sortBy.field) {
    case SortByField.ID:
      if (sortBy.direction === SortByDirection.ASCENDING) {
        return albumIdToString(a.id) < albumIdToString(b.id) ? -1 : 1;
      } else {
        return albumIdToString(a.id) > albumIdToString(b.id) ? -1 : 1;
      }
    case SortByField.NAME:
      if (sortBy.direction === SortByDirection.ASCENDING) {
        return a.name < b.name ? -1 : 1;
      } else {
        return a.name > b.name ? -1 : 1;
      }
  }
}
