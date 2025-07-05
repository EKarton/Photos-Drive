import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';
import { of } from 'rxjs';

import { authState } from '../../../../auth/store';
import { toPending, toSuccess } from '../../../../shared/results/results';
import { Album } from '../../../services/types/album';
import { ListAlbumsResponse } from '../../../services/types/list-albums';
import { WebApiService } from '../../../services/webapi.service';
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
  let mockWebApiService: jasmine.SpyObj<WebApiService>;
  let store: MockStore;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', ['listAlbums']);

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
        { provide: WebApiService, useValue: mockWebApiService },
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
  });

  it('should show spinner and dispatch events correctly when album responses are still pending', () => {
    mockWebApiService.listAlbums.and.returnValue(
      of(toPending<ListAlbumsResponse>()),
    );
    const fixture = TestBed.createComponent(AlbumsListComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelector(
        '[data-testid="albums-list-spinner"]',
      ),
    ).toBeTruthy();
  });

  it('should render albums in cards view when successful', () => {
    store.setState({
      [albumsState.FEATURE_KEY]: {
        idToDetails: ImmutableMap()
          .set('album3', toSuccess(ALBUM_API_RESPONSE_PHOTOS))
          .set('album4', toSuccess(ALBUM_API_RESPONSE_2010))
          .set('album5', toSuccess(ALBUM_API_RESPONSE_2011)),
      },
    });
    store.refreshState();
    mockWebApiService.listAlbums.and.returnValue(
      of(
        toSuccess<ListAlbumsResponse>({
          albums: [ALBUM_API_RESPONSE_2010, ALBUM_API_RESPONSE_2011],
          nextPageToken: undefined,
        }),
      ),
    );

    const fixture = TestBed.createComponent(AlbumsListComponent);
    fixture.componentRef.setInput('albumId', 'album3');
    fixture.detectChanges();

    const albums = fixture.nativeElement.querySelectorAll(
      '[data-testid="album"]',
    );
    expect(albums.length).toBe(2);

    const names = fixture.nativeElement.querySelectorAll(
      '[data-testid="album-card-name"]',
    );
    expect(names[0].textContent).toContain('2010');
    expect(names[1].textContent).toContain('2011');
  });
});
