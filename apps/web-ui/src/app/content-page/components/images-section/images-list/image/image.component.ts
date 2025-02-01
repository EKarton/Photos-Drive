import {
  Component,
  inject,
  input,
  OnDestroy,
  OnInit,
  output,
  Signal,
} from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { Store } from '@ngrx/store';
import { InViewportModule } from 'ng-in-viewport';
import {
  BehaviorSubject,
  combineLatest,
  distinctUntilChanged,
  filter,
  map,
  Observable,
  Subscription,
  switchMap,
} from 'rxjs';

import { WINDOW } from '../../../../../app.tokens';
import { HasFailedPipe } from '../../../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../../../shared/results/pipes/is-pending.pipe';
import { Result, toPending } from '../../../../../shared/results/results';
import { filterOnlySuccess } from '../../../../../shared/results/rxjs/filterOnlySuccess';
import { switchMapResultToResultRxJs } from '../../../../../shared/results/rxjs/switchMapResultToResultRxJs';
import { combineResults2 } from '../../../../../shared/results/utils/combineResults2';
import {
  GPhotosMediaItemDetailsApiResponse,
  MediaItem,
} from '../../../../services/webapi.service';
import {
  gPhotosMediaItemsActions,
  gPhotosMediaItemsState,
} from '../../../../store/gphoto-media-items';
import {
  mediaItemsActions,
  mediaItemsState,
} from '../../../../store/media-items';
import { mediaViewerActions } from '../../../../store/media-viewer';

export interface ImageData {
  id: string;
  baseUrl: string;
  width: number;
  height: number;
  fileName: string;
  onClick: (event: MouseEvent) => void;
  onKeyDown: (event: KeyboardEvent) => void;
}

@Component({
  selector: 'app-image',
  imports: [InViewportModule, HasFailedPipe, IsPendingPipe],
  templateUrl: './image.component.html',
})
export class ImageComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly window = inject(WINDOW);

  readonly mediaItemId = input.required<string>();
  readonly width = input.required<number>();
  readonly imageSizeChanged = output<void>();

  private readonly mediaItemId$ = toObservable(this.mediaItemId);
  private readonly width$ = toObservable(this.width);
  private readonly isInViewport$ = new BehaviorSubject(false);

  private subscription = new Subscription();

  private readonly mediaItemResult$ = this.mediaItemId$.pipe(
    switchMap((mediaItemId: string) =>
      this.store.select(
        mediaItemsState.selectMediaItemDetailsById(mediaItemId),
      ),
    ),
  );

  private readonly gMediaItemResult$ = this.mediaItemResult$.pipe(
    switchMapResultToResultRxJs((mediaItem: MediaItem) => {
      return this.store.select(
        gPhotosMediaItemsState.selectGPhotosMediaItemById(
          mediaItem.gPhotosMediaItemId,
        ),
      );
    }),
  );

  private readonly imageDataResult$: Observable<Result<ImageData>> =
    combineLatest([
      this.mediaItemResult$,
      this.gMediaItemResult$,
      this.width$,
    ]).pipe(
      map(([mediaItemResult, gMediaItemResult, width]) => {
        return combineResults2(
          mediaItemResult,
          gMediaItemResult,
          (mediaItem, gMediaItem) => {
            const originalWidth = Number(gMediaItem.mediaMetadata.width);
            const originalHeight = Number(gMediaItem.mediaMetadata.height);

            return {
              id: mediaItem.id,
              baseUrl: gMediaItem.baseUrl!,
              width: width,
              height: (originalHeight / originalWidth) * width,
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
            };
          },
        );
      }),
    );

  readonly imageDataResult: Signal<Result<ImageData>> = toSignal(
    this.imageDataResult$,
    {
      initialValue: toPending<ImageData>(),
    },
  );

  private openImageInNewTab(detail: GPhotosMediaItemDetailsApiResponse) {
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

  ngOnInit(): void {
    this.subscription.add(
      this.isInViewport$
        .pipe(
          filter(Boolean),
          switchMap(() => this.mediaItemId$),
          distinctUntilChanged(),
        )
        .subscribe((mediaItemId) => {
          this.store.dispatch(
            mediaItemsActions.loadMediaItemDetails({ mediaItemId }),
          );
        }),
    );

    this.subscription.add(
      this.isInViewport$
        .pipe(
          filter(Boolean),
          switchMap(() => {
            return this.mediaItemResult$.pipe(
              filterOnlySuccess(),
              distinctUntilChanged(),
            );
          }),
        )
        .subscribe((mediaItem) => {
          this.store.dispatch(
            gPhotosMediaItemsActions.loadGPhotosMediaItemDetails({
              gPhotosMediaItemId: mediaItem.gPhotosMediaItemId,
            }),
          );
        }),
    );

    this.subscription.add(
      this.imageDataResult$.pipe(distinctUntilChanged()).subscribe(() => {
        this.imageSizeChanged.emit(undefined);
      }),
    );
  }

  setIsInViewport(visible: boolean) {
    this.isInViewport$.next(visible);
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
