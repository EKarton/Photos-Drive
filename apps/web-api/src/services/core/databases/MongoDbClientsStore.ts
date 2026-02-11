import { MongoClient, ServerApiVersion } from 'mongodb';
import { ConfigStore } from '../config/ConfigStore';

/** Represents a repository of all MongoDB clients. */
export interface MongoDbClientsStore {
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
export class MongoDbClientsStoreImpl implements MongoDbClientsStore {
  private idToClient = new Map<string, MongoClient>();

  static async buildFromVault(
    vault: ConfigStore
  ): Promise<MongoDbClientsStoreImpl> {
    const repo = new MongoDbClientsStoreImpl();

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

/** In-memory implementation of MongoDbClientsRepository for testing. */
export class InMemoryMongoDbClientsRepository implements MongoDbClientsStore {
  private clients: Map<string, MongoClient>;

  constructor(initialClients?: [string, MongoClient][]) {
    this.clients = new Map(initialClients);
  }

  getClientFromId(clientId: string): MongoClient {
    const client = this.clients.get(clientId);
    if (!client) {
      throw new MongoDbClientNotFoundError(clientId);
    }
    return client;
  }

  listClients(): [string, MongoClient][] {
    return Array.from(this.clients.entries());
  }

  /** Adds or replaces a client in memory. */
  setClient(clientId: string, client: MongoClient): void {
    this.clients.set(clientId, client);
  }

  /** Removes a client. Useful for testing. */
  deleteClient(clientId: string): void {
    this.clients.delete(clientId);
  }

  /** Clears all clients (for test cleanup). */
  clear(): void {
    this.clients.clear();
  }
}

/** A class that represents when no MongoDB client could be found. */
export class MongoDbClientNotFoundError extends Error {
  constructor(id: string) {
    super(`Cannot find MongoDB client with id ${id}`);
    this.name = 'MongoDbClientNotFoundError';
  }
}
