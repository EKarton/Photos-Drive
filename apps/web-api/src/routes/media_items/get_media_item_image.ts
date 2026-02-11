import { wrap } from 'async-middleware';
import axios from 'axios';
import { Request, Response, Router } from 'express';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../../services/blob_store/gphotos/GPhotosClientsRepository';
import { MediaItemId } from '../../services/metadata_store/MediaItems';
import { MediaItemsStore } from '../../services/metadata_store/MediaItemsStore';

export default async function (
  mediaItemsRepo: MediaItemsStore,
  gPhotoClientRepo: GPhotosClientsRepository
) {
  const router: Router = Router();

  router.get(
    '/api/v1/media-items/:id/image',
    await verifyAuthentication(),
    await verifyAuthorization(),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const rawMediaItemId = req.params.id;
      const rawMediaItemIdParts = rawMediaItemId.split(':');
      const mediaItemId: MediaItemId = {
        clientId: rawMediaItemIdParts[0],
        objectId: rawMediaItemIdParts[1]
      };
      const { width, height } = req.query as {
        width?: string;
        height?: string;
      };

      try {
        const mediaItem = await mediaItemsRepo.getMediaItemById(mediaItemId, {
          abortController: req.abortController
        });
        const client = gPhotoClientRepo.getGPhotosClientById(
          mediaItem.gphotos_client_id
        );
        const gPhotosMediaItem = await client.getMediaItem(
          mediaItem.gphotos_media_item_id
        );

        if (!gPhotosMediaItem.baseUrl) {
          return res.status(404).json({
            error: 'Media item not found'
          });
        }

        if (width && height) {
          return res.redirect(
            `${gPhotosMediaItem.baseUrl}=w${width}-h${height}`
          );
        }

        return res.redirect(gPhotosMediaItem.baseUrl);
      } catch (error) {
        if (error instanceof NoGPhotosClientFoundError) {
          return res.status(404).json({
            error: 'No GPhotos client found'
          });
        } else if (axios.isAxiosError(error)) {
          const errorCode = error.response?.status ?? 500;
          const errorMessage = error.response?.data;

          return res.status(errorCode).json({
            error: errorMessage
          });
        } else {
          return res.status(500).json({
            error: (error as Error)?.message
          });
        }
      }
    })
  );

  return router;
}
