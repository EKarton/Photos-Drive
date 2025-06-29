import { inject, Injectable } from '@angular/core';
import { ComponentStore } from '@ngrx/component-store';
import { Store } from '@ngrx/store';
import { EMPTY, switchMap, tap, withLatestFrom } from 'rxjs';

import { authState } from '../../../auth/store';
import { hasFailed, isPending, Result } from '../../../shared/results/results';
import { Album } from '../../services/types/album';
import {
  ListAlbumsRequest,
  ListAlbumsResponse,
  ListAlbumsSortBy,
} from '../../services/types/list-albums';
import { WebApiService } from '../../services/webapi.service';

export interface AlbumsListState {
  albumId?: string;
  albums: Album[];
  nextPageToken?: string;
  sortBy?: ListAlbumsSortBy;
  isAtEndOfList: boolean;
}

export const INITIAL_STATE: AlbumsListState = {
  albumId: undefined,
  albums: [],
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

@Injectable()
export class AlbumsListStore extends ComponentStore<AlbumsListState> {
  private webApiService = inject(WebApiService);
  private store = inject(Store);

  constructor() {
    super(INITIAL_STATE);
  }

  readonly albums = this.selectSignal((state) => state.albums);

  private readonly clearState = this.updater(
    (): AlbumsListState => INITIAL_STATE,
  );

  private readonly setNewPage = this.updater(
    (
      _: AlbumsListState,
      {
        request,
        response,
      }: {
        request: ListAlbumsRequest;
        response: Result<ListAlbumsResponse>;
      },
    ): AlbumsListState => {
      if (isPending(response) || hasFailed(response)) {
        return {
          albumId: request.parentAlbumId,
          albums: [],
          nextPageToken: undefined,
          sortBy: request.sortBy,
          isAtEndOfList: false,
        };
      } else {
        const newPage = response.data!;
        return {
          albumId: request.parentAlbumId,
          albums: newPage.albums,
          nextPageToken: newPage.nextPageToken,
          isAtEndOfList: newPage.nextPageToken === undefined,
        };
      }
    },
  );

  private readonly appendAlbums = this.updater(
    (
      state: AlbumsListState,
      response: Result<ListAlbumsResponse>,
    ): AlbumsListState => {
      if (isPending(response) || hasFailed(response)) {
        return { ...state };
      } else {
        const newPage = response.data!;
        return {
          ...state,
          albums: state.albums.concat(...newPage.albums),
          nextPageToken: newPage.nextPageToken,
          isAtEndOfList: newPage.nextPageToken === undefined,
        };
      }
    },
  );

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
            return this.webApiService
              .listAlbums(accessToken, apiRequest)
              .pipe(
                tap((response) =>
                  this.setNewPage({ request: apiRequest, response }),
                ),
              );
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
            return this.webApiService
              .listAlbums(accessToken, apiRequest)
              .pipe(tap((response) => this.appendAlbums(response)));
          }),
        );
      }),
    ),
  );
}
