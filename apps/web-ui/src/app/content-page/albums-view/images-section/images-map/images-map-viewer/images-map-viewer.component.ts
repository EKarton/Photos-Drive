import {
  Component,
  effect,
  ElementRef,
  input,
  OnDestroy,
  OnInit,
  output,
  ViewChild,
} from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import * as mapboxgl from 'mapbox-gl';
import { shareReplay, Subscription } from 'rxjs';

import { environment } from '../../../../../../environments/environment';
import { MediaItem } from '../../../../services/types/media-item';

export interface ImageLocations {
  latitude: number;
  longitude: number;
}

export interface MarkerImages {
  id: string;
  location: ImageLocations;
  thumbnailUrl: string;
}

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
  readonly markerImages = input.required<MarkerImages[]>();
  readonly isDarkMode = input.required<boolean>();

  private readonly mediaItems$ = toObservable(this.mediaItems).pipe(
    shareReplay(1),
  );
  private readonly markerImages$ = toObservable(this.markerImages).pipe(
    shareReplay(1),
  );

  private readonly subscriptions = new Subscription();

  boundsChanged = output<Bounds>();

  @ViewChild('mapContainer', { static: true }) mapContainer!: ElementRef;

  private map!: mapboxgl.Map;
  private markers: mapboxgl.Marker[] = [];

  constructor() {
    effect(() => {
      if (this.map) {
        console.log('Changing theme');
        this.map.setStyle(getTheme(this.isDarkMode()));
        this.map.once('styledata', () => {
          console.log('Re-add heatmap layer and markers after style reload');
          // Re-add heatmap layer and markers after style reload
          this.addHeatmapLayer();
          this.updateMarkers(this.markerImages());
        });
      }
    });
  }

  ngOnInit() {
    this.map = new mapboxgl.Map({
      accessToken: environment.mapboxToken,
      container: this.mapContainer.nativeElement,
      style: getTheme(this.isDarkMode()),
      center: [0, 0],
      zoom: 2,
    });

    this.map.on('load', () => {
      this.addHeatmapLayer();
      this.emitBounds();

      this.subscriptions.add(
        this.mediaItems$.subscribe((mediaItems) => {
          const source = this.map.getSource('media-heatmap') as
            | mapboxgl.GeoJSONSource
            | undefined;
          source?.setData(buildGeoJSONFromMediaItems(mediaItems));
        }),
      );

      this.subscriptions.add(
        this.markerImages$.subscribe((markerImages) => {
          this.updateMarkers(markerImages);
        }),
      );
    });

    this.map.on('moveend', () => {
      this.emitBounds();
    });
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

  private updateMarkers(markerImages: MarkerImages[]) {
    // Remove old markers
    this.markers.forEach((m) => m.remove());
    this.markers = [];

    // Add new markers for the 4 images
    markerImages.forEach((image) => {
      const el = document.createElement('div');
      el.className = 'marker';
      el.style.backgroundImage = `url(${image.thumbnailUrl})`;
      el.style.width = '50px';
      el.style.height = '50px';
      el.style.backgroundSize = 'cover';
      el.style.borderRadius = '50%';
      el.style.border = '2px solid white';
      el.style.boxShadow = '0 0 5px rgba(0,0,0,0.3)';

      const marker = new mapboxgl.Marker(el)
        .setLngLat([image.location.longitude, image.location.latitude])
        .setPopup(
          new mapboxgl.Popup({ offset: 25 }).setHTML(
            `<img src="${image.thumbnailUrl}" width="150"><br><b>${image.id}</b>`,
          ),
        )
        .addTo(this.map);

      this.markers.push(marker);
    });
  }

  ngOnDestroy() {
    this.map.remove();
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
        properties: {},
      })),
  };
}
