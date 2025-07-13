import { filter, sum } from 'lodash';
import { Filter, Document as MongoDbDocument } from 'mongodb';
import { AlbumId, albumIdToString } from '../../metadata_store/Albums';
import {
  convertStringToMediaItemId,
  MediaItemId
} from '../../metadata_store/MediaItems';
import { MongoDbClientsRepository } from '../../metadata_store/mongodb/MongoDbClientsRepository';
import { TileId, TilesRepository } from '../TilesRepository';

/** Implementation of {@code TilesRepository} */
export class TilesRepositoryImpl implements TilesRepository {
  private mongoDbRepository: MongoDbClientsRepository;

  constructor(mongoDbRepository: MongoDbClientsRepository) {
    this.mongoDbRepository = mongoDbRepository;
  }

  async getNumMediaItems(
    tileId: TileId,
    albumId: AlbumId | undefined
  ): Promise<number> {
    const filterObj: Filter<MongoDbDocument> = {
      x: tileId.x,
      y: tileId.y,
      z: tileId.z
    };

    if (albumId) {
      filterObj['album_id'] = albumIdToString(albumId);
    }

    const counts = await Promise.all(
      this.mongoDbRepository.listClients().map(async ([_, mongoDbClient]) => {
        const numDocs = await mongoDbClient
          .db('photos_drive')
          .collection('tiles')
          .countDocuments(filterObj);

        return numDocs;
      })
    );

    console.log(counts);

    return sum(counts);
  }

  async getMediaItems(
    tileId: TileId,
    albumId: AlbumId | undefined,
    limit: number | undefined
  ): Promise<MediaItemId[]> {
    const filterObj: Filter<MongoDbDocument> = {
      x: tileId.x,
      y: tileId.y,
      z: tileId.z
    };

    if (albumId) {
      filterObj['album_id'] = albumIdToString(albumId);
    }

    let mediaItemIds: MediaItemId[] = [];

    for (const [_, mongoDbClient] of this.mongoDbRepository.listClients()) {
      let query = mongoDbClient
        .db('photos_drive')
        .collection('tiles')
        .find(filterObj);

      if (limit) {
        query = query.limit(limit - mediaItemIds.length);
      }

      const docs = await query.toArray();
      const curMediaItemIds = docs.map((doc) =>
        convertStringToMediaItemId(doc['media_item_id'])
      );
      mediaItemIds = mediaItemIds.concat(curMediaItemIds);

      if (limit && mediaItemIds.length >= limit) {
        break;
      }
    }

    return mediaItemIds;
  }
}
