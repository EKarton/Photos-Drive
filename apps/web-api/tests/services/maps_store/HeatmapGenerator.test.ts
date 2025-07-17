import { latLngToCell } from 'h3-js';
import { MongoClient } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import {
  HeatmapGenerator,
  Tile
} from '../../../src/services/maps_store/HeatmapGenerator';
import { MapCellsRepositoryImpl } from '../../../src/services/maps_store/mongodb/MapCellsRepositoryImpl';
import {
  AlbumId,
  albumIdToString
} from '../../../src/services/metadata_store/Albums';
import {
  mediaIdToString,
  MediaItemId
} from '../../../src/services/metadata_store/MediaItems';
import { InMemoryMongoDbClientsRepository } from '../../../src/services/metadata_store/mongodb/MongoDbClientsRepository';

const MEDIA_ITEM_ID_1: MediaItemId = {
  clientId: 'client1',
  objectId: 'mediaItem1'
};

const MEDIA_ITEM_ID_2: MediaItemId = {
  clientId: 'client1',
  objectId: 'mediaItem2'
};

const MEDIA_ITEM_ID_3: MediaItemId = {
  clientId: 'client1',
  objectId: 'mediaItem3'
};

const ALBUM_ID_1: AlbumId = {
  clientId: 'client1',
  objectId: 'album1'
};

const ALBUM_ID_2: AlbumId = {
  clientId: 'client1',
  objectId: 'album2'
};

describe('HeatmapGenerator', () => {
  let mongoServer1: MongoMemoryServer;
  let mongoClient1: MongoClient;
  let heatmapGenerator: HeatmapGenerator;

  beforeAll(async () => {
    mongoServer1 = await MongoMemoryServer.create();
    mongoClient1 = await MongoClient.connect(mongoServer1.getUri(), {});

    const mongoDbClientsRepo = new InMemoryMongoDbClientsRepository([
      ['client1', mongoClient1]
    ]);
    const mapCellsRepo = new MapCellsRepositoryImpl(mongoDbClientsRepo);
    heatmapGenerator = new HeatmapGenerator(mapCellsRepo);
  }, 20000);

  afterEach(async () => {
    if (mongoClient1) {
      await mongoClient1.db('photos_drive').dropDatabase();
    }
  });

  afterAll(async () => {
    if (mongoClient1) {
      await mongoClient1.close(true);
    }
    if (mongoServer1) {
      await mongoServer1.stop({ force: true });
    }
  }, 20000);

  it('returns heatmap points given data exists in the region', async () => {
    // Insert some data to the db
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_1,
      40.714236894670336,
      -74.00616064667702,
      ALBUM_ID_1
    );
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_2,
      40.74434432061207,
      -74.00057852268219,
      ALBUM_ID_1
    );
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_3,
      40.77004083960827,
      -74.02383582932607,
      ALBUM_ID_2
    );

    const tile: Tile = { x: 602, y: 769, z: 11 };
    const result = await heatmapGenerator.getHeatmapForTile(tile, undefined);

    expect(result.points.length).toEqual(2);
    const point1 = result.points.find(
      (point) => point.sampledMediaItemId.objectId == MEDIA_ITEM_ID_1.objectId
    );
    expect(point1).toEqual({
      cellId: '8a2a1072c66ffff',
      count: 1,
      latitude: 40.714624300619306,
      longitude: -74.0063425810389,
      sampledMediaItemId: MEDIA_ITEM_ID_1
    });
    const point2 = result.points.find(
      (point) => point.sampledMediaItemId.objectId == MEDIA_ITEM_ID_3.objectId
    );
    expect(point2).toEqual({
      cellId: '8a2a1072466ffff',
      count: 1,
      latitude: 40.7696724616256,
      longitude: -74.02351373030828,
      sampledMediaItemId: MEDIA_ITEM_ID_3
    });
  });

  it('returns points that belong to an album if albumId is passed', async () => {
    // Insert some data to the db
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_1,
      40.714236894670336,
      -74.00616064667702,
      ALBUM_ID_1
    );
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_2,
      40.74434432061207,
      -74.00057852268219,
      ALBUM_ID_1
    );
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_3,
      40.77004083960827,
      -74.02383582932607,
      ALBUM_ID_2
    );

    const tile: Tile = { x: 602, y: 769, z: 11 };
    const result = await heatmapGenerator.getHeatmapForTile(tile, ALBUM_ID_2);

    expect(result.points.length).toEqual(1);
    expect(result.points[0]).toEqual({
      cellId: '8a2a1072466ffff',
      count: 1,
      latitude: 40.7696724616256,
      longitude: -74.02351373030828,
      sampledMediaItemId: MEDIA_ITEM_ID_3
    });
  });

  it('returns empty heatmap if no cells returned', async () => {
    // Insert some data to the db
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_1,
      40.714236894670336,
      -74.00616064667702,
      ALBUM_ID_1
    );
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_1,
      40.74434432061207,
      -74.00057852268219,
      ALBUM_ID_1
    );
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_1,
      40.77004083960827,
      -74.02383582932607,
      ALBUM_ID_2
    );

    const tile: Tile = { x: 1, y: 2, z: 3 };
    const result = await heatmapGenerator.getHeatmapForTile(tile, undefined);

    expect(result).toEqual({ points: [] });
  });

  it('returns empty heatmap if no cells returned and it is zoomed in', async () => {
    // Insert some data to the db
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_1,
      40.714236894670336,
      -74.00616064667702,
      ALBUM_ID_1
    );
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_1,
      40.74434432061207,
      -74.00057852268219,
      ALBUM_ID_1
    );
    await insertMediaItemToDatabase(
      MEDIA_ITEM_ID_1,
      40.77004083960827,
      -74.02383582932607,
      ALBUM_ID_2
    );

    const tile: Tile = { x: 1, y: 2, z: 20 };
    const result = await heatmapGenerator.getHeatmapForTile(tile, undefined);

    expect(result).toEqual({ points: [] });
  });

  /**
   * Inserts an image to the db.
   * It mimics the same behavior as {@code apps/cli-client/photos_drive/shared/maps/mongodb/map_cells_repository_impl.py}
   */
  async function insertMediaItemToDatabase(
    mediaItemId: MediaItemId,
    latitude: number,
    longitude: number,
    albumId: AlbumId
  ) {
    for (let zoom = 0; zoom <= 15; zoom++) {
      await mongoClient1
        .db('photos_drive')
        .collection('map_cells')
        .insertOne({
          cell_id: latLngToCell(latitude, longitude, zoom),
          album_id: albumIdToString(albumId),
          media_item_id: mediaIdToString(mediaItemId)
        });
    }
  }
});
