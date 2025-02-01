import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  inject,
  OnDestroy,
  ViewChild,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { Store } from '@ngrx/store';
import { combineLatest, Observable, of, Subscription, switchMap } from 'rxjs';

import { NAVIGATOR } from '../../../app.tokens';
import { HasFailedPipe } from '../../../shared/results/pipes/has-failed.pipe';
import { HasSucceededPipe } from '../../../shared/results/pipes/has-succeeded.pipe';
import { IsPendingPipe } from '../../../shared/results/pipes/is-pending.pipe';
import { Result, toPending } from '../../../shared/results/results';
import { switchMapResultToResultRxJs } from '../../../shared/results/rxjs/switchMapResultToResultRxJs';
import { combineResults2 } from '../../../shared/results/utils/combineResults2';
import { GPhotosMediaItem, MediaItem } from '../../services/webapi.service';
import { gPhotosMediaItemsState } from '../../store/gphoto-media-items';
import { mediaItemsState } from '../../store/media-items';
import { mediaViewerActions, mediaViewerState } from '../../store/media-viewer';

/** The details to display to the UI. */
interface MediaDetails {
  imageUrl: string;
  imageAlt: string;
  fileName: string;
  formattedDate: string;
  locationName?: string;
  locationUrl?: string;
}

@Component({
  selector: 'app-content-media-viewer',
  imports: [CommonModule, IsPendingPipe, HasFailedPipe, HasSucceededPipe],
  templateUrl: './media-viewer.component.html',
})
export class MediaViewerComponent implements AfterViewInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly navigator = inject(NAVIGATOR);
  private readonly subscription = new Subscription();

  @ViewChild('modal') myModal?: ElementRef;

  private readonly isOpen$ = this.store.select(mediaViewerState.selectIsOpen());

  readonly isShareSupported = !!this.navigator.share;

  readonly mediaDetailsResult = (() => {
    const requests$ = this.store.select(mediaViewerState.selectRequest());

    const mediaItemResult$: Observable<Result<MediaItem>> = requests$.pipe(
      switchMap((request) => {
        if (!request?.mediaItemId) {
          return of(toPending<MediaItem>());
        }
        return this.store.select(
          mediaItemsState.selectMediaItemDetailsById(request.mediaItemId),
        );
      }),
    );

    const gPhotosMediaItemResult$: Observable<Result<GPhotosMediaItem>> =
      mediaItemResult$.pipe(
        switchMapResultToResultRxJs((mediaItem) =>
          this.store.select(
            gPhotosMediaItemsState.selectGPhotosMediaItemById(
              mediaItem.gPhotosMediaItemId,
            ),
          ),
        ),
      );

    const mediaDetailsResult$: Observable<Result<MediaDetails>> = combineLatest(
      [mediaItemResult$, gPhotosMediaItemResult$],
      (mediaItemResult, gPhotosMediaItemResult) => {
        return combineResults2(
          mediaItemResult,
          gPhotosMediaItemResult,
          (mediaItem, gPhotosMediaItem) => ({
            imageUrl: `${gPhotosMediaItem.baseUrl}=w${gPhotosMediaItem.mediaMetadata.width}-h${gPhotosMediaItem.mediaMetadata.height}`,
            imageAlt: `Image of ${mediaItem.fileName}`,
            fileName: mediaItem.fileName,
            formattedDate: 'Sunday, November 20, 2016 at 12:35 PM',
            locationName: mediaItem.location
              ? `@ ${mediaItem.location?.latitude}, ${mediaItem.location?.longitude}`
              : undefined,
            locationUrl: mediaItem.location
              ? `https://www.google.com/maps/place/${mediaItem.location?.latitude},${mediaItem.location?.longitude}`
              : undefined,
          }),
        );
      },
    );

    return toSignal(mediaDetailsResult$, {
      initialValue: toPending<MediaDetails>(),
    });
  })();

  share(url: string, fileName: string) {
    const shareData = {
      title: fileName,
      text: 'Photo from Sharded Photos Drive',
      url,
    };

    if (this.navigator.canShare(shareData)) {
      this.navigator.share(shareData);
    } else {
      console.error(`Data ${shareData} cannot be shared.`);
    }
  }

  closeDialog() {
    this.store.dispatch(mediaViewerActions.closeMediaViewer());
  }

  ngAfterViewInit(): void {
    this.subscription.add(
      this.isOpen$.subscribe((isOpen) => {
        if (isOpen) {
          this.myModal?.nativeElement?.showModal();
        } else {
          this.myModal?.nativeElement?.close();
        }
      }),
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
