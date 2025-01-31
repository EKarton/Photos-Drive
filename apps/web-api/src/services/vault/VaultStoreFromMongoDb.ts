import { MongoClient, ObjectId, ServerApiVersion } from 'mongodb'
import { GPhotosClient, GPhotosCredentials } from '../blob_store/GPhotosClient'
import { AlbumId } from '../metadata_store/Albums'
import { Vault } from './VaultStore'

/** Implementation of {@code Vault} read from Mongo Db. */
export class VaultStoreFromMongoDb implements Vault {
  private _client: MongoClient

  constructor(client: MongoClient) {
    this._client = client
  }

  async getMongoDbClients(): Promise<[string, MongoClient][]> {
    const docs = await this._client
      .db('sharded_google_photos')
      .collection('mongodb_clients')
      .find()
      .toArray()

    return docs.map((doc) => {
      const mongodbClient = new MongoClient(doc['connection_string'], {
        serverApi: ServerApiVersion.v1
      })

      return [doc['_id'].toString(), mongodbClient]
    })
  }

  async getGPhotosClients(): Promise<[string, GPhotosClient][]> {
    const docs = await this._client
      .db('sharded_google_photos')
      .collection('gphotos_clients')
      .find()
      .toArray()

    return docs.map((doc) => {
      const creds: GPhotosCredentials = {
        token: doc['token'],
        refreshToken: doc['refresh_token'],
        clientId: doc['client_id'],
        clientSecret: doc['client_secret']
      }

      const gphotosClient = new GPhotosClient(doc['name'], creds)
      return [doc['_id'].toString(), gphotosClient]
    })
  }

  async getRootAlbumId(): Promise<AlbumId> {
    const doc = await this._client
      .db('sharded_google_photos')
      .collection('root_album')
      .findOne()

    if (doc === null) {
      throw new Error('No root album found!')
    }

    return {
      clientId: (doc['client_id'] as ObjectId).toString(),
      objectId: (doc['object_id'] as ObjectId).toString()
    }
  }
}
