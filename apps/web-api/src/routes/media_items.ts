import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import { addRequestAbortController } from '../middlewares/abort-controller';
import { verifyAuthentication } from '../middlewares/authentication';
import { verifyAuthorization } from '../middlewares/authorization';
import {
  albumIdToString,
  convertStringToAlbumId
} from '../services/metadata_store/Albums';
import {
  convertStringToMediaItemId,
  mediaIdToString,
  MediaItem,
  MediaItemId
} from '../services/metadata_store/MediaItems';
import {
  ListMediaItemsRequest,
  MediaItemNotFoundError,
  MediaItemsStore,
  SortByDirection,
  SortByField
} from '../services/metadata_store/MediaItemsStore';
import { MongoDbClientNotFoundError } from '../services/metadata_store/mongodb/MongoDbClientsStore';
import { BaseVectorStore } from '../services/vector_stores/BaseVectorStore';
import logger from '../utils/logger';
import parseEnumOrElse from '../utils/parseEnumOrElse';

export default async function (
  mediaItemsRepo: MediaItemsStore,
  vectorStore: BaseVectorStore
) {
  const router: Router = Router();

  router.get(
    '/api/v1/media-items/search',
    await verifyAuthentication(),
    await verifyAuthorization(),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const albumId = req.query['albumId'] as string;
      const pageSize = Number(req.query['pageSize']);
      const pageToken = req.query['pageToken'] as string;
      const sortBy = req.query['sortBy'];
      const sortDir = req.query['sortDir'];
      const earliestDateTaken = req.query['earliest'] as string;
      const latestDateTaken = req.query['latest'] as string;
      const latitudeRange = Number(req.query['latitude']);
      const longitudeRange = Number(req.query['longitude']);
      const locationRange = Number(req.query['range']);

      const listMediaItemsRequest: ListMediaItemsRequest = {
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
        pageSize: !isNaN(pageSize) ? Math.min(50, Math.max(0, pageSize)) : 25,
        pageToken: pageToken ? decodeURIComponent(pageToken) : undefined,
        sortBy: {
          field: parseEnumOrElse(SortByField, sortBy, SortByField.ID),
          direction: parseEnumOrElse(
            SortByDirection,
            sortDir,
            SortByDirection.ASCENDING
          )
        }
      };
      const response = await mediaItemsRepo.listMediaItems(
        listMediaItemsRequest,
        { abortController: req.abortController }
      );

      return res.status(200).json({
        mediaItems: response.mediaItems.map(serializeMediaItem),
        nextPageToken: response.nextPageToken
          ? encodeURIComponent(response.nextPageToken)
          : undefined
      });
    })
  );

  router.get(
    '/api/v1/media-items/:id',
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

  router.post(
    '/api/v1/media-items/bulk-get',
    await verifyAuthentication(),
    await verifyAuthorization(),
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

function serializeMediaItem(mediaItem: MediaItem): object {
  return {
    id: mediaIdToString(mediaItem.id),
    fileName: mediaItem.file_name,
    location: mediaItem.location,
    gPhotosMediaItemId: `${mediaItem.gphotos_client_id}:${mediaItem.gphotos_media_item_id}`,
    albumId: albumIdToString(mediaItem.album_id),
    width: mediaItem.width,
    height: mediaItem.height,
    dateTaken: mediaItem.date_taken.toISOString()
  };
}
