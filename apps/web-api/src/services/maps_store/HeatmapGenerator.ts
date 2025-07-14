import { performance } from 'perf_hooks';
import * as tilebelt from '@mapbox/tilebelt';
import { cellToLatLng, polygonToCells } from 'h3-js';
import { AlbumId } from '../metadata_store/Albums';
import { CellId, MapCellsRepository } from './MapCellsRepository';

/** Represents an entry to the heat map.  */
export interface HeatmapEntry {
  cellId: CellId;
  count: number;
  latitude: number;
  longitude: number;
}

/** Represents a heat map. */
export interface Heatmap {
  entries: HeatmapEntry[];
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
    albumId: AlbumId | undefined
  ): Promise<Heatmap> {
    const start = performance.now();

    const bbox = tilebelt.tileToBBOX([tile.x, tile.y, tile.z]);
    const polygon = [
      [bbox[0], bbox[1]], // SW: [minLon, minLat]
      [bbox[2], bbox[1]], // SE: [maxLon, minLat]
      [bbox[2], bbox[3]], // NE: [maxLon, maxLat]
      [bbox[0], bbox[3]], // NW: [minLon, maxLat]
      [bbox[0], bbox[1]] // Close polygon
    ];
    const h3Res = mapboxZoomToH3Resolution(tile.z);
    const cellIds = polygonToCells([polygon], h3Res, true);

    const cellToCountsMap: Map<CellId, number> =
      await this.mapCellRepository.getNumMediaItemsInCells(cellIds, albumId);

    const heatmapData = Array.from(cellToCountsMap)
      .filter(([_, count]) => count > 0)
      .map(([cellId, count]) => {
        const [latitude, longitude] = cellToLatLng(cellId);
        return { cellId, count, latitude, longitude };
      });

    console.log(
      `getHeatmapForTile for ${tile} took ${performance.now() - start} ms`
    );

    return {
      entries: heatmapData.filter((entry) => entry !== undefined)
    };
  }
}

function mapboxZoomToH3Resolution(zoom: number): number {
  if (zoom < 4) {
    return 2;
  } else if (zoom < 5) {
    return 3;
  } else if (zoom < 6) {
    return 4;
  } else if (zoom < 7) {
    return 5;
  } else if (zoom < 8) {
    return 6;
  } else if (zoom < 9) {
    return 7;
  } else if (zoom < 10) {
    return 8;
  } else if (zoom < 11) {
    return 9;
  } else if (zoom < 12) {
    return 10;
  } else if (zoom < 13) {
    return 11;
  } else if (zoom < 14) {
    return 12;
  } else if (zoom < 15) {
    return 13;
  } else if (zoom < 16) {
    return 14;
  } else {
    return 15;
  }
}
