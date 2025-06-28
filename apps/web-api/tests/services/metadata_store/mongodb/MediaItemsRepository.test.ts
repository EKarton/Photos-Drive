import { MongoClient, ObjectId } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { AlbumId } from '../../../../src/services/metadata_store/Albums';
import {
  MediaItem,
  MediaItemId
} from '../../../../src/services/metadata_store/MediaItems';
import {
  MediaItemNotFoundError,
  SortBy,
  SortByDirection,
  SortByField
} from '../../../../src/services/metadata_store/MediaItemsRepository';
import {
  MediaItemsRepositoryImpl,
  sortMediaItem
} from '../../../../src/services/metadata_store/mongodb/MediaItemsRepositoryImpl';
import { InMemoryMongoDbClientsRepository } from '../../../../src/services/metadata_store/mongodb/MongoDbClientsRepository';

describe('MediaItemsRepositoryImpl', () => {
  let mongoServer1: MongoMemoryServer;
  let mongoServer2: MongoMemoryServer;
  let mongoClient1: MongoClient;
  let mongoClient2: MongoClient;

  let mediaItemsRepo: MediaItemsRepositoryImpl;

  beforeAll(async () => {
    // Start the in-memory MongoDB server
    mongoServer1 = await MongoMemoryServer.create();
    mongoServer2 = await MongoMemoryServer.create();
    mongoClient1 = await MongoClient.connect(mongoServer1.getUri(), {});
    mongoClient2 = await MongoClient.connect(mongoServer2.getUri(), {});

    const mongoDbClientsRepo = new InMemoryMongoDbClientsRepository([
      ['client1', mongoClient1],
      ['client2', mongoClient2]
    ]);
    mediaItemsRepo = new MediaItemsRepositoryImpl(mongoDbClientsRepo);
  });

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
  }, 10000);

  describe('getMediaItemById', () => {
    const mediaItemId: MediaItemId = {
      clientId: 'client1',
      objectId: '507f1f77bcf86cd799439011'
    };

    it('should return a media item when found', async () => {
      await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439011'),
          file_name: 'test_image.jpg',
          gphotos_client_id: 'gphotos_client_1',
          gphotos_media_item_id: 'media_item_1',
          location: {
            coordinates: [40.7128, -74.006] // longitude, latitude
          },
          album_id: `407f1f77bcf86cd799439001:407f1f77bcf86cd799439002`,
          width: 1000,
          height: 2000,
          date_taken: new Date(2024, 4, 4)
        });

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
        album_id: {
          clientId: '407f1f77bcf86cd799439001',
          objectId: '407f1f77bcf86cd799439002'
        },
        width: 1000,
        height: 2000,
        date_taken: new Date(2024, 4, 4)
      });
    });

    it('should return the media item correctly when width, height, and date_time is not set', async () => {
      await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439011'),
          file_name: 'test_image.jpg',
          gphotos_client_id: 'gphotos_client_1',
          gphotos_media_item_id: 'media_item_1',
          location: {
            coordinates: [40.7128, -74.006] // longitude, latitude
          },
          album_id: `407f1f77bcf86cd799439001:407f1f77bcf86cd799439002`
        });

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
        album_id: {
          clientId: '407f1f77bcf86cd799439001',
          objectId: '407f1f77bcf86cd799439002'
        },
        width: 0,
        height: 0,
        date_taken: new Date(1970, 1, 1)
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

  describe('getNumMediaItemsInAlbum', () => {
    const albumId: AlbumId = {
      clientId: 'albumClient1',
      objectId: 'albumObject1'
    };

    beforeEach(async () => {
      await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .insertMany([
          {
            _id: new ObjectId(),
            file_name: 'image1.jpg',
            gphotos_client_id: 'client_a',
            gphotos_media_item_id: 'media_1',
            album_id: `${albumId.clientId}:${albumId.objectId}`
          },
          {
            _id: new ObjectId(),
            file_name: 'image2.jpg',
            gphotos_client_id: 'client_a',
            gphotos_media_item_id: 'media_2',
            album_id: `${albumId.clientId}:${albumId.objectId}`
          }
        ]);
      await mongoClient2
        .db('photos_drive')
        .collection('media_items')
        .insertMany([
          {
            _id: new ObjectId(),
            file_name: 'image3.jpg',
            gphotos_client_id: 'client_a',
            gphotos_media_item_id: 'media_1',
            album_id: `${albumId.clientId}:${albumId.objectId}`
          }
        ]);
    });

    it('returns correct count', async () => {
      const count = await mediaItemsRepo.getNumMediaItemsInAlbum(albumId);
      expect(count).toBe(3);
    });
  });

  describe('getMediaItemsInAlbum', () => {
    const albumId: AlbumId = {
      clientId: '407f1f77bcf86cd799439001',
      objectId: '407f1f77bcf86cd799439002'
    };

    beforeEach(async () => {
      await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .insertMany([
          {
            _id: new ObjectId('507f1f77bcf86cd799439011'),
            file_name: 'image1.jpg',
            gphotos_client_id: 'gphotos_client_1',
            gphotos_media_item_id: 'media_item_1',
            album_id: `${albumId.clientId}:${albumId.objectId}`,
            location: {
              coordinates: [40.0, -70.0]
            },
            width: 1000,
            height: 2000,
            date_taken: new Date(2024, 4, 4)
          },
          {
            _id: new ObjectId('507f1f77bcf86cd799439012'),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            album_id: `${albumId.clientId}:${albumId.objectId}`,
            width: 1000,
            height: 2000,
            date_taken: new Date(2024, 4, 4)
          }
        ]);
      await mongoClient2
        .db('photos_drive')
        .collection('media_items')
        .insertMany([
          {
            _id: new ObjectId('507f1f77bcf86cd799439011'),
            file_name: 'image3.jpg',
            gphotos_client_id: 'gphotos_client_3',
            gphotos_media_item_id: 'media_item_3',
            album_id: `${albumId.clientId}:${albumId.objectId}`,
            width: 10,
            height: 20,
            date_taken: new Date(2024, 4, 4)
          }
        ]);
    });

    it('should return all media items in the album across clients', async () => {
      const results = await mediaItemsRepo.getMediaItemsInAlbum(albumId);

      expect(results).toHaveLength(3);

      const fileNames = results.map((item) => item.file_name).sort();
      expect(fileNames).toEqual(['image1.jpg', 'image2.jpg', 'image3.jpg']);
    });
  });

  describe('listMediaItems', () => {
    const albumId1: AlbumId = {
      clientId: '407f1f77bcf86cd799439001',
      objectId: '407f1f77bcf86cd799439002'
    };
    const albumId2: AlbumId = {
      clientId: '407f1f77bcf86cd799439001',
      objectId: '407f1f77bcf86cd799439003'
    };

    beforeEach(async () => {
      // Photos 1, 2, 3, 4 are in Album 1
      await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439010'),
          file_name: 'image1.jpg',
          gphotos_client_id: 'gphotos_client_1',
          gphotos_media_item_id: 'media_item_1',
          album_id: `${albumId1.clientId}:${albumId1.objectId}`,
          location: {
            coordinates: [40.0, -70.0]
          },
          width: 1000,
          height: 2000,
          date_taken: new Date(2024, 4, 4)
        });
      await mongoClient2
        .db('photos_drive')
        .collection('media_items')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439011'),
          file_name: 'image2.jpg',
          gphotos_client_id: 'gphotos_client_2',
          gphotos_media_item_id: 'media_item_2',
          album_id: `${albumId1.clientId}:${albumId1.objectId}`,
          width: 10,
          height: 20,
          date_taken: new Date(2024, 4, 4)
        });
      await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439012'),
          file_name: 'image3.jpg',
          gphotos_client_id: 'gphotos_client_3',
          gphotos_media_item_id: 'media_item_3',
          album_id: `${albumId1.clientId}:${albumId1.objectId}`,
          width: 1000,
          height: 2000,
          date_taken: new Date(2024, 4, 4)
        });
      await mongoClient2
        .db('photos_drive')
        .collection('media_items')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439013'),
          file_name: 'image4.jpg',
          gphotos_client_id: 'gphotos_client_4',
          gphotos_media_item_id: 'media_item_4',
          album_id: `${albumId1.clientId}:${albumId1.objectId}`,
          width: 10,
          height: 20,
          date_taken: new Date(2024, 4, 4)
        });

      // Photo 5 is in Album 2
      await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439014'),
          file_name: 'image5.jpg',
          gphotos_client_id: 'gphotos_client_5',
          gphotos_media_item_id: 'media_item_5',
          album_id: `${albumId2.clientId}:${albumId2.objectId}`,
          width: 1,
          height: 2,
          date_taken: new Date(2024, 4, 4)
        });
    });

    it('should return all albums given no album ID', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image1.jpg',
            gphotos_client_id: 'gphotos_client_1',
            gphotos_media_item_id: 'media_item_1',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439010' },
            location: { latitude: -70, longitude: 40 },
            width: 1000
          },
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image3.jpg',
            gphotos_client_id: 'gphotos_client_3',
            gphotos_media_item_id: 'media_item_3',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            width: 1000
          },
          {
            album_id: albumId2,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image5.jpg',
            gphotos_client_id: 'gphotos_client_5',
            gphotos_media_item_id: 'media_item_5',
            height: 2,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
            width: 1
          },
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            height: 20,
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439011' },
            width: 10
          },
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image4.jpg',
            gphotos_client_id: 'gphotos_client_4',
            gphotos_media_item_id: 'media_item_4',
            height: 20,
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439013' },
            width: 10
          }
        ],
        nextPageToken:
          'client2:507f1f77bcf86cd799439013,client1:507f1f77bcf86cd799439014'
      });
    });

    it('should return all correct albums given album 2', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId2,
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
            album_id: albumId2,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image5.jpg',
            gphotos_client_id: 'gphotos_client_5',
            gphotos_media_item_id: 'media_item_5',
            height: 2,
            width: 1
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439014'
      });
    });

    it('should return response correctly given no media items found', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: {
          clientId: '407f1f77bcf86cd799439001',
          objectId: '407f1f77bcf86cd799439004'
        },
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({ mediaItems: [], nextPageToken: undefined });
    });

    it('should return response correctly given album1 and pageSize=1', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 1,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image1.jpg',
            gphotos_client_id: 'gphotos_client_1',
            gphotos_media_item_id: 'media_item_1',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439010' },
            location: { latitude: -70, longitude: 40 },
            width: 1000
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439010'
      });
    });

    it('should return next media item and page token correctly given album1 and pageSize=1 and the last album ID for client 1', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439010',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image3.jpg',
            gphotos_client_id: 'gphotos_client_3',
            gphotos_media_item_id: 'media_item_3',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            width: 1000
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439012'
      });
    });

    it('should return last media item and page token correctly given album1 and pageSize=1 and sortDir=descending and the last album ID for client 1', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439010',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image4.jpg',
            gphotos_client_id: 'gphotos_client_4',
            gphotos_media_item_id: 'media_item_4',
            height: 20,
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439013' },
            width: 10
          }
        ],
        nextPageToken:
          'client2:507f1f77bcf86cd799439013,client1:507f1f77bcf86cd799439010'
      });
    });

    it('should return no media items given album1 and pageSize=1 and page token is at the last media item IDs of each client', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 1,
        pageToken:
          'client1:507f1f77bcf86cd799439012,client2:507f1f77bcf86cd799439013',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({ mediaItems: [] });
    });

    it('should return media items in reverse order given album1 and pageSize=10 and sortOrder = descending', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image4.jpg',
            gphotos_client_id: 'gphotos_client_4',
            gphotos_media_item_id: 'media_item_4',
            height: 20,
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439013' },
            width: 10
          },
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            height: 20,
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439011' },
            width: 10
          },
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image3.jpg',
            gphotos_client_id: 'gphotos_client_3',
            gphotos_media_item_id: 'media_item_3',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            width: 1000
          },
          {
            album_id: albumId1,
            date_taken: new Date('2024-05-04T07:00:00.000Z'),
            file_name: 'image1.jpg',
            gphotos_client_id: 'gphotos_client_1',
            gphotos_media_item_id: 'media_item_1',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439010' },
            location: { latitude: -70, longitude: 40 },
            width: 1000
          }
        ],
        nextPageToken:
          'client1:507f1f77bcf86cd799439010,client2:507f1f77bcf86cd799439011'
      });
    });
  });
});

describe('sortMediaItem', () => {
  const albumId: AlbumId = {
    clientId: 'albumClient1',
    objectId: 'albumObject1'
  };

  describe('sorting by ID ascending', () => {
    const sortBy: SortBy = {
      field: SortByField.ID,
      direction: SortByDirection.ASCENDING
    };

    it('returns -1 if a.id < b.id', () => {
      const a = createMediaItem('clientA', 'obj1');
      const b = createMediaItem('clientB', 'obj2');

      expect(sortMediaItem(a, b, sortBy)).toBe(-1);
    });

    it('returns 1 if a.id > b.id', () => {
      const a = createMediaItem('clientC', 'obj9');
      const b = createMediaItem('clientB', 'obj2');

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

      expect(sortMediaItem(a, b, sortBy)).toBe(-1);
    });

    it('returns 1 if a.id < b.id', () => {
      const a = createMediaItem('clientA', 'obj1');
      const b = createMediaItem('clientB', 'obj2');

      expect(sortMediaItem(a, b, sortBy)).toBe(1);
    });
  });

  function createMediaItem(clientId: string, objectId: string): MediaItem {
    return {
      id: { clientId, objectId },
      file_name: 'file.jpg',
      gphotos_client_id: 'gphotos_client',
      gphotos_media_item_id: 'gphotos_media_id',
      album_id: albumId,
      width: 1000,
      height: 2000,
      date_taken: new Date(2025, 1, 1)
    };
  }
});
