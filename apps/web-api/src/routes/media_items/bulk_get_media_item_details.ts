import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import { z } from 'zod';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import { MediaItemsStore } from '../../services/core/media_items/BaseMediaItemsStore';
import { convertStringToMediaItemId } from '../../services/core/media_items/MediaItems';
import { serializeMediaItem } from './utils';

const bulkGetMediaItemDetailsBodySchema = z.object({
  mediaItemIds: z.array(z.string()).max(50)
});

export default async function (mediaItemsRepo: MediaItemsStore) {
  const router: Router = Router();

  router.post(
    '/api/v1/media-items/bulk-get',
    await verifyAuthentication(),
    await verifyAuthorization(),
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100
    }),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const body = bulkGetMediaItemDetailsBodySchema.safeParse(req.body);

      if (!body.success) {
        return res.status(400).json({
          error:
            'Invalid request body, mediaItemIds must be string array with at most 50 items'
        });
      }

      const mediaItemIds = body.data.mediaItemIds;

      const mediaItems = await mediaItemsRepo.bulkGetMediaItemByIds(
        mediaItemIds.map(convertStringToMediaItemId),
        { abortController: req.abortController }
      );

      return res.status(200).json({
        mediaItems: mediaItems.map(serializeMediaItem)
      });
    })
  );

  return router;
}
