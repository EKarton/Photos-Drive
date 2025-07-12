import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import * as mapboxgl from 'mapbox-gl';

import { MapboxFactory } from '../MapboxFactory';

describe('MapboxFactory', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmptyComponent],
    }).compileComponents();
  });

  it('should return an instance of mapboxgl.Map when called buildMap()', () => {
    const fixture = TestBed.createComponent(EmptyComponent);

    const factory = new MapboxFactory();
    const map = factory.buildMap({
      container: fixture.nativeElement,
      accessToken: '1234',
      testMode: true,
    });

    expect(map).toBeInstanceOf(mapboxgl.Map);
  });

  it('should return an instance of mapboxgl.Marker when called buildMarker()', () => {
    const fixture = TestBed.createComponent(EmptyComponent);

    const factory = new MapboxFactory();
    const map = factory.buildMarker(fixture.nativeElement);

    expect(map).toBeInstanceOf(mapboxgl.Marker);
  });
});

@Component({
  selector: 'app-empty',
  template: '',
})
export class EmptyComponent {}
