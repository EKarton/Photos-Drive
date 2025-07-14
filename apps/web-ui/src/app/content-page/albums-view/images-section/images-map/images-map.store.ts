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
import {
  GetMapTileHeatmapRequest,
  Heatmap,
} from '../../../services/types/heatmap';
import { GetMapTileRequest } from '../../../services/types/map-tile';
import { WebApiService } from '../../../services/webapi.service';
import { Tile, TileId } from './images-map-viewer/images-map-viewer.component';

export interface ImagesMapState {
  heatmapResult: Result<Heatmap>;
  numTiles: number;
  isFetchingTiles: boolean;
}

export const INITIAL_STATE: ImagesMapState = {
  heatmapResult: toPending(),
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

  readonly heatmapResult = this.selectSignal((state) => state.heatmapResult);

  readonly numTiles = this.selectSignal((state) => state.numTiles);

  readonly loadTiles = this.effect<LoadTilesRequest>((request$) =>
    request$.pipe(
      withLatestFrom(this.state$),
      switchMap(([request]) => {
        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            this.patchState({
              heatmapResult: toPending(),
              numTiles: request.tileIds.length,
              isFetchingTiles: true,
            });

            const apiRequests: GetMapTileHeatmapRequest[] = request.tileIds.map(
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
                    this.webApiService.getMapTileHeatmap(
                      accessToken,
                      apiRequest,
                    ),
                  MAX_CONCURRENCY,
                ),
                toArray(),
                map((results) =>
                  combineResults(results, (heatmaps) => heatmaps),
                ),
              )
              .pipe(
                tap((result: Result<Heatmap[]>) => {
                  this.patchState({
                    heatmapResult: mapResult(result, (heatmaps) => ({
                      entries: heatmaps.map((h) => h.entries).flat(),
                    })),
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
