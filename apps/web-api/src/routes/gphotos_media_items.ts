import { wrap } from 'async-middleware';
import axios from 'axios';
import { Router } from 'express';
import { verifyAuthentication } from '../middlewares/authentication';
import { verifyAuthorization } from '../middlewares/authorization';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../services/core/storage/gphotos/GPhotosClientsRepository';

export default async function (gPhotoClientRepo: GPhotosClientsRepository) {
  const router: Router = Router();

  router.get(
    '/api/v1/gphotos/media-items/:gMediaItemId',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req, res) => {
      const rawGMediaItemIdParts = req.params.gMediaItemId.split(':');
      const gPhotosClientId = rawGMediaItemIdParts[0];
      const gPhotosMediaItemId = rawGMediaItemIdParts[1];

      try {
        const client = gPhotoClientRepo.getGPhotosClientById(gPhotosClientId);
        const mediaItem = await client.getMediaItem(gPhotosMediaItemId);

        return res.status(200).json({
          baseUrl: mediaItem.baseUrl,
          mimeType: mediaItem.mimeType,
          mediaMetadata: mediaItem.mediaMetadata
        });
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
