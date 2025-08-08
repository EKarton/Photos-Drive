import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  effect,
  ElementRef,
  inject,
  OnDestroy,
  ViewChild,
} from '@angular/core';
import { Store } from '@ngrx/store';
import { Subscription } from 'rxjs';

import { NAVIGATOR } from '../../app.tokens';
import { HasFailedPipe } from '../../shared/results/pipes/has-failed.pipe';
import { HasSucceededPipe } from '../../shared/results/pipes/has-succeeded.pipe';
import { IsPendingPipe } from '../../shared/results/pipes/is-pending.pipe';
import { dialogActions, dialogState } from '../store/dialog';
import { ChatDialogRequest } from './chat-dialog.request';

@Component({
  selector: 'app-content-chat-dialog',
  imports: [CommonModule, IsPendingPipe, HasFailedPipe, HasSucceededPipe],
  templateUrl: './chat-dialog.component.html',
})
export class ChatDialogComponent implements AfterViewInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly navigator = inject(NAVIGATOR);
  private readonly subscription = new Subscription();

  @ViewChild('modal') myModal?: ElementRef;

  private readonly isOpen$ = this.store.select(
    dialogState.selectIsDialogOpen(ChatDialogRequest),
  );
  private readonly requests = this.store.selectSignal(
    dialogState.selectDialogRequests(ChatDialogRequest),
  );

  constructor() {
    effect(() => {
      const request = this.requests();
      if (request) {
        // this.mediaViewerStore.loadDetails(request.mediaItemId);
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
