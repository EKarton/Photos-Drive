import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import { verifyAuthentication } from '../middlewares/authentication';
import { verifyAuthorization } from '../middlewares/authorization';
import {
  albumIdToString,
  convertStringToAlbumId
} from '../services/metadata_store/Albums';
import {
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
import parseEnumOrElse from '../utils/parseEnumOrElse';

export default async function (mediaItemsRepo: MediaItemsRepository) {
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

  router.get(
    '/api/v1/media-items/:id',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req, res) => {
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
