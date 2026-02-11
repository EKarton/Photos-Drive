import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import { addRequestAbortController } from '../../middlewares/abort-controller';
import { verifyAuthentication } from '../../middlewares/authentication';
import { verifyAuthorization } from '../../middlewares/authorization';
import {
  HeatmapGenerator,
  Tile
} from '../../services/maps_store/HeatmapGenerator';
import {
  AlbumId,
  convertStringToAlbumId
} from '../../services/metadata_store/Albums';
import { mediaIdToString } from '../../services/metadata_store/MediaItems';

export default async function (
  rootAlbumId: AlbumId,
  heatmapGenerator: HeatmapGenerator
) {
  const router: Router = Router();

  router.get(
    '/api/v1/maps/heatmap',
    await verifyAuthentication(),
    await verifyAuthorization(),
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100
    }),
    addRequestAbortController(),
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
          error: `Bad request for tile id x=${tile.x}, y=${tile.y}, z=${tile.z}`
        });
      }

      const heatmap = await heatmapGenerator.getHeatmapForTile(tile, albumId, {
        abortController: req.abortController
      });

      return res.status(200).json({
        points: heatmap.points.map((point) => ({
          count: point.count,
          latitude: point.latitude,
          longitude: point.longitude,
          sampledMediaItemId: mediaIdToString(point.sampledMediaItemId)
        }))
      });
    })
  );

  return router;
}
