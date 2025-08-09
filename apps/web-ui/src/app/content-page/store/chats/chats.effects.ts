import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { map, startWith, switchMap } from 'rxjs/operators';

import { Result, toPending } from '../../../shared/results/results';
import { toResult } from '../../../shared/results/rxjs/toResult';
import {
  BotMessage,
  ChatAgentService,
} from '../../services/chat-agent.service';
import { addOrUpdateBotMessage, sendUserMessage } from './chats.actions';

@Injectable()
export class ChatsEffects {
  private readonly store = inject(Store);
  private readonly actions$ = inject(Actions);
  private readonly chatAgentService = inject(ChatAgentService);

  sendMessage$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(sendUserMessage),
      switchMap(({ userInput }) => {
        const messageId = crypto.randomUUID();
        return this.chatAgentService.getAgentResponseStream(userInput).pipe(
          toResult(),
          startWith(toPending<BotMessage>()),
          map((botMessage: Result<BotMessage>) =>
            addOrUpdateBotMessage({ id: messageId, botMessage }),
          ),
        );
      }),
    );
  });
}
