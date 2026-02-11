import { Router } from 'express';
import { HeatmapGenerator } from '../../services/maps_store/HeatmapGenerator';
import { AlbumId } from '../../services/metadata_store/Albums';
import getHeatmapPoints from './get_heatmap_points';

export default async function (
  rootAlbumId: AlbumId,
  heatmapGenerator: HeatmapGenerator
) {
  const router: Router = Router();

  router.use(await getHeatmapPoints(rootAlbumId, heatmapGenerator));

  return router;
}
