import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import { convertStringToAlbumId } from '../../services/core/albums/Albums';
import {
  MediaItemsStore,
  SampleMediaItemsRequest
} from '../../services/core/media_items/BaseMediaItemsStore';
import { serializeMediaItem } from './utils';

export default async function (mediaItemsRepo: MediaItemsStore) {
  const router: Router = Router();

  router.get(
    '/api/v1/media-items/sample',
    await verifyAuthentication(),
    await verifyAuthorization(),
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100
    }),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const albumId = req.query['albumId'] as string;
      const pageSize = Number(req.query['pageSize']);
      const earliestDateTaken = req.query['earliest'] as string;
      const latestDateTaken = req.query['latest'] as string;
      const latitudeRange = Number(req.query['latitude']);
      const longitudeRange = Number(req.query['longitude']);
      const locationRange = Number(req.query['range']);

      const sampleMediaItemsRequest: SampleMediaItemsRequest = {
        albumId: albumId ? convertStringToAlbumId(albumId) : undefined,
        earliestDateTaken: earliestDateTaken
          ? new Date(earliestDateTaken)
          : undefined,
        latestDateTaken: latestDateTaken
          ? new Date(latestDateTaken)
          : undefined,
        withinLocation:
          !isNaN(latitudeRange) &&
          !isNaN(longitudeRange) &&
          !isNaN(locationRange)
            ? {
                latitude: latitudeRange,
                longitude: longitudeRange,
                range: locationRange
              }
            : undefined,
        pageSize: !isNaN(pageSize) ? Math.min(50, Math.max(0, pageSize)) : 25
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
