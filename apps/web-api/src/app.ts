import compression from 'compression'
import cookieParser from 'cookie-parser'
import cors from 'cors'
import express, { Application, NextFunction, Request, Response } from 'express'
import helmet from 'helmet'
import { MongoClient } from 'mongodb'
import expressLogger from 'pino-http'
import { Config, getConfig } from './config'
import albumsRouter from './routes/albums'
import authRouter from './routes/authentication'
import gphotoClientsRouter from './routes/gphoto_clients'
import healthRouter from './routes/health'
import mediaItemsRouter from './routes/media_items'
import { GPhotosClientsRepository } from './services/blob_store/GPhotosClientsRepository'
import {
  AlbumsRepository,
  AlbumsRepositoryImpl
} from './services/metadata_store/AlbumsRepository'
import {
  MediaItemsRepository,
  MediaItemsRepositoryImpl
} from './services/metadata_store/MediaItemsRepository'
import {
  MongoDbClientsRepository,
  MongoDbClientsRepositoryImpl
} from './services/metadata_store/MongoDbClientsRepository'
import { Vault } from './services/vault/VaultStore'
import { VaultStoreFromFile } from './services/vault/VaultStoreFromFile'
import { VaultStoreFromMongoDb } from './services/vault/VaultStoreFromMongoDb'
import logger from './utils/logger'

export class App {
  private app: Application
  private appConfig: Config

  private config?: Vault
  private mongoDbClientsRepository?: MongoDbClientsRepository
  private gPhotosClientsRepository?: GPhotosClientsRepository
  private albumsRepository?: AlbumsRepository
  private mediaItemsRepository?: MediaItemsRepository

  constructor() {
    this.app = express()
    this.appConfig = getConfig()
  }

  async run() {
    if (this.appConfig.vaultFilePath) {
      this.config = new VaultStoreFromFile(this.appConfig.vaultFilePath)
    } else if (this.appConfig.vaultMongoDb) {
      this.config = new VaultStoreFromMongoDb(
        new MongoClient(this.appConfig.vaultMongoDb)
      )
    } else {
      throw new Error(
        'Vault file path or vault mongo db env var needs to be set!'
      )
    }

    this.mongoDbClientsRepository =
      await MongoDbClientsRepositoryImpl.buildFromVault(this.config)
    this.gPhotosClientsRepository =
      await GPhotosClientsRepository.buildFromVault(this.config)
    this.albumsRepository = new AlbumsRepositoryImpl(
      this.mongoDbClientsRepository
    )
    this.mediaItemsRepository = new MediaItemsRepositoryImpl(
      this.mongoDbClientsRepository
    )

    this.app.use(compression())
    this.app.use(helmet())
    this.app.use(cookieParser())
    this.app.use(expressLogger())
    this.app.use(
      cors({
        origin: this.appConfig.frontendEndpoint,
        optionsSuccessStatus: 200,
        credentials: true,
      })
    )

    this.app.use(healthRouter())
    this.app.use(await authRouter())
    this.app.use(
      await albumsRouter(
        await this.config.getRootAlbumId(),
        this.albumsRepository
      )
    )
    this.app.use(await mediaItemsRouter(this.mediaItemsRepository))
    this.app.use(await gphotoClientsRouter(this.gPhotosClientsRepository))

    this.app.use(
      (err: Error, _req: Request, res: Response, _next: NextFunction) => {
        console.error(err.stack)
        res.status(500).send({ error: err.message })
      }
    )

    this.app.listen(this.appConfig.serverPort, () =>
      logger.info(`Server running on Port ${this.appConfig.serverPort}`)
    )
  }

  async shutdown() {
    const clients = await this.mongoDbClientsRepository?.listClients()
    clients?.forEach(([_, client]) => client.close())
  }
}
