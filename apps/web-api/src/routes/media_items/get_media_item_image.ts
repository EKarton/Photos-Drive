import { wrap } from 'async-middleware';
import axios from 'axios';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import { z } from 'zod';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import { MediaItemsStore } from '../../services/core/media_items/BaseMediaItemsStore';
import { MediaItemId } from '../../services/core/media_items/MediaItems';
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../../services/core/storage/gphotos/GPhotosClientsRepository';
import { rateLimitKey } from '../../utils/rateLimitKey';

const getMediaItemImageParamsSchema = z.object({
  id: z.string().includes(':')
});

const getMediaItemImageQuerySchema = z.object({
  width: z.coerce.number().optional(),
  height: z.coerce.number().optional()
});

export default async function (
  mediaItemsRepo: MediaItemsStore,
  gPhotoClientRepo: GPhotosClientsRepository
) {
  const router: Router = Router();

  router.get(
    '/api/v1/media-items/:id/image',
    await verifyAuthentication(),
    await verifyAuthorization(),
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100,
      keyGenerator: rateLimitKey
    }),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const params = getMediaItemImageParamsSchema.safeParse(req.params);
      const query = getMediaItemImageQuerySchema.safeParse(req.query);

      if (!params.success || !query.success) {
        return res.status(400).json({ error: 'Invalid request' });
      }

      const rawMediaItemId = params.data.id;
      const rawMediaItemIdParts = rawMediaItemId.split(':');
      const mediaItemId: MediaItemId = {
        clientId: rawMediaItemIdParts[0],
        objectId: rawMediaItemIdParts[1]
      };
      const { width, height } = query.data;

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
