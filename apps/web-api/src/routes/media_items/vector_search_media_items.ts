import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import {
  convertStringToMediaItemId,
  mediaIdToString,
  MediaItemId
} from '../../services/metadata_store/MediaItems';
import { MediaItemsStore } from '../../services/metadata_store/MediaItemsStore';
import { BaseVectorStore } from '../../services/vector_stores/BaseVectorStore';
import logger from '../../utils/logger';
import { serializeMediaItem } from './utils';

export default async function (
  mediaItemsRepo: MediaItemsStore,
  vectorStore: BaseVectorStore
) {
  const router: Router = Router();

  router.post(
    '/api/v1/media-items/vector-search',
    await verifyAuthentication(),
    await verifyAuthorization(),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const {
        queryEmbedding,
        earliestDateTaken,
        latestDateTaken,
        withinMediaItemIds,
        topK
      }: {
        queryEmbedding?: number[];
        earliestDateTaken?: string;
        latestDateTaken?: string;
        withinMediaItemIds?: string[];
        topK?: number;
      } = req.body;

      if (!queryEmbedding) {
        return res
          .status(400)
          .json({ error: 'Missing or invalid "queryEmbedding" field' });
      }

      // Convert dates to Date objects if provided
      let earliestDateObj: Date | undefined;
      if (earliestDateTaken) {
        earliestDateObj = new Date(earliestDateTaken);
        if (isNaN(earliestDateObj.getTime())) {
          return res
            .status(400)
            .json({ error: 'Invalid earliestDateTaken format' });
        }
      }

      let latestDateObj: Date | undefined;
      if (latestDateTaken) {
        latestDateObj = new Date(latestDateTaken);
        if (isNaN(latestDateObj.getTime())) {
          return res
            .status(400)
            .json({ error: 'Invalid latestDateTaken format' });
        }
      }

      let mediaItemIdObjects: MediaItemId[] = [];
      if (withinMediaItemIds && Array.isArray(withinMediaItemIds)) {
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
