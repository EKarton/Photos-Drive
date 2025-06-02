import { inject, Injectable } from '@angular/core';
import { ComponentStore } from '@ngrx/component-store';
import { Store } from '@ngrx/store';
import { EMPTY, switchMap, tap, withLatestFrom } from 'rxjs';

import { authState } from '../../../../auth/store';
import {
  hasFailed,
  isPending,
  Result,
} from '../../../../shared/results/results';
import {
  ListMediaItemsInAlbumRequest,
  ListMediaItemsInAlbumResponse,
  ListMediaItemsInAlbumSortBy,
  MediaItem,
  WebApiService,
} from '../../../services/webapi.service';

export interface ImagesListState {
  albumId?: string;
  mediaItems: MediaItem[];
  nextPageToken?: string;
  isAtEndOfList: boolean;
}

export const INITIAL_STATE: ImagesListState = {
  albumId: undefined,
  mediaItems: [],
  nextPageToken: undefined,
  isAtEndOfList: false,
};

export interface LoadInitialPageRequest {
  albumId: string;
  pageSize?: number;
  sortBy?: ListMediaItemsInAlbumSortBy;
}

export interface LoadMoreMediaItemsRequest {
  pageSize?: number;
  sortBy?: ListMediaItemsInAlbumSortBy;
}

@Injectable()
export class ImagesListStore extends ComponentStore<ImagesListState> {
  private webApiService = inject(WebApiService);
  private store = inject(Store);

  constructor() {
    super(INITIAL_STATE);
  }

  readonly mediaItems = this.selectSignal((state) => state.mediaItems);

  private readonly setNewPage = this.updater(
    (
      _: ImagesListState,
      {
        request,
        response,
      }: {
        request: ListMediaItemsInAlbumRequest;
        response: Result<ListMediaItemsInAlbumResponse>;
      },
    ): ImagesListState => {
      if (isPending(response) || hasFailed(response)) {
        return {
          albumId: request.albumId,
          mediaItems: [],
          nextPageToken: undefined,
          isAtEndOfList: false,
        };
      } else {
        const newPage = response.data!;
        return {
          albumId: request.albumId,
          mediaItems: newPage.mediaItems,
          nextPageToken: newPage.nextPageToken,
          isAtEndOfList: newPage.nextPageToken === undefined,
        };
      }
    },
  );

  private readonly appendMediaItems = this.updater(
    (
      state: ImagesListState,
      response: Result<ListMediaItemsInAlbumResponse>,
    ): ImagesListState => {
      if (isPending(response) || hasFailed(response)) {
        return { ...state };
      } else {
        const newPage = response.data!;
        return {
          ...state,
          mediaItems: state.mediaItems.concat(...newPage.mediaItems),
          nextPageToken: newPage.nextPageToken,
          isAtEndOfList: newPage.nextPageToken === undefined,
        };
      }
    },
  );

  readonly loadInitialPage = this.effect<LoadInitialPageRequest>((request$) =>
    request$.pipe(
      switchMap((request) => {
        return this.store.select(authState.selectAuthToken).pipe(
          switchMap((accessToken) => {
            const apiRequest: ListMediaItemsInAlbumRequest = {
              albumId: request.albumId!,
              pageSize: request.pageSize,
              sortBy: request.sortBy,
              pageToken: undefined,
            };
            return this.webApiService
              .listMediaItemsInAlbum(accessToken, apiRequest)
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

  readonly loadMoreMediaItems = this.effect<LoadMoreMediaItemsRequest>(
    (request$) =>
      request$.pipe(
        withLatestFrom(this.state$),
        switchMap(([request, state]) => {
          if (state.isAtEndOfList) {
            return EMPTY;
          }

          return this.store.select(authState.selectAuthToken).pipe(
            switchMap((accessToken) => {
              const apiRequest: ListMediaItemsInAlbumRequest = {
                albumId: state.albumId!,
                pageSize: request.pageSize,
                sortBy: request.sortBy,
                pageToken: state.nextPageToken,
              };
              return this.webApiService
                .listMediaItemsInAlbum(accessToken, apiRequest)
                .pipe(tap((response) => this.appendMediaItems(response)));
            }),
          );
        }),
      ),
  );
}
