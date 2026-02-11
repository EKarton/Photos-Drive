import compression from 'compression';
import cors from 'cors';
import express, { Application, NextFunction, Request, Response } from 'express';
import helmet from 'helmet';
import { MongoClient } from 'mongodb';
import expressLogger from 'pino-http';
import { AppConfig, getAppConfig } from './app_config';
import albumsRouter from './routes/albums';
import authRouter from './routes/authentication';
import gPhotosMediaItemsRouter from './routes/gphotos_media_items';
import healthRouter from './routes/health';
import mapsRouter from './routes/heatmap';
import mediaItemsRouter from './routes/media_items';
import { AlbumsStore } from './services/core/albums/BaseAlbumsStore';
import { DistributedAlbumsStore } from './services/core/albums/DistributedAlbumsStore';
import { MongoDbAlbumsStore } from './services/core/albums/MongoDbAlbumsStore';
import { ConfigStore } from './services/core/config/ConfigStore';
import { ConfigStoreFromFile } from './services/core/config/ConfigStoreFromFile';
import { ConfigStoreFromMongoDb } from './services/core/config/ConfigStoreFromMongoDb';
import {
  MongoDbClientsStore,
  MongoDbClientsStoreImpl
} from './services/core/databases/MongoDbClientsStore';
import { MediaItemsStore } from './services/core/media_items/BaseMediaItemsStore';
import { DistributedMediaItemsStore } from './services/core/media_items/DistributedMediaItemsStore';
import { MongoDbMediaItemsStore } from './services/core/media_items/MongoDbMediaItemsStore';
import { GPhotosClientsRepository } from './services/core/storage/gphotos/GPhotosClientsRepository';
import { configToVectorStore } from './services/features/llm/vector_stores/configToVectorStore';
import { DistributedVectorStore } from './services/features/llm/vector_stores/DistributedVectorStore';
import { HeatmapGenerator } from './services/features/maps/HeatmapGenerator';
import { MapCellsRepository } from './services/features/maps/MapCellsRepository';
import { MapCellsRepositoryImpl } from './services/features/maps/mongodb/MapCellsRepositoryImpl';
import logger from './utils/logger';

export class App {
  private app: Application;
  private appConfig: AppConfig;

  private config?: ConfigStore;
  private mongoDbClientsRepository?: MongoDbClientsStore;
  private gPhotosClientsRepository?: GPhotosClientsRepository;
  private albumsStore?: AlbumsStore;
  private mediaItemsStore?: MediaItemsStore;
  private mapCellsRepository?: MapCellsRepository;
  private heatmapGenerator?: HeatmapGenerator;
  private vectorStore?: DistributedVectorStore;

  constructor() {
    this.app = express();
    this.appConfig = getAppConfig();
  }

  async run() {
    if (this.appConfig.vaultFilePath) {
      this.config = new ConfigStoreFromFile(this.appConfig.vaultFilePath);
    } else if (this.appConfig.vaultMongoDb) {
      this.config = new ConfigStoreFromMongoDb(
        new MongoClient(this.appConfig.vaultMongoDb)
      );
    } else {
      throw new Error(
        'Vault file path or vault mongo db env var needs to be set!'
      );
    }

    this.mongoDbClientsRepository =
      await MongoDbClientsStoreImpl.buildFromVault(this.config);
    this.gPhotosClientsRepository =
      await GPhotosClientsRepository.buildFromVault(this.config);

    this.albumsStore = new DistributedAlbumsStore(
      this.mongoDbClientsRepository
        .listClients()
        .map(
          ([clientId, mongoClient]) =>
            new MongoDbAlbumsStore(clientId, mongoClient)
        )
    );

    this.mediaItemsStore = new DistributedMediaItemsStore(
      this.mongoDbClientsRepository
        .listClients()
        .map(
          ([clientId, mongoClient]) =>
            new MongoDbMediaItemsStore(clientId, mongoClient)
        )
    );
    this.mapCellsRepository = new MapCellsRepositoryImpl(
      this.mongoDbClientsRepository
    );
    this.heatmapGenerator = new HeatmapGenerator(this.mapCellsRepository);

    this.vectorStore = new DistributedVectorStore(
      (await this.config.getVectorStoreConfigs()).map((config) =>
        configToVectorStore(config)
      )
    );

    const rootAlbumId = await this.config.getRootAlbumId();

    this.app.use(helmet());
    this.app.use(compression());
    this.app.use(express.json());
    this.app.use(expressLogger());
    this.app.use(
      cors({
        origin: this.appConfig.corsFrontendEndpoint,
        optionsSuccessStatus: 200
      })
    );

    this.app.use(healthRouter());
    this.app.use(await authRouter());
    this.app.use(
      await albumsRouter(rootAlbumId, this.albumsStore, this.mediaItemsStore)
    );
    this.app.use(
      await mediaItemsRouter(
        this.mediaItemsStore,
        this.gPhotosClientsRepository,
        this.vectorStore
      )
    );
    this.app.use(await gPhotosMediaItemsRouter(this.gPhotosClientsRepository));
    this.app.use(await mapsRouter(rootAlbumId, this.heatmapGenerator));

    this.app.use(
      (err: Error, _req: Request, res: Response, _next: NextFunction) => {
        console.error(err.stack);
        res.status(500).send({ error: err.message });
      }
    );

    this.app.listen(this.appConfig.serverPort, () =>
      logger.info(`Server running on Port ${this.appConfig.serverPort}`)
    );
  }

  async shutdown() {
    const clients = await this.mongoDbClientsRepository?.listClients();
    clients?.forEach(([_, client]) => client.close());
  }
}
