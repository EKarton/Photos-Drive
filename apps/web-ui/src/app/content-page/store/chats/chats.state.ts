import { createFeatureSelector, createSelector } from '@ngrx/store';

export type MessageType = 'Bot' | 'User';

export interface Message {
  type: MessageType;
  content: string;
  reasoning?: string[];
}

export interface ChatsState {
  messages: Message[];
}

export const initialState: ChatsState = {
  messages: [],
};

export const FEATURE_KEY = 'Chats';

export const selectChatsState = createFeatureSelector<ChatsState>(FEATURE_KEY);

export const selectMessages = () =>
  createSelector(selectChatsState, (state) => state.messages);
