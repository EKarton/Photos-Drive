import axios from 'axios';
import qs from 'qs';
import checkNotNull from '../../utils/checkNotNull';
import logger from '../../utils/logger';

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
