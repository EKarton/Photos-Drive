/* eslint-disable security/detect-object-injection */

import { MongoClient, ObjectId } from 'mongodb'
import { MongoMemoryServer } from 'mongodb-memory-server'
import {
  DatabaseCollections,
  DatabaseName,
  VaultStoreFromMongoDb
} from '../../../src/services/vault/VaultStoreFromMongoDb'

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
    const db = mongoClient.db(DatabaseName)
    await db.collection(DatabaseCollections.MONGODB_CONFIGS).deleteMany({})
    await db.collection(DatabaseCollections.GPHOTOS_CONFIGS).deleteMany({})
    await db.collection(DatabaseCollections.ROOT_ALBUM).deleteMany({})
  })

  describe('getMongoDbConfigs', () => {
    it('should return MongoDB clients', async () => {
      const testClients = [
        {
          _id: new ObjectId(),
          name: 'bob@gmail.com',
          read_only_connection_string: 'mongodb://localhost:27017'
        },
        {
          _id: new ObjectId(),
          name: 'sam@gmail.com',
          read_only_connection_string: 'mongodb://localhost:27018'
        }
      ]
      await mongoClient
        .db(DatabaseName)
        .collection(DatabaseCollections.MONGODB_CONFIGS)
        .insertMany(testClients)

      const result = await vaultStore.getMongoDbConfigs()

      expect(result).toHaveLength(2)
      expect(result[0]).toEqual({
        id: testClients[0]._id.toString(),
        name: 'bob@gmail.com',
        connectionString: 'mongodb://localhost:27017'
      })
      expect(result[1]).toEqual({
        id: testClients[1]._id.toString(),
        name: 'sam@gmail.com',
        connectionString: 'mongodb://localhost:27018'
      })
    })
  })

  describe('getGPhotosConfigs', () => {
    it('should return GPhotos clients', async () => {
      const testClients = [
        {
          _id: new ObjectId(),
          name: 'bob@gmail.com',
          read_write_credentials: {
            token: 'token1',
            token_uri: 'google.com',
            refresh_token: 'refresh1',
            client_id: 'id1',
            client_secret: 'secret1'
          }
        },
        {
          _id: new ObjectId(),
          name: 'sam@gmail.com',
          read_write_credentials: {
            token: 'token2',
            token_uri: 'google.com',
            refresh_token: 'refresh2',
            client_id: 'id2',
            client_secret: 'secret2'
          }
        }
      ]
      await mongoClient
        .db(DatabaseName)
        .collection(DatabaseCollections.GPHOTOS_CONFIGS)
        .insertMany(testClients)

      const configs = await vaultStore.getGPhotosConfigs()

      expect(configs).toHaveLength(2)
      configs.forEach((config, i) => {
        expect(config.id).toEqual(testClients[i]._id.toString())
        expect(config.name).toEqual(testClients[i].name)
        expect(config.credentials.token).toEqual(
          testClients[i].read_write_credentials.token
        )
        expect(config.credentials.tokenUri).toEqual(
          testClients[i].read_write_credentials.token_uri
        )
        expect(config.credentials.refreshToken).toEqual(
          testClients[i].read_write_credentials.refresh_token
        )
        expect(config.credentials.clientId).toEqual(
          testClients[i].read_write_credentials.client_id
        )
        expect(config.credentials.clientSecret).toEqual(
          testClients[i].read_write_credentials.client_secret
        )
      })
    })
  })

  describe('getRootAlbumId', () => {
    it('should return the root album ID', async () => {
      const rootAlbum = {
        client_id: new ObjectId(),
        object_id: new ObjectId()
      }

      await mongoClient
        .db(DatabaseName)
        .collection(DatabaseCollections.ROOT_ALBUM)
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
