import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { MAPBOX_FACTORY_TOKEN } from '../../../../../../app.tokens';
import { authState } from '../../../../../../auth/store';
import { MockMapboxFactory } from '../../../../../../shared/mapbox-factory/__mocks__/MockMapboxFactory';
import { toSuccess } from '../../../../../../shared/results/results';
import { GPhotosMediaItem } from '../../../../../services/types/gphotos-media-item';
import { MediaItem } from '../../../../../services/types/media-item';
import { WebApiService } from '../../../../../services/webapi.service';
import { mediaViewerState } from '../../../../../store/media-viewer';
import { openMediaViewer } from '../../../../../store/media-viewer/media-viewer.actions';
import { ImageMapMarkerComponent } from '../image-map-marker/image-map-marker.component';
import {
  Bounds,
  ImagesMapViewerComponent,
} from '../images-map-viewer.component';

const MEDIA_ITEM_1: MediaItem = {
  id: 'photos1',
  fileName: 'cat.png',
  hashCode: '',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1',
  width: 200,
  height: 300,
  location: {
    latitude: -79,
    longitude: 80,
  },
  dateTaken: new Date('2024-05-27T13:17:46.000Z'),
};

const MEDIA_ITEM_2: MediaItem = {
  id: 'photos2',
  fileName: 'dog.png',
  hashCode: '',
  gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem2',
  width: 200,
  height: 300,
  location: {
    latitude: -79,
    longitude: 80.1,
  },
  dateTaken: new Date('2024-05-27T13:17:46.000Z'),
};

const G_MEDIA_ITEM: GPhotosMediaItem = {
  baseUrl: 'http://www.google.com/photos/1',
  mimeType: 'image/jpeg',
  mediaMetadata: {
    creationTime: '',
    width: '4032',
    height: '3024',
  },
};

describe('ImagesMapViewerComponent', () => {
  let store: MockStore;
  let mockWebApiService: jasmine.SpyObj<WebApiService>;
  let mockMapboxFactory: MockMapboxFactory<ImageMapMarkerComponent>;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'getGPhotosMediaItem',
    ]);
    mockMapboxFactory = new MockMapboxFactory();

    await TestBed.configureTestingModule({
      imports: [ImagesMapViewerComponent],
      providers: [
        provideNoopAnimations(),
        provideMockStore({
          initialState: {
            [mediaViewerState.FEATURE_KEY]: mediaViewerState.initialState,
          },
          selectors: [
            { selector: authState.selectAuthToken, value: 'mockAccessToken' },
          ],
        }),
        {
          provide: WebApiService,
          useValue: mockWebApiService,
        },
        {
          provide: MAPBOX_FACTORY_TOKEN,
          useValue: mockMapboxFactory,
        },
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    spyOn(store, 'dispatch');

    mockWebApiService.getGPhotosMediaItem.and.returnValue(
      of(toSuccess(G_MEDIA_ITEM)),
    );
  });

  it('should add heat map and map markers when map loads and map markers is in the viewport', () => {
    const fixture = TestBed.createComponent(ImagesMapViewerComponent);
    fixture.componentRef.setInput('mediaItems', [MEDIA_ITEM_1, MEDIA_ITEM_2]);
    fixture.componentRef.setInput('isDarkMode', false);
    fixture.detectChanges();

    // Load the map
    const mapInstances = mockMapboxFactory.getMapInstances();
    expect(mapInstances.length).toEqual(1);
    mapInstances[0].setBounds(-70, 90, -80, 70);
    mapInstances[0].triggerOnEvent('load');

    // It should set the correct style
    expect(mapInstances[0].setStyle).toHaveBeenCalledWith(
      'mapbox://styles/mapbox/streets-v12',
    );

    // It should build the heat map
    expect(mapInstances[0].addSource).toHaveBeenCalled();
    expect(mapInstances[0].addLayer).toHaveBeenCalled();

    // It should show two markers
    const markers = mockMapboxFactory.getVisibleMarkerInstances();
    expect(markers.length).toEqual(2);
  });

  it('should re-render the map when isDarkMode changes', () => {
    const fixture = TestBed.createComponent(ImagesMapViewerComponent);
    fixture.componentRef.setInput('mediaItems', [MEDIA_ITEM_1, MEDIA_ITEM_2]);
    fixture.componentRef.setInput('isDarkMode', false);
    fixture.detectChanges();

    // Load the map
    const mapInstances = mockMapboxFactory.getMapInstances();
    expect(mapInstances.length).toEqual(1);
    mapInstances[0].setBounds(-70, 90, -80, 70);
    mapInstances[0].triggerOnEvent('load');

    // Change the mode to dark mode
    fixture.componentRef.setInput('isDarkMode', true);
    fixture.detectChanges();
    mapInstances[0].triggerOnceEvents('styledata');
    fixture.detectChanges();

    // It should set the style to a new style
    expect(mapInstances[0].setStyle).toHaveBeenCalledWith(
      'mapbox://styles/mapbox/dark-v11',
    );

    // It should only call addLayer() and addSource() once
    expect(mapInstances[0].addLayer).toHaveBeenCalledTimes(1);
    expect(mapInstances[0].addSource).toHaveBeenCalledTimes(1);

    // It should show two markers
    const markers = mockMapboxFactory.getVisibleMarkerInstances();
    expect(markers.length).toEqual(2);
    expect(markers[0].getComponentInstance()?.instance.badgeCount()).toEqual(1);
    expect(markers[1].getComponentInstance()?.instance.badgeCount()).toEqual(1);
  });

  it('should output boundsChanged when map pans', () => {
    const fixture = TestBed.createComponent(ImagesMapViewerComponent);
    fixture.componentRef.setInput('mediaItems', [MEDIA_ITEM_1, MEDIA_ITEM_2]);
    fixture.componentRef.setInput('isDarkMode', false);
    fixture.detectChanges();

    // Listen to boundsChanged events
    const boundsEmitted: Bounds[] = [];
    fixture.componentInstance.boundsChanged.subscribe((newBounds) =>
      boundsEmitted.push(newBounds),
    );

    // Load the map
    const mapInstances = mockMapboxFactory.getMapInstances();
    expect(mapInstances.length).toEqual(1);
    mapInstances[0].setBounds(-70, 90, -80, 70);
    mapInstances[0].triggerOnEvent('load');

    // Move map to the right
    mapInstances[0].setBounds(-70, 95, -80, 75);
    mapInstances[0].triggerOnEvent('moveend');

    // Expect boundsChanged to be emitted
    expect(boundsEmitted).toEqual([
      { north: -70, south: -80, east: 90, west: 70 },
      { north: -70, south: -80, east: 95, west: 75 },
    ]);
  });

  it('should render the map with a cluster map marker when media items have the same gps locations', () => {
    const fixture = TestBed.createComponent(ImagesMapViewerComponent);
    fixture.componentRef.setInput('mediaItems', [
      MEDIA_ITEM_1,
      { ...MEDIA_ITEM_2, location: MEDIA_ITEM_1.location },
    ]);
    fixture.componentRef.setInput('isDarkMode', false);
    fixture.detectChanges();

    const mapInstances = mockMapboxFactory.getMapInstances();
    expect(mapInstances.length).toEqual(1);
    mapInstances[0].setBounds(-70, 90, -80, 70);
    mapInstances[0].triggerOnEvent('load');

    expect(mapInstances[0].addSource).toHaveBeenCalled();
    expect(mapInstances[0].addLayer).toHaveBeenCalled();

    // It should show only one marker since the two images are clustered together
    const markers = mockMapboxFactory.getVisibleMarkerInstances();
    expect(markers.length).toEqual(1);
    expect(markers[0].getComponentInstance()?.instance.badgeCount()).toEqual(2);
  });

  it('should zoom into the map when user clicks on a cluster marker', () => {
    const fixture = TestBed.createComponent(ImagesMapViewerComponent);
    fixture.componentRef.setInput('mediaItems', [
      MEDIA_ITEM_1,
      { ...MEDIA_ITEM_2, location: MEDIA_ITEM_1.location },
    ]);
    fixture.componentRef.setInput('isDarkMode', false);
    fixture.detectChanges();

    // Load the map
    const mapInstances = mockMapboxFactory.getMapInstances();
    expect(mapInstances.length).toEqual(1);
    mapInstances[0].setBounds(-70, 90, -80, 70);
    mapInstances[0].triggerOnEvent('load');

    // Check there is only one cluster marker
    const markers = mockMapboxFactory.getVisibleMarkerInstances();
    expect(markers.length).toEqual(1);

    // Click on the marker
    const mouseEvent = new MouseEvent('click');
    markers[0].getComponentInstance()?.instance.markerClick.emit(mouseEvent);
    fixture.detectChanges();

    // Expect the map to zoom in
    expect(mapInstances[0].easeTo).toHaveBeenCalled();
  });

  it('should open the image viewer when user clicks on an individual map marker', () => {
    const fixture = TestBed.createComponent(ImagesMapViewerComponent);
    fixture.componentRef.setInput('mediaItems', [MEDIA_ITEM_1, MEDIA_ITEM_2]);
    fixture.componentRef.setInput('isDarkMode', false);
    fixture.detectChanges();

    // Load the map
    const mapInstances = mockMapboxFactory.getMapInstances();
    expect(mapInstances.length).toEqual(1);
    mapInstances[0].setBounds(-70, 90, -80, 70);
    mapInstances[0].triggerOnEvent('load');

    // Check there is only one cluster marker
    const markers = mockMapboxFactory.getVisibleMarkerInstances();
    expect(markers.length).toEqual(2);

    // Click on one of the markers
    const mouseEvent = new MouseEvent('click');
    markers[0].getComponentInstance()?.instance.markerClick.emit(mouseEvent);
    fixture.detectChanges();

    // Expect the media viewer to be dispatched
    expect(store.dispatch).toHaveBeenCalledWith(
      openMediaViewer({
        request: {
          mediaItemId: MEDIA_ITEM_1.id,
        },
      }),
    );
  });

  it('should not create map markers when map has not loaded yet but user has moved the map', () => {
    const fixture = TestBed.createComponent(ImagesMapViewerComponent);
    fixture.componentRef.setInput('mediaItems', [MEDIA_ITEM_1, MEDIA_ITEM_2]);
    fixture.componentRef.setInput('isDarkMode', false);
    fixture.detectChanges();

    // Listen to boundsChanged events
    const boundsEmitted: Bounds[] = [];
    fixture.componentInstance.boundsChanged.subscribe((newBounds) =>
      boundsEmitted.push(newBounds),
    );

    // Move the map without the map loading yet
    const mapInstances = mockMapboxFactory.getMapInstances();
    expect(mapInstances.length).toEqual(1);
    mapInstances[0].setBounds(-70, 90, -80, 70);
    mapInstances[0].triggerOnEvent('moveend');

    // Expect no map markers to be created
    expect(mockMapboxFactory.getMarkerInstances().length).toEqual(0);
  });

  it('should not create map markers when map has no bounds yet', () => {
    const fixture = TestBed.createComponent(ImagesMapViewerComponent);
    fixture.componentRef.setInput('mediaItems', [MEDIA_ITEM_1, MEDIA_ITEM_2]);
    fixture.componentRef.setInput('isDarkMode', false);
    fixture.detectChanges();

    // Listen to boundsChanged events
    const boundsEmitted: Bounds[] = [];
    fixture.componentInstance.boundsChanged.subscribe((newBounds) =>
      boundsEmitted.push(newBounds),
    );

    // Move the map without the map loading yet
    const mapInstances = mockMapboxFactory.getMapInstances();
    expect(mapInstances.length).toEqual(1);
    mapInstances[0].triggerOnEvent('load');
    mapInstances[0].triggerOnEvent('moveend');

    // Expect no map markers to be created
    expect(mockMapboxFactory.getMarkerInstances().length).toEqual(0);
  });
});
