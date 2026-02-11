import { Router } from 'express';
import { AlbumId } from '../../services/core/albums/Albums';
import { HeatmapGenerator } from '../../services/features/maps/HeatmapGenerator';
import getHeatmapPoints from './get_heatmap_points';

export default async function (
  rootAlbumId: AlbumId,
  heatmapGenerator: HeatmapGenerator
) {
  const router: Router = Router();

  router.use(await getHeatmapPoints(rootAlbumId, heatmapGenerator));

  return router;
}
