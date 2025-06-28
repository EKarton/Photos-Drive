import { MongoClient, ObjectId } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { Album, AlbumId } from '../../../../src/services/metadata_store/Albums';
import {
  AlbumNotFoundError,
  SortBy,
  SortByDirection,
  SortByField
} from '../../../../src/services/metadata_store/AlbumsRepository';
import {
  AlbumsRepositoryImpl,
  sortAlbum
} from '../../../../src/services/metadata_store/mongodb/AlbumsRepositoryImpl';
import { InMemoryMongoDbClientsRepository } from '../../../../src/services/metadata_store/mongodb/MongoDbClientsRepository';

describe('AlbumsRepositoryImpl', () => {
  let mongoServer1: MongoMemoryServer;
  let mongoServer2: MongoMemoryServer;

  let mongoClient1: MongoClient;
  let mongoClient2: MongoClient;

  let albumsRepo: AlbumsRepositoryImpl;

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
    albumsRepo = new AlbumsRepositoryImpl(mongoDbClientsRepo);
  }, 10000);

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

  describe('getAlbumById', () => {
    beforeEach(async () => {
      // Set up the database and collection
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439010'),
          name: 'Test Album',
          parent_album_id: null,
          child_album_ids: ['client2:507f1f77bcf86cd799439011']
        });

      await mongoClient2
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439011'),
          name: 'Test Album',
          parent_album_id: 'client1:507f1f77bcf86cd799439010',
          child_album_ids: ['client1:987654321098', 'client1:111111111111']
        });
    });

    it('should return an album correctly for an album with a parent album', async () => {
      const albumId: AlbumId = {
        clientId: 'client2',
        objectId: '507f1f77bcf86cd799439011'
      };

      const result = await albumsRepo.getAlbumById(albumId);

      expect(result).toEqual({
        id: albumId,
        name: 'Test Album',
        parent_album_id: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439010'
        },
        child_album_ids: [
          { clientId: 'client1', objectId: '987654321098' },
          { clientId: 'client1', objectId: '111111111111' }
        ]
      });
    });

    it('should return an album correctly for an album without a parent album', async () => {
      const albumId: AlbumId = {
        clientId: 'client1',
        objectId: '507f1f77bcf86cd799439010'
      };

      const result = await albumsRepo.getAlbumById(albumId);

      expect(result).toEqual({
        id: albumId,
        name: 'Test Album',
        parent_album_id: undefined,
        child_album_ids: [
          { clientId: 'client2', objectId: '507f1f77bcf86cd799439011' }
        ]
      });
    });

    it('should throw AlbumNotFoundError when album is not found', async () => {
      const albumId: AlbumId = {
        clientId: 'client1',
        objectId: '507f1f77bcf86cd799439012' // Non-existent ID
      };

      await expect(albumsRepo.getAlbumById(albumId)).rejects.toThrow(
        AlbumNotFoundError
      );
      await expect(albumsRepo.getAlbumById(albumId)).rejects.toThrow(
        `Cannot find album with id ${albumId}`
      );
    });
  });

  describe('getNumAlbumsInAlbum', () => {
    beforeEach(async () => {
      /**
       * Structure:
       * client1:
       *   - parent album: client1:parent1
       *   - 2 child albums with parent_album_id = client1:parent1
       * client2:
       *   - 1 child album with parent_album_id = client1:parent1
       */
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertMany([
          {
            _id: new ObjectId('507f1f77bcf86cd799439050'),
            name: 'Child 1',
            parent_album_id: 'client1:parent1',
            child_album_ids: []
          },
          {
            _id: new ObjectId('507f1f77bcf86cd799439051'),
            name: 'Child 2',
            parent_album_id: 'client1:parent1',
            child_album_ids: []
          }
        ]);

      await mongoClient2
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439052'),
          name: 'Child 3',
          parent_album_id: 'client1:parent1',
          child_album_ids: []
        });
    });

    it('should return the correct number of child albums across clients', async () => {
      const parentAlbumId: AlbumId = {
        clientId: 'client1',
        objectId: 'parent1'
      };

      const result = await albumsRepo.getNumAlbumsInAlbum(parentAlbumId);

      expect(result).toBe(3); // 2 from client1 + 1 from client2
    });

    it('should return 0 when no albums have the specified parent_album_id', async () => {
      const parentAlbumId: AlbumId = {
        clientId: 'client1',
        objectId: 'nonexistent'
      };

      const result = await albumsRepo.getNumAlbumsInAlbum(parentAlbumId);

      expect(result).toBe(0);
    });
  });

  describe('listAlbums', () => {
    beforeEach(async () => {
      /**
       * Builds this tree structure:
       *
       * └── client1: Archives
       *     └── client2: Photos
       *         ├── client1: 2010
       *         ├── client2: 2011
       *         ├── client1: 2012
       *         └── client2: 2013
       */
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439010'),
          name: 'Archives',
          parent_album_id: '',
          child_album_ids: ['client2:507f1f77bcf86cd799439011']
        });
      await mongoClient2
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439011'),
          name: 'Photos',
          parent_album_id: 'client1:507f1f77bcf86cd799439010',
          child_album_ids: [
            'client1:507f1f77bcf86cd799439012',
            'client2:507f1f77bcf86cd799439013',
            'client1:507f1f77bcf86cd799439014',
            'client2:507f1f77bcf86cd799439015'
          ]
        });
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439012'),
          name: '2010',
          parent_album_id: 'client1:507f1f77bcf86cd799439011',
          child_album_ids: []
        });
      await mongoClient2
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439013'),
          name: '2011',
          parent_album_id: 'client1:507f1f77bcf86cd799439011',
          child_album_ids: []
        });
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439014'),
          name: '2012',
          parent_album_id: 'client1:507f1f77bcf86cd799439011',
          child_album_ids: []
        });
      await mongoClient2
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439015'),
          name: '2014',
          parent_album_id: 'client1:507f1f77bcf86cd799439011',
          child_album_ids: []
        });
    });

    it('should return albums correctly', async () => {
      const res = await albumsRepo.listAlbums({
        pageSize: 1,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439010' },
            name: 'Archives',
            parent_album_id: undefined,
            child_album_ids: [
              { clientId: 'client2', objectId: '507f1f77bcf86cd799439011' }
            ]
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439010'
      });
    });

    it('should return response correctly given no albums found', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client4',
          objectId: '1111111111111'
        },
        pageSize: 1,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({ albums: [], nextPageToken: undefined });
    });

    it('should return albums correctly given parent album "Archives" and pageSize=1', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439010'
        },
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439011' },
            name: 'Photos',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439010'
            },
            child_album_ids: [
              { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
              { clientId: 'client2', objectId: '507f1f77bcf86cd799439013' },
              { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
              { clientId: 'client2', objectId: '507f1f77bcf86cd799439015' }
            ]
          }
        ],
        nextPageToken: 'client2:507f1f77bcf86cd799439011'
      });
    });

    it('should return albums and page token correctly given parent album "Photos" and pageSize=5', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 5,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            child_album_ids: [],
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            name: '2010',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            child_album_ids: [],
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
            name: '2012',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            child_album_ids: [],
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439013' },
            name: '2011',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            child_album_ids: [],
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439015' },
            name: '2014',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken:
          'client2:507f1f77bcf86cd799439015,client1:507f1f77bcf86cd799439014'
      });
    });

    it('should return albums and page token correctly given parent album "Photos" and pageSize=1 and last album ID for client 1', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439014',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            child_album_ids: [],
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439013' },
            name: '2011',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken:
          'client2:507f1f77bcf86cd799439013,client1:507f1f77bcf86cd799439014'
      });
    });

    it('should return albums correctly given parent album "Photos" and pageSize=1 and sortDir=Descending and last album ID for client 1', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439014',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            child_album_ids: [],
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439015' },
            name: '2014',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken:
          'client2:507f1f77bcf86cd799439015,client1:507f1f77bcf86cd799439014'
      });
    });

    it('should return no albums given parent album "Photos" and page token is at the last album IDs of each client', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 1,
        pageToken:
          'client2:507f1f77bcf86cd799439015,client1:507f1f77bcf86cd799439014',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        albums: []
      });
    });

    it('should return albums in reverse order given parent album "Photos" and pageSize=10 and sortOrder = descending', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 10,
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            child_album_ids: [],
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439015' },
            name: '2014',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            child_album_ids: [],
            id: { clientId: 'client2', objectId: '507f1f77bcf86cd799439013' },
            name: '2011',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            child_album_ids: [],
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
            name: '2012',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            child_album_ids: [],
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            name: '2010',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken:
          'client1:507f1f77bcf86cd799439012,client2:507f1f77bcf86cd799439013'
      });
    });
  });
});

describe('sortAlbum', () => {
  const albumA = makeAlbum('client1', 'aaa111');
  const albumB = makeAlbum('client2', 'bbb222');

  const ascendingSortBy: SortBy = {
    field: SortByField.ID,
    direction: SortByDirection.ASCENDING
  };

  const descendingSortBy: SortBy = {
    field: SortByField.ID,
    direction: SortByDirection.DESCENDING
  };

  it('should return -1 when a < b (ascending)', () => {
    const result = sortAlbum(albumA, albumB, ascendingSortBy);

    expect(result).toBe(-1);
  });

  it('should return 1 when a > b (ascending)', () => {
    const result = sortAlbum(albumB, albumA, ascendingSortBy);

    expect(result).toBe(1);
  });

  it('should return -1 when a > b (descending)', () => {
    const result = sortAlbum(albumB, albumA, descendingSortBy);

    expect(result).toBe(-1);
  });

  it('should return 1 when a < b (descending)', () => {
    const result = sortAlbum(albumA, albumB, descendingSortBy);

    expect(result).toBe(1);
  });

  it('should treat equal IDs as 1 or -1 (never 0)', () => {
    const albumC = makeAlbum('client1', 'aaa111');

    const result = sortAlbum(albumA, albumC, ascendingSortBy);

    expect([1, -1]).toContain(result);
  });

  function makeAlbum(clientId: string, objectId: string): Album {
    return {
      id: { clientId, objectId },
      name: '',
      parent_album_id: undefined,
      child_album_ids: []
    };
  }
});
