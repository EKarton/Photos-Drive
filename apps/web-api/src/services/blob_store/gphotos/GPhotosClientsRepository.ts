import logger from '../../../utils/logger';
import { ConfigStore } from '../../config/ConfigStore';
import { GPhotosClient } from './GPhotosClient';

/** Stores all of the GPhotoClients in the repository. */
export class GPhotosClientsRepository {
  private idToClient = new Map<string, GPhotosClient>();

  /**
   * Builds the {@code GPhotosClientsRepository} from a config file.
   * @param vault The config.
   * @returns An instance of {@code GPhotosClientsRepository}.
   */
  static async buildFromVault(vault: ConfigStore): Promise<GPhotosClientsRepository> {
    const repo = new GPhotosClientsRepository();

    const configs = await vault.getGPhotosConfigs();
    configs.forEach((config) => {
      const gPhotosClient = new GPhotosClient(config.name, config.credentials);

      gPhotosClient.setRefreshCredentialsListener({
        beforeRefresh: () => {
          return Promise.resolve();
        },

        afterRefresh: (err?: Error) => {
          if (!err) {
            vault.updateGPhotosConfig({
              id: config.id,
              newCredentials: gPhotosClient.getCredentials()
            });
            return Promise.resolve();
          } else {
            logger.error(`Failed to update gphotos config ${err}`);
            return Promise.reject(err);
          }
        }
      });

      repo.idToClient.set(config.id, gPhotosClient);
    });

    return repo;
  }

  /**
   * Gets the {@code GPhotosClient} by its id.
   * @param id The ID of the GPhotosClient
   * @throws {@code NoGPhotosClientFoundError} if no client is found with that id.
   * @returns {@code GPhotosClient} the client.
   */
  getGPhotosClientById(id: string): GPhotosClient {
    if (!this.idToClient.has(id)) {
      throw new NoGPhotosClientFoundError(id);
    }

    return this.idToClient.get(id)!;
  }

  /**
   * Returns all GPhotoClients with their IDs.
   * @returns a list of all GPhotoClients with their IDs.
   */
  getGPhotosClients(): [string, GPhotosClient][] {
    const results: [string, GPhotosClient][] = [];

    for (const [id, client] of this.idToClient) {
      results.push([id, client]);
    }

    return results;
  }
}

/** Represents an error for when no GPhotosClient is found. */
export class NoGPhotosClientFoundError extends Error {
  constructor(id: string) {
    super(`No google photos client found with id ${id}`);
  }
}
