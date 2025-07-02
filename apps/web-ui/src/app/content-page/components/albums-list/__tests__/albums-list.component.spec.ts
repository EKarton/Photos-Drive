import { fakeAsync, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { authState } from '../../../../auth/store';
import {
  toFailure,
  toPending,
  toSuccess,
} from '../../../../shared/results/results';
import { Album } from '../../../services/types/album';
import { ListAlbumsResponse } from '../../../services/types/list-albums';
import { WebApiService } from '../../../services/webapi.service';
import { AlbumsListComponent } from '../albums-list.component';

const ALBUM_1: Album = {
  id: 'album1',
  albumName: 'Test Album',
  parentAlbumId: 'parent-id',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 1,
};

const ALBUM_2: Album = {
  id: 'album2',
  albumName: 'Test Album 2',
  parentAlbumId: 'parent-id',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 1,
};

const ALBUM_3: Album = {
  id: 'album3',
  albumName: 'Test Album 3',
  parentAlbumId: 'parent-id',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 1,
};

describe('AlbumsListComponent', () => {
  let mockWebApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(async () => {
    mockWebApiService = jasmine.createSpyObj('WebApiService', ['listAlbums']);

    await TestBed.configureTestingModule({
      imports: [AlbumsListComponent],
      providers: [
        provideRouter([]),
        provideMockStore({
          selectors: [
            {
              selector: authState.selectAuthToken,
              value: 'auth123',
            },
          ],
        }),
        { provide: WebApiService, useValue: mockWebApiService },
      ],
    }).compileComponents();
  });

  it('should render cards view by default with loading skeleton', () => {
    mockWebApiService.listAlbums.and.returnValue(
      of(toPending<ListAlbumsResponse>()),
    );

    const fixture = TestBed.createComponent(AlbumsListComponent);
    fixture.componentRef.setInput('albumId', 'album123');
    fixture.detectChanges();

    const skeleton = fixture.nativeElement.querySelector(
      '[data-testid="album-skeleton"]',
    );
    expect(skeleton).toBeTruthy();
  });

  it('should render error in cards view when loading fails', () => {
    mockWebApiService.listAlbums.and.returnValue(
      of(toFailure<ListAlbumsResponse>(new Error('Load failed'))),
    );

    const fixture = TestBed.createComponent(AlbumsListComponent);
    fixture.componentRef.setInput('albumId', 'album123');
    fixture.detectChanges();

    const error = fixture.nativeElement.querySelector(
      '[data-testid="albums-error"]',
    );
    expect(error?.textContent).toContain('Load failed');
  });

  it('should render albums in cards view when successful', fakeAsync(() => {
    mockWebApiService.listAlbums.and.returnValue(
      of(
        toSuccess<ListAlbumsResponse>({
          albums: [ALBUM_1, ALBUM_2],
          nextPageToken: undefined,
        }),
      ),
    );

    const fixture = TestBed.createComponent(AlbumsListComponent);
    fixture.componentRef.setInput('albumId', 'album123');
    fixture.detectChanges();

    const albums = fixture.nativeElement.querySelectorAll(
      '[data-testid="album"]',
    );
    expect(albums.length).toBe(2);

    const names = fixture.nativeElement.querySelectorAll(
      '[data-testid="album-card-name"]',
    );
    expect(names[0].textContent).toContain('Test Album');
  }));

  it('should switch to table view when checkbox is clicked', fakeAsync(() => {
    mockWebApiService.listAlbums.and.returnValue(
      of(
        toSuccess<ListAlbumsResponse>({
          albums: [ALBUM_1, ALBUM_2, ALBUM_3],
          nextPageToken: undefined,
        }),
      ),
    );

    const fixture = TestBed.createComponent(AlbumsListComponent);
    fixture.componentRef.setInput('albumId', 'album123');
    fixture.detectChanges();

    // Click toggle to switch to table view
    const toggle = fixture.nativeElement.querySelector(
      '[data-testid="table-view-checkbox"]',
    );
    toggle.click();
    fixture.detectChanges();

    const tableRows = fixture.nativeElement.querySelectorAll(
      '[data-testid="table-row-album"]',
    );
    expect(tableRows.length).toBe(3);
  }));
});
