import { MongoClient } from 'mongodb';
import { GPhotosClient, GPhotosCredentials } from '../blob_store/GPhotosClient';
import { AlbumId } from '../metadata_store/Albums';

/** Represents a Google Photos config. */
export interface GPhotosConfig {
  /** Unique ID for this Google Photos config. */
  id: string;

  /** The name for this GPhotos config */
  name: string;

  /** Its credentials. */
  credentials: GPhotosCredentials;
}

/** Represents a MongoDB config */
export interface MongoDbConfig {
  /** Unique ID for this MongoDB configuration. */
  id: string;

  /** The name for this MongoDB config */
  name: string;

  /** The connection string to this MongoDB config. */
  connectionString: string;
}

/** Represents a request to update the GPhotos Config. */
export interface UpdateGPhotosConfigRequest {
  /** The ID of the config you want to update. */
  id: string;

  /** New credentials, if they exist. */
  newCredentials?: GPhotosCredentials;
}

/** Represents the config of the entire system. */
export interface Vault {
  /**
   * Returns a list of MongoDB clients with their IDs.
   */
  getMongoDbClients(): Promise<[string, MongoClient][]>;

  /**
   * Returns a list of MongoDB configs.
   */
  getMongoDbConfigs(): Promise<MongoDbConfig[]>;

  /**
   * Returns a list of tuples, where each tuple is a Google Photo client ID and a Google Photos client instance.
   */
  getGPhotosClients(): Promise<[string, GPhotosClient][]>;

  /**
   * Returns a list of GPhotos configs.
   */
  getGPhotosConfigs(): Promise<GPhotosConfig[]>;

  /**
   * Updates a GPhotos config.
   *
   * @param request The request to update a particular config.
   */
  updateGPhotosConfig(request: UpdateGPhotosConfigRequest): Promise<void>;

  /**
   * Gets the ID of the root album.
   *
   * @throws Error if there is no root album ID.
   * @returns The album ID.
   */
  getRootAlbumId(): Promise<AlbumId>;
}
