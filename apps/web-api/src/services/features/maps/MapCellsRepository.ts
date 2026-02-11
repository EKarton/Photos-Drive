import { AlbumId } from '../../core/albums/Albums';
import { MediaItemId } from '../../core/media_items/MediaItems';

export type CellId = string;

/**
 * A class that represents a heatmap cell.
 */
export interface HeatmapPoints {
  cellId: CellId;
  count: number;
  sampledMediaItemId: MediaItemId;
}

/** A class that fetches thee map cells from the database. */
export interface MapCellsRepository {
  getHeatmapPointsInCells(
    cellIds: CellId[],
    albumId: AlbumId | undefined,
    options?: { abortController?: AbortController }
  ): Promise<HeatmapPoints[]>;
}
