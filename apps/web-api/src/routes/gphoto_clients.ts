import { wrap } from 'async-middleware';
import axios from 'axios';
import { Router } from 'express';
import { verifyAuthentication } from '../middlewares/authentication';
import { verifyAuthorization } from '../middlewares/authorization';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../services/blob_store/GPhotosClientsRepository';

export default async function (gPhotoClientRepo: GPhotosClientsRepository) {
  const router: Router = Router();

  router.get(
    '/api/v1/gphotos-clients',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (_req, res) => {
      const results = gPhotoClientRepo.getGPhotosClients();
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
        const client = gPhotoClientRepo.getGPhotosClientById(gphotosClientId);
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

  router.get(
    '/api/v1/gphotos/:clientId/media-items/:mediaItemId',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req, res) => {
      const gPhotosClientId = req.params.clientId;
      const gPhotosMediaItemId = req.params.mediaItemId;

      try {
        const client = gPhotoClientRepo.getGPhotosClientById(gPhotosClientId);
        const mediaItem = await client.getMediaItem(gPhotosMediaItemId);

        return res.status(200).json(mediaItem);
      } catch (err) {
        if (err instanceof NoGPhotosClientFoundError) {
          return res.status(404).json({
            error: 'No GPhotos client found'
          });
        } else if (axios.isAxiosError(err)) {
          const errorCode = err.response?.status ?? 500;
          const errorMessage = err.response?.data;

          return res.status(errorCode).json({
            error: errorMessage
          });
        } else {
          return res.status(500).json({
            error: (err as Error)?.message
          });
        }
      }
    })
  );

  return router;
}
