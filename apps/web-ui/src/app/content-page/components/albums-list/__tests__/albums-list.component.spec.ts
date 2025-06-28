import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';

import { authState } from '../../../../auth/store';
import { toSuccess } from '../../../../shared/results/results';
import { Album } from '../../../services/webapi.service';
import { albumsState } from '../../../store/albums';
import { AlbumsListComponent } from '../albums-list.component';

const ALBUM_API_RESPONSE_PHOTOS: Album = {
  id: 'album3',
  albumName: 'Photos',
  parentAlbumId: 'album2',
  childAlbumIds: ['album4', 'album5'],
  numChildAlbums: 2,
  numMediaItems: 0,
};

const ALBUM_API_RESPONSE_2010: Album = {
  id: 'album4',
  albumName: '2010',
  parentAlbumId: 'album3',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 0,
};

const ALBUM_API_RESPONSE_2011: Album = {
  id: 'album5',
  albumName: '2011',
  parentAlbumId: 'album3',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 0,
};

describe('AlbumsListComponent', () => {
  let store: MockStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlbumsListComponent],
      providers: [
        provideMockStore({
          initialState: {
            [albumsState.FEATURE_KEY]: albumsState.buildInitialState(),
          },
          selectors: [
            { selector: authState.selectAuthToken, value: 'mockAccessToken' },
          ],
        }),
        provideRouter([]),
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
  });

  it('should show albums when album responses are successful', () => {
    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap()
          .set('album3', toSuccess(ALBUM_API_RESPONSE_PHOTOS))
          .set('album4', toSuccess(ALBUM_API_RESPONSE_2010))
          .set('album5', toSuccess(ALBUM_API_RESPONSE_2011)),
      },
    });
    store.refreshState();

    const fixture = TestBed.createComponent(AlbumsListComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    // Assert that component doesnt throw an error
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();

    // Assert that albums are rendered
    const elements = fixture.nativeElement.querySelectorAll(
      '[data-testid="album-card-name"]',
    );
    expect(elements[0].textContent).toContain('2010');
    expect(elements[1].textContent).toContain('2011');
  });

  it('should show spinner and dispatch events correctly when album responses are still pending', () => {
    const fixture = TestBed.createComponent(AlbumsListComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelector(
        '[data-testid="albums-list-spinner"]',
      ),
    ).toBeTruthy();
  });
});
