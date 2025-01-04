/* eslint-disable security/detect-non-literal-fs-filename */

import * as fs from 'fs'
import * as os from 'os'
import * as path from 'path'
import { MongoClient } from 'mongodb'
import { MongoMemoryServer } from 'mongodb-memory-server'
import { GPhotosClient } from '../../../src/services/blob_store/GPhotosClient'
import { VaultStoreFromFile } from '../../../src/services/vault/VaultStoreFromFile'

describe('VaultStoreFromFile', () => {
  let mongoDb: MongoMemoryServer
  let tempConfigPath: string
  let vaultStore: VaultStoreFromFile

  beforeAll(async () => {
    // Create an in-memory MongoDB server
    mongoDb = await MongoMemoryServer.create()
    const uri = mongoDb.getUri()

    // Create a temporary file
    const tempDir = os.tmpdir()
    tempConfigPath = path.join(tempDir, 'test-config.ini')

    // Write test configuration to the temporary file
    const testConfig =
      '[mongodb_section]\n' +
      'type = mongodb\n' +
      `connection_string = ${uri}\n` +
      '\n' +
      '[gphotos_section]\n' +
      'type = gphotos\n' +
      'name = TestGPhotos\n' +
      'token = test_access_token\n' +
      'refresh_token = test_refresh_token\n' +
      'client_id = test_client_id\n' +
      'client_secret = test_client_secret\n' +
      '\n' +
      '[root_album_section]\n' +
      'type = root_album\n' +
      'client_id = test_client_id\n' +
      'object_id = test_object_id\n' +
      '\n' +
      '[invalid_section]\n' +
      'type = invalid'
    fs.writeFileSync(tempConfigPath, testConfig)

    // Create VaultStoreFromFile instance
    vaultStore = new VaultStoreFromFile(tempConfigPath)
  })

  afterAll(async () => {
    // Clean up the temporary file
    fs.unlinkSync(tempConfigPath)

    // Shut down MongoDB server
    await mongoDb.stop()
  })

  describe('getMongoDbClients', () => {
    it('should return MongoDB clients for valid sections', async () => {
      const clients = await vaultStore.getMongoDbClients()

      expect(clients.length).toBe(1)
      expect(clients[0][0]).toBe('mongodb_section')
      expect(clients[0][1]).toBeInstanceOf(MongoClient)
    })
  })

  describe('getGPhotosClients', () => {
    it('should return GPhotos clients for valid sections', async () => {
      const clients = await vaultStore.getGPhotosClients()

      expect(clients.length).toBe(1)
      expect(clients[0][0]).toBe('gphotos_section')
      expect(clients[0][1]).toBeInstanceOf(GPhotosClient)
      expect(clients[0][1].getName()).toBe('TestGPhotos')
    })
  })

  describe('getRootAlbumId', () => {
    it('should return the root album ID', async () => {
      const rootAlbumId = await vaultStore.getRootAlbumId()

      expect(rootAlbumId).toEqual({
        clientId: 'test_client_id',
        objectId: 'test_object_id'
      })
    })

    it('should throw an error if root album is not found', async () => {
      // Create a new config without root album section
      const newConfigPath = path.join(os.tmpdir(), 'test-config-no-root.ini')
      fs.writeFileSync(newConfigPath, '[some_section]\ntype = other')

      const newVaultStore = new VaultStoreFromFile(newConfigPath)

      await expect(newVaultStore.getRootAlbumId()).rejects.toThrow(
        'Cannot find root album'
      )

      fs.unlinkSync(newConfigPath)
    })
  })
})
