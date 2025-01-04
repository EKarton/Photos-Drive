import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { distinct, map, mergeMap } from 'rxjs/operators';

import { toResult } from '../../../shared/results/rxjs/toResult';
import {
  AlbumDetailsApiResponse,
  WebapiService,
} from '../../services/webapi.service';
import * as albumsActions from './albums.actions';

@Injectable()
export class AlbumsEffects {
  private readonly actions$ = inject(Actions);
  private readonly webApiService = inject(WebapiService);

  loadAlbumDetails$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(albumsActions.loadAlbumDetails),
      distinct((prop) => prop.albumId),
      mergeMap(({ albumId }) => {
        return this.webApiService.fetchAlbumDetails(albumId).pipe(
          toResult<AlbumDetailsApiResponse>(),
          map((result) =>
            albumsActions.loadAlbumDetailsResult({ albumId, result }),
          ),
        );
      }),
    );
  });
}
