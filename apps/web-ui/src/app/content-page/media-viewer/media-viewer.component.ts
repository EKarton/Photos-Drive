import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  OnDestroy,
  Signal,
  ViewChild,
} from '@angular/core';
import { Store } from '@ngrx/store';
import { Subscription } from 'rxjs';

import { NAVIGATOR } from '../../app.tokens';
import { HasFailedPipe } from '../../shared/results/pipes/has-failed.pipe';
import { HasSucceededPipe } from '../../shared/results/pipes/has-succeeded.pipe';
import { IsPendingPipe } from '../../shared/results/pipes/is-pending.pipe';
import { Result } from '../../shared/results/results';
import { combineResults2 } from '../../shared/results/utils/combineResults2';
import { GPhotosMediaItem } from '../services/types/gphotos-media-item';
import { dialogActions, dialogState } from '../store/dialog';
import { MediaViewerRequest } from './media-viewer.request';
import { MediaViewerStore } from './media-viewer.store';

/** The details to display to the UI. */
interface MediaDetails {
  url: string;
  downloadUrl: string;
  mimeType: string;
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
  providers: [MediaViewerStore],
})
export class MediaViewerComponent implements AfterViewInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly navigator = inject(NAVIGATOR);
  private readonly subscription = new Subscription();
  private readonly mediaViewerStore = inject(MediaViewerStore);

  @ViewChild('modal') myModal?: ElementRef;

  private readonly isOpen$ = this.store.select(
    dialogState.selectIsDialogOpen(MediaViewerRequest),
  );
  private readonly requests = this.store.selectSignal(
    dialogState.selectDialogRequests(MediaViewerRequest),
  );

  readonly isShareSupported = !!this.navigator.share;

  readonly mediaDetailsResult: Signal<Result<MediaDetails>> = computed(() => {
    return combineResults2(
      this.mediaViewerStore.mediaItemResult(),
      this.mediaViewerStore.gMediaItemResult(),
      (mediaItem, gMediaItem) => {
        return {
          url: getUrl(gMediaItem),
          downloadUrl: getDownloadUrl(gMediaItem),
          mimeType: gMediaItem.mimeType,
          imageAlt: `Image of ${mediaItem.fileName}`,
          fileName: mediaItem.fileName,
          formattedDate: mediaItem.dateTaken.toLocaleString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          }),
          locationName: mediaItem.location
            ? `@ ${mediaItem.location?.latitude}, ${mediaItem.location?.longitude}`
            : undefined,
          locationUrl: mediaItem.location
            ? `https://www.google.com/maps/place/${mediaItem.location?.latitude},${mediaItem.location?.longitude}`
            : undefined,
        };
      },
    );
  });

  constructor() {
    effect(() => {
      const request = this.requests();
      if (request) {
        this.mediaViewerStore.loadDetails(request.mediaItemId);
      }
    });
  }

  share(url: string, fileName: string) {
    const shareData = {
      title: fileName,
      text: 'Photo from Photos Drive',
      url,
    };

    if (this.navigator.canShare(shareData)) {
      this.navigator.share(shareData);
    } else {
      console.error(`Data ${shareData} cannot be shared.`);
    }
  }

  closeDialog() {
    this.store.dispatch(dialogActions.closeDialog());
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

function getUrl(gMediaItem: GPhotosMediaItem): string {
  if (gMediaItem.mimeType.startsWith('image')) {
    return `${gMediaItem.baseUrl}=w${gMediaItem.mediaMetadata.width}-h${gMediaItem.mediaMetadata.height}`;
  }

  return `${gMediaItem.baseUrl}=dv`;
}

function getDownloadUrl(gMediaItem: GPhotosMediaItem): string {
  if (gMediaItem.mimeType.startsWith('image')) {
    return `${gMediaItem.baseUrl}=d`;
  }

  return `${gMediaItem.baseUrl}=dv`;
}
