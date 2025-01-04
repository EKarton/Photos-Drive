import { TestBed } from '@angular/core/testing';
import { provideMockActions } from '@ngrx/effects/testing';
import { of, throwError } from 'rxjs';

import { toFailure, toSuccess } from '../../../../shared/results/results';
import { WebapiService } from '../../../services/webapi.service';
import * as albumsActions from '../albums.actions';
import { AlbumsEffects } from '../albums.effects';

describe('AlbumsEffects', () => {
  let effects: AlbumsEffects;
  let webapiService: jasmine.SpyObj<WebapiService>;

  beforeEach(() => {
    const webapiServiceSpy = jasmine.createSpyObj('WebapiService', [
      'fetchAlbumDetails',
    ]);
    const actions$ = of(albumsActions.loadAlbumDetails({ albumId: '123' }));

    TestBed.configureTestingModule({
      providers: [
        AlbumsEffects,
        provideMockActions(() => actions$),
        { provide: WebapiService, useValue: webapiServiceSpy },
      ],
    });

    effects = TestBed.inject(AlbumsEffects);
    webapiService = TestBed.inject(
      WebapiService,
    ) as jasmine.SpyObj<WebapiService>;
  });

  it('should fetch album details successfully', (done) => {
    const albumDetails = {
      id: '123',
      albumName: 'Test Album',
      childAlbumIds: [],
      mediaItemIds: [],
    };
    webapiService.fetchAlbumDetails.and.returnValue(of(albumDetails));

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
    webapiService.fetchAlbumDetails.and.returnValue(throwError(() => error));

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
