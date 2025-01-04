import { MongoClient } from 'mongodb'
import { GPhotosClient } from '../blob_store/GPhotosClient'
import { AlbumId } from '../metadata_store/Albums'

/** Represents the config of the entire system. */
export interface Vault {
  /**
   * Returns a list of MongoDB clients with their IDs.
   */
  getMongoDbClients(): Promise<[string, MongoClient][]>

  /**
   * Returns a list of tuples, where each tuple is a Google Photo client ID and a Google Photos client instance.
   */
  getGPhotosClients(): Promise<[string, GPhotosClient][]>

  /**
   * Gets the ID of the root album.
   *
   * @throws Error if there is no root album ID.
   * @returns The album ID.
   */
  getRootAlbumId(): Promise<AlbumId>
}
