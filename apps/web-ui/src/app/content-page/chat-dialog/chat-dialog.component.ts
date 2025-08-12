import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
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

import { HasFailedPipe } from '../../shared/results/pipes/has-failed.pipe';
import { HasSucceededPipe } from '../../shared/results/pipes/has-succeeded.pipe';
import { IsPendingPipe } from '../../shared/results/pipes/is-pending.pipe';
import { sendUserMessage, startNewChat } from '../store/chats/chats.actions';
import { Message, selectMessages } from '../store/chats/chats.state';
import { dialogsActions, dialogsState } from '../store/dialogs';
import { ChatDialogRequest } from './chat-dialog.request';
import { ReasoningCollapseComponent } from './reasoning-collapse/reasoning-collapse.component';

@Component({
  selector: 'app-content-chat-dialog',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    NgxTypedWriterComponent,
    IsPendingPipe,
    HasFailedPipe,
    HasSucceededPipe,
    ReasoningCollapseComponent,
  ],
  templateUrl: './chat-dialog.component.html',
})
export class ChatDialogComponent implements AfterViewInit, OnDestroy {
  searchControl = new FormControl('');
  @ViewChild('chatDialog') myModal?: ElementRef;

  private readonly store = inject(Store);
  private readonly subscription = new Subscription();

  readonly isOpen$ = this.store.select(
    dialogsState.selectIsDialogOpen(ChatDialogRequest),
  );

  readonly messages: Signal<readonly Message[]> =
    this.store.selectSignal(selectMessages());

  closeDialog() {
    this.store.dispatch(dialogsActions.closeDialog());
  }

  clearChat() {
    this.store.dispatch(startNewChat());
  }

  onSearch() {
    const userInput = this.searchControl.value?.trim();
    if (userInput) {
      this.store.dispatch(sendUserMessage({ userInput }));
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
