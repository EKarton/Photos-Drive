import { MongoClient, ObjectId } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { AlbumId } from '../../../../src/services/core/albums/Albums';
import {
  MediaItemNotFoundError,
  SortByDirection,
  SortByField
} from '../../../../src/services/core/media_items/BaseMediaItemsStore';
import { MediaItemId } from '../../../../src/services/core/media_items/MediaItems';
import { MongoDbMediaItemsStore } from '../../../../src/services/core/media_items/MongoDbMediaItemsStore';

describe('MongoDbMediaItemsStore', () => {
  let mongoServer1: MongoMemoryServer;
  let mongoClient1: MongoClient;

  let mediaItemsRepo: MongoDbMediaItemsStore;

  beforeAll(async () => {
    // Start the in-memory MongoDB server
    mongoServer1 = await MongoMemoryServer.create();
    mongoClient1 = await MongoClient.connect(mongoServer1.getUri(), {});

    mediaItemsRepo = new MongoDbMediaItemsStore('client1', mongoClient1);
  });

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

  describe('bulkGetMediaItemByIds', () => {
    let id1: MediaItemId;
    let id3: MediaItemId;

    beforeEach(async () => {
      // Insert into client1
      const inserted1 = await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .insertOne({
          file_name: 'from_client1.jpg',
          gphotos_client_id: 'g1',
          gphotos_media_item_id: 'm1',
          album_id: 'a1:a2',
          width: 100,
          height: 200,
          date_taken: new Date('2024-01-01')
        });
      id1 = {
        clientId: 'client1',
        objectId: inserted1.insertedId.toString()
      };

      // Insert second doc into client1
      const inserted3 = await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .insertOne({
          file_name: 'another_from_client1.jpg',
          gphotos_client_id: 'g3',
          gphotos_media_item_id: 'm3',
          album_id: 'a5:a6',
          width: 500,
          height: 600,
          date_taken: new Date('2024-03-03')
        });
      id3 = {
        clientId: 'client1',
        objectId: inserted3.insertedId.toHexString()
      };
    });

    it('returns all matching media items', async () => {
      const results = await mediaItemsRepo.bulkGetMediaItemByIds([id1, id3]);
      expect(Array.isArray(results)).toBe(true);
      expect(results).toHaveLength(2);

      const byId = Object.fromEntries(results.map((r) => [r.id.objectId, r]));
      expect(byId[id1.objectId].file_name).toBe('from_client1.jpg');
      expect(byId[id3.objectId].file_name).toBe('another_from_client1.jpg');
    });

    it('returns only the items that exist if some ids are not found', async () => {
      const fakeId: MediaItemId = {
        clientId: 'client2',
        objectId: new ObjectId().toString()
      };

      const results = await mediaItemsRepo.bulkGetMediaItemByIds([id1, fakeId]);
      expect(results).toHaveLength(1);
      expect(results[0].id.objectId).toBe(id1.objectId);
    });

    it('returns empty array when no ids match', async () => {
      const fakeId1: MediaItemId = {
        clientId: 'client1',
        objectId: new ObjectId().toString()
      };
      const fakeId2: MediaItemId = {
        clientId: 'client2',
        objectId: new ObjectId().toString()
      };

      const results = await mediaItemsRepo.bulkGetMediaItemByIds([
        fakeId1,
        fakeId2
      ]);
      expect(results).toEqual([]);
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
    });

    it('returns correct count', async () => {
      const count = await mediaItemsRepo.getNumMediaItemsInAlbum(albumId);
      expect(count).toBe(2);
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
    const album3: AlbumId = {
      clientId: '407f1f77bcf86cd799439001',
      objectId: '407f1f77bcf86cd799439004'
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
            type: 'Point',
            coordinates: [40.0, -70.0]
          },
          width: 1000,
          height: 2000
        });
      await mongoClient1
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
          date_taken: new Date(2024, 4, 2)
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
          date_taken: new Date(2024, 4, 3)
        });
      await mongoClient1
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
          date_taken: new Date(2024, 4, 5)
        });

      // Enable geospatial queries
      await mongoClient1
        .db('photos_drive')
        .collection('media_items')
        .createIndex({ location: '2dsphere' });
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
            date_taken: new Date(1970, 1, 1),
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
            date_taken: new Date(2024, 4, 2),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            height: 20,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439011' },
            width: 10
          },
          {
            album_id: albumId1,
            date_taken: new Date(2024, 4, 3),
            file_name: 'image3.jpg',
            gphotos_client_id: 'gphotos_client_3',
            gphotos_media_item_id: 'media_item_3',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            width: 1000
          },
          {
            album_id: albumId1,
            date_taken: new Date(2024, 4, 4),
            file_name: 'image4.jpg',
            gphotos_client_id: 'gphotos_client_4',
            gphotos_media_item_id: 'media_item_4',
            height: 20,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            width: 10
          },
          {
            album_id: albumId2,
            date_taken: new Date(2024, 4, 5),
            file_name: 'image5.jpg',
            gphotos_client_id: 'gphotos_client_5',
            gphotos_media_item_id: 'media_item_5',
            height: 2,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
            width: 1
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439014'
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
            date_taken: new Date(2024, 4, 5),
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
        albumId: album3,
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
            date_taken: new Date(1970, 1, 1),
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

    it('should return next media item and page token correctly given album1 and pageSize=1 and sortBy=id and sortDir=ascending and a page token', async () => {
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
            date_taken: new Date(2024, 4, 2),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            height: 20,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439011' },
            width: 10
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439011'
      });
    });

    it('should return nothing given album1 and pageSize=1 and sortBy=id and sortDir=descending and the last page token', async () => {
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
        mediaItems: [],
        nextPageToken: undefined
      });
    });

    it('should return last media item and page token correctly given album1 and pageSize=1 and sortBy=date-taken and sortDir=ascending and a page token', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439010',
        sortBy: {
          field: SortByField.DATE_TAKEN,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            album_id: {
              clientId: '407f1f77bcf86cd799439001',
              objectId: '407f1f77bcf86cd799439002'
            },
            date_taken: new Date(2024, 4, 2),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            height: 20,
            id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            },
            width: 10
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439011'
      });
    });

    it('should return last media item and page token correctly given album1 and pageSize=1 and sortBy=date-taken and sortDir=descending and the last media item ID', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439010',
        sortBy: {
          field: SortByField.DATE_TAKEN,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [],
        nextPageToken: undefined
      });
    });

    it('should return no media items given album1 and pageSize=1 and page token is at the last media item IDs', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439013',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({ mediaItems: [] });
    });

    it('should return media items in reverse order given album1 and pageSize=10 and sortBy=id and sortOrder=descending', async () => {
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
            date_taken: new Date(2024, 4, 4),
            file_name: 'image4.jpg',
            gphotos_client_id: 'gphotos_client_4',
            gphotos_media_item_id: 'media_item_4',
            height: 20,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            width: 10
          },
          {
            album_id: albumId1,
            date_taken: new Date(2024, 4, 3),
            file_name: 'image3.jpg',
            gphotos_client_id: 'gphotos_client_3',
            gphotos_media_item_id: 'media_item_3',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            width: 1000
          },
          {
            album_id: albumId1,
            date_taken: new Date(2024, 4, 2),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            height: 20,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439011' },
            width: 10
          },
          {
            album_id: albumId1,
            date_taken: new Date(1970, 1, 1),
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

    it('should return media items in order given album1 and pageSize=10 and sortBy=date-taken and sortOrder=ascending', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 10,
        sortBy: {
          field: SortByField.DATE_TAKEN,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            album_id: albumId1,
            date_taken: new Date(1970, 1, 1),
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
            date_taken: new Date(2024, 4, 2),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            height: 20,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439011' },
            width: 10
          },
          {
            album_id: albumId1,
            date_taken: new Date(2024, 4, 3),
            file_name: 'image3.jpg',
            gphotos_client_id: 'gphotos_client_3',
            gphotos_media_item_id: 'media_item_3',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            width: 1000
          },
          {
            album_id: albumId1,
            date_taken: new Date(2024, 4, 4),
            file_name: 'image4.jpg',
            gphotos_client_id: 'gphotos_client_4',
            gphotos_media_item_id: 'media_item_4',
            height: 20,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            width: 10
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439013'
      });
    });

    it('should return media items in order given album1 and pageSize=10 and sortBy=date-taken and sortOrder=descending', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        albumId: albumId1,
        pageSize: 10,
        sortBy: {
          field: SortByField.DATE_TAKEN,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            album_id: albumId1,
            date_taken: new Date(2024, 4, 4),
            file_name: 'image4.jpg',
            gphotos_client_id: 'gphotos_client_4',
            gphotos_media_item_id: 'media_item_4',
            height: 20,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            width: 10
          },
          {
            album_id: albumId1,
            date_taken: new Date(2024, 4, 3),
            file_name: 'image3.jpg',
            gphotos_client_id: 'gphotos_client_3',
            gphotos_media_item_id: 'media_item_3',
            height: 2000,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            width: 1000
          },
          {
            album_id: albumId1,
            date_taken: new Date(2024, 4, 2),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            height: 20,
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439011' },
            width: 10
          },
          {
            album_id: albumId1,
            date_taken: new Date(1970, 1, 1),
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

    it('should return no media items given withinLocation filter is set', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        withinLocation: {
          latitude: -49,
          longitude: 90,
          range: 100
        },
        pageSize: 100,
        sortBy: {
          field: SortByField.DATE_TAKEN,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [],
        nextPageToken: undefined
      });
    });

    it('should return media items with correct date_taken fields given earliestDateTaken and latestDateTaken filter is set', async () => {
      const res = await mediaItemsRepo.listMediaItems({
        earliestDateTaken: new Date(2024, 4, 1),
        latestDateTaken: new Date(2024, 4, 2),
        pageSize: 100,
        sortBy: {
          field: SortByField.DATE_TAKEN,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        mediaItems: [
          {
            album_id: {
              clientId: '407f1f77bcf86cd799439001',
              objectId: '407f1f77bcf86cd799439002'
            },
            date_taken: new Date(2024, 4, 2),
            file_name: 'image2.jpg',
            gphotos_client_id: 'gphotos_client_2',
            gphotos_media_item_id: 'media_item_2',
            height: 20,
            id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            },
            width: 10
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439011'
      });
    });
  });

  describe('sampleMediaItems', () => {
    const albumId1: AlbumId = {
      clientId: '407f1f77bcf86cd799439001',
      objectId: '407f1f77bcf86cd799439002'
    };

    const doc1 = {
      _id: new ObjectId('507f1f77bcf86cd799439010'),
      file_name: 'image1.jpg',
      gphotos_client_id: 'gphotos_client_1',
      gphotos_media_item_id: 'media_item_1',
      album_id: `${albumId1.clientId}:${albumId1.objectId}`,
      location: {
        type: 'Point',
        coordinates: [40.0, -70.0]
      },
      width: 1000,
      height: 2000,
      date_taken: new Date(2024, 4, 1)
    };

    const doc2 = {
      _id: new ObjectId('507f1f77bcf86cd799439011'),
      file_name: 'image2.jpg',
      gphotos_client_id: 'gphotos_client_2',
      gphotos_media_item_id: 'media_item_2',
      album_id: `${albumId1.clientId}:${albumId1.objectId}`,
      width: 10,
      height: 20,
      date_taken: new Date(2024, 4, 2)
    };

    let aggregateFn: jest.SpyInstance;

    beforeEach(() => {
      // Mock aggregate() to fake Atlas vector search results
      aggregateFn = jest
        .spyOn(mediaItemsRepo['collection'], 'aggregate')
        .mockReturnValue({
          [Symbol.asyncIterator]: async function* () {
            yield doc1;
            yield doc2;
          },
          toArray: () => [doc1, doc2]
        } as never);
    });

    it('should call aggregation pipeline and returns media items given optional query fields', async () => {
      const res = await mediaItemsRepo.sampleMediaItems({
        pageSize: 2
      });

      expect(res.mediaItems.length).toBe(2);
      expect(aggregateFn).toHaveBeenCalledWith(
        [{ $match: {} }, { $sample: { size: 2 } }],
        { signal: undefined }
      );
    });

    it('should call aggregation pipeline and returns media items given query fields are all populated', async () => {
      const res = await mediaItemsRepo.sampleMediaItems({
        albumId: albumId1,
        earliestDateTaken: new Date(2024, 4, 3),
        latestDateTaken: new Date(2024, 4, 3),
        withinLocation: { latitude: 90, longitude: -49, range: 100 },
        pageSize: 2
      });

      expect(res.mediaItems.length).toBe(2);
      expect(aggregateFn).toHaveBeenCalledWith(
        [
          {
            $match: {
              album_id: '407f1f77bcf86cd799439001:407f1f77bcf86cd799439002',
              date_taken: {
                $gte: new Date(2024, 4, 3),
                $lte: new Date(2024, 4, 3)
              },
              location: {
                $near: {
                  $geometry: { coordinates: [-49, 90], type: 'Point' },
                  $maxDistance: 100
                }
              }
            }
          },
          { $sample: { size: 2 } }
        ],
        { signal: undefined }
      );
    });
  });
});
