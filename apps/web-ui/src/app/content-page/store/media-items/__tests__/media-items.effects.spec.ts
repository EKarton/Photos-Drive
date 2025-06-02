import { TestBed } from '@angular/core/testing';
import { Actions } from '@ngrx/effects';
import { provideMockActions } from '@ngrx/effects/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { of, throwError } from 'rxjs';

import { authState } from '../../../../auth/store';
import { toFailure, toSuccess } from '../../../../shared/results/results';
import {
  MediaItemDetailsApiResponse,
  WebApiService,
} from '../../../services/webapi.service';
import * as mediaItemsActions from '../media-items.actions';
import { MediaItemsEffects } from '../media-items.effects';

describe('MediaItemsEffects', () => {
  let actions$: Actions;
  let effects: MediaItemsEffects;
  let webApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        MediaItemsEffects,
        provideMockActions(() => actions$),
        {
          provide: WebApiService,
          useValue: jasmine.createSpyObj('WebApiService', [
            'fetchMediaItemDetails',
          ]),
        },
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

    effects = TestBed.inject(MediaItemsEffects);
    webApiService = TestBed.inject(
      WebApiService,
    ) as jasmine.SpyObj<WebApiService>;
  });

  it('should dispatch loadMediaItemDetailsResult on successful fetch', (done) => {
    const mediaItemId = 'item123';
    const mockResponse: MediaItemDetailsApiResponse = {
      id: 'item123',
      fileName: '',
      hashCode: '',
      gPhotosMediaItemId: '',
    };
    actions$ = new Actions(
      of(mediaItemsActions.loadMediaItemDetails({ mediaItemId })),
    );
    webApiService.fetchMediaItemDetails.and.returnValue(of(mockResponse));

    effects.loadMediaItemDetails$.subscribe((action) => {
      expect(action).toEqual(
        mediaItemsActions.loadMediaItemDetailsResult({
          mediaItemId,
          result: toSuccess(mockResponse),
        }),
      );
      done();
    });
  });

  it('should handle error when fetching media item details', (done) => {
    const mediaItemId = 'item123';
    actions$ = new Actions(
      of(mediaItemsActions.loadMediaItemDetails({ mediaItemId })),
    );
    const error = new Error('Error fetching details');
    webApiService.fetchMediaItemDetails.and.returnValue(
      throwError(() => error),
    );

    effects.loadMediaItemDetails$.subscribe((action) => {
      expect(action).toEqual(
        mediaItemsActions.loadMediaItemDetailsResult({
          mediaItemId,
          result: toFailure(error),
        }),
      );
      done();
    });
  });
});
