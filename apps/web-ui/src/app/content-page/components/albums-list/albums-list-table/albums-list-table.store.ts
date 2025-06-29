import { inject, Injectable } from '@angular/core';
import { ComponentStore } from '@ngrx/component-store';
import { Store } from '@ngrx/store';
import { EMPTY, switchMap, tap, withLatestFrom } from 'rxjs';

import { authState } from '../../../../auth/store';
import {
  hasFailed,
  hasSucceed,
  isPending,
  Result,
  toFailure,
  toPending,
  toSuccess,
} from '../../../../shared/results/results';
import { Album } from '../../../services/types/album';
import {
  ListAlbumsRequest,
  ListAlbumsResponse,
  ListAlbumsSortBy,
} from '../../../services/types/list-albums';
import { WebApiService } from '../../../services/webapi.service';
import { addAlbum } from '../../../store/albums/albums.actions';

export interface AlbumsListTableState {
  albumId?: string;
  albumsResult: Result<Album[]>;
  nextPageToken?: string;
  sortBy?: ListAlbumsSortBy;
  isAtEndOfList: boolean;
}

export const INITIAL_STATE: AlbumsListTableState = {
  albumId: undefined,
  albumsResult: toFailure(new Error('Random error happened')),
  nextPageToken: undefined,
  sortBy: undefined,
  isAtEndOfList: false,
};

export interface LoadInitialPageRequest {
  albumId: string;
  pageSize?: number;
  sortBy?: ListAlbumsSortBy;
}

export interface LoadMoreAlbumsRequest {
  pageSize?: number;
}

export interface GoToNextPageRequest {}

@Injectable()
export class AlbumsListTableStore extends ComponentStore<AlbumsListTableState> {
  private webApiService = inject(WebApiService);
  private store = inject(Store);

  constructor() {
    super(INITIAL_STATE);
  }

  readonly albumsResult = this.selectSignal((state) => state.albumsResult);

  private readonly clearState = this.updater(
    (): AlbumsListTableState => ({ ...INITIAL_STATE }),
  );

  private readonly setNewPage = this.updater(
    (
      _: AlbumsListTableState,
      {
        request,
        response,
      }: {
        request: ListAlbumsRequest;
        response: Result<ListAlbumsResponse>;
      },
    ): AlbumsListTableState => {
      if (isPending(response)) {
        return {
          albumId: request.parentAlbumId,
          albumsResult: toPending(),
          nextPageToken: undefined,
          sortBy: request.sortBy,
          isAtEndOfList: false,
        };
      } else if (hasFailed(response)) {
        return {
          albumId: request.parentAlbumId,
          albumsResult: toFailure(response.error!),
          nextPageToken: undefined,
          sortBy: request.sortBy,
          isAtEndOfList: false,
        };
      } else {
        const newPage = response.data!;
        return {
          albumId: request.parentAlbumId,
          albumsResult: toSuccess(newPage.albums),
          nextPageToken: newPage.nextPageToken,
          isAtEndOfList: newPage.nextPageToken === undefined,
        };
      }
    },
  );

  private readonly appendAlbums = this.updater(
    (
      state: AlbumsListTableState,
      response: Result<ListAlbumsResponse>,
    ): AlbumsListTableState => {
      if (isPending(response) || hasFailed(response)) {
        return { ...state };
      } else {
        const newPage = response.data!;
        return {
          ...state,
          albumsResult: hasSucceed(state.albumsResult)
            ? toSuccess(state.albumsResult.data!.concat(...newPage.albums))
            : toSuccess(newPage.albums),
          nextPageToken: newPage.nextPageToken,
          isAtEndOfList: newPage.nextPageToken === undefined,
        };
      }
    },
  );

  private saveAlbumsToStore(response: ListAlbumsResponse) {
    response.albums.forEach((album) =>
      this.store.dispatch(addAlbum({ album })),
    );
  }

  readonly loadInitialPage = this.effect<LoadInitialPageRequest>((request$) =>
    request$.pipe(
      switchMap((request) => {
        this.clearState();

        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            const apiRequest: ListAlbumsRequest = {
              parentAlbumId: request.albumId!,
              pageSize: request.pageSize,
              sortBy: request.sortBy,
              pageToken: undefined,
            };
            return this.webApiService.listAlbums(accessToken, apiRequest).pipe(
              tap((response) => {
                this.setNewPage({ request: apiRequest, response });

                if (hasSucceed(response)) {
                  this.saveAlbumsToStore(response.data!);
                }
              }),
            );
          }),
        );
      }),
    ),
  );

  readonly goToNextPage = this.effect<GoToNextPageRequest>((request$) =>
    request$.pipe(
      withLatestFrom(this.state$),
      switchMap(([request, state]) => {
        if (state.isAtEndOfList) {
          return EMPTY;
        }

        const apiRequest: ListAlbumsRequest = {
          parentAlbumId: state.albumId!,
          pageSize: request.pageSize,
          sortBy: state.sortBy,
          pageToken: state.nextPageToken,
        };
        return this.webApiService.listAlbums(accessToken, apiRequest).pipe(
          tap((response) => {
            this.appendAlbums(response);
            if (hasSucceed(response)) {
              this.saveAlbumsToStore(response.data!);
            }
          }),
        );
      }),
    ),
  );

  readonly loadMoreAlbums = this.effect<LoadMoreAlbumsRequest>((request$) =>
    request$.pipe(
      withLatestFrom(this.state$),
      switchMap(([request, state]) => {
        if (state.isAtEndOfList) {
          return EMPTY;
        }

        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            const apiRequest: ListAlbumsRequest = {
              parentAlbumId: state.albumId!,
              pageSize: request.pageSize,
              sortBy: state.sortBy,
              pageToken: state.nextPageToken,
            };
            return this.webApiService.listAlbums(accessToken, apiRequest).pipe(
              tap((response) => {
                this.appendAlbums(response);
                if (hasSucceed(response)) {
                  this.saveAlbumsToStore(response.data!);
                }
              }),
            );
          }),
        );
      }),
    ),
  );
}
