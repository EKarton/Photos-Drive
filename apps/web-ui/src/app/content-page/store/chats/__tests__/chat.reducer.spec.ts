import { toSuccess } from '../../../../shared/results/results';
import * as chatActions from '../chats.actions';
import { chatsReducer } from '../chats.reducer';
import { ChatsState, initialState } from '../chats.state';

describe('Chat Reducer', () => {
  it('should handle startNewChat by clearing messages', () => {
    const prevState: ChatsState = {
      ...initialState,
      messages: [
        { id: '1', type: 'User', content: toSuccess({ output: 'hi' }) },
      ],
    };

    const action = chatActions.startNewChat();
    const newState = chatsReducer(prevState, action);

    expect(newState.messages.length).toBe(0);
  });

  it('should handle sendUserMessage by adding a User message', () => {
    const userInput = 'Hello world';
    const action = chatActions.sendUserMessage({ userInput });

    const newState = chatsReducer(initialState, action);

    expect(newState.messages.length).toBe(1);
    expect(newState.messages[0]).toEqual({
      id: jasmine.any(String),
      type: 'User',
      content: toSuccess({
        output: userInput,
      }),
    });
  });

  it('should handle addOrUpdateBotMessage by adding a new Bot message if id not found', () => {
    const botMessage = { content: 'Hello from bot', reasoning: [] };
    const id = 'bot-msg-1';
    const action = chatActions.addOrUpdateBotMessage({
      id,
      botMessage: toSuccess(botMessage),
    });

    const newState = chatsReducer(initialState, action);

    expect(newState.messages.length).toBe(1);
    expect(newState.messages[0]).toEqual({
      id: id,
      type: 'Bot',
      content: toSuccess({
        output: botMessage.content,
        reasoning: [],
      }),
    });
  });

  it('should handle addOrUpdateBotMessage by updating existing Bot message', () => {
    const existingId = 'bot-msg-1';
    const prevState: ChatsState = {
      ...initialState,
      messages: [
        {
          id: existingId,
          type: 'Bot',
          content: toSuccess({ output: 'Old content', reasoning: [] }),
        },
      ],
    };

    const updatedBotMessage = {
      content: 'Updated content',
      reasoning: [{ id: 'r1', content: 'some reasoning' }],
    };
    const action = chatActions.addOrUpdateBotMessage({
      id: existingId,
      botMessage: toSuccess(updatedBotMessage),
    });

    const newState = chatsReducer(prevState, action);

    expect(newState.messages.length).toBe(1);
    expect(newState.messages[0]).toEqual({
      id: existingId,
      type: 'Bot',
      content: toSuccess({
        output: updatedBotMessage.content,
        reasoning: updatedBotMessage.reasoning,
      }),
    });
  });
});
