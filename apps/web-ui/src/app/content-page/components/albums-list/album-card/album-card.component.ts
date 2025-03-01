import { CommonModule } from '@angular/common';
import {
  Component,
  inject,
  input,
  OnDestroy,
  OnInit,
  Signal,
} from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { Store } from '@ngrx/store';
import {
  BehaviorSubject,
  filter,
  Observable,
  of,
  Subscription,
  switchMap,
} from 'rxjs';

import { HasFailedPipe } from '../../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../../shared/results/pipes/is-pending.pipe';
import {
  Result,
  toPending,
  toSuccess,
} from '../../../../shared/results/results';
import { filterOnlySuccess } from '../../../../shared/results/rxjs/filterOnlySuccess';
import { mapResultRxJs } from '../../../../shared/results/rxjs/mapResultRxJs';
import { switchMapResultToResultRxJs } from '../../../../shared/results/rxjs/switchMapResultToResultRxJs';
import {
  Album,
  GPhotosMediaItem,
  MediaItem,
} from '../../../services/webapi.service';
import { albumsActions, albumsState } from '../../../store/albums';
import {
  gPhotosMediaItemsActions,
  gPhotosMediaItemsState,
} from '../../../store/gphoto-media-items';
import { mediaItemsActions, mediaItemsState } from '../../../store/media-items';

@Component({
  selector: 'app-content-album-card',
  imports: [CommonModule, IsPendingPipe, HasFailedPipe],
  templateUrl: './album-card.component.html',
  styleUrl: './album-card.component.scss',
})
export class AlbumCardComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly subscription = new Subscription();

  readonly albumId = input.required<string>();
  private readonly albumId$ = toObservable(this.albumId);

  private readonly albumDetails$ = this.albumId$.pipe(
    switchMap((albumId) =>
      this.store.select(albumsState.selectAlbumDetailsById(albumId)),
    ),
  );
  readonly albumDetails: Signal<Result<Album>> = toSignal(this.albumDetails$, {
    initialValue: toPending<Album>(),
  });

  private readonly chosenMediaItemId$ = new BehaviorSubject<
    Result<string | null>
  >(toPending());

  private readonly chosenMediaItem$: Observable<Result<MediaItem | null>> =
    this.chosenMediaItemId$.pipe(
      switchMapResultToResultRxJs((mediaItemId: string | null) => {
        if (!mediaItemId) {
          return of(toSuccess(null));
        }

        return this.store.select(
          mediaItemsState.selectMediaItemDetailsById(mediaItemId),
        );
      }),
    );
  private readonly chosenGMediaItem$: Observable<
    Result<GPhotosMediaItem | null>
  > = this.chosenMediaItem$.pipe(
    switchMapResultToResultRxJs((mediaItem: MediaItem | null) => {
      if (!mediaItem) {
        return of(toSuccess(null));
      }

      return this.store.select(
        gPhotosMediaItemsState.selectGPhotosMediaItemById(
          mediaItem.gPhotosMediaItemId,
        ),
      );
    }),
  );
  private readonly chosenAlbumImageUrl$: Observable<Result<string>> =
    this.chosenGMediaItem$.pipe(
      mapResultRxJs((image: GPhotosMediaItem | null) => {
        if (!image) {
          return '/assets/404-page/sad-cat.png';
        }

        return image.baseUrl || '/assets/404-page/sad-cat.png';
      }),
    );
  readonly chosenAlbumImageUrl: Signal<Result<string>> = toSignal(
    this.chosenAlbumImageUrl$,
    {
      initialValue: toPending<string>(),
    },
  );

  ngOnInit(): void {
    this.subscription.add(
      this.albumId$.subscribe((albumId) => {
        this.store.dispatch(albumsActions.loadAlbumDetails({ albumId }));
      }),
    );

    this.subscription.add(
      this.albumDetails$.pipe(filterOnlySuccess()).subscribe((album) => {
        if (album.mediaItemIds.length === 0) {
          this.chosenMediaItemId$.next(toSuccess(null));
        }

        const randomIndex = Math.floor(
          Math.random() * album.mediaItemIds.length,
        );
        this.chosenMediaItemId$.next(
          toSuccess(album.mediaItemIds[randomIndex]),
        );
      }),
    );

    this.subscription.add(
      this.chosenMediaItemId$
        .pipe(
          filterOnlySuccess(),
          filter((id) => id !== null),
        )
        .subscribe((mediaItemId: string) => {
          console.log('mDispatch', mediaItemId);
          this.store.dispatch(
            mediaItemsActions.loadMediaItemDetails({ mediaItemId }),
          );
        }),
    );

    this.subscription.add(
      this.chosenMediaItem$
        .pipe(
          filterOnlySuccess(),
          filter((mediaItem) => mediaItem !== null),
        )
        .subscribe((mediaItem: MediaItem) => {
          console.log('gDispatch', mediaItem.gPhotosMediaItemId);
          this.store.dispatch(
            gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
              gMediaItemId: mediaItem.gPhotosMediaItemId,
            }),
          );
        }),
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
