import { mock } from 'jest-mock-extended';
import nock from 'nock';
import { GPhotosCredentials } from '../../../../src/services/blob_store/gphotos/GPhotosClient';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../../../../src/services/blob_store/gphotos/GPhotosClientsRepository';
import { Vault } from '../../../../src/services/vault/VaultStore';

const gPhotosCredentials1: GPhotosCredentials = {
  token: 'token1',
  tokenUri: 'https://oauth2.googleapis.com/token',
  refreshToken: 'refresh1',
  clientId: 'client_id_1',
  clientSecret: 'client_secret_1'
};

const gPhotosCredentials2: GPhotosCredentials = {
  token: 'token2',
  tokenUri: 'https://oauth2.googleapis.com/token',
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
    nock.cleanAll();
  });

  describe('buildFromVault', () => {
    it('should update configs when client refreshes token', async () => {
      const newAccessToken = 'new_access_token';
      nock('https://oauth2.googleapis.com')
        .post('/token')
        .reply(200, { access_token: newAccessToken });

      const client = gphotosClientsRepo.getGPhotosClientById('1');
      await client.refreshCredentials();

      expect(mockVault.updateGPhotosConfig).toHaveBeenCalledWith({
        id: '1',
        newCredentials: {
          clientId: 'client_id_1',
          clientSecret: 'client_secret_1',
          refreshToken: 'refresh1',
          token: 'new_access_token',
          tokenUri: 'https://oauth2.googleapis.com/token'
        }
      });
    });

    it('should not update configs when client refreshes token and throws an exception', async () => {
      nock('https://oauth2.googleapis.com').post('/token').reply(500);

      const client = gphotosClientsRepo.getGPhotosClientById('1');
      try {
        await client.refreshCredentials();
      } catch {
        /* empty */
      }

      expect(mockVault.updateGPhotosConfig).not.toHaveBeenCalled();
    });
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
