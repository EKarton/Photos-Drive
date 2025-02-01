import { wrap } from 'async-middleware';
import { Router } from 'express';
import { verifyAuthentication } from '../middlewares/authentication';
import { verifyAuthorization } from '../middlewares/authorization';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../services/blob_store/GPhotosClientsRepository';

export default async function (gphotoClientRepo: GPhotosClientsRepository) {
  const router: Router = Router();

  router.get(
    '/api/v1/gphotos-clients',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (_req, res) => {
      const results = gphotoClientRepo.getGPhotosClients();
      const response = {
        gphotoClients: results.map(([id, client]) => ({
          id: id,
          token: client.getCredentials().token
        }))
      };

      return res.status(200).json(response);
    })
  );

  router.post(
    '/api/v1/gphotos-clients/:id/token-refresh',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req, res) => {
      const gphotosClientId = req.params.id;

      try {
        const client = gphotoClientRepo.getGPhotosClientById(gphotosClientId);
        await client.refreshCredentials();
        return res.status(200).json({
          newToken: client.getCredentials().token
        });
      } catch (error) {
        if (error instanceof NoGPhotosClientFoundError) {
          return res.status(404).json({
            error: 'No GPhotos client found'
          });
        }

        throw error;
      }
    })
  );

  return router;
}
