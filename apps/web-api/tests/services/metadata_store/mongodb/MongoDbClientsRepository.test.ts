import { mock } from 'jest-mock-extended';
import { ConfigStore } from '../../../../src/services/config_store/ConfigStore';
import {
  MongoDbClientNotFoundError,
  MongoDbClientsRepositoryImpl
} from '../../../../src/services/metadata_store/mongodb/MongoDbClientsRepository';

describe('MongoDbClientsRepositoryImpl', () => {
  let mockConfigStore: jest.Mocked<ConfigStore>;
  let mongoDbClientsRepo: MongoDbClientsRepositoryImpl;

  beforeEach(async () => {
    // Create a mocked implementation of Vault
    mockConfigStore = mock<ConfigStore>();
    mockConfigStore.getMongoDbConfigs.mockResolvedValue([
      {
        id: '1',
        name: 'bob@gmail.com',
        connectionString: 'mongodb://localhost:27017/testdb'
      },
      {
        id: '2',
        name: 'sam@gmail.com',
        connectionString: 'mongodb://localhost:27017/testdb'
      }
    ]);

    // Build the repository from the mocked vault
    mongoDbClientsRepo =
      await MongoDbClientsRepositoryImpl.buildFromVault(mockConfigStore);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('getClientFromId', () => {
    it('should return the MongoDB client when it exists', () => {
      const client = mongoDbClientsRepo.getClientFromId('1');

      expect(client).toBeTruthy();
    });

    it('should throw an error when the client does not exist', () => {
      const fnToTest = () => mongoDbClientsRepo.getClientFromId('nonexistent');

      expect(fnToTest).toThrow(MongoDbClientNotFoundError);
      expect(fnToTest).toThrow(
        'Cannot find MongoDB client with id nonexistent'
      );
    });
  });

  describe('listClients', () => {
    it('should return a list of all clients', () => {
      const clients = mongoDbClientsRepo.listClients();
      expect(clients.length).toEqual(2);
    });
  });
});
