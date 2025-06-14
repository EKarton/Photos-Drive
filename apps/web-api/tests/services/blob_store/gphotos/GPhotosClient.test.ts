import { AxiosError } from 'axios';
import nock from 'nock';
import { MediaItem } from '../../../../src/services/blob_store/gphotos/GMediaItems';
import {
  GPhotosClient,
  GPhotosCredentials,
  RefreshCredentialsListener
} from '../../../../src/services/blob_store/gphotos/GPhotosClient';

const sampleMediaItem: MediaItem = {
  id: 'sample-media-item-001',
  description: 'A sample media item representing a beautiful landscape photo.',
  productUrl: 'https://photos.google.com/lr/album/sample-media-item-001',
  baseUrl: 'https://lh3.googleusercontent.com/sample-media-item-001',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '2021-06-15T12:34:56Z',
    width: '1920',
    height: '1080',
    photo: {
      cameraMake: 'Canon',
      cameraModel: 'EOS 80D',
      focalLength: 50,
      apertureFNumber: 1.8,
      isoEquivalent: 200,
      exposureTime: '0.005s'
    }
  },
  contributorInfo: {
    profilePictureBaseUrl: 'https://example.com/profiles/johndoe.jpg',
    displayName: 'John Doe'
  },
  filename: 'beautiful-landscape.jpg'
};

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

  describe('getMediaItem', () => {
    const mediaItemId = 'media_item_123';
    const mediaItemUrl = `/v1/mediaItems/${mediaItemId}`;

    it('should return media item details when the request is successful', async () => {
      // Arrange: Mock the GET request to return a successful response.
      nock('https://photoslibrary.googleapis.com')
        .get(mediaItemUrl)
        .matchHeader('Authorization', `Bearer ${credentials.token}`)
        .reply(200, sampleMediaItem);

      const client = new GPhotosClient('Test Account', credentials);

      // Act
      const result = await client.getMediaItem(mediaItemId);

      // Assert
      expect(result).toEqual(sampleMediaItem);
    });

    it('should refresh token and retry when access token is expired (401)', async () => {
      const newAccessToken = 'new_access_token';

      // Arrange:
      // First GET returns a 401 indicating token expiration.
      nock('https://photoslibrary.googleapis.com')
        .get(mediaItemUrl)
        .matchHeader('Authorization', `Bearer ${credentials.token}`)
        .reply(401);

      // Mock the POST request for refreshing the token.
      nock('https://oauth2.googleapis.com')
        .post('/token')
        .reply(200, { access_token: newAccessToken });

      // After refreshing, the GET request should be retried with the new token.
      nock('https://photoslibrary.googleapis.com')
        .get(mediaItemUrl)
        .matchHeader('Authorization', `Bearer ${newAccessToken}`)
        .reply(200, sampleMediaItem);

      const client = new GPhotosClient('Test Account', credentials);

      // Act
      const result = await client.getMediaItem(mediaItemId);

      // Assert: Check that the result is returned and the token was updated.
      expect(result).toEqual(sampleMediaItem);
      expect(client.getCredentials().token).toBe(newAccessToken);
    });

    it('should throw an error if a non-401 error occurs', async () => {
      // Arrange: Mock the GET request to return a 500 error.
      nock('https://photoslibrary.googleapis.com')
        .get(mediaItemUrl)
        .matchHeader('Authorization', `Bearer ${credentials.token}`)
        .reply(500, { error: 'Internal Server Error' });

      const client = new GPhotosClient('Test Account', credentials);

      // Act & Assert: The getMediaItem() method should reject with an error.
      await expect(client.getMediaItem(mediaItemId)).rejects.toThrow();
    });
  });
});
