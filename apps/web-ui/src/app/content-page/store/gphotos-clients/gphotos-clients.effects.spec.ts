import { TestBed } from '@angular/core/testing';
import { Actions } from '@ngrx/effects';
import { provideMockActions } from '@ngrx/effects/testing';
import { of, throwError } from 'rxjs';

import { toFailure, toSuccess } from '../../../shared/results/results';
import {
  GPhotosClientsListApiResponse,
  RefreshTokenApiResponse,
  WebApiService,
} from '../../services/webapi.service';
import * as gPhotosClientsActions from './gphotos-clients.actions';
import { GPhotosClientsEffects } from './gphotos-clients.effects';

describe('GPhotosClientsEffects', () => {
  let actions$: Actions;
  let effects: GPhotosClientsEffects;
  let webApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        GPhotosClientsEffects,
        provideMockActions(() => actions$),
        {
          provide: WebApiService,
          useValue: jasmine.createSpyObj('WebapiService', [
            'fetchGPhotosClients',
            'refreshGPhotoClientAccessToken',
          ]),
        },
      ],
    });

    effects = TestBed.inject(GPhotosClientsEffects);
    webApiService = TestBed.inject(
      WebApiService,
    ) as jasmine.SpyObj<WebApiService>;
  });

  it('should dispatch loadGPhotoClientsResults on successful fetch of GPhotos clients', (done) => {
    const mockResponse: GPhotosClientsListApiResponse = {
      gphotoClients: [],
    };
    actions$ = new Actions(of(gPhotosClientsActions.loadGPhotoClients()));
    webApiService.fetchGPhotosClients.and.returnValue(of(mockResponse));

    effects.loadGPhotosClients$.subscribe((action) => {
      expect(action).toEqual(
        gPhotosClientsActions.loadGPhotoClientsResults({
          result: toSuccess(mockResponse),
        }),
      );
      done();
    });
  });

  it('should handle error when fetching GPhotos clients', (done) => {
    actions$ = new Actions(of(gPhotosClientsActions.loadGPhotoClients()));
    const error = new Error('Error fetching clients');
    webApiService.fetchGPhotosClients.and.returnValue(throwError(() => error));

    effects.loadGPhotosClients$.subscribe((action) => {
      expect(action).toEqual(
        gPhotosClientsActions.loadGPhotoClientsResults({
          result: toFailure(error),
        }),
      );
      done();
    });
  });

  it('should dispatch loadRefreshTokenResult on successful refresh token', (done) => {
    const clientId = 'client123';
    const mockResponse: RefreshTokenApiResponse = {
      newToken: 'newAccessToken',
    };
    webApiService.refreshGPhotoClientAccessToken.and.returnValue(
      of(mockResponse),
    );
    actions$ = new Actions(
      of(gPhotosClientsActions.refreshToken({ clientId })),
    );

    effects.loadRefreshToken$.subscribe((action) => {
      expect(action).toEqual(
        gPhotosClientsActions.loadRefreshTokenResult({
          clientId,
          result: toSuccess(mockResponse),
        }),
      );
      done();
    });
  });

  it('should handle error when refreshing token', (done) => {
    const clientId = 'client123';
    actions$ = new Actions(
      of(gPhotosClientsActions.refreshToken({ clientId })),
    );
    const error = new Error('Error refreshing token');
    webApiService.refreshGPhotoClientAccessToken.and.returnValue(
      throwError(() => error),
    );

    effects.loadRefreshToken$.subscribe((action) => {
      expect(action).toEqual(
        gPhotosClientsActions.loadRefreshTokenResult({
          clientId,
          result: toFailure(error),
        }),
      );
      done();
    });
  });
});
