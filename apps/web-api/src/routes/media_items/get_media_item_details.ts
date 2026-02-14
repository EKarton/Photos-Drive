import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import { z } from 'zod';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import { MongoDbClientNotFoundError } from '../../services/core/databases/MongoDbClientsStore';
import {
  MediaItemNotFoundError,
  MediaItemsStore
} from '../../services/core/media_items/BaseMediaItemsStore';
import { MediaItemId } from '../../services/core/media_items/MediaItems';
import { serializeMediaItem } from './utils';
import { rateLimitKey } from '../../utils/rateLimitKey';

const getMediaItemDetailsParamsSchema = z.object({
  id: z.string().includes(':')
});

export default async function (mediaItemsRepo: MediaItemsStore) {
  const router: Router = Router();

  router.get(
    '/api/v1/media-items/:id',
    await verifyAuthentication(),
    await verifyAuthorization(),
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100,
      keyGenerator: rateLimitKey
    }),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const params = getMediaItemDetailsParamsSchema.safeParse(req.params);

      if (!params.success) {
        return res.status(400).json({ error: 'Invalid media item ID format' });
      }

      const rawMediaItemId = params.data.id;
      const rawMediaItemIdParts = rawMediaItemId.split(':');
      const mediaItemId: MediaItemId = {
        clientId: rawMediaItemIdParts[0],
        objectId: rawMediaItemIdParts[1]
      };

      try {
        const mediaItem = await mediaItemsRepo.getMediaItemById(mediaItemId, {
          abortController: req.abortController
        });
        return res.status(200).json(serializeMediaItem(mediaItem));
      } catch (error) {
        const isNotFound =
          error instanceof MongoDbClientNotFoundError ||
          error instanceof MediaItemNotFoundError;

        if (isNotFound) {
          return res.status(404).json({
            error: 'Media item not found'
          });
        }

        throw error;
      }
    })
  );

  return router;
}
