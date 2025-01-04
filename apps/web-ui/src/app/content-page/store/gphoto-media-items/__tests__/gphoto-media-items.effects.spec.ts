import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Actions } from '@ngrx/effects';
import { provideMockActions } from '@ngrx/effects/testing';
import { Action, Store } from '@ngrx/store';
import { BehaviorSubject, of, throwError } from 'rxjs';

import { toFailure, toSuccess } from '../../../../shared/results/results';
import {
  GhotosApiService,
  GPhotosMediaItemApiResponse,
} from '../../../services/gphotos-api.service';
import * as gPhotosClientsActions from '../../gphotos-clients/gphotos-clients.actions';
import * as gPhotosMediaItemsActions from '../gphoto-media-items.actions';
import { GPhotosMediaItemsEffects } from '../gphoto-media-items.effects';

describe('GPhotosMediaItemsEffects', () => {
  let actions$: Actions;
  let effects: GPhotosMediaItemsEffects;
  let store: jasmine.SpyObj<Store>;
  let gPhotosApiService: jasmine.SpyObj<GhotosApiService>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        GPhotosMediaItemsEffects,
        provideMockActions(() => actions$),
        {
          provide: GhotosApiService,
          useValue: jasmine.createSpyObj<GhotosApiService>('GhotosApiService', [
            'fetchMediaItemDetail',
          ]),
        },
        {
          provide: Store,
          useValue: jasmine.createSpyObj<Store>('Store', [
            'select',
            'dispatch',
          ]),
        },
      ],
    });

    effects = TestBed.inject(GPhotosMediaItemsEffects);
    store = TestBed.inject(Store) as jasmine.SpyObj<Store>;

    gPhotosApiService = TestBed.inject(
      GhotosApiService,
    ) as jasmine.SpyObj<GhotosApiService>;
  });

  it('should dispatch loadGPhotosMediaItemDetailsResult on successful fetch', (done) => {
    const gPhotosMediaItemId = 'clientId:mediaItemId';
    const mockResponse: GPhotosMediaItemApiResponse = {
      id: 'mediaItemId',
      description: '',
      productUrl: '',
      baseUrl: '',
      mimeType: '',
      mediaMetadata: {
        creationTime: '',
        width: 0,
        height: 0,
      },
      contributorInfo: {
        profilePictureBaseUrl: '',
        displayName: '',
      },
      filename: '',
    };
    store.select.and.returnValue(of(toSuccess('mockToken')));
    gPhotosApiService.fetchMediaItemDetail.and.returnValue(of(mockResponse));
    actions$ = new Actions(
      of(
        gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
          gPhotosMediaItemId,
        }),
      ),
    );

    effects.loadGPhotosMediaItemDetails$.subscribe((action) => {
      expect(action).toEqual(
        gPhotosMediaItemsActions.loadGPhotosMediaItemDetailsResult({
          gPhotosMediaItemId,
          result: toSuccess(mockResponse),
        }),
      );
      done();
    });
  });

  it('should handle error when fetching media item details', (done) => {
    const gPhotosMediaItemId = 'clientId:mediaItemId';
    store.select.and.returnValue(of(toSuccess('mockToken')));
    const error = new Error('Error fetching details');
    gPhotosApiService.fetchMediaItemDetail.and.returnValue(
      throwError(() => error),
    );
    actions$ = new Actions(
      of(
        gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
          gPhotosMediaItemId,
        }),
      ),
    );

    effects.loadGPhotosMediaItemDetails$.subscribe((action) => {
      expect(action).toEqual(
        gPhotosMediaItemsActions.loadGPhotosMediaItemDetailsResult({
          gPhotosMediaItemId,
          result: toFailure(error),
        }),
      );
      done();
    });
  });

  it('should refresh token when receiving a 401 error', (done) => {
    const storeSelectAccessTokens$ = new BehaviorSubject(
      toSuccess('mockToken'),
    );
    const gPhotosMediaItemId = 'clientId:mediaItemId';
    store.select.and.returnValue(storeSelectAccessTokens$);
    store.dispatch.and.callFake((action: Action) => {
      if (action.type === gPhotosClientsActions.refreshToken.type) {
        storeSelectAccessTokens$.next(toSuccess('mockNewToken'));
      }
      return {
        destroy: () => Object,
      };
    });
    const mockResponse: GPhotosMediaItemApiResponse = {
      id: 'mediaItemId',
      description: '',
      productUrl: '',
      baseUrl: '',
      mimeType: '',
      mediaMetadata: {
        creationTime: '',
        width: 0,
        height: 0,
      },
      contributorInfo: {
        profilePictureBaseUrl: '',
        displayName: '',
      },
      filename: '',
    };
    gPhotosApiService.fetchMediaItemDetail.and.callFake((token: string) => {
      if (token === 'mockNewToken') {
        return of(mockResponse);
      }
      return throwError(() => new HttpErrorResponse({ status: 401 }));
    });

    actions$ = new Actions(
      of(
        gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
          gPhotosMediaItemId,
        }),
      ),
    );

    effects.loadGPhotosMediaItemDetails$.subscribe((action) => {
      expect(store.dispatch).toHaveBeenCalledWith(
        gPhotosClientsActions.refreshToken({ clientId: 'clientId' }),
      );
      expect(action).toEqual(
        gPhotosMediaItemsActions.loadGPhotosMediaItemDetailsResult({
          gPhotosMediaItemId,
          result: toSuccess(mockResponse),
        }),
      );
      done();
    });
  });
});
