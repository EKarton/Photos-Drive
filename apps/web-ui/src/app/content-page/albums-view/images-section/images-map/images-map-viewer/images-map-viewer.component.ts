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
import Supercluster from 'supercluster';

import { MAPBOX_FACTORY_TOKEN } from '../../../../../app.tokens';
import { authState } from '../../../../../auth/store';
import { MediaItem } from '../../../../services/types/media-item';
import { mediaViewerActions } from '../../../../store/media-viewer';
import { ImageMapMarkerComponent } from './image-map-marker/image-map-marker.component';

export interface Bounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

@Component({
  selector: 'app-images-map-viewer',
  templateUrl: './images-map-viewer.component.html',
  styleUrls: ['./images-map-viewer.component.scss'],
  standalone: true,
})
export class ImagesMapViewerComponent implements OnInit, OnDestroy {
  readonly mediaItems = input.required<MediaItem[]>();
  readonly isDarkMode = input.required<boolean>();

  private readonly mediaItems$ = toObservable(this.mediaItems).pipe(
    shareReplay(1),
  );

  private readonly subscriptions = new Subscription();

  boundsChanged = output<Bounds>();

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
          this.addHeatmapLayer();
          this.prepareSupercluster();
          this.updateImageMarkers();
          this.addTileGridLayer();
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

    // Center the map to the first item in mediaItems$
    this.subscriptions.add(
      this.mediaItems$
        .pipe(
          map((mediaItems) =>
            mediaItems.find((mediaItem) => mediaItem.location),
          ),
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
      this.addHeatmapLayer();
      this.prepareSupercluster();
      this.updateImageMarkers();
      this.addTileGridLayer();
      this.emitBounds();

      this.subscriptions.add(
        this.mediaItems$.subscribe((mediaItems) => {
          this.prepareSupercluster();
          this.updateHeatmapLayer(mediaItems);
          this.updateImageMarkers();
          this.updateTileGridLayer();
        }),
      );
    });

    // Update the map whenever the map has moved
    this.map.on('moveend', () => {
      this.updateImageMarkers();
      this.emitBounds();
      this.updateTileGridLayer();
    });
  }

  private prepareSupercluster() {
    const seen = new Map<string, number>();

    const geojsonPoints: Supercluster.PointFeature<{ mediaItem: MediaItem }>[] =
      this.mediaItems()
        .filter((mediaItem) => mediaItem.location)
        .map((mediaItem) => {
          const lng = mediaItem.location!.longitude;
          const lat = mediaItem.location!.latitude;
          const key = `${lng},${lat}`;
          let jitteredLng = lng;
          let jitteredLat = lat;

          // If this location has been seen before, apply jitter
          const count = seen.get(key) || 0;
          if (count > 0) {
            jitteredLng = jitterCoordinate(lng, 0.0001 * (count + 1));
            jitteredLat = jitterCoordinate(lat, 0.0001 * (count + 1));
          }
          seen.set(key, count + 1);

          return {
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [jitteredLng, jitteredLat],
            },
            properties: {
              mediaItem,
            },
          };
        });

    this.supercluster = new Supercluster({
      radius: 48,
      maxZoom: this.map.getMaxZoom() - 1,
    });
    this.supercluster.load(geojsonPoints);
  }

  private emitBounds() {
    const bounds = this.map.getBounds();

    if (bounds) {
      this.boundsChanged.emit({
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      });
    }
  }

  private addHeatmapLayer() {
    const sourceId = 'media-heatmap';
    const layerId = 'heatmap-layer';

    if (!this.map.getSource(sourceId)) {
      this.map.addSource(sourceId, {
        type: 'geojson',
        data: buildGeoJSONFromMediaItems(this.mediaItems()),
      });
    }

    if (!this.map.getLayer(layerId)) {
      this.map.addLayer({
        id: layerId,
        type: 'heatmap',
        source: sourceId,
        maxzoom: 22,
        paint: {
          // Customize heatmap style as you want
          'heatmap-weight': 1,
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
    }
  }

  private updateHeatmapLayer(mediaItems: MediaItem[]) {
    const source = this.map.getSource('media-heatmap') as
      | mapboxgl.GeoJSONSource
      | undefined;
    source?.setData(buildGeoJSONFromMediaItems(mediaItems));
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
      const [longitude, latitude] = cluster.geometry.coordinates;
      let componentRef: ComponentRef<ImageMapMarkerComponent>;

      if (cluster.properties.cluster) {
        const count = cluster.properties.point_count;
        const leaf = this.supercluster.getLeaves(cluster.id as number, 1)[0];
        const mediaItem = leaf.properties['mediaItem'] as MediaItem;

        componentRef = this.viewContainerRef.createComponent(
          ImageMapMarkerComponent,
        );
        componentRef.setInput('mediaItem', mediaItem);
        componentRef.setInput('badgeCount', count);

        const expansionZoom = this.supercluster.getClusterExpansionZoom(
          cluster.properties.cluster_id as number,
        );
        this.subscriptions.add(
          componentRef.instance.markerClick.subscribe(() => {
            this.map.easeTo({
              center: [longitude, latitude],
              zoom: expansionZoom,
            });
          }),
        );
      } else {
        const mediaItem = cluster.properties['mediaItem'] as MediaItem;
        componentRef = this.viewContainerRef.createComponent(
          ImageMapMarkerComponent,
        );
        componentRef.setInput('mediaItem', mediaItem);

        this.subscriptions.add(
          componentRef.instance.markerClick.subscribe(() => {
            this.store.dispatch(
              mediaViewerActions.openMediaViewer({
                request: { mediaItemId: mediaItem.id },
              }),
            );
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

  private addTileGridLayer() {
    const tileSource = this.createTileGridSource();

    if (!this.map.getSource('tile-grid')) {
      this.map.addSource('tile-grid', {
        type: 'geojson',
        data: tileSource,
      });

      // Optional: fill layer for tile background
      this.map.addLayer({
        id: 'tile-grid-fill',
        type: 'fill',
        source: 'tile-grid',
        paint: {
          'fill-color': ['rgba', 255, 255, 255, 0.1], // white, 10% opacity
          'fill-outline-color': '#000000',
        },
      });

      // Line layer for tile outlines
      this.map.addLayer({
        id: 'tile-grid-outline',
        type: 'line',
        source: 'tile-grid',
        paint: {
          'line-color': '#ff0000',
          'line-width': 2,
        },
      });
    } else {
      // Update source data if it already exists
      (this.map.getSource('tile-grid') as mapboxgl.GeoJSONSource).setData(
        tileSource,
      );
    }
  }

  private updateTileGridLayer() {
    this.addTileGridLayer();
  }

  private createTileGridSource(): GeoJSON.FeatureCollection {
    const bounds = this.map.getBounds();
    if (!bounds) {
      console.log('There are no bounds');
      return {
        type: 'FeatureCollection',
        features: [],
      };
    }

    console.log(this.map.getZoom());

    const zoom = Math.max(4, Math.floor(this.map.getZoom()));
    const maxIndex = Math.pow(2, zoom) - 1;

    function clampLat(lat: number): number {
      return Math.max(-89.99999, Math.min(89.9999, lat));
    }

    function clampLng(lng: number): number {
      return Math.max(-179.99999, Math.min(179.9999, lng));
    }

    // Compute Y range from visible latitudes
    // const north = clampLat(northEast.lat);
    // const south = clampLat(southWest.lat);
    // const east = clampLng(northEast.lng);
    // const west = clampLng(southWest.lng);

    const north = clampLat(bounds.getNorth());
    const south = clampLat(bounds.getSouth());
    const east = clampLng(bounds.getEast());
    const west = clampLng(bounds.getWest());

    console.log(
      'raw bounds:',
      bounds.getWest(),
      bounds.getEast(),
      bounds.getNorth(),
      bounds.getSouth(),
    );

    console.log('fixed bounds:', west, east, north, south);

    const [xTop, yTop] = tilebelt.pointToTile(west, north, zoom);
    const [xBottom, yBottom] = tilebelt.pointToTile(east, south, zoom);

    console.log('tile coords', xTop, xBottom, yTop, yBottom);

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

    const tiles: [number, number, number][] = [];
    for (const x of xValues) {
      for (const y of yValues) {
        tiles.push([x, y, zoom]);
      }
    }

    const features: GeoJSON.Feature[] = this.filterVisibleTiles(
      this.map,
      tiles,
    ).map((tile) => ({
      type: 'Feature',
      geometry: tilebelt.tileToGeoJSON([tile[0], tile[1], tile[2]]),
      properties: { x: tile[0], y: tile[1], z: tile[2] },
    }));

    console.log('Num tiles', tiles.length);
    console.log('Num visible tiles', features.length);

    return {
      type: 'FeatureCollection',
      features,
    };
  }

  latLngToVec3(lat: number, lng: number): [number, number, number] {
    const radLat = (lat * Math.PI) / 180;
    const radLng = (lng * Math.PI) / 180;
    return [
      Math.cos(radLat) * Math.cos(radLng),
      Math.cos(radLat) * Math.sin(radLng),
      Math.sin(radLat),
    ];
  }

  /**
   * Returns true if the tile is on the visible hemisphere of the globe.
   */
  isTileVisibleInGlobe(
    tile: [number, number, number],
    cameraLat: number,
    cameraLng: number,
  ): boolean {
    // Get tile center
    const bbox = tilebelt.tileToBBOX(tile); // [west, south, east, north]
    const centerLng = (bbox[0] + bbox[2]) / 2;
    const centerLat = (bbox[1] + bbox[3]) / 2;

    // Convert to 3D vectors
    const tileVec = this.latLngToVec3(centerLat, centerLng);
    const cameraVec = this.latLngToVec3(cameraLat, cameraLng);

    // Dot product > 0 means on same hemisphere
    return (
      tileVec[0] * cameraVec[0] +
        tileVec[1] * cameraVec[1] +
        tileVec[2] * cameraVec[2] >
      0
    );
  }

  /**
   * Filters a list of tiles to only those visible in the current Mapbox globe viewport.
   */
  filterVisibleTiles(
    map: mapboxgl.Map,
    tiles: [number, number, number][],
  ): [number, number, number][] {
    const center = map.getCenter();
    return tiles.filter((tile) =>
      this.isTileVisibleInGlobe(tile, center.lat, center.lng),
    );
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

function buildGeoJSONFromMediaItems(
  mediaItems: MediaItem[],
): GeoJSON.FeatureCollection {
  console.log('building', mediaItems.length);
  return {
    type: 'FeatureCollection',
    features: mediaItems
      .filter((mediaItem) => mediaItem.location)
      .map((mediaItem) => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [
            mediaItem.location!.longitude,
            mediaItem.location!.latitude,
          ],
        },
        properties: {
          ...mediaItem,
        },
      })),
  };
}

function jitterCoordinate(coord: number, magnitude: number): number {
  // Magnitude is in degrees; 0.00005 ~ 5 meters
  return coord + (Math.random() - 0.5) * 2 * magnitude;
}
