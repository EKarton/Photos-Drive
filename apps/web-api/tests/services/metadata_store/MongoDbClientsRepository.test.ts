import { mock } from 'jest-mock-extended'
import { MongoClient } from 'mongodb'
import {
  MongoDbClientNotFoundError,
  MongoDbClientsRepositoryImpl
} from '../../../src/services/metadata_store/MongoDbClientsRepository'
import { Vault } from '../../../src/services/vault/VaultStore'

describe('MongoDbClientsRepositoryImpl', () => {
  let mockVault: jest.Mocked<Vault>
  let mongoDbClientsRepo: MongoDbClientsRepositoryImpl
  let mockClient: MongoClient

  beforeEach(async () => {
    // Create a mock MongoDB client
    mockClient = new MongoClient('mongodb://localhost:27017/testdb')

    // Create a mocked implementation of Vault
    mockVault = mock<Vault>()
    mockVault.getMongoDbClients.mockResolvedValue([
      ['client1', mockClient],
      ['client2', mockClient]
    ])

    // Build the repository from the mocked vault
    mongoDbClientsRepo =
      await MongoDbClientsRepositoryImpl.buildFromVault(mockVault)
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('getClientFromId', () => {
    it('should return the MongoDB client when it exists', () => {
      const client = mongoDbClientsRepo.getClientFromId('client1')
      expect(client).toBe(mockClient)
    })

    it('should throw an error when the client does not exist', () => {
      expect(() => mongoDbClientsRepo.getClientFromId('nonexistent')).toThrow(
        MongoDbClientNotFoundError
      )
      expect(() => mongoDbClientsRepo.getClientFromId('nonexistent')).toThrow(
        'Cannot find MongoDB client with id nonexistent'
      )
    })
  })

  describe('listClients', () => {
    it('should return a list of all clients', () => {
      const clients = mongoDbClientsRepo.listClients()
      expect(clients).toEqual([
        ['client1', mockClient],
        ['client2', mockClient]
      ])
    })
  })
})
