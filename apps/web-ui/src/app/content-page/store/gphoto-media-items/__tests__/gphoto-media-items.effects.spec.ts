import { TestBed } from '@angular/core/testing';
import { Actions } from '@ngrx/effects';
import { provideMockActions } from '@ngrx/effects/testing';
import { Store } from '@ngrx/store';
import { of, throwError } from 'rxjs';

import { toFailure, toSuccess } from '../../../../shared/results/results';
import {
  GPhotosMediaItemDetailsApiResponse,
  WebApiService,
} from '../../../services/webapi.service';
import * as gPhotosMediaItemsActions from '../gphoto-media-items.actions';
import { GPhotosMediaItemsEffects } from '../gphoto-media-items.effects';

describe('GPhotosMediaItemsEffects', () => {
  let actions$: Actions;
  let effects: GPhotosMediaItemsEffects;
  let store: jasmine.SpyObj<Store>;
  let gPhotosApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        GPhotosMediaItemsEffects,
        provideMockActions(() => actions$),
        {
          provide: WebApiService,
          useValue: jasmine.createSpyObj<WebApiService>('WebApiService', [
            'fetchGPhotosMediaItemDetails',
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
      WebApiService,
    ) as jasmine.SpyObj<WebApiService>;
  });

  it('should dispatch loadGPhotosMediaItemDetailsResult on successful fetch', (done) => {
    const gPhotosMediaItemId = 'clientId:mediaItemId';
    const mockResponse: GPhotosMediaItemDetailsApiResponse = {
      baseUrl: '',
      mimeType: '',
      mediaMetadata: {
        creationTime: '',
        width: '0',
        height: '0',
      },
    };
    store.select.and.returnValue(of(toSuccess('mockToken')));
    gPhotosApiService.fetchGPhotosMediaItemDetails.and.returnValue(
      of(mockResponse),
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
    gPhotosApiService.fetchGPhotosMediaItemDetails.and.returnValue(
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
});
