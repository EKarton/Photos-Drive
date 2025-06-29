import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { concatLatestFrom } from '@ngrx/operators';
import { Store } from '@ngrx/store';
import { distinct, filter, map, mergeMap, switchMap } from 'rxjs/operators';

import { authState } from '../../../auth/store';
import { WebApiService } from '../../services/webapi.service';
import * as albumsActions from './albums.actions';
import { selectAlbumsState } from './albums.state';

@Injectable()
export class AlbumsEffects {
  private readonly store = inject(Store);
  private readonly actions$ = inject(Actions);
  private readonly webApiService = inject(WebApiService);

  loadAlbumDetails$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(albumsActions.loadAlbumDetails),
      distinct((prop) => prop.albumId),
      concatLatestFrom(() => this.store.select(selectAlbumsState)),
      filter(([action, albumsState]) => {
        return !albumsState.idToDetails.has(action.albumId);
      }),
      mergeMap(([{ albumId }]) => {
        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            return this.webApiService
              .getAlbum(accessToken, albumId)
              .pipe(
                map((result) =>
                  albumsActions.addAlbumResult({ albumId, result }),
                ),
              );
          }),
        );
      }),
    );
  });
}
