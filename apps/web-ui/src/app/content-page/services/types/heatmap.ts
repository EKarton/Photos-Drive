export interface GetHeatmapRequest {
  x: number;
  y: number;
  z: number;
  albumId?: string | undefined;
}

/** Represents an entry to the heat map.  */
export interface HeatmapPoints {
  count: number;
  latitude: number;
  longitude: number;
  sampledMediaItemId: string;
}

/** Represents a heat map. */
export interface Heatmap {
  points: HeatmapPoints[];
}

export type GetHeatmapResponse = Heatmap;
