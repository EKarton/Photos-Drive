import { performance } from 'perf_hooks';
import { filter, sum } from 'lodash';
import { Filter, Document as MongoDbDocument } from 'mongodb';
import { AlbumId, albumIdToString } from '../../metadata_store/Albums';
import {
  convertStringToMediaItemId,
  MediaItemId
} from '../../metadata_store/MediaItems';
import { MongoDbClientsRepository } from '../../metadata_store/mongodb/MongoDbClientsRepository';
import { TileId, TilesRepository } from '../TilesRepository';

export const MAX_ZOOM_LEVEL = 15;

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
    const start = performance.now();
    const filterObj: Filter<MongoDbDocument> = {
      x: tileId.x,
      y: tileId.y,
      z: tileId.z
    };

    if (tileId.z > MAX_ZOOM_LEVEL) {
      filterObj['z'] = { $gt: MAX_ZOOM_LEVEL };
    }

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

    console.log(`Time for getNumMediaItems: ${performance.now() - start}`);

    return sum(counts);
  }

  async getMediaItems(
    tileId: TileId,
    albumId: AlbumId | undefined,
    limit: number | undefined
  ): Promise<MediaItemId[]> {
    const start = performance.now();
    const filterObj: Filter<MongoDbDocument> = {
      x: tileId.x,
      y: tileId.y,
      z: tileId.z
    };

    if (tileId.z > MAX_ZOOM_LEVEL) {
      filterObj['z'] = { $gt: MAX_ZOOM_LEVEL };
    }

    if (albumId) {
      filterObj['album_id'] = albumIdToString(albumId);
    }

    // Run all queries concurrently
    const queryPromises = [...this.mongoDbRepository.listClients()].map(
      async ([_, mongoDbClient]) => {
        let query = mongoDbClient
          .db('photos_drive')
          .collection('tiles')
          .find(filterObj)
          .project({ media_item_id: 1 });

        // We can apply limit here if you want per-client limiting,
        if (limit) {
          query = query.limit(limit);
        }

        const docs = await query.toArray();
        return docs.map((doc) =>
          convertStringToMediaItemId(doc['media_item_id'])
        );
      }
    );

    const resultsArrays = await Promise.all(queryPromises);

    // Flatten results
    let mediaItemIds = resultsArrays.flat();
    if (limit) {
      mediaItemIds = mediaItemIds.slice(0, limit);
    }

    console.log(`Time for getMediaItems: ${performance.now() - start}`);

    return mediaItemIds;
  }
}
