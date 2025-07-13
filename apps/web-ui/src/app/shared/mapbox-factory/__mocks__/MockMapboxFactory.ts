import { ComponentRef } from '@angular/core';

import { MockMapboxMap } from './MockMapboxMap';
import { MockMapboxMarker } from './MockMapboxMarker';

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

  buildMap(options: mapboxgl.MapOptions): MockMapboxMap {
    const instance = new MockMapboxMap({
      ...options,
      testMode: true,
    });
    this.mapInstances.push(instance);
    return instance;
  }

  buildMarker(componentInstance: ComponentRef<T>): MockMapboxMarker<T> {
    const instance = new MockMapboxMarker<T>(componentInstance);
    this.markerInstances.push(instance);
    return instance;
  }
}
