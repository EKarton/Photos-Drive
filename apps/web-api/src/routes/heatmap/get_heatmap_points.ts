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
import { mediaIdToString } from '../../services/core/media_items/MediaItems';
import {
  HeatmapGenerator,
  Tile
} from '../../services/features/maps/HeatmapGenerator';
import { rateLimitKey } from '../../utils/rateLimitKey';

const getHeatmapPointsQuerySchema = z.object({
  x: z.coerce.number(),
  y: z.coerce.number(),
  z: z.coerce.number(),
  albumId: z.union([z.literal('root'), z.string().includes(':')]).optional()
});

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
      max: 100,
      keyGenerator: rateLimitKey
    }),
    addRequestAbortController(),
    wrap(async (req: Request, res: Response) => {
      const query = getHeatmapPointsQuerySchema.safeParse(req.query);

      if (!query.success) {
        return res.status(400).json({ error: 'Invalid request' });
      }

      const { x, y, z, albumId: inputAlbumId } = query.data;
      const tile: Tile = { x, y, z };

      let albumId: AlbumId | undefined = undefined;
      if (inputAlbumId === 'root') {
        albumId = rootAlbumId;
      } else if (inputAlbumId) {
        albumId = convertStringToAlbumId(inputAlbumId);
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
