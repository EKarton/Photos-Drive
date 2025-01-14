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
  combineLatest,
  distinctUntilChanged,
  map,
  Observable,
  of,
  Subscription,
  switchMap,
} from 'rxjs';

import { WINDOW } from '../../../app.tokens';
import { zip } from '../../../shared/lists/zip';
import { HasFailedPipe } from '../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../shared/results/pipes/is-pending.pipe';
import { Result, toPending, toSuccess } from '../../../shared/results/results';
import { filterOnlySuccess } from '../../../shared/results/rxjs/filterOnlySuccess';
import { switchMapResultToResultRxJs } from '../../../shared/results/rxjs/switchMapResultToResultRxJs';
import { combineResults } from '../../../shared/results/utils/combineResults';
import { combineResults2 } from '../../../shared/results/utils/combineResults2';
import { GPhotosMediaItemDetails } from '../../services/gphotos-api.service';
import { Album, MediaItem } from '../../services/webapi.service';
import { albumsActions, albumsState } from '../../store/albums';
import {
  gPhotosMediaItemsActions,
  gPhotosMediaItemsState,
} from '../../store/gphoto-media-items';
import { mediaItemsActions, mediaItemsState } from '../../store/media-items';
import { mediaViewerActions } from '../../store/media-viewer';
import {
  ImageData,
  ImagesListComponent,
} from './images-list/images-list.component';

@Component({
  standalone: true,
  selector: 'app-content-images-section',
  imports: [CommonModule, IsPendingPipe, HasFailedPipe, ImagesListComponent],
  templateUrl: './images-section.component.html',
})
export class ImagesSectionComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly window = inject(WINDOW);
  private subscription = new Subscription();

  readonly albumId = input.required<string>();
  private readonly albumId$ = toObservable(this.albumId);

  private readonly albumResult$: Observable<Result<Album>> = this.albumId$.pipe(
    switchMap((albumId) =>
      this.store.select(albumsState.selectAlbumDetailsById(albumId)),
    ),
  );

  private readonly mediaItemsResult$: Observable<Result<MediaItem[]>> =
    this.albumResult$.pipe(
      switchMapResultToResultRxJs((album: Album) => {
        const mediaItems$ = album.mediaItemIds.map((id) =>
          this.store.select(mediaItemsState.selectMediaItemDetailsById(id)),
        );

        if (mediaItems$.length === 0) {
          return of(toSuccess<MediaItem[]>([]));
        }

        return combineLatest(mediaItems$).pipe(
          map((results) => combineResults(results, (mediaItems) => mediaItems)),
        );
      }),
    );

  private readonly gMediaItemsResult$: Observable<
    Result<GPhotosMediaItemDetails[]>
  > = this.mediaItemsResult$.pipe(
    switchMapResultToResultRxJs((mediaItems: MediaItem[]) => {
      const gMediaItems$ = mediaItems.map((mediaItem) => {
        return this.store.select(
          gPhotosMediaItemsState.selectGPhotosMediaItemById(
            mediaItem.gPhotosMediaItemId,
          ),
        );
      });

      if (gMediaItems$.length === 0) {
        return of(toSuccess<GPhotosMediaItemDetails[]>([]));
      }

      return combineLatest(gMediaItems$).pipe(
        map((results) => combineResults(results, (gMediaItems) => gMediaItems)),
      );
    }),
  );

  private readonly mediaItems$: Observable<Result<ImageData[]>> = combineLatest(
    [this.mediaItemsResult$, this.gMediaItemsResult$],
  ).pipe(
    map(([mediaItemsListResult, gMediaItemsListResult]) => {
      return combineResults2(
        mediaItemsListResult,
        gMediaItemsListResult,
        (mediaItems, gMediaItems) => {
          return zip(mediaItems, gMediaItems).map(
            ([mediaItem, gMediaItem]) => ({
              id: mediaItem.id,
              baseUrl: gMediaItem.baseUrl,
              width: gMediaItem.mediaMetadata.width,
              height: gMediaItem.mediaMetadata.height,
              fileName: mediaItem.fileName,
              onClick: (event: MouseEvent) => {
                if (event.ctrlKey) {
                  this.openImageInNewTab(gMediaItem);
                } else {
                  this.openImageInDialog(mediaItem.id);
                }
              },
              onKeyDown: (event: KeyboardEvent) => {
                if (event.ctrlKey && event.key === 'Enter') {
                  event.preventDefault();
                  this.openImageInNewTab(gMediaItem);
                } else if (event.key === 'Enter') {
                  event.preventDefault();
                  this.openImageInDialog(mediaItem.id);
                }
              },
            }),
          );
        },
      );
    }),
  );

  private openImageInNewTab(detail: GPhotosMediaItemDetails) {
    const width = detail.mediaMetadata.width;
    const height = detail.mediaMetadata.height;
    const fullPageUrl = `${detail.baseUrl}=w${width}-h${height}`;
    this.window.open(fullPageUrl, '_blank');
  }

  private openImageInDialog(mediaItemId: string) {
    this.store.dispatch(
      mediaViewerActions.openMediaViewer({
        request: { mediaItemId },
      }),
    );
  }

  readonly imagesResult: Signal<Result<ImageData[]>> = (() => {
    return toSignal(this.mediaItems$, {
      initialValue: toPending<ImageData[]>(),
    });
  })();

  ngOnInit(): void {
    // Fetch the album details
    this.subscription.add(
      this.albumId$.subscribe((albumId) => {
        this.store.dispatch(albumsActions.loadAlbumDetails({ albumId }));
      }),
    );

    // Fetch the list of media items.
    this.subscription.add(
      this.albumResult$.pipe(filterOnlySuccess()).subscribe((album) => {
        album.mediaItemIds.forEach((mediaItemId) => {
          this.store.dispatch(
            mediaItemsActions.loadMediaItemDetails({ mediaItemId }),
          );
        });
      }),
    );

    // Fetch the list of media items from Google Photos.
    this.subscription.add(
      this.mediaItemsResult$
        .pipe(filterOnlySuccess(), distinctUntilChanged())
        .subscribe((mediaItems) => {
          mediaItems.forEach((mediaItem) => {
            this.store.dispatch(
              gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
                gPhotosMediaItemId: mediaItem.gPhotosMediaItemId,
              }),
            );
          });
        }),
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
