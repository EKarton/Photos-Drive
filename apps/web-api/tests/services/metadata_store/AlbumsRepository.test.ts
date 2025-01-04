import { mock } from 'jest-mock-extended'
import { MongoClient, ObjectId } from 'mongodb'
import { MongoMemoryServer } from 'mongodb-memory-server'
import { AlbumId } from '../../../src/services/metadata_store/Albums'
import {
  AlbumNotFoundError,
  AlbumsRepositoryImpl
} from '../../../src/services/metadata_store/AlbumsRepository'
import { MongoDbClientsRepository } from '../../../src/services/metadata_store/MongoDbClientsRepository'

describe('AlbumsRepositoryImpl', () => {
  let mongoServer: MongoMemoryServer
  let mongoClient: MongoClient
  let albumsRepo: AlbumsRepositoryImpl
  let mockMongoDbClientsRepository: jest.Mocked<MongoDbClientsRepository>

  beforeAll(async () => {
    // Start the in-memory MongoDB server
    mongoServer = await MongoMemoryServer.create()
    mongoClient = await MongoClient.connect(mongoServer.getUri())

    // Mock the MongoDbClientsRepository to return our in-memory client
    mockMongoDbClientsRepository = mock<MongoDbClientsRepository>()
    mockMongoDbClientsRepository.getClientFromId.mockReturnValue(mongoClient)

    // Initialize the repository
    albumsRepo = new AlbumsRepositoryImpl(mockMongoDbClientsRepository)

    // Set up the database and collection
    const db = mongoClient.db('sharded_google_photos')
    await db.collection('albums').insertOne({
      _id: new ObjectId('507f1f77bcf86cd799439010'),
      name: 'Test Album',
      parent_album_id: null,
      child_album_ids: ['client1:507f1f77bcf86cd799439011'],
      media_item_ids: []
    })
    await db.collection('albums').insertOne({
      _id: new ObjectId('507f1f77bcf86cd799439011'),
      name: 'Test Album',
      parent_album_id: 'client1:507f1f77bcf86cd799439010',
      child_album_ids: ['client1:987654321098', 'client1:111111111111'],
      media_item_ids: ['client1:222222222222', 'client1:333333333333']
    })
  })

  afterAll(async () => {
    await mongoClient.close()
    await mongoServer.stop()
  })

  describe('getAlbumById', () => {
    it('should return an album correctly for an album with a parent album', async () => {
      const albumId: AlbumId = {
        clientId: 'client1',
        objectId: '507f1f77bcf86cd799439011'
      }

      const result = await albumsRepo.getAlbumById(albumId)

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
        ],
        media_item_ids: [
          { clientId: 'client1', objectId: '222222222222' },
          { clientId: 'client1', objectId: '333333333333' }
        ]
      })
    })

    it('should return an album correctly for an album without a parent album', async () => {
      const albumId: AlbumId = {
        clientId: 'client1',
        objectId: '507f1f77bcf86cd799439010'
      }

      const result = await albumsRepo.getAlbumById(albumId)

      expect(result).toEqual({
        id: albumId,
        name: 'Test Album',
        parent_album_id: undefined,
        child_album_ids: [
          { clientId: 'client1', objectId: '507f1f77bcf86cd799439011' }
        ],
        media_item_ids: []
      })
    })

    it('should throw AlbumNotFoundError when album is not found', async () => {
      const albumId: AlbumId = {
        clientId: 'client1',
        objectId: '507f1f77bcf86cd799439012' // Non-existent ID
      }

      await expect(albumsRepo.getAlbumById(albumId)).rejects.toThrow(
        AlbumNotFoundError
      )
      await expect(albumsRepo.getAlbumById(albumId)).rejects.toThrow(
        `Cannot find album with id ${albumId}`
      )
    })
  })
})
