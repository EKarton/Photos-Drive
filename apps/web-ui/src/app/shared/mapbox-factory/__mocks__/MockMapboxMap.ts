import mapboxgl from 'mapbox-gl';

/** A mock of the {@code mapboxgl.Map} */
export class MockMapboxMap extends mapboxgl.Map {
  private onToLambda = new Map<string, () => void>();
  private onceToLambda = new Map<string, () => void>();

  private sourceIdToSource = new Map<string, mapboxgl.SourceSpecification>();
  private layerIdToLayer = new Map<string, mapboxgl.AnyLayer>();

  private zoom = 10;
  private bounds: mapboxgl.LngLatBounds | undefined = undefined;

  override on = jasmine
    .createSpy('on')
    .and.callFake((event: string, lambda: () => void) => {
      this.onToLambda.set(event, lambda);
    });

  override once = jasmine
    .createSpy('once')
    .and.callFake((event: string, lambda: () => void) => {
      this.onceToLambda.set(event, lambda);
    });

  override setStyle = jasmine.createSpy('setStyle');
  override setCenter = jasmine.createSpy('setCenter');
  override easeTo = jasmine.createSpy('easeTo');
  override remove = jasmine.createSpy('remove');
  override getZoom = jasmine.createSpy('getZoom').and.callFake(() => this.zoom);
  override getMaxZoom = jasmine.createSpy('getMaxZoom').and.returnValue(22);

  override getSource = jasmine
    .createSpy('getSource')
    .and.callFake((sourceId) => {
      if (this.sourceIdToSource.has(sourceId)) {
        return jasmine.createSpyObj<mapboxgl.GeoJSONSource>('GeoJSONSource', [
          'setData',
          'getClusterExpansionZoom',
          'getClusterChildren',
          'getClusterLeaves',
        ]);
      }
      return undefined;
    });

  override addSource = jasmine
    .createSpy('addSource')
    .and.callFake((sourceId: string, specs: mapboxgl.SourceSpecification) =>
      this.sourceIdToSource.set(sourceId, specs),
    );

  override getLayer = jasmine
    .createSpy('getLayer')
    .and.callFake((layerId: string) => this.layerIdToLayer.get(layerId));

  override addLayer = jasmine
    .createSpy('addLayer')
    .and.callFake((specs: mapboxgl.AnyLayer) =>
      this.layerIdToLayer.set(specs.id, specs),
    );

  override getBounds = jasmine
    .createSpy('getBounds')
    .and.callFake(() => this.bounds);

  setBounds(north: number, east: number, south: number, west: number) {
    this.bounds = new mapboxgl.LngLatBounds(
      [west, south], // Southwest corner
      [east, north], // Northeast corner
    );
  }

  triggerOnEvent(event: string) {
    this.onToLambda.get(event)!();
  }

  triggerOnceEvents(event: string) {
    this.onceToLambda.get(event)!();
    this.onceToLambda.delete(event);
  }
}
