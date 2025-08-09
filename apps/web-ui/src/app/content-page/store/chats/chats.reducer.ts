import { createFeature, createReducer, on } from '@ngrx/store';

import { addBotMessage, sendUserMessage, startNewChat } from './chats.actions';
import { ChatsState, FEATURE_KEY, initialState } from './chats.state';

export const chatsReducer = createReducer(
  initialState,

  on(startNewChat, (state): ChatsState => {
    return {
      ...state,
      messages: [
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
      ],
    };
  }),

  on(sendUserMessage, (state, { message }): ChatsState => {
    return {
      ...state,
      messages: [
        ...state.messages,
        {
          type: 'User',
          content: message,
        },
      ],
    };
  }),

  on(addBotMessage, (state, { message, reasoning }): ChatsState => {
    return {
      ...state,
      messages: [
        ...state.messages,
        {
          type: 'Bot',
          content: message,
          reasoning,
        },
      ],
    };
  }),
);

export const chatsFeature = createFeature({
  name: FEATURE_KEY,
  reducer: chatsReducer,
});
