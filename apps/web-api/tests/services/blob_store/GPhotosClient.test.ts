import { AxiosError } from 'axios';
import nock from 'nock';
import {
  GPhotosClient,
  GPhotosCredentials,
  RefreshCredentialsListener
} from '../../../src/services/blob_store/GPhotosClient';

describe('GPhotosClient', () => {
  const credentials: GPhotosCredentials = {
    token: 'initial_access_token',
    tokenUri: 'https://oauth2.googleapis.com/token',
    refreshToken: 'valid_refresh_token',
    clientId: 'test_client_id',
    clientSecret: 'test_client_secret'
  };

  afterEach(() => {
    nock.cleanAll();
  });

  describe('getName', () => {
    it('should return the name of the Google Photos client', () => {
      const gphotosClient = new GPhotosClient('Test Account', credentials);

      expect(gphotosClient.getName()).toBe('Test Account');
    });
  });

  describe('getCredentials', () => {
    it('should return the credentials', () => {
      const gphotosClient = new GPhotosClient('Test Account', credentials);

      expect(gphotosClient.getCredentials()).toEqual(credentials);
    });
  });

  describe('setCredentials', () => {
    it('should set new credentials', () => {
      const gphotosClient = new GPhotosClient('Test Account', credentials);

      const newCredentials: GPhotosCredentials = {
        token: 'token2',
        tokenUri: 'https://oauth2.googleapis.com/token',
        refreshToken: 'refresh2',
        clientId: 'client_id_2',
        clientSecret: 'client_secret_2'
      };
      gphotosClient.setCredentials(newCredentials);

      expect(gphotosClient.getCredentials()).toEqual(newCredentials);
    });
  });

  describe('refreshCredentials', () => {
    it('should refresh the access token successfully', async () => {
      const newAccessToken = 'new_access_token';

      // Mocking the POST request to Google's OAuth2 token endpoint
      nock('https://oauth2.googleapis.com')
        .post('/token')
        .reply(200, { access_token: newAccessToken });

      const gphotosClient = new GPhotosClient('Test Account', credentials);
      await gphotosClient.refreshCredentials();

      // Check that the access token has been updated
      expect(gphotosClient.getCredentials().token).toBe(newAccessToken);
    });

    it('should throw an error if refreshing the access token fails', async () => {
      // Mocking a failed request to Google's OAuth2 token endpoint
      nock('https://oauth2.googleapis.com')
        .post('/token')
        .reply(400, { error: 'invalid_grant' });

      const gphotosClient = new GPhotosClient('Test Account', credentials);
      await expect(gphotosClient.refreshCredentials()).rejects.toThrow();

      // Check that the credentials were not modified
      expect(gphotosClient.getCredentials()).toEqual(credentials);
    });

    it('should pause on RefreshCredentialsListener.beforeRefresh() and call RefreshCredentialsListener.afterRefresh() on successful refresh', async () => {
      const listener: RefreshCredentialsListener = {
        beforeRefresh: jest.fn(() => Promise.resolve()),
        afterRefresh: jest.fn(() => Promise.resolve())
      };
      const gphotosClient = new GPhotosClient('Test Account', credentials);
      gphotosClient.setRefreshCredentialsListener(listener);

      // Mocking the POST request to Google's OAuth2 token endpoint
      const newAccessToken = 'new_access_token';
      nock('https://oauth2.googleapis.com')
        .post('/token')
        .reply(200, { access_token: newAccessToken });

      await gphotosClient.refreshCredentials();

      // Check that the listeners were called
      expect(listener.beforeRefresh).toHaveBeenCalled();
      expect(listener.afterRefresh).toHaveBeenCalled();

      // Check that the access token has been updated
      expect(gphotosClient.getCredentials().token).toBe(newAccessToken);
    });

    it('should call RefreshCredentialsListener.afterRefresh() with error on failed refresh', async () => {
      const listener: RefreshCredentialsListener = {
        beforeRefresh: jest.fn(() => Promise.resolve()),
        afterRefresh: jest.fn(() => Promise.resolve())
      };
      const gphotosClient = new GPhotosClient('Test Account', credentials);
      gphotosClient.setRefreshCredentialsListener(listener);

      // Mocking a failed request to Google's OAuth2 token endpoint
      nock('https://oauth2.googleapis.com')
        .post('/token')
        .reply(400, { error: 'invalid_grant' });

      await expect(gphotosClient.refreshCredentials()).rejects.toThrow();

      // Check that the listeners were called
      expect(listener.beforeRefresh).toHaveBeenCalled();
      expect(listener.afterRefresh).toHaveBeenCalledWith(
        new AxiosError('Request failed with status code 400')
      );

      // Check that the credentials were not modified
      expect(gphotosClient.getCredentials()).toEqual(credentials);
    });
  });
});
