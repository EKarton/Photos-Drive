import {
  Component,
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
import { shareReplay, Subscription } from 'rxjs';
import Supercluster from 'supercluster';

import { MAPBOX_FACTORY_TOKEN } from '../../../../../app.tokens';
import { authState } from '../../../../../auth/store';
import { Heatmap } from '../../../../services/types/heatmap';
import { mediaViewerActions } from '../../../../store/media-viewer';
import { ImageMapMarkerComponent } from './image-map-marker/image-map-marker.component';

export interface TileId {
  x: number;
  y: number;
  z: number;
}

@Component({
  selector: 'app-images-map-viewer',
  templateUrl: './images-map-viewer.component.html',
  styleUrls: ['./images-map-viewer.component.scss'],
  standalone: true,
})
export class ImagesMapViewerComponent implements OnInit, OnDestroy {
  readonly heatmap = input.required<Heatmap>();
  readonly isDarkMode = input.required<boolean>();

  readonly visibleTilesChanged = output<TileId[]>();

  private readonly heatmap$ = toObservable(this.heatmap).pipe(shareReplay(1));

  private readonly subscriptions = new Subscription();

  @ViewChild('mapContainer', { static: true }) mapContainer!: ElementRef;
  private readonly viewContainerRef = inject(ViewContainerRef);
  private readonly store = inject(Store);
  private readonly mapboxFactory = inject(MAPBOX_FACTORY_TOKEN);
  private readonly mapboxApiToken = this.store.selectSignal(
    authState.selectMapboxApiToken,
  );

  private map!: mapboxgl.Map;
  private supercluster!: Supercluster;
  private imageMarkers: mapboxgl.Marker[] = [];

  constructor() {
    effect(() => {
      if (this.map) {
        this.map.setStyle(getTheme(this.isDarkMode()));

        // Re-add heatmap layer and markers after style reload
        this.map.once('styledata', () => {
          this.updateTileGridLayer();
          this.updateHeatmapLayer();
          this.updateImageMarkers();
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

    // Set the map layers whenever it has finished loading
    this.map.on('load', () => {
      this.updateTileGridLayer();
      this.updateHeatmapLayer();
      this.prepareSupercluster();
      this.updateImageMarkers();
      this.emitVisibleTiles();

      this.subscriptions.add(
        this.heatmap$.subscribe(() => {
          this.updateHeatmapLayer();
          this.prepareSupercluster();
          this.updateImageMarkers();
        }),
      );
    });

    // Update the map whenever the map has moved
    this.map.on('moveend', () => {
      this.updateTileGridLayer();
      this.updateHeatmapLayer();
      this.updateImageMarkers();
      this.emitVisibleTiles();
    });
  }

  private updateTileGridLayer() {
    const sourceId = 'tile-grid';
    const tileSource: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: this.getVisibleTiles().map((tile) => ({
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

  private getVisibleTiles(): TileId[] {
    const bounds = this.map.getBounds();
    if (!bounds) {
      return [];
    }

    const zoom = this.map.getZoom();
    const maxIndex = Math.pow(2, zoom) - 1;

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

  private prepareSupercluster() {
    const geojsonPoints: Supercluster.PointFeature<{
      sampledMediaItemId: string;
      count: number;
    }>[] = this.heatmap().points.map((point) => {
      return {
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [point.longitude, point.latitude],
        },
        properties: {
          sampledMediaItemId: point.sampledMediaItemId,
          count: point.count,
        },
      };
    });

    this.supercluster = new Supercluster({
      radius: 60,
      maxZoom: this.map.getMaxZoom() - 1,
      map: (props) => {
        return {
          count: props['count'] as number,
        };
      },
      reduce: (accumulated, props) => {
        accumulated.count += props.count;
      },
    });
    this.supercluster.load(geojsonPoints);
  }

  private updateImageMarkers() {
    // Remove old markers
    this.imageMarkers.forEach((marker) => marker.remove());
    this.imageMarkers = [];

    // Get clusters for current viewport and zoom
    const bounds = this.map.getBounds();
    if (!bounds || !this.supercluster) {
      return;
    }

    const bbox: GeoJSON.BBox = [
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth(),
    ];
    const clusters = this.supercluster.getClusters(bbox, this.map.getZoom());

    for (const cluster of clusters) {
      const longitude = cluster.geometry.coordinates[0];
      const latitude = cluster.geometry.coordinates[1];

      let mediaItemId: string;
      let count: number;

      if (cluster.properties.cluster) {
        const leaf = this.supercluster.getLeaves(cluster.id as number, 1)[0];
        mediaItemId = leaf.properties['sampledMediaItemId'] as string;

        count = cluster.properties['count'] as number;
      } else {
        mediaItemId = cluster.properties['sampledMediaItemId'] as string;
        count = cluster.properties['count'] as number;
      }

      const componentRef = this.viewContainerRef.createComponent(
        ImageMapMarkerComponent,
      );
      componentRef.setInput('mediaItemId', mediaItemId);
      componentRef.setInput('badgeCount', count);

      if (count === 1) {
        this.subscriptions.add(
          componentRef.instance.markerClick.subscribe(() => {
            this.store.dispatch(
              mediaViewerActions.openMediaViewer({
                request: { mediaItemId: mediaItemId },
              }),
            );
          }),
        );
      } else {
        const expansionZoom = this.supercluster.getClusterExpansionZoom(
          cluster.id as number,
        );
        this.subscriptions.add(
          componentRef.instance.markerClick.subscribe(() => {
            this.map.easeTo({
              center: [longitude, latitude],
              zoom: expansionZoom,
            });
          }),
        );
      }

      const marker = this.mapboxFactory
        .buildMarker(componentRef)
        .setLngLat([longitude, latitude])
        .addTo(this.map);

      this.imageMarkers.push(marker);
    }
  }

  private updateHeatmapLayer() {
    const sourceId = 'media-heatmap';
    const layerId = 'heatmap-layer';

    // Prepare GeoJSON from your Heatmap object
    const geojson = this.buildGeoJSONFromHeatmap(this.heatmap());

    // Add or update the source
    if (!this.map.getSource(sourceId)) {
      this.map.addSource(sourceId, {
        type: 'geojson',
        data: geojson,
      });

      // Add the heatmap layer
      this.map.addLayer({
        id: layerId,
        type: 'heatmap',
        source: sourceId,
        maxzoom: 22,
        paint: {
          'heatmap-weight': [
            'interpolate',
            ['linear'],
            ['get', 'count'],
            0,
            0,
            10,
            0.2,
            50,
            0.5,
            100,
            0.8,
            200,
            1,
          ],
          'heatmap-intensity': 1,
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0,
            'rgba(33,102,172,0)',
            0.2,
            'rgb(103,169,207)',
            0.4,
            'rgb(209,229,240)',
            0.6,
            'rgb(253,219,199)',
            0.8,
            'rgb(239,138,98)',
            1,
            'rgb(178,24,43)',
          ],
          'heatmap-radius': 20,
          'heatmap-opacity': 0.8,
        },
      });
    } else {
      // Update the data if the source already exists
      const source = this.map.getSource(sourceId) as
        | mapboxgl.GeoJSONSource
        | undefined;
      source?.setData(geojson);
    }
  }

  private buildGeoJSONFromHeatmap(heatmap: Heatmap): GeoJSON.GeoJSON {
    return {
      type: 'FeatureCollection',
      features: heatmap.points.map((entry) => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [entry.longitude, entry.latitude],
        },
        properties: {
          count: entry.count,
        },
      })),
    };
  }

  private emitVisibleTiles() {
    const visibleTiles = this.getVisibleTiles();
    this.visibleTilesChanged.emit(visibleTiles);
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
