import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import z from 'zod';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import {
  AlbumId,
  convertStringToAlbumId
} from '../../services/core/albums/Albums';
import {
  AlbumsStore,
  ListAlbumsRequest,
  SortByDirection,
  SortByField
} from '../../services/core/albums/BaseAlbumsStore';
import { MediaItemsStore } from '../../services/core/media_items/BaseMediaItemsStore';
import parseEnumOrElse from '../../utils/parseEnumOrElse';
import { rateLimitKey } from '../../utils/rateLimitKey';
import { serializeAlbum } from './utils';

const listAlbumsQuerySchema = z.object({
  pageSize: z.coerce.number().min(0).max(50).default(25),
  pageToken: z.string().optional(),
  sortBy: z.enum(SortByField).optional(),
  sortDir: z.enum(SortByDirection).optional(),
  parentAlbumId: z
    .union([z.literal('root'), z.string().includes(':')])
    .optional()
});

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
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100,
      keyGenerator: rateLimitKey
    }),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const query = listAlbumsQuerySchema.safeParse(req.query);

      if (!query.success) {
        return res.status(400).json({ error: 'Invalid query parameters' });
      }

      const {
        pageSize,
        pageToken,
        sortBy,
        sortDir,
        parentAlbumId: rawParentAlbumId
      } = query.data;

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
        pageSize,
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
