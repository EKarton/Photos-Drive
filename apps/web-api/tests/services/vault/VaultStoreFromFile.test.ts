/* eslint-disable security/detect-non-literal-fs-filename */

import * as fs from 'fs'
import * as os from 'os'
import * as path from 'path'
import { VaultStoreFromFile } from '../../../src/services/vault/VaultStoreFromFile'

describe('VaultStoreFromFile', () => {
  let tempConfigPath: string
  let vaultStore: VaultStoreFromFile

  beforeAll(async () => {
    // Create a temporary file
    const tempDir = os.tmpdir()
    tempConfigPath = path.join(tempDir, 'test-config.ini')

    // Write test configuration to the temporary file
    const testConfig =
      '[1]\n' +
      'type = mongodb_config\n' +
      'name = bob@gmail.com\n' +
      `read_only_connection_string = localhost:8080\n` +
      '\n' +
      '[2]\n' +
      'type = gphotos_config\n' +
      'name = sam@gmail.com\n' +
      'read_write_credentials_token = test_access_token\n' +
      'read_write_credentials_token_uri = https://oauth2.googleapis.com/token\n' +
      'read_write_credentials_refresh_token = test_refresh_token\n' +
      'read_write_credentials_client_id = test_client_id\n' +
      'read_write_credentials_client_secret = test_client_secret\n' +
      '\n' +
      '[3]\n' +
      'type = root_album\n' +
      'client_id = 1\n' +
      'object_id = 123\n' +
      '\n' +
      '[4]\n' +
      'type = invalid'
    fs.writeFileSync(tempConfigPath, testConfig)

    // Create VaultStoreFromFile instance
    vaultStore = new VaultStoreFromFile(tempConfigPath)
  })

  afterAll(async () => {
    // Clean up the temporary file
    fs.unlinkSync(tempConfigPath)
  })

  describe('getMongoDbConfigs', () => {
    it('should return MongoDB clients for valid sections', async () => {
      const clients = await vaultStore.getMongoDbConfigs()

      expect(clients.length).toEqual(1)
      expect(clients[0]).toEqual({
        id: '1',
        name: 'bob@gmail.com',
        connectionString: 'localhost:8080'
      })
    })
  })

  describe('getGPhotosConfigs', () => {
    it('should return GPhotos clients for valid sections', async () => {
      const clients = await vaultStore.getGPhotosConfigs()

      expect(clients.length).toEqual(1)
      expect(clients[0]).toEqual({
        id: '2',
        name: 'sam@gmail.com',
        credentials: {
          token: 'test_access_token',
          tokenUri: 'https://oauth2.googleapis.com/token',
          refreshToken: 'test_refresh_token',
          clientId: 'test_client_id',
          clientSecret: 'test_client_secret'
        }
      })
    })
  })

  describe('getRootAlbumId', () => {
    it('should return the root album ID', async () => {
      const rootAlbumId = await vaultStore.getRootAlbumId()

      expect(rootAlbumId).toEqual({
        clientId: '1',
        objectId: '123'
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
