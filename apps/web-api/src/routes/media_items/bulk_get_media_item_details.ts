import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import { MediaItemsStore } from '../../services/core/media_items/BaseMediaItemsStore';
import { convertStringToMediaItemId } from '../../services/core/media_items/MediaItems';
import { serializeMediaItem } from './utils';

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
      const mediaItemIds: string[] = req.body['mediaItemIds'] as string[];

      if (mediaItemIds.length > 50) {
        return res.status(413).json({
          error: 'Too many media item IDs to fetch (needs to be under 50)'
        });
      }

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
