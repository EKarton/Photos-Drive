import {
  MongoClient,
  Document as MongoDBDocument,
  ObjectId,
  WithId
} from 'mongodb';
import { AlbumId } from '../metadata_store/Albums';
import {
  ConfigStore,
  GPhotosConfig,
  MongoDbConfig,
  MongoDbVectorStoreConfig,
  UpdateGPhotosConfigRequest,
  VectorStoreConfig
} from './ConfigStore';

export const DatabaseName = 'photos_drive';

/** Possible collections in the database */
export enum DatabaseCollections {
  MONGODB_CONFIGS = 'mongodb_configs',
  GPHOTOS_CONFIGS = 'gphotos_configs',
  ROOT_ALBUM = 'root_album',
  VECTOR_STORE_CONFIGS = 'vector_store_configs'
}

export enum VECTOR_STORE_TYPES {
  MONGO_DB = 'mongodb-vector-store-type'
}

/** Implementation of {@code Vault} read from Mongo Db. */
export class ConfigStoreFromMongoDb implements ConfigStore {
  private _client: MongoClient;

  constructor(client: MongoClient) {
    this._client = client;
  }

  async getMongoDbConfigs(): Promise<MongoDbConfig[]> {
    const docs = await this._client
      .db(DatabaseName)
      .collection(DatabaseCollections.MONGODB_CONFIGS)
      .find()
      .toArray();

    return docs.map((doc) => ({
      id: doc['_id'].toString(),
      name: doc['name'],
      connectionString: doc['read_only_connection_string']
    }));
  }

  async getGPhotosConfigs(): Promise<GPhotosConfig[]> {
    const docs = await this._client
      .db(DatabaseName)
      .collection(DatabaseCollections.GPHOTOS_CONFIGS)
      .find()
      .toArray();

    return docs.map((doc) => ({
      id: doc['_id'].toString(),
      name: doc['name'],
      credentials: {
        token: doc['read_write_credentials']['token'],
        refreshToken: doc['read_write_credentials']['refresh_token'],
        tokenUri: doc['read_write_credentials']['token_uri'],
        clientId: doc['read_write_credentials']['client_id'],
        clientSecret: doc['read_write_credentials']['client_secret']
      }
    }));
  }

  async updateGPhotosConfig(
    request: UpdateGPhotosConfigRequest
  ): Promise<void> {
    const filter = { _id: new ObjectId(request.id) };
    const update: { $set: { [key: string]: object } } = { $set: {} };

    if (request.newCredentials) {
      update['$set']['read_write_credentials'] = {
        token: request.newCredentials.token,
        token_uri: request.newCredentials.tokenUri,
        refresh_token: request.newCredentials.refreshToken,
        client_id: request.newCredentials.clientId,
        client_secret: request.newCredentials.clientSecret
      };
    }

    const result = await this._client
      .db(DatabaseName)
      .collection(DatabaseCollections.GPHOTOS_CONFIGS)
      .updateOne(filter, update);

    if (result.matchedCount !== 1) {
      throw new Error(`Could not find ${request.id} in config`);
    }
  }

  async getRootAlbumId(): Promise<AlbumId> {
    const doc = await this._client
      .db(DatabaseName)
      .collection(DatabaseCollections.ROOT_ALBUM)
      .findOne();

    if (doc === null) {
      throw new Error('No root album found!');
    }

    return {
      clientId: (doc['client_id'] as ObjectId).toString(),
      objectId: (doc['object_id'] as ObjectId).toString()
    };
  }

  async getVectorStoreConfigs(): Promise<VectorStoreConfig[]> {
    const docs = await this._client
      .db(DatabaseName)
      .collection(DatabaseCollections.VECTOR_STORE_CONFIGS)
      .find()
      .toArray();

    const configs: VectorStoreConfig[] = [];
    for (const doc of docs) {
      if (doc['type'] === VECTOR_STORE_TYPES.MONGO_DB) {
        configs.push(this.convertDocToMongoDbVectorStoreConfig(doc));
      }
    }
    return configs;
  }

  private convertDocToMongoDbVectorStoreConfig(
    doc: WithId<MongoDBDocument>
  ): MongoDbVectorStoreConfig {
    return {
      id: doc['_id'].toString(),
      name: doc['name'],
      connectionString: doc['read_only_connection_string']
    };
  }
}
