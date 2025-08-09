import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  effect,
  ElementRef,
  inject,
  OnDestroy,
  Signal,
  signal,
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

export type MessageType = 'Bot' | 'User';

export interface Message {
  type: MessageType;
  content: string;
  reasoning?: string[];
}

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

  readonly messages: Signal<readonly Message[]> = signal([
    {
      type: 'Bot',
      content: 'Hi there! How can I help you today?',
      reasoning: undefined,
    },
    {
      type: 'User',
      content: 'Can you recommend a hiking trail in the Dolomites?',
      reasoning: undefined,
    },
    {
      type: 'Bot',
      content:
        "Absolutely! I recommend the Tre Cime di Lavaredo loop. It's about 10km with stunning views.",
      reasoning: [
        'I considered your interest in photography and nature.',
        'Tre Cime offers panoramic views and multiple photo spots.',
        'The trail is moderately challenging but well-marked.',
      ],
    },
    {
      type: 'User',
      content: 'Perfect. Can you also suggest a nearby lake?',
    },
    {
      type: 'Bot',
      content:
        "Lago di Misurina is only a short drive away. It's a beautiful spot for sunrise photography.",
    },
    {
      type: 'Bot',
      content: 'Hi there! How can I help you today?',
      reasoning: undefined,
    },
    {
      type: 'User',
      content: 'Can you recommend a hiking trail in the Dolomites?',
      reasoning: undefined,
    },
    {
      type: 'Bot',
      content:
        "Absolutely! I recommend the Tre Cime di Lavaredo loop. It's about 10km with stunning views.",
      reasoning: [
        'I considered your interest in photography and nature.',
        'Tre Cime offers panoramic views and multiple photo spots.',
        'The trail is moderately challenging but well-marked.',
      ],
    },
    {
      type: 'User',
      content: 'Perfect. Can you also suggest a nearby lake?',
    },
    {
      type: 'Bot',
      content:
        "Lago di Misurina is only a short drive away. It's a beautiful spot for sunrise photography.",
    },
  ]);

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
