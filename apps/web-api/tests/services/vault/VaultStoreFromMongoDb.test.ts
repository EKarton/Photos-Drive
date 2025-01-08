import { MongoClient, ObjectId } from 'mongodb'
import { MongoMemoryServer } from 'mongodb-memory-server'
import { GPhotosClient } from '../../../src/services/blob_store/GPhotosClient'
import { VaultStoreFromMongoDb } from '../../../src/services/vault/VaultStoreFromMongoDb'

describe('VaultStoreFromMongoDb', () => {
  let mongoServer: MongoMemoryServer
  let mongoClient: MongoClient
  let vaultStore: VaultStoreFromMongoDb

  beforeAll(async () => {
    mongoServer = await MongoMemoryServer.create()
    const mongoUri = mongoServer.getUri()

    mongoClient = await MongoClient.connect(mongoUri)
    vaultStore = new VaultStoreFromMongoDb(mongoClient)
  })

  afterAll(async () => {
    await mongoClient.close()
    await mongoServer.stop()
  })

  beforeEach(async () => {
    const db = mongoClient.db('sharded_google_photos')
    await db.collection('mongodb_clients').deleteMany({})
    await db.collection('gphotos_clients').deleteMany({})
    await db.collection('root_album').deleteMany({})
  })

  describe('getMongoDbClients', () => {
    it('should return MongoDB clients', async () => {
      const testClients = [
        { _id: new ObjectId(), connection_string: 'mongodb://localhost:27017' },
        { _id: new ObjectId(), connection_string: 'mongodb://localhost:27018' }
      ]

      await mongoClient
        .db('sharded_google_photos')
        .collection('mongodb_clients')
        .insertMany(testClients)

      const result = await vaultStore.getMongoDbClients()

      expect(result).toHaveLength(2)
      expect(result[0][0]).toBe(testClients[0]._id.toString())
      expect(result[0][1]).toBeInstanceOf(MongoClient)
      expect(result[1][0]).toBe(testClients[1]._id.toString())
      expect(result[1][1]).toBeInstanceOf(MongoClient)
    })

    it('should return an empty array when no clients are found', async () => {
      const result = await vaultStore.getMongoDbClients()
      expect(result).toHaveLength(0)
    })
  })

  describe('getGPhotosClients', () => {
    it('should return GPhotos clients', async () => {
      const testClients = [
        {
          _id: new ObjectId(),
          name: 'Client1',
          token: 'token1',
          refresh_token: 'refresh1',
          client_id: 'id1',
          client_secret: 'secret1'
        },
        {
          _id: new ObjectId(),
          name: 'Client2',
          token: 'token2',
          refresh_token: 'refresh2',
          client_id: 'id2',
          client_secret: 'secret2'
        }
      ]

      await mongoClient
        .db('sharded_google_photos')
        .collection('gphotos_clients')
        .insertMany(testClients)

      const result = await vaultStore.getGPhotosClients()

      expect(result).toHaveLength(2)
      expect(result[0][0]).toBe(testClients[0]._id.toString())
      expect(result[0][1]).toBeInstanceOf(GPhotosClient)
      expect(result[1][0]).toBe(testClients[1]._id.toString())
      expect(result[1][1]).toBeInstanceOf(GPhotosClient)
    })

    it('should return an empty array when no clients are found', async () => {
      const result = await vaultStore.getGPhotosClients()
      expect(result).toHaveLength(0)
    })
  })

  describe('getRootAlbumId', () => {
    it('should return the root album ID', async () => {
      const rootAlbum = {
        client_id: new ObjectId(),
        object_id: new ObjectId()
      }

      await mongoClient
        .db('sharded_google_photos')
        .collection('root_album')
        .insertOne(rootAlbum)

      const result = await vaultStore.getRootAlbumId()

      expect(result).toEqual({
        clientId: rootAlbum.client_id.toString(),
        objectId: rootAlbum.object_id.toString()
      })
    })

    it('should throw an error when no root album is found', async () => {
      await expect(vaultStore.getRootAlbumId()).rejects.toThrow(
        'No root album found!'
      )
    })
  })
})
