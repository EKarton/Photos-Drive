import {
  Component,
  ComponentRef,
  effect,
  ElementRef,
  inject,
  input,
  OnDestroy,
  OnInit,
  output,
  ViewChild,
  ViewContainerRef,
} from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import * as tilebelt from '@mapbox/tilebelt';
import { Store } from '@ngrx/store';
import range from 'lodash/range';
import * as mapboxgl from 'mapbox-gl';
import { filter, map, shareReplay, Subscription, take } from 'rxjs';

import { MAPBOX_FACTORY_TOKEN } from '../../../../../app.tokens';
import { authState } from '../../../../../auth/store';
import { MediaItem } from '../../../../services/types/media-item';
import { mediaViewerActions } from '../../../../store/media-viewer';
import { ImageMapMarkerComponent } from './image-map-marker/image-map-marker.component';

export interface Tile {
  tileId: TileId;
  chosenMediaItem?: MediaItem;
  numMediaItems: number;
}

export interface TileId {
  x: number;
  y: number;
  z: number;
}

const TARGET_TILES_TO_DISPLAY = 50;

@Component({
  selector: 'app-images-map-viewer',
  templateUrl: './images-map-viewer.component.html',
  styleUrls: ['./images-map-viewer.component.scss'],
  standalone: true,
})
export class ImagesMapViewerComponent implements OnInit, OnDestroy {
  readonly tiles = input<Tile[]>([]);
  readonly isDarkMode = input.required<boolean>();

  readonly visibleTilesChanged = output<TileId[]>();

  private readonly tiles$ = toObservable(this.tiles).pipe(shareReplay(1));

  private readonly subscriptions = new Subscription();

  @ViewChild('mapContainer', { static: true }) mapContainer!: ElementRef;
  private readonly viewContainerRef = inject(ViewContainerRef);
  private readonly store = inject(Store);
  private readonly mapboxFactory = inject(MAPBOX_FACTORY_TOKEN);
  private readonly mapboxApiToken = this.store.selectSignal(
    authState.selectMapboxApiToken,
  );

  private map!: mapboxgl.Map;
  private imageMarkers: mapboxgl.Marker[] = [];

  constructor() {
    effect(() => {
      if (this.map) {
        this.map.setStyle(getTheme(this.isDarkMode()));

        // Re-add heatmap layer and markers after style reload
        this.map.once('styledata', () => {
          this.updateImageMarkers();
          this.updateTileGridLayer();
        });
      }
    });
  }

  ngOnInit() {
    this.map = this.mapboxFactory.buildMap({
      accessToken: this.mapboxApiToken(),
      container: this.mapContainer.nativeElement,
      style: getTheme(this.isDarkMode()),
      center: [0, 0],
      zoom: 10,
    });

    // Center the map to the first item in tiles$
    this.subscriptions.add(
      this.tiles$
        .pipe(
          map((tiles) => tiles[0]?.chosenMediaItem),
          filter(Boolean),
          take(1),
        )
        .subscribe((mediaItem) => {
          this.map.setCenter([
            mediaItem.location!.longitude,
            mediaItem.location!.latitude,
          ]);
        }),
    );

    // Set the map layers whenever it has finished loading
    this.map.on('load', () => {
      this.updateImageMarkers();
      this.updateTileGridLayer();
      this.emitVisibleTiles();

      this.subscriptions.add(
        this.tiles$.subscribe(() => {
          this.updateImageMarkers();
          this.updateTileGridLayer();
        }),
      );
    });

    // Update the map whenever the map has moved
    this.map.on('moveend', () => {
      this.updateImageMarkers();
      this.updateTileGridLayer();
      this.emitVisibleTiles();
    });
  }

  private emitVisibleTiles() {
    const bounds = this.map.getBounds();
    if (!bounds) {
      return;
    }

    const zoom = this.findBestZoomLevel(
      TARGET_TILES_TO_DISPLAY,
      Math.floor(this.map.getZoom()),
      bounds,
    );
    const visibleTiles = this.getVisibleTiles(zoom, bounds);

    this.visibleTilesChanged.emit(visibleTiles);
  }

  private updateImageMarkers() {
    // Remove old markers
    this.imageMarkers.forEach((marker) => marker.remove());
    this.imageMarkers = [];

    for (const tile of this.tiles()) {
      if (tile.numMediaItems === 0 || !tile.chosenMediaItem) {
        continue;
      }

      let componentRef: ComponentRef<ImageMapMarkerComponent>;

      if (tile.numMediaItems > 1) {
        componentRef = this.viewContainerRef.createComponent(
          ImageMapMarkerComponent,
        );
        componentRef.setInput('mediaItem', tile.chosenMediaItem!);
        componentRef.setInput('badgeCount', tile.numMediaItems);

        const location = tile.chosenMediaItem!.location!;
        this.subscriptions.add(
          componentRef.instance.markerClick.subscribe(() => {
            this.map.easeTo({
              center: [location.longitude, location.latitude],
              zoom: tile.tileId.z + 1,
            });
          }),
        );
      } else {
        componentRef = this.viewContainerRef.createComponent(
          ImageMapMarkerComponent,
        );
        componentRef.setInput('mediaItem', tile.chosenMediaItem);

        this.subscriptions.add(
          componentRef.instance.markerClick.subscribe(() => {
            this.store.dispatch(
              mediaViewerActions.openMediaViewer({
                request: { mediaItemId: tile.chosenMediaItem!.id },
              }),
            );
          }),
        );
      }

      if (componentRef && tile.chosenMediaItem.location) {
        const marker = this.mapboxFactory
          .buildMarker(componentRef)
          .setLngLat([
            tile.chosenMediaItem.location.longitude,
            tile.chosenMediaItem.location.latitude,
          ])
          .addTo(this.map);

        this.imageMarkers.push(marker);
      }
    }
  }

  private updateTileGridLayer() {
    const sourceId = 'tile-grid';
    const bounds = this.map.getBounds();
    if (!bounds) {
      return;
    }

    const zoom = this.findBestZoomLevel(
      TARGET_TILES_TO_DISPLAY,
      Math.floor(this.map.getZoom()),
      bounds,
    );

    const tileSource: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: this.getVisibleTiles(zoom, bounds).map((tile) => ({
        type: 'Feature',
        geometry: tilebelt.tileToGeoJSON([tile.x, tile.y, tile.z]),
        properties: {},
      })),
    };

    if (!this.map.getSource(sourceId)) {
      this.map.addSource(sourceId, {
        type: 'geojson',
        data: tileSource,
      });

      // Fill layer for tile background
      this.map.addLayer({
        id: 'tile-grid-fill',
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': ['rgba', 255, 255, 255, 0.1], // white, 10% opacity
          'fill-outline-color': '#000000',
        },
      });

      // Line layer for tile outlines
      this.map.addLayer({
        id: 'tile-grid-outline',
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#ff0000',
          'line-width': 2,
        },
      });
    } else {
      // Update source data if it already exists
      (this.map.getSource(sourceId) as mapboxgl.GeoJSONSource).setData(
        tileSource,
      );
    }
  }

  findBestZoomLevel(
    target: number,
    initialZoomLevel: number,
    bounds: mapboxgl.LngLatBounds,
  ): number {
    let low = initialZoomLevel;
    let high = 24;
    let bestZoom = 0;
    let bestDiff = Infinity;

    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      const tiles = this.getNumTiles(mid, bounds);
      const diff = Math.abs(tiles - target);

      if (diff < bestDiff) {
        bestDiff = diff;
        bestZoom = mid;
      }

      if (tiles < target) {
        low = mid + 1;
      } else if (tiles > target) {
        high = mid - 1;
      } else {
        // Exact match
        return mid;
      }
    }

    return bestZoom;
  }

  private getNumTiles(zoom: number, bounds: mapboxgl.LngLatBounds): number {
    if (!bounds) {
      return 0;
    }

    const maxIndex = Math.pow(2, zoom) - 1;

    const north = clampLat(bounds.getNorth());
    const south = clampLat(bounds.getSouth());
    const east = clampLng(bounds.getEast());
    const west = clampLng(bounds.getWest());

    const [xTop, yTop] = tilebelt.pointToTile(west, north, zoom);
    const [xBottom, yBottom] = tilebelt.pointToTile(east, south, zoom);

    function numbersInclusive(x: number, y: number): number {
      if (x <= y) {
        return y + 1 - x;
      } else {
        // If x > y, that means that it wrap around the antimeridian
        // So we compute values from x, ..., maxIndex and from 0, ... y
        return maxIndex + 1 - x + (y + 1 - 0);
      }
    }

    const numXValues = numbersInclusive(xTop, xBottom);
    const numYValues = numbersInclusive(yTop, yBottom);

    return numXValues * numYValues;
  }

  private getVisibleTiles(
    zoom: number,
    bounds: mapboxgl.LngLatBounds,
  ): TileId[] {
    if (!bounds) {
      return [];
    }

    const maxIndex = Math.pow(2, zoom) - 1;

    console.log('Zoom:', zoom);

    const north = clampLat(bounds.getNorth());
    const south = clampLat(bounds.getSouth());
    const east = clampLng(bounds.getEast());
    const west = clampLng(bounds.getWest());

    const [xTop, yTop] = tilebelt.pointToTile(west, north, zoom);
    const [xBottom, yBottom] = tilebelt.pointToTile(east, south, zoom);

    function numbersInclusive(x: number, y: number): number[] {
      if (x <= y) {
        return range(x, y + 1);
      } else {
        // If x > y, that means that it wrap around the antimeridian
        // So we compute values from x, ..., maxIndex and from 0, ... y
        return [...range(x, maxIndex + 1), ...range(0, y + 1)];
      }
    }

    const xValues = numbersInclusive(xTop, xBottom);
    const yValues = numbersInclusive(yTop, yBottom);

    const center = this.map.getCenter();
    const tiles: TileId[] = [];

    for (const x of xValues) {
      for (const y of yValues) {
        if (isTileVisibleInGlobe([x, y, zoom], center.lat, center.lng)) {
          tiles.push({ x, y, z: zoom });
        }
      }
    }

    return tiles;
  }

  ngOnDestroy() {
    this.map.remove();
    this.imageMarkers.forEach((marker) => marker.remove());
    this.subscriptions.unsubscribe();
  }
}

function getTheme(isDarkMode: boolean) {
  return isDarkMode
    ? 'mapbox://styles/mapbox/dark-v11'
    : 'mapbox://styles/mapbox/streets-v12';
}

/** Clamp the latitude value from -89.99999 to 89.99999 */
function clampLat(lat: number): number {
  return Math.max(-89.9999, Math.min(89.9999, lat));
}

/** Clamp the longitude value from -179.99999 to 179.99999 */
function clampLng(lng: number): number {
  return Math.max(-179.9999, Math.min(179.9999, lng));
}

/**
 * Returns true if the tile is on the visible hemisphere of the globe.
 */
function isTileVisibleInGlobe(
  tile: [number, number, number],
  cameraLat: number,
  cameraLng: number,
): boolean {
  // Get tile center
  const bbox = tilebelt.tileToBBOX(tile); // [west, south, east, north]
  const centerLng = (bbox[0] + bbox[2]) / 2;
  const centerLat = (bbox[1] + bbox[3]) / 2;

  // Convert to 3D vectors
  const tileVec = latLngToVec3(centerLat, centerLng);
  const cameraVec = latLngToVec3(cameraLat, cameraLng);

  // Dot product > 0 means on same hemisphere
  return (
    tileVec[0] * cameraVec[0] +
      tileVec[1] * cameraVec[1] +
      tileVec[2] * cameraVec[2] >
    0
  );
}

function latLngToVec3(lat: number, lng: number): [number, number, number] {
  const radLat = (lat * Math.PI) / 180;
  const radLng = (lng * Math.PI) / 180;
  return [
    Math.cos(radLat) * Math.cos(radLng),
    Math.cos(radLat) * Math.sin(radLng),
    Math.sin(radLat),
  ];
}
