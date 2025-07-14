import { performance } from 'perf_hooks';
import { sum } from 'lodash';
import { Filter, Document as MongoDbDocument } from 'mongodb';
import { AlbumId, albumIdToString } from '../../metadata_store/Albums';
import { MediaItemId } from '../../metadata_store/MediaItems';
import { MongoDbClientsRepository } from '../../metadata_store/mongodb/MongoDbClientsRepository';
import { CellId, MapCellsRepository } from '../MapCellsRepository';

export const MAX_ZOOM_LEVEL = 15;

/** Implementation of {@code TilesRepository} */
export class MapCellsRepositoryImpl implements MapCellsRepository {
  private mongoDbRepository: MongoDbClientsRepository;

  constructor(mongoDbRepository: MongoDbClientsRepository) {
    this.mongoDbRepository = mongoDbRepository;
  }

  async getNumMediaItemInCell(
    cellId: CellId,
    albumId: AlbumId | undefined
  ): Promise<number> {
    const start = performance.now();
    const counts = await Promise.all(
      this.mongoDbRepository.listClients().map(async ([_, client]) => {
        const query: Filter<MongoDbDocument> = {
          cell_id: cellId
        };
        if (albumId) {
          query['album_id'] = albumIdToString(albumId);
        }

        return client
          .db('photos_drive')
          .collection('map_cells')
          .countDocuments(query);
      })
    );

    console.log('getNumMediaItemInCells took', performance.now() - start);

    return sum(counts);
  }

  async getNumMediaItemsInCells(
    cellIds: CellId[],
    albumId: AlbumId | undefined
  ): Promise<Map<CellId, number>> {
    const start = performance.now();

    const clientCounts = await Promise.all(
      this.mongoDbRepository.listClients().map(async ([_, client]) => {
        const query: Filter<MongoDbDocument> = {
          cell_id: { $in: cellIds }
        };
        if (albumId) {
          query['album_id'] = albumIdToString(albumId);
        }

        const docs = await client
          .db('photos_drive')
          .collection('map_cells')
          .aggregate([
            {
              $match: query
            },
            {
              $group: {
                _id: '$cell_id',
                count: { $sum: 1 }
              }
            }
          ])
          .toArray();

        return docs.map((doc) => ({
          cellId: doc['_id'] as string,
          count: doc['count'] as number
        }));
      })
    );

    const counts = clientCounts.flat();
    const results = new Map<CellId, number>();
    for (const entry of counts) {
      results.set(entry.cellId, (results.get(entry.cellId) || 0) + entry.count);
    }

    console.log('getNumMediaItemsInCells took', performance.now() - start);

    return results;
  }

  async getMediaItems(
    cellIds: CellId[],
    albumId: AlbumId | undefined,
    limit: number | undefined
  ): Promise<MediaItemId[]> {
    throw new Error('Method not implemented.');
  }
}
