import { MongoClient } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { MapCellsRepositoryImpl } from '../../../../src/services/maps_store/mongodb/MapCellsRepositoryImpl';
import { InMemoryMongoDbClientsRepository } from '../../../../src/services/metadata_store/mongodb/MongoDbClientsRepository';

describe('MapCellsRepositoryImpl', () => {
  let mongoServer1: MongoMemoryServer;
  let mongoServer2: MongoMemoryServer;
  let mongoClient1: MongoClient;
  let mongoClient2: MongoClient;
  let mapCellsRepo: MapCellsRepositoryImpl;

  beforeAll(async () => {
    mongoServer1 = await MongoMemoryServer.create();
    mongoServer2 = await MongoMemoryServer.create();
    mongoClient1 = await MongoClient.connect(mongoServer1.getUri(), {});
    mongoClient2 = await MongoClient.connect(mongoServer2.getUri(), {});

    const mongoDbClientsRepo = new InMemoryMongoDbClientsRepository([
      ['client1', mongoClient1],
      ['client2', mongoClient2]
    ]);
    mapCellsRepo = new MapCellsRepositoryImpl(mongoDbClientsRepo);
  }, 20000);

  afterEach(async () => {
    if (mongoClient1) {
      await mongoClient1.db('photos_drive').dropDatabase();
    }
    if (mongoClient2) {
      await mongoClient2.db('photos_drive').dropDatabase();
    }
  });

  afterAll(async () => {
    if (mongoClient1) {
      await mongoClient1.close(true);
    }
    if (mongoClient2) {
      await mongoClient2.close(true);
    }
    if (mongoServer1) {
      await mongoServer1.stop({ force: true });
    }
    if (mongoServer2) {
      await mongoServer2.stop({ force: true });
    }
  }, 20000);

  describe('getHeatmapPointsInCells', () => {
    beforeEach(async () => {
      await mongoClient1
        .db('photos_drive')
        .collection('map_cells')
        .insertMany([
          { cell_id: 'A1', album_id: 'client1:album1', media_item_id: 'client1:mid11' },
          { cell_id: 'A1', album_id: 'client1:album1', media_item_id: 'client1:mid12' },
          { cell_id: 'B2', album_id: 'client1:album2', media_item_id: 'client1:mid13' }
        ]);

      await mongoClient2
        .db('photos_drive')
        .collection('map_cells')
        .insertMany([
          { cell_id: 'A1', album_id: 'client2:album1', media_item_id: 'client2:mid21' },
          { cell_id: 'C3', album_id: 'client2:album3', media_item_id: 'client2:mid22' }
        ]);
    });

    it('should return correct heatmap points for a single cell across clients, all albums', async () => {
      const results = await mapCellsRepo.getHeatmapPointsInCells(
        ['A1'],
        undefined
      );

      // Only A1 should be present since others aren't queried
      expect(results.length).toBe(1);

      // Combines counts from both clients for A1
      const matchA1 = results.find((h) => h.cellId === 'A1');
      expect(matchA1?.count).toBe(3);
      expect(matchA1?.cellId).toBe('A1');
      expect(matchA1?.sampledMediaItemId).toBeDefined();

      expect(results.length).toBe(1);
      expect(results[0].cellId).toBe('A1');
      expect(results[0].count).toBe(3);
    });

    it('should return correct heatmap for multiple cells', async () => {
      const results = await mapCellsRepo.getHeatmapPointsInCells(
        ['A1', 'B2', 'C3'],
        undefined
      );

      expect(results.length).toEqual(3);
      expect(results.map((r) => r.cellId).sort()).toEqual(
        ['A1', 'B2', 'C3'].sort()
      );
      const b2 = results.find((r) => r.cellId === 'B2');
      const c3 = results.find((r) => r.cellId === 'C3');
      expect(b2?.count).toBe(1);
      expect(c3?.count).toBe(1);
    });

    it('should return empty array if no cell matches', async () => {
      const results = await mapCellsRepo.getHeatmapPointsInCells(
        ['Z9'],
        undefined
      );

      expect(results).toEqual([]);
    });

    it('should filter by albumId correctly', async () => {
      const albumId = { clientId: 'client1', objectId: 'album1' };
      const results = await mapCellsRepo.getHeatmapPointsInCells(
        ['A1', 'B2'],
        albumId
      );

      // Only cell A1 documents from client1:album1, and no B2 in album1
      expect(results.length).toBe(1);
      expect(results[0].cellId).toBe('A1');
      expect(results[0].count).toBe(2);
    });
  });
});
