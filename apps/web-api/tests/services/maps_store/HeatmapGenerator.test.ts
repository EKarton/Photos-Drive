import { cellToLatLng, latLngToCell, polygonToCells } from 'h3-js';
import { MongoClient } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import {
  HeatmapGenerator,
  Tile
} from '../../../src/services/maps_store/HeatmapGenerator';
import { MapCellsRepository } from '../../../src/services/maps_store/MapCellsRepository';
import { MapCellsRepositoryImpl } from '../../../src/services/maps_store/mongodb/MapCellsRepositoryImpl';
import {
  Album,
  AlbumId,
  albumIdToString
} from '../../../src/services/metadata_store/Albums';
import {
  mediaIdToString,
  MediaItem,
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
  objectId: 'album1'
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
    await insertMediaItemToDatabase(MEDIA_ITEM_ID_1, -70, 90, ALBUM_ID_1);
    await insertMediaItemToDatabase(MEDIA_ITEM_ID_1, -71, 91, ALBUM_ID_1);
    await insertMediaItemToDatabase(MEDIA_ITEM_ID_1, -72, 92, ALBUM_ID_2);

    const tile: Tile = { x: 48, y: 53, z: 6 };
    const result = await heatmapGenerator.getHeatmapForTile(tile, undefined);

    expect(result).toBeNull();
  });

  it('returns points that belong to an album if albumId is passed', async () => {
    // Insert some data to the db
    await insertMediaItemToDatabase(MEDIA_ITEM_ID_1, -70, 90, ALBUM_ID_1);
    await insertMediaItemToDatabase(MEDIA_ITEM_ID_1, -71, 91, ALBUM_ID_1);
    await insertMediaItemToDatabase(MEDIA_ITEM_ID_1, -72, 92, ALBUM_ID_2);

    const tile: Tile = { x: 48, y: 53, z: 6 };
    const result = await heatmapGenerator.getHeatmapForTile(tile, ALBUM_ID_1);

    expect(result).toBeNull();
  });

  it('returns empty heatmap if no cells returned', async () => {
    const tile: Tile = { x: 0, y: 0, z: 4 };
    const result = await heatmapGenerator.getHeatmapForTile(tile, undefined);

    expect(result).toBeNull();
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
