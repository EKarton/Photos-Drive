import nock from 'nock';
import {
  GPhotosClient,
  GPhotosCredentials
} from '../../../src/services/blob_store/GPhotosClient';

describe('GPhotosClient', () => {
  const credentials: GPhotosCredentials = {
    accessToken: 'initial_access_token',
    refreshToken: 'valid_refresh_token',
    clientId: 'test_client_id',
    clientSecret: 'test_client_secret'
  };

  const gphotosClient = new GPhotosClient('Test Account', credentials);

  afterEach(() => {
    nock.cleanAll(); // Clean up all nocks after each test
  });

  describe('getName', () => {
    it('should return the name of the Google Photos client', () => {
      expect(gphotosClient.getName()).toBe('Test Account');
    });
  });

  describe('getCredentials', () => {
    it('should return the credentials of the Google Photos client', () => {
      expect(gphotosClient.getCredentials()).toEqual(credentials);
    });
  });

  describe('refreshAccessToken', () => {
    it('should refresh the access token successfully', async () => {
      const newAccessToken = 'new_access_token';

      // Mocking the POST request to Google's OAuth2 token endpoint
      nock('https://oauth2.googleapis.com')
        .post('/token')
        .reply(200, { access_token: newAccessToken });

      await gphotosClient.refreshAccessToken();

      // Check that the access token has been updated
      expect(gphotosClient.getCredentials().accessToken).toBe(newAccessToken);
    });

    it('should throw an error if refreshing the access token fails', async () => {
      // Mocking a failed request to Google's OAuth2 token endpoint
      nock('https://oauth2.googleapis.com')
        .post('/token')
        .reply(400, { error: 'invalid_grant' });

      await expect(gphotosClient.refreshAccessToken()).rejects.toThrow();
    });
  });
});
