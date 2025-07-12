import * as mapboxgl from 'mapbox-gl';

/** A factory class used to build an instance of Mapbox class. */
export class MapboxFactory {
  buildMap(options: mapboxgl.MapOptions): mapboxgl.Map {
    return new mapboxgl.Map(options);
  }

  buildMarker(options: mapboxgl.MarkerOptions): mapboxgl.Marker {
    return new mapboxgl.Marker(options);
  }
}
