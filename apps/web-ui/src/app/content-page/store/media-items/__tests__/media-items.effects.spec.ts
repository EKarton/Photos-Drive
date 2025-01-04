import { TestBed } from '@angular/core/testing';
import { Actions } from '@ngrx/effects';
import { provideMockActions } from '@ngrx/effects/testing';
import { of, throwError } from 'rxjs';

import { toFailure, toSuccess } from '../../../../shared/results/results';
import {
  MediaItemDetailsApiResponse,
  WebapiService,
} from '../../../services/webapi.service';
import * as mediaItemsActions from '../media-items.actions';
import { MediaItemsEffects } from '../media-items.effects';

describe('MediaItemsEffects', () => {
  let actions$: Actions;
  let effects: MediaItemsEffects;
  let webApiService: jasmine.SpyObj<WebapiService>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        MediaItemsEffects,
        provideMockActions(() => actions$),
        {
          provide: WebapiService,
          useValue: jasmine.createSpyObj('WebapiService', [
            'fetchMediaItemDetails',
          ]),
        },
      ],
    });

    effects = TestBed.inject(MediaItemsEffects);
    webApiService = TestBed.inject(
      WebapiService,
    ) as jasmine.SpyObj<WebapiService>;
  });

  it('should dispatch loadMediaItemDetailsResult on successful fetch', (done) => {
    const mediaItemId = 'item123';
    const mockResponse: MediaItemDetailsApiResponse = {
      id: 'item123',
      fileName: '',
      hashCode: '',
      gPhotosClientId: '',
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
