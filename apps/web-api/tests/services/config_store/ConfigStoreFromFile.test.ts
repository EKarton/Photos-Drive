/* eslint-disable security/detect-non-literal-fs-filename */

import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { UpdateGPhotosConfigRequest } from '../../../src/services/config_store/ConfigStore';
import {
  ConfigStoreFromFile,
  SectionTypes
} from '../../../src/services/config_store/ConfigStoreFromFile';

describe('ConfigStoreFromFile', () => {
  let tempConfigPath: string;
  let vaultStore: ConfigStoreFromFile;

  beforeEach(async () => {
    // Create a temporary file
    const tempDir = os.tmpdir();
    tempConfigPath = path.join(tempDir, 'test-config.ini');

    // Write test configuration to the temporary file
    const testConfig =
      '[1]\n' +
      `type = ${SectionTypes.MONGODB_CONFIG}\n` +
      'name = bob@gmail.com\n' +
      `read_only_connection_string = localhost:8080\n` +
      '\n' +
      '[2]\n' +
      `type = ${SectionTypes.GPHOTOS_CONFIG}\n` +
      'name = sam@gmail.com\n' +
      'read_write_credentials_token = test_access_token\n' +
      'read_write_credentials_token_uri = https://oauth2.googleapis.com/token\n' +
      'read_write_credentials_refresh_token = test_refresh_token\n' +
      'read_write_credentials_client_id = test_client_id\n' +
      'read_write_credentials_client_secret = test_client_secret\n' +
      '\n' +
      '[3]\n' +
      `type = ${SectionTypes.ROOT_ALBUM}\n` +
      'client_id = 1\n' +
      'object_id = 123\n' +
      '\n' +
      '[4]\n' +
      'type = invalid-section';
    fs.writeFileSync(tempConfigPath, testConfig);

    // Create ConfigStoreFromFile instance
    vaultStore = new ConfigStoreFromFile(tempConfigPath);
  });

  afterEach(async () => {
    // Clean up the temporary file
    fs.unlinkSync(tempConfigPath);
  });

  describe('getMongoDbConfigs', () => {
    it('should return MongoDB clients for valid sections', async () => {
      const clients = await vaultStore.getMongoDbConfigs();

      expect(clients.length).toEqual(1);
      expect(clients[0]).toEqual({
        id: '1',
        name: 'bob@gmail.com',
        connectionString: 'localhost:8080'
      });
    });
  });

  describe('getGPhotosConfigs', () => {
    it('should return GPhotos clients for valid sections', async () => {
      const clients = await vaultStore.getGPhotosConfigs();

      expect(clients.length).toEqual(1);
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
      });
    });
  });

  describe('updateGPhotosConfig', () => {
    it('should update GPhotos config with new credentials', async () => {
      const request: UpdateGPhotosConfigRequest = {
        id: '2',
        newCredentials: {
          token: 'new_access_token',
          refreshToken: 'new_refresh_token',
          tokenUri: 'https://new.oauth2.googleapis.com/token',
          clientId: 'new_client_id',
          clientSecret: 'new_client_secret'
        }
      };

      await vaultStore.updateGPhotosConfig(request);

      // Verify the update
      const updatedConfigs = await vaultStore.getGPhotosConfigs();
      expect(updatedConfigs.length).toEqual(1);
      expect(updatedConfigs[0]).toEqual({
        id: '2',
        name: 'sam@gmail.com',
        credentials: request.newCredentials
      });

      // Verify the file was updated
      const fileContent = fs.readFileSync(tempConfigPath, 'utf-8');
      expect(fileContent).toEqual(
        '[1]\n' +
          'type=mongodb_config\n' +
          'name=bob@gmail.com\n' +
          'read_only_connection_string=localhost:8080\n' +
          '\n' +
          '[2]\n' +
          'type=gphotos_config\n' +
          'name=sam@gmail.com\n' +
          'read_write_credentials_token=new_access_token\n' +
          'read_write_credentials_token_uri=https://new.oauth2.googleapis.com/token\n' +
          'read_write_credentials_refresh_token=new_refresh_token\n' +
          'read_write_credentials_client_id=new_client_id\n' +
          'read_write_credentials_client_secret=new_client_secret\n' +
          '\n' +
          '[3]\n' +
          'type=root_album\n' +
          'client_id=1\n' +
          'object_id=123\n' +
          '\n' +
          '[4]\n' +
          'type=invalid-section\n'
      );
    });

    it('should throw an error for non-existent config', async () => {
      const request: UpdateGPhotosConfigRequest = {
        id: 'non-existent',
        newCredentials: {
          token: 'new_token',
          refreshToken: 'new_refresh_token',
          tokenUri: 'https://new.oauth2.googleapis.com/token',
          clientId: 'new_client_id',
          clientSecret: 'new_client_secret'
        }
      };

      await expect(vaultStore.updateGPhotosConfig(request)).rejects.toThrow(
        'Cannot find config non-existent'
      );
    });

    it('should throw an error for non-GPhotos config', async () => {
      const request: UpdateGPhotosConfigRequest = {
        id: '1', // This is a MongoDB config in the test setup
        newCredentials: {
          token: 'new_token',
          refreshToken: 'new_refresh_token',
          tokenUri: 'https://new.oauth2.googleapis.com/token',
          clientId: 'new_client_id',
          clientSecret: 'new_client_secret'
        }
      };

      await expect(vaultStore.updateGPhotosConfig(request)).rejects.toThrow(
        '1 is not a GPhotos config'
      );
    });

    it('should not update if newCredentials is not provided', async () => {
      const request: UpdateGPhotosConfigRequest = {
        id: '2'
      };

      await vaultStore.updateGPhotosConfig(request);

      // Verify no changes were made
      const updatedConfigs = await vaultStore.getGPhotosConfigs();
      expect(updatedConfigs.length).toEqual(1);
      expect(updatedConfigs[0]).toEqual({
        id: '2',
        name: 'sam@gmail.com',
        credentials: {
          token: 'test_access_token',
          tokenUri: 'https://oauth2.googleapis.com/token',
          refreshToken: 'test_refresh_token',
          clientId: 'test_client_id',
          clientSecret: 'test_client_secret'
        }
      });
    });
  });

  describe('getVectorStoreConfigs', () => {
    it('should return vector store configs for valid sections', async () => {
      // Create a new config file containing a MongoDB vector store config
      const vectorConfigPath = path.join(os.tmpdir(), 'test-config-vector.ini');
      const vectorTestConfig =
        '[vec1]\n' +
        `type = ${SectionTypes.MONGODB_VECTOR_STORE_CONFIG}\n` +
        'name = my_vector_store\n' +
        'read_only_connection_string = mongodb://localhost:27017\n';

      fs.writeFileSync(vectorConfigPath, vectorTestConfig);

      const vectorVaultStore = new ConfigStoreFromFile(vectorConfigPath);
      const configs = await vectorVaultStore.getVectorStoreConfigs();

      expect(configs.length).toBe(1);
      expect(configs[0]).toEqual({
        id: 'vec1',
        name: 'my_vector_store',
        connectionString: 'mongodb://localhost:27017'
      });

      fs.unlinkSync(vectorConfigPath);
    });

    it('should return an empty array if no vector store configs are present', async () => {
      // Create a config file without mongodb_vector_store_config type
      const noVectorConfigPath = path.join(
        os.tmpdir(),
        'test-config-no-vector.ini'
      );
      const nonVectorTestConfig =
        '[1]\n' +
        `type = ${SectionTypes.MONGODB_CONFIG}\n` +
        'name = db1\n' +
        'read_only_connection_string = localhost:8080\n';
      fs.writeFileSync(noVectorConfigPath, nonVectorTestConfig);

      const noVectorVaultStore = new ConfigStoreFromFile(noVectorConfigPath);
      const configs = await noVectorVaultStore.getVectorStoreConfigs();

      expect(configs).toEqual([]);

      fs.unlinkSync(noVectorConfigPath);
    });
  });

  describe('getRootAlbumId', () => {
    it('should return the root album ID', async () => {
      const rootAlbumId = await vaultStore.getRootAlbumId();

      expect(rootAlbumId).toEqual({
        clientId: '1',
        objectId: '123'
      });
    });

    it('should throw an error if root album is not found', async () => {
      // Create a new config without root album section
      const newConfigPath = path.join(os.tmpdir(), 'test-config-no-root.ini');
      fs.writeFileSync(newConfigPath, '[some_section]\ntype = other');

      const newVaultStore = new ConfigStoreFromFile(newConfigPath);

      await expect(newVaultStore.getRootAlbumId()).rejects.toThrow(
        'Cannot find root album'
      );

      fs.unlinkSync(newConfigPath);
    });
  });
});
