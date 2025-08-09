import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  effect,
  ElementRef,
  inject,
  OnDestroy,
  Signal,
  ViewChild,
} from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Store } from '@ngrx/store';
import { NgxTypedWriterComponent } from 'ngx-typed-writer';
import { Subscription } from 'rxjs';

import { NAVIGATOR } from '../../app.tokens';
import { HasFailedPipe } from '../../shared/results/pipes/has-failed.pipe';
import { HasSucceededPipe } from '../../shared/results/pipes/has-succeeded.pipe';
import { IsPendingPipe } from '../../shared/results/pipes/is-pending.pipe';
import { sendUserMessage } from '../store/chats/chats.actions';
import { Message, selectMessages } from '../store/chats/chats.state';
import { dialogActions, dialogState } from '../store/dialog';
import { ChatDialogRequest } from './chat-dialog.request';

@Component({
  selector: 'app-content-chat-dialog',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    NgxTypedWriterComponent,
    IsPendingPipe,
    HasFailedPipe,
    HasSucceededPipe,
  ],
  templateUrl: './chat-dialog.component.html',
})
export class ChatDialogComponent implements AfterViewInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly navigator = inject(NAVIGATOR);
  searchControl = new FormControl('');
  private readonly subscription = new Subscription();

  @ViewChild('modal') myModal?: ElementRef;

  private readonly isOpen$ = this.store.select(
    dialogState.selectIsDialogOpen(ChatDialogRequest),
  );
  private readonly requests = this.store.selectSignal(
    dialogState.selectDialogRequests(ChatDialogRequest),
  );

  readonly messages: Signal<readonly Message[]> =
    this.store.selectSignal(selectMessages());

  constructor() {
    effect(() => {
      const request = this.requests();
      if (request) {
        // this.mediaViewerStore.loadDetails(request.mediaItemId);
      }
    });
  }

  closeDialog() {
    this.store.dispatch(dialogActions.closeDialog());
  }

  onSearch() {
    const query = this.searchControl.value?.trim();
    if (query) {
      this.store.dispatch(sendUserMessage({ message: query }));
      this.searchControl.reset();
    }
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
