import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import { verifyAuthentication } from '../middlewares/authentication';
import { verifyAuthorization } from '../middlewares/authorization';
import {
  AlbumId,
  albumIdToString,
  convertStringToAlbumId
} from '../services/metadata_store/Albums';
import {
  AlbumNotFoundError,
  AlbumsRepository
} from '../services/metadata_store/AlbumsRepository';
import { mediaIdToString } from '../services/metadata_store/MediaItems';
import {
  MediaItemsRepository,
  SortByDirection,
  SortByField
} from '../services/metadata_store/MediaItemsRepository';
import { MongoDbClientNotFoundError } from '../services/metadata_store/MongoDbClientsRepository';

export default async function (
  rootAlbumId: AlbumId,
  albumsRepo: AlbumsRepository,
  mediaItemsRepo: MediaItemsRepository
) {
  const router: Router = Router();

  router.get(
    '/api/v1/albums/root',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (_, res: Response) => {
      const rawAlbumId = `${rootAlbumId.clientId}:${rootAlbumId.objectId}`;
      return res.redirect(`/api/v1/albums/${rawAlbumId}`);
    })
  );

  router.get(
    '/api/v1/albums/:albumId',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      try {
        const albumId = convertStringToAlbumId(req.params.albumId);
        const [album, mediaItems] = await Promise.all([
          albumsRepo.getAlbumById(albumId),
          mediaItemsRepo.getMediaItemsInAlbum(albumId)
        ]);

        const response = {
          id: `${album.id.clientId}:${album.id.objectId}`,
          albumName: album.name,
          parentAlbumId: album.parent_album_id
            ? albumIdToString(album.parent_album_id)
            : null,
          childAlbumIds: album.child_album_ids.map((id) => albumIdToString(id)),
          mediaItemIds: mediaItems.map((mediaItem) =>
            mediaIdToString(mediaItem.id)
          )
        };
        return res.status(200).json(response);
      } catch (error) {
        if (error instanceof MongoDbClientNotFoundError) {
          return res.status(404).json({ error: 'Album not found' });
        }
        if (error instanceof AlbumNotFoundError) {
          return res.status(404).json({ error: 'Album not found' });
        }

        throw error;
      }
    })
  );

  router.get(
    '/api/v1/albums/:albumId/media-items',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      const albumId = req.params.albumId;
      const pageSize = Number(req.query['pageSize']);
      const pageToken = req.query['pageToken'] as string;
      const sortBy = req.query['sortBy'];
      const sortDir = req.query['sortDir'];

      try {
        const response = await mediaItemsRepo.listMediaItemsInAlbum({
          albumId: convertStringToAlbumId(albumId),
          pageSize: !isNaN(pageSize) ? pageSize : 25,
          pageToken,
          sortBy:
            sortBy && sortDir
              ? {
                  field: SortByField.ID,
                  direction:
                    sortDir === 'asc'
                      ? SortByDirection.ASCENDING
                      : SortByDirection.DESCENDING
                }
              : undefined
        });
        return res.status(200).json(response);
      } catch (error) {
        if (error instanceof MongoDbClientNotFoundError) {
          return res.status(404).json({ error: 'Album not found' });
        }
        if (error instanceof AlbumNotFoundError) {
          return res.status(404).json({ error: 'Album not found' });
        }

        throw error;
      }
    })
  );

  return router;
}
