import { AlbumId } from '../metadata_store/Albums';
import { MediaItemId } from '../metadata_store/MediaItems';

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
