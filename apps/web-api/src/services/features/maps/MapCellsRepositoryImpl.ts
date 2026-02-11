import { Filter, Document as MongoDbDocument } from 'mongodb';
import { AlbumId, albumIdToString } from '../../core/albums/Albums';
import { MongoDbClientsStore } from '../../core/databases/MongoDbClientsStore';
import { convertStringToMediaItemId } from '../../core/media_items/MediaItems';
import {
  CellId,
  HeatmapPoints,
  MapCellsRepository
} from './MapCellsRepository';

/** The max h3 zoom level */
export const MAX_ZOOM_LEVEL = 15;

/** The max query time for MongoDB */
export const MAX_QUERY_TIME_MS = 5000;

/** Implementation of {@code TilesRepository} */
export class MapCellsRepositoryImpl implements MapCellsRepository {
  private mongoDbRepository: MongoDbClientsStore;

  constructor(mongoDbRepository: MongoDbClientsStore) {
    this.mongoDbRepository = mongoDbRepository;
  }

  async getHeatmapPointsInCells(
    cellIds: CellId[],
    albumId: AlbumId | undefined,
    options?: { abortController?: AbortController }
  ): Promise<HeatmapPoints[]> {
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
          .aggregate(
            [
              {
                $match: query
              },
              {
                $group: {
                  _id: '$cell_id',
                  count: { $sum: 1 },
                  sampleMediaItemId: { $first: '$media_item_id' }
                }
              }
            ],
            {
              signal: options?.abortController?.signal
            }
          )
          .maxTimeMS(MAX_QUERY_TIME_MS)
          .toArray();

        return docs.map((doc) => ({
          cellId: doc['_id'] as string,
          count: doc['count'] as number,
          sampledMediaItemId: convertStringToMediaItemId(
            doc['sampleMediaItemId'] as string
          )
        }));
      })
    );

    const counts = clientCounts.flat();
    const results = new Map<CellId, HeatmapPoints>();
    for (const { cellId, count, sampledMediaItemId } of counts) {
      results.set(cellId, {
        cellId,
        count: (results.get(cellId)?.count || 0) + count,
        sampledMediaItemId:
          results.get(cellId)?.sampledMediaItemId ?? sampledMediaItemId
      });
    }

    return [...results.values()];
  }
}
