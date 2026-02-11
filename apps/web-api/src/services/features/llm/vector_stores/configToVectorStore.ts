import { MongoClient } from 'mongodb';
import {
  MongoDbVectorStoreConfig,
  VectorStoreConfig
} from '../config/ConfigStore';
import { BaseVectorStore } from './BaseVectorStore';
import { MongoDbVectorStore } from './MongoDbVectorStore';

export function configToVectorStore(
  config: VectorStoreConfig
): BaseVectorStore {
  if (isMongoDbVectorStoreConfig(config)) {
    return configToMongoDbVectorStore(config);
  } else {
    throw new Error(`${config} not supported yet`);
  }
}

function configToMongoDbVectorStore(
  config: MongoDbVectorStoreConfig
): MongoDbVectorStore {
  return new MongoDbVectorStore(
    config.id,
    new MongoClient(config.connectionString),
    'photos_drive',
    'media_item_embeddings'
  );
}

// Type guard to check if config is MongoDbVectorStoreConfig
function isMongoDbVectorStoreConfig(
  config: VectorStoreConfig
): config is MongoDbVectorStoreConfig {
  return (config as MongoDbVectorStoreConfig).connectionString !== undefined;
}
