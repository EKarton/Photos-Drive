import { mock } from 'jest-mock-extended';
import { GPhotosCredentials } from '../../../src/services/blob_store/GPhotosClient';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../../../src/services/blob_store/GPhotosClientsRepository';
import { Vault } from '../../../src/services/vault/VaultStore';

const gPhotosCredentials1: GPhotosCredentials = {
  token: 'token1',
  tokenUri: 'google.com',
  refreshToken: 'refresh1',
  clientId: 'client_id_1',
  clientSecret: 'client_secret_1'
};

const gPhotosCredentials2: GPhotosCredentials = {
  token: 'token2',
  tokenUri: 'google.com',
  refreshToken: 'refresh2',
  clientId: 'client_id_2',
  clientSecret: 'client_secret_2'
};

describe('GPhotosClientsRepository', () => {
  let mockVault: jest.Mocked<Vault>;
  let gphotosClientsRepo: GPhotosClientsRepository;

  beforeEach(async () => {
    mockVault = mock<Vault>();
    mockVault.getGPhotosConfigs.mockResolvedValue([
      {
        id: '1',
        name: 'bob@gmail.com',
        credentials: gPhotosCredentials1
      },
      {
        id: '2',
        name: 'sam@gmail.com',
        credentials: gPhotosCredentials2
      }
    ]);

    gphotosClientsRepo =
      await GPhotosClientsRepository.buildFromVault(mockVault);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('getGPhotosClientById', () => {
    it('should return the GPhotosClient when found', () => {
      const client = gphotosClientsRepo.getGPhotosClientById('1');

      expect(client.getName()).toBeTruthy();
    });

    it('should throw NoGPhotosClientFoundError when client is not found', () => {
      const fnToTest = () =>
        gphotosClientsRepo.getGPhotosClientById('nonexistent');

      expect(fnToTest).toThrow(NoGPhotosClientFoundError);
      expect(fnToTest).toThrow(
        'No google photos client found with id nonexistent'
      );
    });
  });

  describe('getGPhotosClients', () => {
    it('should return all GPhotos clients with their IDs', () => {
      const clients = gphotosClientsRepo.getGPhotosClients();

      expect(clients.length).toEqual(2);
    });
  });
});
