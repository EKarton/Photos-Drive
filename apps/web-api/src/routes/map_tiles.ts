import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import { verifyAuthentication } from '../middlewares/authentication';
import { verifyAuthorization } from '../middlewares/authorization';
import {
  AlbumId,
  convertStringToAlbumId
} from '../services/metadata_store/Albums';
import { mediaIdToString } from '../services/metadata_store/MediaItems';
import { TilesRepository } from '../services/tiles_store/TilesRepository';

export default async function (
  rootAlbumId: AlbumId,
  tilesRepo: TilesRepository
) {
  const router: Router = Router();
  router.get(
    '/api/v1/map-tiles',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      const inputAlbumId = req.query['albumId'] as string;
      const inputTileX = Number(req.query['x']);
      const inputTileY = Number(req.query['y']);
      const inputTileZ = Number(req.query['z']);

      let albumId: AlbumId | undefined = undefined;
      if (inputAlbumId === 'root') {
        albumId = rootAlbumId;
      } else if (inputAlbumId) {
        albumId = convertStringToAlbumId(inputAlbumId);
      }

      if (isNaN(inputTileX) || isNaN(inputTileY) || isNaN(inputTileZ)) {
        return res.status(400).json({ error: 'Bad request for tile id' });
      }

      const [mediaItemIds, numMediaItems] = await Promise.all([
        tilesRepo.getMediaItems(
          {
            x: inputTileX,
            y: inputTileY,
            z: inputTileZ
          },
          albumId,
          1
        ),
        tilesRepo.getNumMediaItems(
          {
            x: inputTileX,
            y: inputTileY,
            z: inputTileZ
          },
          albumId
        )
      ]);

      return res.status(200).json({
        mediaItemId:
          numMediaItems > 0 ? mediaIdToString(mediaItemIds[0]) : undefined,
        numMediaItems: numMediaItems
      });
    })
  );

  return router;
}
