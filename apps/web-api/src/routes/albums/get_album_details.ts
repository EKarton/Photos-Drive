import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import z from 'zod';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import {
  AlbumId,
  convertStringToAlbumId
} from '../../services/core/albums/Albums';
import {
  AlbumNotFoundError,
  AlbumsStore
} from '../../services/core/albums/BaseAlbumsStore';
import { MongoDbClientNotFoundError } from '../../services/core/databases/MongoDbClientsStore';
import { MediaItemsStore } from '../../services/core/media_items/BaseMediaItemsStore';
import { serializeAlbum } from './utils';
import rateLimit from 'express-rate-limit';
import { rateLimitKey } from '../../utils/rateLimitKey';

const getAlbumDetailsParamsSchema = z.object({
  albumId: z.union([z.literal('root'), z.string().includes(':')])
});

export default async function (
  rootAlbumId: AlbumId,
  albumsRepo: AlbumsStore,
  mediaItemsRepo: MediaItemsStore
) {
  const router: Router = Router();

  router.get(
    '/api/v1/albums/:albumId',
    await verifyAuthentication(),
    await verifyAuthorization(),
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100,
      keyGenerator: rateLimitKey
    }),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      try {
        const params = getAlbumDetailsParamsSchema.safeParse(req.params);

        if (!params.success) {
          return res.status(400).json({ error: 'Invalid request' });
        }

        const inputAlbumId = params.data.albumId;

        let albumId: AlbumId;
        if (inputAlbumId === 'root') {
          albumId = rootAlbumId;
        } else {
          albumId = convertStringToAlbumId(inputAlbumId);
        }

        const [album, numChildAlbums, numMediaItems] = await Promise.all([
          albumsRepo.getAlbumById(albumId, {
            abortController: req.abortController
          }),
          albumsRepo.getNumAlbumsInAlbum(albumId, {
            abortController: req.abortController
          }),
          mediaItemsRepo.getNumMediaItemsInAlbum(albumId, {
            abortController: req.abortController
          })
        ]);

        return res
          .status(200)
          .json(serializeAlbum(album, numChildAlbums, numMediaItems));
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
