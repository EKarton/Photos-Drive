import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
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
  MediaItemsRepository,
  SortByDirection,
  SortByField
} from '../services/metadata_store/MediaItemsRepository';
import { MongoDbClientNotFoundError } from '../services/metadata_store/mongodb/MongoDbClientsRepository';
import { ImageEmbedder } from '../services/ml/models/ImageEmbeddings';
import { BaseVectorStore } from '../services/ml/vector_stores/BaseVectorStore';
import parseEnumOrElse from '../utils/parseEnumOrElse';

export default async function (
  mediaItemsRepo: MediaItemsRepository,
  vectorStore: BaseVectorStore,
  imageEmbedder: ImageEmbedder
) {
  const router: Router = Router();

  router.get(
    '/api/v1/media-items',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      const albumId = req.query['albumId'] as string;
      const pageSize = Number(req.query['pageSize']);
      const pageToken = req.query['pageToken'] as string;
      const sortBy = req.query['sortBy'];
      const sortDir = req.query['sortDir'];

      const abortController = new AbortController();
      req.on('close', () => abortController.abort());

      const listMediaItemsRequest: ListMediaItemsRequest = {
        albumId: albumId ? convertStringToAlbumId(albumId) : undefined,
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
        { abortController }
      );

      return res.status(200).json({
        mediaItems: response.mediaItems.map(serializeMediaItem),
        nextPageToken: response.nextPageToken
          ? encodeURIComponent(response.nextPageToken)
          : undefined
      });
    })
  );

  router.post(
    '/api/v1/media-items/search',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      const {
        query,
        earliestDateTaken,
        latestDateTaken,
        withinMediaItemIds,
        topK
      }: {
        query: string;
        earliestDateTaken?: string;
        latestDateTaken?: string;
        withinMediaItemIds?: string[];
        topK?: number;
      } = req.body;

      if (!query || typeof query !== 'string') {
        return res
          .status(400)
          .json({ error: 'Missing or invalid "query" field' });
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

      // Convert withinMediaItemIds strings to MediaItemId objects, if needed
      let mediaItemIdObjects: MediaItemId[] = [];
      if (withinMediaItemIds && Array.isArray(withinMediaItemIds)) {
        mediaItemIdObjects = withinMediaItemIds.map((idStr) =>
          convertStringToMediaItemId(idStr)
        );
      }

      const abortController = new AbortController();
      req.on('close', () => abortController.abort());

      let start = performance.now();
      const embedding = await imageEmbedder.embedText(query);
      console.log(
        `Execution time to embedText: ${performance.now() - start} milliseconds`
      );

      start = performance.now();
      const searchResult = await vectorStore.getReleventMediaItemEmbeddings(
        {
          embedding: embedding,
          startDateTaken: earliestDateObj,
          endDateTaken: latestDateObj,
          withinMediaItemIds: mediaItemIdObjects,
          topK: topK ?? 10
        },
        { abortController }
      );
      console.log(
        `Execution time to getReleventMediaItemEmbeddings: ${performance.now() - start} milliseconds`
      );

      start = performance.now();
      const mediaItems = await mediaItemsRepo.bulkGetMediaItemByIds(
        searchResult.map((result) => result.mediaItemId)
      );
      console.log(
        `Execution time to getMediaItemByIds: ${performance.now() - start} milliseconds`
      );

      // Serialize media items for response
      return res.status(200).json({
        mediaItems: mediaItems.map(serializeMediaItem)
      });
    })
  );

  router.get(
    '/api/v1/media-items/:id',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      const rawMediaItemId = req.params.id;
      const rawMediaItemIdParts = rawMediaItemId.split(':');
      const mediaItemId: MediaItemId = {
        clientId: rawMediaItemIdParts[0],
        objectId: rawMediaItemIdParts[1]
      };

      try {
        const abortController = new AbortController();
        req.on('close', () => abortController.abort());

        const mediaItem = await mediaItemsRepo.getMediaItemById(mediaItemId, {
          abortController
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
