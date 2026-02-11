import { mock } from 'jest-mock-extended';
import { MongoClient } from 'mongodb';
import { ConfigStore } from '../../../../src/services/core/config/ConfigStore';
import {
  InMemoryMongoDbClientsRepository,
  MongoDbClientNotFoundError,
  MongoDbClientsStoreImpl
} from '../../../../src/services/core/databases/MongoDbClientsStore';

describe('MongoDbClientsRepositoryImpl', () => {
  let mockConfigStore: jest.Mocked<ConfigStore>;
  let mongoDbClientsRepo: MongoDbClientsStoreImpl;

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
      await MongoDbClientsStoreImpl.buildFromVault(mockConfigStore);
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

describe('InMemoryMongoDbClientsRepository', () => {
  let repo: InMemoryMongoDbClientsRepository;
  let mockClient1: MongoClient;
  let mockClient2: MongoClient;

  beforeEach(() => {
    mockClient1 = {} as MongoClient;
    mockClient2 = {} as MongoClient;

    repo = new InMemoryMongoDbClientsRepository([
      ['client1', mockClient1],
      ['client2', mockClient2]
    ]);
  });

  afterEach(() => {
    repo.clear();
  });

  describe('getClientFromId', () => {
    it('should return the client when it exists', () => {
      const result = repo.getClientFromId('client1');
      expect(result).toBe(mockClient1);
    });

    it('should throw an error when the client does not exist', () => {
      const fnToTest = () => repo.getClientFromId('nonexistent');
      expect(fnToTest).toThrow(MongoDbClientNotFoundError);
      expect(fnToTest).toThrow(
        'Cannot find MongoDB client with id nonexistent'
      );
    });
  });

  describe('listClients', () => {
    it('should return all clients in the repository', () => {
      const clients = repo.listClients();
      expect(clients).toEqual([
        ['client1', mockClient1],
        ['client2', mockClient2]
      ]);
    });
  });

  describe('setClient', () => {
    it('should add a new client', () => {
      const newClient = {} as MongoClient;
      repo.setClient('client3', newClient);

      const result = repo.getClientFromId('client3');
      expect(result).toBe(newClient);
    });

    it('should overwrite an existing client', () => {
      const updatedClient = {} as MongoClient;
      repo.setClient('client1', updatedClient);

      const result = repo.getClientFromId('client1');
      expect(result).toBe(updatedClient);
    });
  });

  describe('deleteClient', () => {
    it('should remove the client from the repository', () => {
      repo.deleteClient('client1');

      expect(() => repo.getClientFromId('client1')).toThrow(
        MongoDbClientNotFoundError
      );
    });
  });

  describe('clear', () => {
    it('should remove all clients from the repository', () => {
      repo.clear();
      expect(repo.listClients()).toEqual([]);
    });
  });
});
