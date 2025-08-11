import { GPhotosCredentials } from '../blob_store/gphotos/GPhotosClient';
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

/** Represents a Vector Store config */
export interface VectorStoreConfig {
  /** Unique ID to this vector store. */
  id: string;

  /** Name of this vector store. */
  name: string;
}

/** Represents a MongoDB Vector Store config */
export interface MongoDbVectorStoreConfig extends VectorStoreConfig {
  /** The connection string to this config. */
  connectionString: string;
}

/** Represents the config of the entire system. */
export interface ConfigStore {
  /**
   * Returns a list of MongoDB configs.
   */
  getMongoDbConfigs(): Promise<MongoDbConfig[]>;

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

  /** 
   * Returns a list of vector store configs.
   */
  getVectorStoreConfigs(): Promise<VectorStoreConfig[]>;
}
