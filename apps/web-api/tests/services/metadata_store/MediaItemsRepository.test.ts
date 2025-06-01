import { mock } from 'jest-mock-extended';
import { MongoClient, ObjectId } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { AlbumId } from '../../../src/services/metadata_store/Albums';
import {
  MediaItem,
  MediaItemId
} from '../../../src/services/metadata_store/MediaItems';
import {
  MediaItemNotFoundError,
  MediaItemsRepositoryImpl,
  SortBy,
  SortByDirection,
  SortByField,
  sortMediaItem
} from '../../../src/services/metadata_store/MediaItemsRepository';
import { MongoDbClientsRepository } from '../../../src/services/metadata_store/MongoDbClientsRepository';

describe('MediaItemsRepositoryImpl', () => {
  let mongoServer: MongoMemoryServer;
  let mongoClient: MongoClient;
  let mediaItemsRepo: MediaItemsRepositoryImpl;
  let mockMongoDbClientsRepository: jest.Mocked<MongoDbClientsRepository>;

  beforeAll(async () => {
    // Start the in-memory MongoDB server
    mongoServer = await MongoMemoryServer.create();
    mongoClient = await MongoClient.connect(mongoServer.getUri());

    // Mock the MongoDbClientsRepository to return our in-memory client
    mockMongoDbClientsRepository = mock<MongoDbClientsRepository>();
    mockMongoDbClientsRepository.getClientFromId.mockReturnValue(mongoClient);

    // Initialize the repository
    mediaItemsRepo = new MediaItemsRepositoryImpl(mockMongoDbClientsRepository);
  });

  afterAll(async () => {
    await mongoClient.close();
    await mongoServer.stop();
  });

  describe('getMediaItemById', () => {
    beforeEach(async () => {
      // Set up the database and collection
      const db = mongoClient.db('sharded_google_photos');
      await db.collection('media_items').deleteMany({});
      await db.collection('media_items').insertOne({
        _id: new ObjectId('507f1f77bcf86cd799439011'),
        file_name: 'test_image.jpg',
        gphotos_client_id: 'gphotos_client_1',
        gphotos_media_item_id: 'media_item_1',
        location: {
          coordinates: [40.7128, -74.006] // longitude, latitude
        },
        album_id: `407f1f77bcf86cd799439001:407f1f77bcf86cd799439002`
      });
    });

    it('should return a media item when found', async () => {
      const mediaItemId: MediaItemId = {
        clientId: 'client1',
        objectId: '507f1f77bcf86cd799439011'
      };
      const albumId: AlbumId = {
        clientId: '407f1f77bcf86cd799439001',
        objectId: '407f1f77bcf86cd799439002'
      };

      const result = await mediaItemsRepo.getMediaItemById(mediaItemId);

      expect(result).toEqual({
        id: mediaItemId,
        file_name: 'test_image.jpg',
        gphotos_client_id: 'gphotos_client_1',
        gphotos_media_item_id: 'media_item_1',
        location: {
          longitude: 40.7128,
          latitude: -74.006
        },
        album_id: albumId
      });
    });

    it('should throw MediaItemNotFoundError when media item is not found', async () => {
      const mediaItemId: MediaItemId = {
        clientId: 'client1',
        objectId: '507f1f77bcf86cd799439012' // Non-existent ID
      };

      await expect(
        mediaItemsRepo.getMediaItemById(mediaItemId)
      ).rejects.toThrow(MediaItemNotFoundError);
      await expect(
        mediaItemsRepo.getMediaItemById(mediaItemId)
      ).rejects.toThrow(`Cannot find media item with id ${mediaItemId}`);
    });
  });

  describe('getMediaItemsInAlbum', () => {
    const albumId: AlbumId = {
      clientId: '407f1f77bcf86cd799439001',
      objectId: '407f1f77bcf86cd799439002'
    };

    beforeEach(async () => {
      // Clear and repopulate collection for each test
      const db = mongoClient.db('sharded_google_photos');
      await db.collection('media_items').deleteMany({});
      await db.collection('media_items').insertMany([
        {
          _id: new ObjectId('507f1f77bcf86cd799439011'),
          file_name: 'image1.jpg',
          gphotos_client_id: 'gphotos_client_1',
          gphotos_media_item_id: 'media_item_1',
          album_id: `${albumId.clientId}:${albumId.objectId}`,
          location: {
            coordinates: [40.0, -70.0]
          }
        },
        {
          _id: new ObjectId('507f1f77bcf86cd799439012'),
          file_name: 'image2.jpg',
          gphotos_client_id: 'gphotos_client_2',
          gphotos_media_item_id: 'media_item_2',
          album_id: `${albumId.clientId}:${albumId.objectId}`
        }
      ]);
    });

    it('should return all media items in the album across clients', async () => {
      // Simulate two clients sharing the same underlying MongoDB
      mockMongoDbClientsRepository.listClients.mockReturnValue([
        ['client1', mongoClient],
        ['client2', mongoClient]
      ]);

      const results = await mediaItemsRepo.getMediaItemsInAlbum(albumId);

      expect(results).toHaveLength(4);

      const fileNames = results.map((item) => item.file_name).sort();
      expect(fileNames).toEqual([
        'image1.jpg',
        'image1.jpg',
        'image2.jpg',
        'image2.jpg'
      ]);

      for (const item of results) {
        expect(item.album_id).toEqual(albumId);
        expect(item.id.clientId).toMatch(/client1|client2/);
        expect(item.id.objectId).toMatch(/507f1f77bcf86cd79943901[1|2]/);
      }
    });

    it('should return an empty array when no media items match the albumId', async () => {
      // Use different albumId to query
      const emptyAlbumId: AlbumId = {
        clientId: 'nonexistent',
        objectId: 'nothinghere'
      };

      mockMongoDbClientsRepository.listClients.mockReturnValue([
        ['client1', mongoClient]
      ]);

      const results = await mediaItemsRepo.getMediaItemsInAlbum(emptyAlbumId);

      expect(results).toEqual([]);
    });
  });

  describe('listMediaItemsInAlbum', () => {
    const albumId: AlbumId = {
      clientId: 'client1',
      objectId: 'album123'
    };

    beforeEach(async () => {
      const db = mongoClient.db('sharded_google_photos');
      await db.collection('media_items').deleteMany({});
      await db.collection('media_items').insertMany([
        {
          _id: new ObjectId('507f1f77bcf86cd799439010'),
          id: 'client1:item_1',
          file_name: 'a.jpg',
          gphotos_client_id: 'gphotos_client_1',
          gphotos_media_item_id: 'item_1',
          album_id: `${albumId.clientId}:${albumId.objectId}`
        },
        {
          _id: new ObjectId('507f1f77bcf86cd799439011'),
          id: 'client1:item_2',
          file_name: 'b.jpg',
          gphotos_client_id: 'gphotos_client_1',
          gphotos_media_item_id: 'item_2',
          album_id: `${albumId.clientId}:${albumId.objectId}`
        },
        {
          _id: new ObjectId('507f1f77bcf86cd799439012'),
          id: 'client1:item_3',
          file_name: 'c.jpg',
          gphotos_client_id: 'gphotos_client_1',
          gphotos_media_item_id: 'item_3',
          album_id: `${albumId.clientId}:${albumId.objectId}`
        }
      ]);

      mockMongoDbClientsRepository.listClients.mockReturnValue([
        ['client1', mongoClient]
      ]);
    });

    it('returns sorted media items in ascending order', async () => {
      const res = await mediaItemsRepo.listMediaItemsInAlbum({
        albumId,
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res.mediaItems).toHaveLength(3);
      expect(res.mediaItems.map((m) => m.file_name)).toEqual([
        'a.jpg',
        'b.jpg',
        'c.jpg'
      ]);
    });

    it('returns sorted media items in descending order', async () => {
      const res = await mediaItemsRepo.listMediaItemsInAlbum({
        albumId,
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res.mediaItems.map((m) => m.file_name)).toEqual([
        'c.jpg',
        'b.jpg',
        'a.jpg'
      ]);
    });

    it('respects the page size', async () => {
      const res = await mediaItemsRepo.listMediaItemsInAlbum({
        albumId,
        pageSize: 2,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res.mediaItems).toHaveLength(2);
      expect(res.nextPageToken).toBeDefined();
    });

    it('uses nextPageToken to continue pagination', async () => {
      const firstPage = await mediaItemsRepo.listMediaItemsInAlbum({
        albumId,
        pageSize: 2,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      const secondPage = await mediaItemsRepo.listMediaItemsInAlbum({
        albumId,
        pageSize: 2,
        pageToken: firstPage.nextPageToken!,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(secondPage.mediaItems).toHaveLength(1);
      expect(secondPage.mediaItems[0].file_name).toEqual('c.jpg');
    });

    it('returns empty result if no items match the album', async () => {
      const emptyAlbum: AlbumId = {
        clientId: 'other',
        objectId: 'nothing'
      };

      const res = await mediaItemsRepo.listMediaItemsInAlbum({
        albumId: emptyAlbum,
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res.mediaItems).toHaveLength(0);
      expect(res.nextPageToken).toBeUndefined();
    });

    it('throws if sort field is invalid', async () => {
      const invalidSortReq = {
        albumId,
        pageSize: 10,
        sortBy: {
          field: 'invalid' as SortByField,
          direction: SortByDirection.ASCENDING
        }
      };

      await expect(
        mediaItemsRepo.listMediaItemsInAlbum(invalidSortReq)
      ).rejects.toThrow('Unhandled sortBy field: invalid');
    });

    it('returns merged results in sorted order from multiple clients', async () => {
      // Simulate same data under two clients
      mockMongoDbClientsRepository.listClients.mockReturnValue([
        ['client1', mongoClient],
        ['client2', mongoClient]
      ]);

      const res = await mediaItemsRepo.listMediaItemsInAlbum({
        albumId,
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res.mediaItems).toHaveLength(6);
      const clientIds = new Set(res.mediaItems.map((m) => m.id.clientId));
      expect(clientIds.has('client1')).toBe(true);
      expect(clientIds.has('client2')).toBe(true);
    });
  });
});

describe('sortMediaItem', () => {
  const albumId: AlbumId = {
    clientId: 'albumClient1',
    objectId: 'albumObject1'
  };

  // Helper to create MediaItem with a given id string
  function createMediaItem(clientId: string, objectId: string): MediaItem {
    return {
      id: { clientId, objectId },
      file_name: 'file.jpg',
      gphotos_client_id: 'gphotos_client',
      gphotos_media_item_id: 'gphotos_media_id',
      album_id: albumId
    };
  }

  describe('sorting by ID ascending', () => {
    const sortBy: SortBy = {
      field: SortByField.ID,
      direction: SortByDirection.ASCENDING
    };

    it('returns -1 if a.id < b.id', () => {
      const a = createMediaItem('clientA', 'obj1');
      const b = createMediaItem('clientB', 'obj2');
      // Compare string versions: "clientA:obj1" < "clientB:obj2"?

      // Since 'clientA:obj1' < 'clientB:obj2' lex order, expect -1
      expect(sortMediaItem(a, b, sortBy)).toBe(-1);
    });

    it('returns 1 if a.id > b.id', () => {
      const a = createMediaItem('clientC', 'obj9');
      const b = createMediaItem('clientB', 'obj2');
      // "clientC:obj9" > "clientB:obj2" lex order, expect 1
      expect(sortMediaItem(a, b, sortBy)).toBe(1);
    });
  });

  describe('sorting by ID descending', () => {
    const sortBy: SortBy = {
      field: SortByField.ID,
      direction: SortByDirection.DESCENDING
    };

    it('returns -1 if a.id > b.id', () => {
      const a = createMediaItem('clientC', 'obj9');
      const b = createMediaItem('clientB', 'obj2');
      // Descending means reversed logic:
      // if a.id > b.id => return -1
      expect(sortMediaItem(a, b, sortBy)).toBe(-1);
    });

    it('returns 1 if a.id < b.id', () => {
      const a = createMediaItem('clientA', 'obj1');
      const b = createMediaItem('clientB', 'obj2');
      // Descending means if a.id < b.id => return 1
      expect(sortMediaItem(a, b, sortBy)).toBe(1);
    });
  });
});
