import { MongoClient, ServerApiVersion } from 'mongodb';
import { Vault } from '../vault/VaultStore';

/** Represents a repository of all MongoDB clients. */
export interface MongoDbClientsRepository {
  /**
   * Returns the MongoDB client from its ID.
   * @param clientId The MongoDB client ID.
   * @throws MongoDbClientNotFoundError when it cannot find the MongoDB client.
   * @returns The MongoDB client.
   */
  getClientFromId(clientId: string): MongoClient;

  /**
   * Returns a list of MongoDB clients with their IDs.
   * @returns A list of tuples, where each tuple contains the ID and the MongoDB client.
   */
  listClients(): [string, MongoClient][];
}

/** Implementation class of {@code MongoDbClientsRepository} */
export class MongoDbClientsRepositoryImpl implements MongoDbClientsRepository {
  private idToClient = new Map<string, MongoClient>();

  static async buildFromVault(
    vault: Vault
  ): Promise<MongoDbClientsRepositoryImpl> {
    const repo = new MongoDbClientsRepositoryImpl();

    const configs = await vault.getMongoDbConfigs();
    configs.forEach((config) => {
      const mongodbClient = new MongoClient(config.connectionString, {
        serverApi: ServerApiVersion.v1
      });

      repo.idToClient.set(config.id, mongodbClient);
    });

    return repo;
  }

  getClientFromId(clientId: string): MongoClient {
    if (!this.idToClient.has(clientId)) {
      throw new MongoDbClientNotFoundError(clientId);
    }

    return this.idToClient.get(clientId)!;
  }

  listClients(): [string, MongoClient][] {
    const results: [string, MongoClient][] = [];

    for (const [id, client] of this.idToClient) {
      results.push([id, client]);
    }

    return results;
  }
}

/** A class that represents when no MongoDB client could be found. */
export class MongoDbClientNotFoundError extends Error {
  constructor(id: string) {
    super(`Cannot find MongoDB client with id ${id}`);
    this.name = 'MongoDbClientNotFoundError';
  }
}
