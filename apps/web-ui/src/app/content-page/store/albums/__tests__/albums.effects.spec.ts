import { TestBed } from '@angular/core/testing';
import { provideMockActions } from '@ngrx/effects/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { authState } from '../../../../auth/store';
import { toFailure, toSuccess } from '../../../../shared/results/results';
import {
  AlbumDetailsApiResponse,
  WebApiService,
} from '../../../services/webapi.service';
import * as albumsActions from '../albums.actions';
import { AlbumsEffects } from '../albums.effects';

describe('AlbumsEffects', () => {
  let effects: AlbumsEffects;
  let webapiService: jasmine.SpyObj<WebApiService>;

  beforeEach(() => {
    const webapiServiceSpy = jasmine.createSpyObj('WebApiService', [
      'fetchAlbumDetails',
    ]);
    const actions$ = of(albumsActions.loadAlbumDetails({ albumId: '123' }));

    TestBed.configureTestingModule({
      providers: [
        AlbumsEffects,
        provideMockActions(() => actions$),
        { provide: WebApiService, useValue: webapiServiceSpy },
        provideMockStore({
          selectors: [
            {
              selector: authState.selectAuthToken,
              value: 'mockAccessToken123',
            },
          ],
        }),
      ],
    });

    effects = TestBed.inject(AlbumsEffects);
    webapiService = TestBed.inject(
      WebApiService,
    ) as jasmine.SpyObj<WebApiService>;
  });

  it('should fetch album details successfully', (done) => {
    const albumDetails = {
      id: '123',
      albumName: 'Test Album',
      childAlbumIds: [],
      mediaItemIds: [],
    };
    webapiService.fetchAlbumDetails.and.returnValue(
      of(toSuccess(albumDetails)),
    );

    effects.loadAlbumDetails$.subscribe((action) => {
      expect(action).toEqual(
        albumsActions.loadAlbumDetailsResult({
          albumId: '123',
          result: toSuccess(albumDetails),
        }),
      );
      done();
    });
  });

  it('should handle error when fetching album details', (done) => {
    const error = new Error('Test error');
    webapiService.fetchAlbumDetails.and.returnValue(
      of(toFailure<AlbumDetailsApiResponse>(error)),
    );

    effects.loadAlbumDetails$.subscribe((action) => {
      expect(action).toEqual(
        albumsActions.loadAlbumDetailsResult({
          albumId: '123',
          result: toFailure(error),
        }),
      );
      done();
    });
  });
});
