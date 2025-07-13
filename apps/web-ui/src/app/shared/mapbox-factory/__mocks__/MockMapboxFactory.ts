import * as mapboxgl from 'mapbox-gl';

import { MockMapboxMap, MockMapboxMarker } from './mocks';

/** A factory class used to build an instance of Mapbox class. */
export class MockMapboxFactory<T> {
  private mapInstances: MockMapboxMap[] = [];
  private markerInstances: MockMapboxMarker<T>[] = [];

  getMapInstances(): MockMapboxMap[] {
    return [...this.mapInstances];
  }

  getMarkerInstances(): MockMapboxMarker<T>[] {
    return [...this.markerInstances];
  }

  buildMap(_: mapboxgl.MapOptions): MockMapboxMap {
    const instance = new MockMapboxMap();
    this.mapInstances.push(instance);
    return instance;
  }

  buildMarker(_: mapboxgl.MarkerOptions): MockMapboxMarker<T> {
    const instance = new MockMapboxMarker<T>();
    this.markerInstances.push(instance);
    return instance;
  }
}
