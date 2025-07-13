import { ComponentRef } from '@angular/core';

/** A mock of the {@code mapboxgl.Marker} */

export class MockMapboxMarker<T> {
  private componentInstance: ComponentRef<T> | undefined = undefined;

  setLngLat = jasmine.createSpy('setLngLat').and.returnValue(this);
  addTo = jasmine.createSpy('addTo').and.returnValue(this);
  remove = jasmine.createSpy('remove');

  setComponentInstance(instance: ComponentRef<T>) {
    this.componentInstance = instance;
  }

  getComponentInstance(): ComponentRef<T> | undefined {
    return this.componentInstance;
  }
}
