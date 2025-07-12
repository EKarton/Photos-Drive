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

  it('should return an instance of mapboxgl.Map when called build()', () => {
    const fixture = TestBed.createComponent(EmptyComponent);

    const factory = new MapboxFactory();
    const map = factory.build({
      container: fixture.nativeElement,
      accessToken: '1234',
      testMode: true,
    });

    expect(map).toBeInstanceOf(mapboxgl.Map);
  });
});

@Component({
  selector: 'app-empty',
  template: '',
})
export class EmptyComponent {}
