import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import { verifyAuthentication } from '../middlewares/authentication';
import { verifyAuthorization } from '../middlewares/authorization';
import {
  HeatmapGenerator,
  Tile
} from '../services/maps_store/HeatmapGenerator';
import {
  AlbumId,
  convertStringToAlbumId
} from '../services/metadata_store/Albums';

export default async function (
  rootAlbumId: AlbumId,
  heatmapGenerator: HeatmapGenerator
) {
  const router: Router = Router();
  router.get(
    '/api/v1/maps/heatmap',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      const inputAlbumId = req.query['albumId'] as string;
      const tile: Tile = {
        x: Number(req.query['x']),
        y: Number(req.query['y']),
        z: Number(req.query['z'])
      };

      let albumId: AlbumId | undefined = undefined;
      if (inputAlbumId === 'root') {
        albumId = rootAlbumId;
      } else if (inputAlbumId) {
        albumId = convertStringToAlbumId(inputAlbumId);
      }

      if (isNaN(tile.x) || isNaN(tile.y) || isNaN(tile.z)) {
        return res.status(400).json({
          error: `Bad request for tile id ${tile}`
        });
      }

      const heatmap = await heatmapGenerator.getHeatmapForTile(tile, albumId);
      return res.status(200).json(heatmap);
    })
  );

  return router;
}
