import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import { z } from 'zod';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import { MediaItemsStore } from '../../services/core/media_items/BaseMediaItemsStore';
import {
  convertStringToMediaItemId,
  mediaIdToString,
  MediaItemId
} from '../../services/core/media_items/MediaItems';
import { BaseVectorStore } from '../../services/features/llm/vector_stores/BaseVectorStore';
import logger from '../../utils/logger';
import { serializeMediaItem } from './utils';

const vectorSearchMediaItemsBodySchema = z.object({
  queryEmbedding: z.array(z.number()),
  earliestDateTaken: z.iso.datetime().optional(),
  latestDateTaken: z.iso.datetime().optional(),
  withinMediaItemIds: z.array(z.string()).optional(),
  topK: z.number().optional()
});

export default async function (
  mediaItemsRepo: MediaItemsStore,
  vectorStore: BaseVectorStore
) {
  const router: Router = Router();

  router.post(
    '/api/v1/media-items/vector-search',
    await verifyAuthentication(),
    await verifyAuthorization(),
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100
    }),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const body = vectorSearchMediaItemsBodySchema.safeParse(req.body);

      if (!body.success) {
        return res
          .status(400)
          .json({ error: 'Invalid request' });
      }

      const {
        queryEmbedding,
        earliestDateTaken,
        latestDateTaken,
        withinMediaItemIds,
        topK
      } = body.data;

      // Convert dates to Date objects if provided
      let earliestDateObj: Date | undefined;
      if (earliestDateTaken) {
        earliestDateObj = new Date(earliestDateTaken);
      }

      let latestDateObj: Date | undefined;
      if (latestDateTaken) {
        latestDateObj = new Date(latestDateTaken);
      }

      let mediaItemIdObjects: MediaItemId[] = [];
      if (withinMediaItemIds) {
        mediaItemIdObjects = withinMediaItemIds.map((idStr) =>
          convertStringToMediaItemId(idStr)
        );
      }

      const searchResult = await vectorStore.getReleventMediaItemEmbeddings(
        {
          embedding: new Float32Array(queryEmbedding),
          startDateTaken: earliestDateObj,
          endDateTaken: latestDateObj,
          withinMediaItemIds: mediaItemIdObjects,
          topK: topK ?? 10
        },
        { abortController: req.abortController }
      );

      logger.info(`Found ${searchResult.length} results`);

      const mediaItems = await mediaItemsRepo.bulkGetMediaItemByIds(
        searchResult.map((result) => result.mediaItemId),
        { abortController: req.abortController }
      );

      logger.info(`Got ${mediaItems.length} details`);

      // Create a map from mediaItemId to mediaItem for lookup
      const mediaItemMap = new Map(
        mediaItems.map((item) => [mediaIdToString(item.id), item])
      );

      const orderedMediaItems = searchResult
        .map((result) => mediaItemMap.get(mediaIdToString(result.mediaItemId)))
        .filter((mediaItem) => mediaItem !== undefined);

      return res.status(200).json({
        mediaItems: orderedMediaItems.map(serializeMediaItem)
      });
    })
  );

  return router;
}
