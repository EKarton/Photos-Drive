import { createAction, props } from '@ngrx/store';

/** An action that requests for the chat to be restarted. */
export const startNewChat = createAction(
  '[Chats] Clears the old chat and requests for a new chat',
);

/** An action that adds a user message to the chats. */
export const sendUserMessage = createAction(
  '[Chats] Send a user message',
  props<{ message: string }>(),
);

/** An action that adds a bot message to the list of chats. */
export const addBotMessage = createAction(
  '[Chats] Add a bot message',
  props<{ message: string; reasoning?: string[] }>(),
);
