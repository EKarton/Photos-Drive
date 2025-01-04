import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { toSuccess } from '../../../../../shared/results/results';
import { Album } from '../../../../services/webapi.service';
import { albumsState } from '../../../../store/albums';
import { AlbumCardComponent } from '../album-card.component';

describe('AlbumCardComponent', () => {
  let store: MockStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlbumCardComponent],
      providers: [
        provideMockStore({
          initialState: {
            [albumsState.FEATURE_KEY]: albumsState.buildInitialState(),
          },
        }),
        provideRouter([]),
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
  });

  [
    { numPhotos: 10, numAlbums: 10, expectedString: '10 photos · 10 albums' },
    { numPhotos: 1, numAlbums: 10, expectedString: '1 photo · 10 albums' },
    { numPhotos: 10, numAlbums: 1, expectedString: '10 photos · 1 album' },
    { numPhotos: 0, numAlbums: 10, expectedString: '10 albums' },
    { numPhotos: 10, numAlbums: 0, expectedString: '10 photos' },
    { numPhotos: 0, numAlbums: 1, expectedString: '1 album' },
    { numPhotos: 1, numAlbums: 0, expectedString: '1 photo' },
  ].forEach(({ numPhotos, numAlbums, expectedString }) => {
    it(`should render component correctly given num photos = ${numPhotos} and num child albums = ${numAlbums}`, () => {
      const apiResponse: Album = {
        id: 'album3',
        albumName: 'Photos',
        parentAlbumId: 'album2',
        childAlbumIds: Array.from({ length: numAlbums }, (i) => `c-${i}`),
        mediaItemIds: Array.from({ length: numPhotos }, (i) => `m-${i}`),
      };
      store.setState({
        [albumsState.FEATURE_KEY]: {
          idToDetails: ImmutableMap().set('album3', toSuccess(apiResponse)),
        },
      });
      store.refreshState();

      const fixture = TestBed.createComponent(AlbumCardComponent);
      fixture.componentRef.setInput('albumId', 'album3');
      fixture.detectChanges();

      const element = fixture.nativeElement.querySelector(
        '.album-card__sub-text',
      );
      expect(element.textContent).toContain(expectedString);
      const component = fixture.componentInstance;
      expect(component).toBeTruthy();
    });
  });

  it('should render spinner given no response', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.skeleton')).toBeTruthy();
  });
});
