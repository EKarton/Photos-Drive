import { MongoClient, ObjectId } from 'mongodb';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { AlbumId } from '../../../../src/services/metadata_store/Albums';
import {
  AlbumNotFoundError,
  SortByDirection,
  SortByField
} from '../../../../src/services/metadata_store/AlbumsStore';
import { MongoDbAlbumsStore } from '../../../../src/services/metadata_store/mongodb/MongoDbAlbumsStore';

describe('MongoDbAlbumsStore', () => {
  let mongoServer1: MongoMemoryServer;
  let mongoClient1: MongoClient;

  let albumsRepo: MongoDbAlbumsStore;

  beforeAll(async () => {
    // Start the in-memory MongoDB server
    mongoServer1 = await MongoMemoryServer.create();
    mongoClient1 = await MongoClient.connect(mongoServer1.getUri(), {});

    albumsRepo = new MongoDbAlbumsStore('client1', mongoClient1);
  }, 10000);

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

  describe('getAlbumById', () => {
    beforeEach(async () => {
      // Set up the database and collection
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439010'),
          name: 'Test Album',
          parent_album_id: null
        });

      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439011'),
          name: 'Test Album',
          parent_album_id: 'client1:507f1f77bcf86cd799439010'
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
        }
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
        parent_album_id: undefined
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
       */
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertMany([
          {
            _id: new ObjectId('507f1f77bcf86cd799439050'),
            name: 'Child 1',
            parent_album_id: 'client1:parent1'
          },
          {
            _id: new ObjectId('507f1f77bcf86cd799439051'),
            name: 'Child 2',
            parent_album_id: 'client1:parent1'
          }
        ]);
    });

    it('should return the correct number of child albums across clients', async () => {
      const parentAlbumId: AlbumId = {
        clientId: 'client1',
        objectId: 'parent1'
      };

      const result = await albumsRepo.getNumAlbumsInAlbum(parentAlbumId);

      expect(result).toBe(2);
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
       *         ├── client1: 2011
       *         ├── client1: 2012
       *         └── client1: 2013
       */
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439010'),
          name: 'Archives',
          parent_album_id: ''
        });
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439011'),
          name: 'Photos',
          parent_album_id: 'client1:507f1f77bcf86cd799439010'
        });
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439012'),
          name: '2010',
          parent_album_id: 'client1:507f1f77bcf86cd799439011'
        });
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439013'),
          name: '2011',
          parent_album_id: 'client1:507f1f77bcf86cd799439011'
        });
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439014'),
          name: '2012',
          parent_album_id: 'client1:507f1f77bcf86cd799439011'
        });
      await mongoClient1
        .db('photos_drive')
        .collection('albums')
        .insertOne({
          _id: new ObjectId('507f1f77bcf86cd799439015'),
          name: '2014',
          parent_album_id: 'client1:507f1f77bcf86cd799439011'
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
            parent_album_id: undefined
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
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439011' },
            name: 'Photos',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439010'
            }
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439011'
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
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            name: '2010',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            name: '2011',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
            name: '2012',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439015' },
            name: '2014',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439015'
      });
    });

    it('should return next album and page token correctly given parent album "Photos" and pageSize=1 and sortBy=id and 2012 as last album ID for client 1', async () => {
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
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439015' },
            name: '2014',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439015'
      });
    });

    it('should return last album given parent album "Photos" and pageSize=1 and sortBy=id and sortDir=Descending and last album ID for client 1', async () => {
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
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            name: '2011',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439013'
      });
    });

    it('should return next album and page token correctly given parent album "Photos" and pageSize=1 and sortBy=name and 2012 as last album ID for client 1', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439014',
        sortBy: {
          field: SortByField.NAME,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439015' },
            name: '2014',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439015'
      });
    });

    it('should return last album given parent album "Photos" and pageSize=1 and sortBy=name and sortDir=Descending and last album ID for client 1', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439014',
        sortBy: {
          field: SortByField.NAME,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            name: '2011',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439013'
      });
    });

    it('should return no albums given parent album "Photos" and page token is at the last album IDs of each client', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 1,
        pageToken: 'client1:507f1f77bcf86cd799439015',
        sortBy: {
          field: SortByField.ID,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        albums: []
      });
    });

    it('should return albums in reverse order given sortBy=id and sortOrder = descending', async () => {
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
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439015' },
            name: '2014',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
            name: '2012',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            name: '2011',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            name: '2010',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439012'
      });
    });

    it('should return albums in order given sortBy=name and sortOrder=ascending', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 10,
        sortBy: {
          field: SortByField.NAME,
          direction: SortByDirection.ASCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            name: '2010',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            name: '2011',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
            name: '2012',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439015' },
            name: '2014',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439015'
      });
    });

    it('should return albums in order given sortBy=name and sortOrder=descending', async () => {
      const res = await albumsRepo.listAlbums({
        parentAlbumId: {
          clientId: 'client1',
          objectId: '507f1f77bcf86cd799439011'
        },
        pageSize: 10,
        sortBy: {
          field: SortByField.NAME,
          direction: SortByDirection.DESCENDING
        }
      });

      expect(res).toEqual({
        albums: [
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439015' },
            name: '2014',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439014' },
            name: '2012',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439013' },
            name: '2011',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          },
          {
            id: { clientId: 'client1', objectId: '507f1f77bcf86cd799439012' },
            name: '2010',
            parent_album_id: {
              clientId: 'client1',
              objectId: '507f1f77bcf86cd799439011'
            }
          }
        ],
        nextPageToken: 'client1:507f1f77bcf86cd799439012'
      });
    });
  });
});
