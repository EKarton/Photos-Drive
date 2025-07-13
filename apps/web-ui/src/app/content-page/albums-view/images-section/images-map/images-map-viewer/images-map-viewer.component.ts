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
import { Store } from '@ngrx/store';
import * as mapboxgl from 'mapbox-gl';
import {
  debounceTime,
  filter,
  map,
  shareReplay,
  Subscription,
  take,
} from 'rxjs';
import Supercluster from 'supercluster';

import { environment } from '../../../../../../environments/environment';
import { MAPBOX_FACTORY_TOKEN } from '../../../../../app.tokens';
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
        });
      }
    });
  }

  ngOnInit() {
    this.map = this.mapboxFactory.buildMap({
      accessToken: environment.mapboxToken,
      container: this.mapContainer.nativeElement,
      style: getTheme(this.isDarkMode()),
      center: [0, 0],
      zoom: 2,
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
      this.emitBounds();

      this.subscriptions.add(
        this.mediaItems$.subscribe((mediaItems) => {
          this.prepareSupercluster();
          this.updateHeatmapLayer(mediaItems);
          this.updateImageMarkers();
        }),
      );
    });

    // Update the map whenever the map has moved
    this.map.on('moveend', () => {
      this.updateImageMarkers();
      this.emitBounds();
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
            jitteredLng = jitterCoordinate(lng, 0.00005 * (count + 1));
            jitteredLat = jitterCoordinate(lat, 0.00005 * (count + 1));
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
      maxZoom: this.map.getMaxZoom(),
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

  ngOnDestroy() {
    this.map.remove();
    this.subscriptions.unsubscribe();
    this.imageMarkers.forEach((marker) => marker.remove());
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
