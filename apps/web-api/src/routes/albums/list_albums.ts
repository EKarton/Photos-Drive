import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import {
  AlbumId,
  convertStringToAlbumId
} from '../../services/metadata_store/Albums';
import {
  AlbumsStore,
  ListAlbumsRequest,
  SortByDirection,
  SortByField
} from '../../services/metadata_store/AlbumsStore';
import { MediaItemsStore } from '../../services/metadata_store/MediaItemsStore';
import parseEnumOrElse from '../../utils/parseEnumOrElse';
import { serializeAlbum } from './utils';

export default async function (
  rootAlbumId: AlbumId,
  albumsRepo: AlbumsStore,
  mediaItemsRepo: MediaItemsStore
) {
  const router: Router = Router();

  router.get(
    '/api/v1/albums',
    await verifyAuthentication(),
    await verifyAuthorization(),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const pageSize = Number(req.query['pageSize']);
      const pageToken = req.query['pageToken'] as string;
      const sortBy = req.query['sortBy'];
      const sortDir = req.query['sortDir'];
      const rawParentAlbumId = req.query['parentAlbumId'] as string;

      let parentAlbumId: AlbumId | undefined = undefined;
      if (rawParentAlbumId) {
        if (rawParentAlbumId === 'root') {
          parentAlbumId = rootAlbumId;
        } else {
          parentAlbumId = convertStringToAlbumId(rawParentAlbumId);
        }
      }

      const listAlbumsRequest: ListAlbumsRequest = {
        parentAlbumId,
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
      const response = await albumsRepo.listAlbums(listAlbumsRequest, {
        abortController: req.abortController
      });

      const [mediaItemCounts, childAlbumCounts] = await Promise.all([
        Promise.all(
          response.albums.map((album) =>
            mediaItemsRepo.getNumMediaItemsInAlbum(album.id)
          )
        ),
        Promise.all(
          response.albums.map((album) =>
            albumsRepo.getNumAlbumsInAlbum(album.id)
          )
        )
      ]);

      return res.status(200).json({
        albums: response.albums.map((album, i) =>
          serializeAlbum(album, childAlbumCounts.at(i)!, mediaItemCounts.at(i)!)
        ),
        nextPageToken: response.nextPageToken
          ? encodeURIComponent(response.nextPageToken)
          : undefined
      });
    })
  );

  return router;
}
