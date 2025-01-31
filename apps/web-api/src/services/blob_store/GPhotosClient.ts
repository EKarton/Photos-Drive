import axios from 'axios'
import qs from 'qs'
import checkNotNull from '../../utils/checkNotNull'
import logger from '../../utils/logger'

/** Represents the credentials of a Google Photos client. */
export type GPhotosCredentials = {
  /** The access token. */
  token: string

  /** The refresh token. */
  refreshToken: string

  /** The token uri to fetch new tokens. */
  tokenUri: string

  /** The client ID. */
  clientId: string

  /** The client secret. */
  clientSecret: string
}

/**
 * A class that represents an account on Google Photos.
 * It should be able to do the same stuff as in {@link https://developers.google.com/photos/library/reference/rest}.
 */
export class GPhotosClient {
  private name: string
  private credentials: GPhotosCredentials

  /**
   * Constructs the {@code GPhotosClient} class.
   * @param name the name of the Google Photos account.
   * @param credentials the account credentials that is observable.
   */
  constructor(name: string, credentials: GPhotosCredentials) {
    this.name = name
    this.credentials = credentials
  }

  /** Returns the name of the Google Photos client */
  public getName(): string {
    return this.name
  }

  /** Returns the credentials. */
  public getCredentials(): GPhotosCredentials {
    return { ...this.credentials }
  }

  /** Refreshes the access token. */
  async refreshAccessToken() {
    const uri = 'https://oauth2.googleapis.com/token'
    const requestBody = {
      client_id: this.credentials.clientId,
      client_secret: this.credentials.clientSecret,
      refresh_token: this.credentials.refreshToken,
      grant_type: 'refresh_token'
    }
    const headers = {
      'content-type': 'application/x-www-form-urlencoded'
    }

    logger.info(`Fetching new access token for account ${this.name}`)
    const response = await axios.post(uri, qs.stringify(requestBody), {
      headers
    })

    this.credentials = {
      ...this.credentials,
      token: checkNotNull(response.data['access_token'])
    }
  }
}
