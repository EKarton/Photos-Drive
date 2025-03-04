import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { toFailure, toSuccess } from '../../../../../shared/results/results';
import { Album } from '../../../../services/webapi.service';
import { albumsState } from '../../../../store/albums';
import { AlbumCardComponent } from '../album-cards-list.component';

const ALBUM_DETAILS_1: Album = {
  id: 'album1',
  albumName: 'Photos',
  parentAlbumId: 'album0',
  childAlbumIds: ['childAlbum1', 'childAlbum2', 'childAlbum3'],
  mediaItemIds: [],
};

const CHILD_ALBUM_DETAILS_1: Album = {
  id: 'childAlbum1',
  albumName: '2010',
  parentAlbumId: 'album1',
  childAlbumIds: [],
  mediaItemIds: ['photos1'],
};

const CHILD_ALBUM_DETAILS_2: Album = {
  id: 'childAlbum2',
  albumName: '2011',
  parentAlbumId: 'album1',
  childAlbumIds: [],
  mediaItemIds: ['photos2'],
};

const CHILD_ALBUM_DETAILS_3: Album = {
  id: 'childAlbum3',
  albumName: '2012',
  parentAlbumId: 'album1',
  childAlbumIds: [],
  mediaItemIds: ['photos3'],
};

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
    spyOn(store, 'dispatch');
  });

  it('should render skeleton when media item is not loaded yet', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('album', ALBUM_DETAILS_1);
    fixture.detectChanges();

    const skeletons = fixture.nativeElement.querySelectorAll(
      '[data-testid="album-skeleton"]',
    );
    expect(skeletons.length).toEqual(3);
  });

  it('should show error when child album has failed to load', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('album', ALBUM_DETAILS_1);
    fixture.detectChanges();

    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap().set(
          'childAlbum1',
          toFailure(new Error('Random error')),
        ),
      },
    });
    store.refreshState();
    fixture.detectChanges();

    const error = fixture.nativeElement.querySelector(
      '[data-testid="albums-error"]',
    );
    expect(error).toBeTruthy();
  });

  it('should render correctly when child albums has loaded already', () => {
    const fixture = TestBed.createComponent(AlbumCardComponent);
    fixture.componentRef.setInput('album', ALBUM_DETAILS_1);
    fixture.detectChanges();

    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap()
          .set('childAlbum1', toSuccess(CHILD_ALBUM_DETAILS_1))
          .set('childAlbum2', toSuccess(CHILD_ALBUM_DETAILS_2))
          .set('childAlbum3', toSuccess(CHILD_ALBUM_DETAILS_3)),
      },
    });
    store.refreshState();
    fixture.detectChanges();

    const subAlbums = fixture.nativeElement.querySelectorAll(
      '[data-testid="album"]',
    );
    expect(subAlbums.length).toEqual(3);
  });
});
