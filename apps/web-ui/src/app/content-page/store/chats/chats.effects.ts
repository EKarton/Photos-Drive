import { inject, Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';

import { ChatAgentService } from '../../services/chat-agent.service';
import { addBotMessage, sendUserMessage } from './chats.actions';

@Injectable()
export class ChatsEffects {
  private readonly store = inject(Store);
  private readonly actions$ = inject(Actions);
  private readonly chatAgentService = inject(ChatAgentService);

  sendMessage$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(sendUserMessage),
      switchMap(({ message }) =>
        this.chatAgentService.getAgentResponse(message).pipe(
          map(({ content, reasoning }) =>
            addBotMessage({ message: content, reasoning }),
          ),
          catchError(() =>
            of(
              addBotMessage({
                message: 'Sorry, something went wrong.',
                reasoning: ['No reasoning available'],
              }),
            ),
          ),
        ),
      ),
    );
  });
}
