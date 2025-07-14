import { inject, Injectable } from '@angular/core';
import { ComponentStore } from '@ngrx/component-store';
import { Store } from '@ngrx/store';
import {
  from,
  map,
  mergeMap,
  of,
  switchMap,
  tap,
  toArray,
  withLatestFrom,
} from 'rxjs';

import { authState } from '../../../../auth/store';
import {
  Result,
  toPending,
  toSuccess,
} from '../../../../shared/results/results';
import { mapResultRxJs } from '../../../../shared/results/rxjs/mapResultRxJs';
import { switchMapResultToResultRxJs } from '../../../../shared/results/rxjs/switchMapResultToResultRxJs';
import { combineResults } from '../../../../shared/results/utils/combineResults';
import { mapResult } from '../../../../shared/results/utils/mapResult';
import { takeSuccessfulDataOrElse } from '../../../../shared/results/utils/takeSuccessfulDataOrElse';
import { GetMapTileRequest } from '../../../services/types/map-tile';
import { WebApiService } from '../../../services/webapi.service';
import { Tile, TileId } from './images-map-viewer/images-map-viewer.component';

export interface ImagesMapState {
  tilesResult: Result<Tile[]>;
  numTiles: number;
  isFetchingTiles: boolean;
}

export const INITIAL_STATE: ImagesMapState = {
  tilesResult: toPending(),
  numTiles: 0,
  isFetchingTiles: false,
};

export interface LoadTilesRequest {
  tileIds: TileId[];
  albumId: string;
}

export const DEFAULT_DELAY_BETWEEN_PAGES = 150;

export const MAX_CONCURRENCY = 4;

@Injectable()
export class ImagesMapStore extends ComponentStore<ImagesMapState> {
  private webApiService = inject(WebApiService);
  private store = inject(Store);

  constructor() {
    super(INITIAL_STATE);
  }

  readonly isFetchingTiles = this.selectSignal(
    (state) => state.isFetchingTiles,
  );
  readonly tilesResult = this.selectSignal((state) => state.tilesResult);

  readonly numTiles = this.selectSignal((state) => state.numTiles);

  readonly loadTiles = this.effect<LoadTilesRequest>((request$) =>
    request$.pipe(
      withLatestFrom(this.state$),
      switchMap(([request]) => {
        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            this.patchState({
              tilesResult: toPending(),
              numTiles: request.tileIds.length,
              isFetchingTiles: true,
            });

            const apiRequests: GetMapTileRequest[] = request.tileIds.map(
              (tileId) => ({
                x: tileId.x,
                y: tileId.y,
                z: tileId.z,
                albumId: request.albumId,
              }),
            );

            return from(apiRequests)
              .pipe(
                mergeMap(
                  (apiRequest) =>
                    this.webApiService.getMapTile(accessToken, apiRequest).pipe(
                      switchMapResultToResultRxJs((response) => {
                        if (!response.mediaItemId) {
                          return of(
                            toSuccess({
                              tileId: {
                                x: apiRequest.x,
                                y: apiRequest.y,
                                z: apiRequest.z,
                              },
                              chosenMediaItem: undefined,
                              numMediaItems: 0,
                            }),
                          );
                        }

                        return this.webApiService
                          .getMediaItem(accessToken, response.mediaItemId)
                          .pipe(
                            mapResultRxJs((mediaItem) => {
                              const tile: Tile = {
                                tileId: {
                                  x: apiRequest.x,
                                  y: apiRequest.y,
                                  z: apiRequest.z,
                                },
                                chosenMediaItem: mediaItem,
                                numMediaItems: response.numMediaItems,
                              };
                              return tile;
                            }),
                          );
                      }),
                    ),
                  MAX_CONCURRENCY,
                ),
                toArray(),
                map((results) => combineResults(results, (tiles) => tiles)),
              )
              .pipe(
                tap((result: Result<Tile[]>) => {
                  this.patchState({
                    tilesResult: result,
                    isFetchingTiles: takeSuccessfulDataOrElse(
                      mapResult(result, () => false),
                      true,
                    ),
                  });
                }),
              );
          }),
        );
      }),
    ),
  );
}
