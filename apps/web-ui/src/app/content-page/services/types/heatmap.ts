export interface GetMapTileHeatmapRequest {
  x: number;
  y: number;
  z: number;
  albumId: string | undefined;
}

/** Represents an entry to the heat map.  */
export interface HeatmapEntry {
  cellId: string;
  count: number;
  latitude: number;
  longitude: number;
}

/** Represents a heat map. */
export interface Heatmap {
  entries: HeatmapEntry[];
}

export type GetMapTileHeatmapResponse = Heatmap;
