import { mock } from 'jest-mock-extended'
import { GPhotosClient } from '../../../src/services/blob_store/GPhotosClient'
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../../../src/services/blob_store/GPhotosClientsRepository'
import { Vault } from '../../../src/services/vault/VaultStore'

const gPhotosClient1 = new GPhotosClient('Client One', {
  accessToken: 'token1',
  refreshToken: 'refresh1',
  clientId: 'client_id_1',
  clientSecret: 'client_secret_1'
})
const gPhotosClient2 = new GPhotosClient('Client Two', {
  accessToken: 'token2',
  refreshToken: 'refresh2',
  clientId: 'client_id_2',
  clientSecret: 'client_secret_2'
})
describe('GPhotosClientsRepository', () => {
  let mockVault: jest.Mocked<Vault>
  let gphotosClientsRepo: GPhotosClientsRepository

  beforeEach(async () => {
    mockVault = mock<Vault>()
    mockVault.getGPhotosClients.mockResolvedValue([
      ['client1', gPhotosClient1],
      ['client2', gPhotosClient2]
    ])

    gphotosClientsRepo =
      await GPhotosClientsRepository.buildFromVault(mockVault)
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('getGPhotosClientById', () => {
    it('should return the GPhotosClient when found', () => {
      const client = gphotosClientsRepo.getGPhotosClientById('client1')

      expect(client.getName()).toBe('Client One')
    })

    it('should throw NoGPhotosClientFoundError when client is not found', () => {
      const fnToTest = () =>
        gphotosClientsRepo.getGPhotosClientById('nonexistent')

      expect(fnToTest).toThrow(NoGPhotosClientFoundError)
      expect(fnToTest).toThrow(
        'No google photos client found with id nonexistent'
      )
    })
  })

  describe('getGPhotosClients', () => {
    it('should return all GPhotos clients with their IDs', () => {
      const clients = gphotosClientsRepo.getGPhotosClients()

      expect(clients).toEqual([
        ['client1', gPhotosClient1],
        ['client2', gPhotosClient2]
      ])
    })
  })
})
