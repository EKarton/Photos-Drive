/* eslint-disable security/detect-non-literal-fs-filename */
/* eslint-disable security/detect-object-injection */

import * as fs from 'fs'
import * as ini from 'ini'
import { MongoClient, ServerApiVersion } from 'mongodb'
import { GPhotosClient, GPhotosCredentials } from '../blob_store/GPhotosClient'
import { AlbumId } from '../metadata_store/Albums'
import { Vault } from './VaultStore'

/** What the config file should look like */
interface Config {
  [key: string]: ConfigSection
}

/** A section in the config */
interface ConfigSection {
  type: string
  connection_string?: string
  token?: string
  refresh_token?: string
  client_id?: string
  client_secret?: string
  name?: string
  object_id?: string
}

/** Implementation of {@code Vault}. */
export class VaultStoreFromFile implements Vault {
  private _config: Config

  constructor(configFilePath: string) {
    this._config = ini.parse(fs.readFileSync(configFilePath, 'utf-8'))
  }

  getMongoDbClients(): Promise<[string, MongoClient][]> {
    const results: [string, MongoClient][] = []

    for (const sectionId in this._config) {
      if (this._config[sectionId].type !== 'mongodb') {
        continue
      }

      const mongodbClient = new MongoClient(
        this._config[sectionId].connection_string!,
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
        accessToken: this._config[sectionId].token!,
        refreshToken: this._config[sectionId].refresh_token!,
        clientId: this._config[sectionId].client_id!,
        clientSecret: this._config[sectionId].client_secret!
      }

      const gphotosClient = new GPhotosClient(
        this._config[sectionId].name!,
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
        clientId: this._config[sectionId].client_id!.trim(),
        objectId: this._config[sectionId].object_id!.trim()
      }

      return new Promise((resolve, _) => resolve(data))
    }

    return new Promise((_, reject) =>
      reject(new Error('Cannot find root album'))
    )
  }
}
