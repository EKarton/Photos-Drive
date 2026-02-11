import axios from 'axios';
import qs from 'qs';
import checkNotNull from '../../../../utils/checkNotNull';
import logger from '../../../../utils/logger';
import { MediaItem } from './GMediaItems';

/** Represents the credentials of a Google Photos client. */
export type GPhotosCredentials = {
  /** The access token. */
  token: string;

  /** The refresh token. */
  refreshToken: string;

  /** The token uri to fetch new tokens. */
  tokenUri: string;

  /** The client ID. */
  clientId: string;

  /** The client secret. */
  clientSecret: string;
};

/**
 * A class that represents an account on Google Photos.
 * It should be able to do the same stuff as in {@link https://developers.google.com/photos/library/reference/rest}.
 */
export class GPhotosClient {
  private name: string;
  private credentials: GPhotosCredentials;
  private refreshListener?: RefreshCredentialsListener;

  /**
   * Constructs the {@code GPhotosClient} class.
   * @param name the name of the Google Photos account.
   * @param credentials the account credentials that is observable.
   */
  constructor(name: string, initialCredentials: GPhotosCredentials) {
    this.name = name;
    this.credentials = initialCredentials;
  }

  /** Returns the name of the Google Photos client */
  public getName(): string {
    return this.name;
  }

  /** Returns the credentials. */
  public getCredentials(): GPhotosCredentials {
    return { ...this.credentials };
  }

  /** Sets the credentials. */
  public setCredentials(newCredentials: GPhotosCredentials) {
    this.credentials = newCredentials;
  }

  /** Sets the refresh listener. */
  public setRefreshCredentialsListener(listener: RefreshCredentialsListener) {
    this.refreshListener = listener;
  }

  /** Refreshes the access token. */
  async refreshCredentials() {
    await this.refreshListener?.beforeRefresh();

    try {
      const uri = this.credentials.tokenUri;
      const requestBody = {
        client_id: this.credentials.clientId,
        client_secret: this.credentials.clientSecret,
        refresh_token: this.credentials.refreshToken,
        grant_type: 'refresh_token'
      };
      const headers = {
        'content-type': 'application/x-www-form-urlencoded'
      };

      logger.info(`Fetching new token for account ${this.name}`);
      const response = await axios.post(uri, qs.stringify(requestBody), {
        headers
      });

      this.credentials = {
        ...this.credentials,
        token: checkNotNull(response.data['access_token'])
      };

      await this.refreshListener?.afterRefresh();
    } catch (error) {
      await this.refreshListener?.afterRefresh(error as Error);
      throw error;
    }
  }

  /**
   * Gets the media item details for a given media item id.
   * If the access token has expired, it will refresh the token and retry the request.
   *
   * @param mediaItemId the id of the media item.
   * @returns the details of the media item.
   */
  public async getMediaItem(mediaItemId: string): Promise<MediaItem> {
    const url = `https://photoslibrary.googleapis.com/v1/mediaItems/${mediaItemId}`;

    try {
      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${this.credentials.token}`
        }
      });
      return response.data as MediaItem;
    } catch (error) {
      // If the error is an AxiosError and the status is 401, try refreshing the credentials
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        logger.info(
          `Access token expired for ${this.name}. Refreshing token and retrying...`
        );
        await this.refreshCredentials();

        // Retry the request with the new token
        const retryResponse = await axios.get(url, {
          headers: {
            Authorization: `Bearer ${this.credentials.token}`
          }
        });
        return retryResponse.data as MediaItem;
      }

      // If the error was not a 401, rethrow it
      throw error;
    }
  }
}

/** An event listener for whenever the GPhotosClient refreshes the access token. */
export interface RefreshCredentialsListener {
  /**
   * Called right before refreshing the access token.
   * It will wait until the return value resolves before refreshing the access token.
   */
  beforeRefresh: () => Promise<void>;

  /**
   * Called right after refreshing the access token.
   * It will wait until the return value resolves before completing refreshing the access token.
   *
   * @param err If there was an error, it would pass the error here.
   */
  afterRefresh: (err?: Error) => Promise<void>;
}
