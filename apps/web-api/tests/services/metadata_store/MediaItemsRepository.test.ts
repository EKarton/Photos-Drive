import { mock } from 'jest-mock-extended';
import { MongoClient, ObjectId } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { AlbumId } from '../../../src/services/metadata_store/Albums';
import { MediaItemId } from '../../../src/services/metadata_store/MediaItems';
import {
  MediaItemNotFoundError,
  MediaItemsRepositoryImpl
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

    // Set up the database and collection
    const db = mongoClient.db('sharded_google_photos');
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

  afterAll(async () => {
    await mongoClient.close();
    await mongoServer.stop();
  });

  describe('getMediaItemById', () => {
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
});
