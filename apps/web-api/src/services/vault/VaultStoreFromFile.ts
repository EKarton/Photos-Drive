/* eslint-disable security/detect-non-literal-fs-filename */
/* eslint-disable security/detect-object-injection */

import * as fs from 'fs'
import * as ini from 'ini'
import { MongoClient, ServerApiVersion } from 'mongodb'
import { GPhotosClient, GPhotosCredentials } from '../blob_store/GPhotosClient'
import { AlbumId } from '../metadata_store/Albums'
import {
  GPhotosConfig,
  MongoDbConfig,
  UpdateGPhotosConfigRequest,
  Vault
} from './VaultStore'

/** The config type */
type INIParseResult = Record<string, Record<string, string | number | boolean>>

/** Implementation of {@code Vault} read from a file. */
export class VaultStoreFromFile implements Vault {
  private _config: INIParseResult

  constructor(configFilePath: string) {
    this._config = ini.parse(fs.readFileSync(configFilePath, 'utf-8'))
  }

  getMongoDbConfigs(): Promise<MongoDbConfig[]> {
    const configs: MongoDbConfig[] = []

    for (const sectionId in this._config) {
      if (this._config[sectionId]['type'] !== 'mongodb_config') {
        continue
      }

      const rawConfigs = this._config[sectionId]

      const config: MongoDbConfig = {
        id: rawConfigs['id'] as string,
        connectionString: rawConfigs['read_only_connection_string'] as string
      }

      configs.push(config)
    }

    return new Promise((resolve, _) => resolve(configs))
  }

  getGPhotosConfigs(): Promise<GPhotosConfig[]> {
    const configs: GPhotosConfig[] = []

    for (const sectionId in this._config) {
      if (this._config[sectionId].type !== 'gphotos_config') {
        continue
      }

      const section = this._config[sectionId]

      const creds: GPhotosCredentials = {
        token: section['read_write_credentials_token'] as string,
        refreshToken: section['read_write_credentials_refresh_token'] as string,
        tokenUri: section['read_write_credentials_token_uri'] as string,
        clientId: section['read_write_credentials_client_id'] as string,
        clientSecret: section['read_write_credentials_client_secret'] as string
      }
      const config: GPhotosConfig = {
        id: sectionId,
        credentials: creds
      }

      configs.push(config)
    }

    return new Promise((resolve, _) => resolve(configs))
  }

  updateGPhotosConfig(request: UpdateGPhotosConfigRequest): Promise<void> {
    throw new Error('Method not implemented.')
  }

  getMongoDbClients(): Promise<[string, MongoClient][]> {
    const results: [string, MongoClient][] = []

    for (const sectionId in this._config) {
      if (this._config[sectionId].type !== 'mongodb') {
        continue
      }

      const mongodbClient = new MongoClient(
        this._config[sectionId]['connection_string'] as string,
        { serverApi: ServerApiVersion.v1 }
      )

      results.push([sectionId.trim(), mongodbClient])
    }

    return new Promise((resolve, _) => resolve(results))
  }

  getGPhotosClients(): Promise<[string, GPhotosClient][]> {
    const results: [string, GPhotosClient][] = []
    for (const sectionId in this._config) {
      if (this._config[sectionId].type !== 'gphotos') {
        continue
      }

      const creds: GPhotosCredentials = {
        token: this._config[sectionId]['token'] as string,
        refreshToken: this._config[sectionId]['refresh_token'] as string,
        tokenUri: '',
        clientId: this._config[sectionId]['client_id'] as string,
        clientSecret: this._config[sectionId]['client_secret'] as string
      }

      const gphotosClient = new GPhotosClient(
        this._config[sectionId]['name'] as string,
        creds
      )
      results.push([sectionId.trim(), gphotosClient])
    }

    return new Promise((resolve, _) => resolve(results))
  }

  async getRootAlbumId(): Promise<AlbumId> {
    for (const sectionId in this._config) {
      if (this._config[sectionId].type !== 'root_album') {
        continue
      }

      const data: AlbumId = {
        clientId: (this._config[sectionId]['client_id'] as string).trim(),
        objectId: (this._config[sectionId]['object_id'] as string).trim()
      }

      return new Promise((resolve, _) => resolve(data))
    }

    return new Promise((_, reject) =>
      reject(new Error('Cannot find root album'))
    )
  }
}
