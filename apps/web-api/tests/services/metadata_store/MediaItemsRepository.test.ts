import { mock } from 'jest-mock-extended'
import { MongoClient, ObjectId } from 'mongodb'
import { MongoMemoryServer } from 'mongodb-memory-server'
import { MediaItemId } from '../../../src/services/metadata_store/MediaItems'
import {
  MediaItemNotFoundError,
  MediaItemsRepositoryImpl
} from '../../../src/services/metadata_store/MediaItemsRepository'
import { MongoDbClientsRepository } from '../../../src/services/metadata_store/MongoDbClientsRepository'

describe('MediaItemsRepositoryImpl', () => {
  let mongoServer: MongoMemoryServer
  let mongoClient: MongoClient
  let mediaItemsRepo: MediaItemsRepositoryImpl
  let mockMongoDbClientsRepository: jest.Mocked<MongoDbClientsRepository>

  beforeAll(async () => {
    // Start the in-memory MongoDB server
    mongoServer = await MongoMemoryServer.create()
    mongoClient = await MongoClient.connect(mongoServer.getUri())

    // Mock the MongoDbClientsRepository to return our in-memory client
    mockMongoDbClientsRepository = mock<MongoDbClientsRepository>()
    mockMongoDbClientsRepository.getClientFromId.mockReturnValue(mongoClient)

    // Initialize the repository
    mediaItemsRepo = new MediaItemsRepositoryImpl(mockMongoDbClientsRepository)

    // Set up the database and collection
    const db = mongoClient.db('sharded_google_photos')
    await db.collection('media_items').insertOne({
      _id: new ObjectId('507f1f77bcf86cd799439011'),
      file_name: 'test_image.jpg',
      gphotos_client_id: 'gphotos_client_1',
      gphotos_media_item_id: 'media_item_1',
      location: {
        coordinates: [40.7128, -74.006] // longitude, latitude
      }
    })
  })

  afterAll(async () => {
    await mongoClient.close()
    await mongoServer.stop()
  })

  describe('getMediaItemById', () => {
    it('should return a media item when found', async () => {
      const mediaItemId: MediaItemId = {
        clientId: 'client1',
        objectId: '507f1f77bcf86cd799439011'
      }

      const result = await mediaItemsRepo.getMediaItemById(mediaItemId)

      expect(result).toEqual({
        id: mediaItemId,
        file_name: 'test_image.jpg',
        gphotos_client_id: 'gphotos_client_1',
        gphotos_media_item_id: 'media_item_1',
        location: {
          longitude: 40.7128,
          latitude: -74.006
        }
      })
    })

    it('should throw MediaItemNotFoundError when media item is not found', async () => {
      const mediaItemId: MediaItemId = {
        clientId: 'client1',
        objectId: '507f1f77bcf86cd799439012' // Non-existent ID
      }

      await expect(
        mediaItemsRepo.getMediaItemById(mediaItemId)
      ).rejects.toThrow(MediaItemNotFoundError)
      await expect(
        mediaItemsRepo.getMediaItemById(mediaItemId)
      ).rejects.toThrow(`Cannot find media item with id ${mediaItemId}`)
    })
  })
})
