import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import { z } from 'zod';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import { convertStringToAlbumId } from '../../services/core/albums/Albums';
import {
  MediaItemsStore,
  SampleMediaItemsRequest
} from '../../services/core/media_items/BaseMediaItemsStore';
import { serializeMediaItem } from './utils';
import { rateLimitKey } from '../../utils/rateLimitKey';

const sampleMediaItemsQuerySchema = z.object({
  albumId: z.string().optional(),
  pageSize: z.coerce.number().min(0).max(50).default(25),
  earliest: z.iso.datetime().optional(),
  latest: z.iso.datetime().optional(),
  latitude: z.coerce.number().optional(),
  longitude: z.coerce.number().optional(),
  range: z.coerce.number().optional()
});

export default async function (mediaItemsRepo: MediaItemsStore) {
  const router: Router = Router();

  router.get(
    '/api/v1/media-items/sample',
    await verifyAuthentication(),
    await verifyAuthorization(),
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100,
      keyGenerator: rateLimitKey
    }),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const query = sampleMediaItemsQuerySchema.safeParse(req.query);

      if (!query.success) {
        return res.status(400).json({ error: 'Invalid query parameters' });
      }

      const {
        albumId,
        pageSize,
        earliest,
        latest,
        latitude,
        longitude,
        range
      } = query.data;

      const sampleMediaItemsRequest: SampleMediaItemsRequest = {
        albumId: albumId ? convertStringToAlbumId(albumId) : undefined,
        earliestDateTaken: earliest ? new Date(earliest) : undefined,
        latestDateTaken: latest ? new Date(latest) : undefined,
        withinLocation:
          latitude !== undefined &&
            longitude !== undefined &&
            range !== undefined
            ? {
              latitude,
              longitude,
              range
            }
            : undefined,
        pageSize
      };
      const response = await mediaItemsRepo.sampleMediaItems(
        sampleMediaItemsRequest,
        { abortController: req.abortController }
      );

      return res.status(200).json({
        mediaItems: response.mediaItems.map(serializeMediaItem)
      });
    })
  );

  return router;
}
