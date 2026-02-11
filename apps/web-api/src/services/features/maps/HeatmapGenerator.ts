import * as tilebelt from '@mapbox/tilebelt';
import { cellToLatLng, polygonToCells } from 'h3-js';
import { AlbumId } from '../metadata_store/Albums';
import { MediaItemId } from '../metadata_store/MediaItems';
import { CellId, MapCellsRepository } from './MapCellsRepository';

/** Represents an entry to the heat map.  */
export interface HeatmapPoint {
  cellId: CellId;
  count: number;
  latitude: number;
  longitude: number;
  sampledMediaItemId: MediaItemId;
}

/** Represents a heat map. */
export interface Heatmap {
  points: HeatmapPoint[];
}

/** Represents a tile on the map. */
export interface Tile {
  x: number;
  y: number;
  z: number;
}

export class HeatmapGenerator {
  private mapCellRepository: MapCellsRepository;

  constructor(mapCellRepository: MapCellsRepository) {
    this.mapCellRepository = mapCellRepository;
  }

  async getHeatmapForTile(
    tile: Tile,
    albumId: AlbumId | undefined,
    options?: { abortController?: AbortController }
  ): Promise<Heatmap> {
    const bbox = tilebelt.tileToBBOX([tile.x, tile.y, tile.z]);
    const polygon = [
      [bbox[0], bbox[1]], // SW: [minLon, minLat]
      [bbox[2], bbox[1]], // SE: [maxLon, minLat]
      [bbox[2], bbox[3]], // NE: [maxLon, maxLat]
      [bbox[0], bbox[3]], // NW: [minLon, maxLat]
      [bbox[0], bbox[1]] // Close polygon
    ];
    const h3Res = tileZoomToH3Resolution(tile.z);
    const cellIds = polygonToCells([polygon], h3Res, true);

    const heatmapCells = await this.mapCellRepository.getHeatmapPointsInCells(
      cellIds,
      albumId,
      options
    );

    return {
      points: heatmapCells
        .filter((heatmapCell) => heatmapCell.count > 0)
        .map((heatmapCell) => {
          const [latitude, longitude] = cellToLatLng(heatmapCell.cellId);
          return {
            cellId: heatmapCell.cellId,
            count: heatmapCell.count,
            latitude,
            longitude,
            sampledMediaItemId: heatmapCell.sampledMediaItemId
          };
        })
    };
  }
}

function tileZoomToH3Resolution(zoom: number): number {
  return Math.max(1, Math.min(15, zoom - 1));
  // return Math.min(15, Math.max(1, Math.floor(zoom / 1.5)));
}
