import { Injectable } from '@angular/core';
import { BaseMessage } from '@langchain/core/messages';
import { Runnable } from '@langchain/core/runnables';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { createReactAgent } from '@langchain/langgraph/prebuilt';
import { MemorySaver } from '@langchain/langgraph/web';
import type { Tool } from 'langchain/tools';
import { Observable, throwError } from 'rxjs';

import { environment } from '../../../../environments/environment';

export interface BotMessage {
  content: string;
  reasoning?: BotMessageReasoning[];
}

export interface BotMessageReasoning {
  id: string;
  content: string;
}

const DEFAULT_THREAD_ID = 'default_thread';

@Injectable({ providedIn: 'root' })
export class ChatAgentService {
  private agent?: Runnable;
  private memory?: MemorySaver;

  constructor() {
    this.loadAgent();
  }

  async loadAgent() {
    const llm = new ChatGoogleGenerativeAI({
      model: 'gemini-2.5-flash',
      temperature: 0.7,
      apiKey: environment.geminiApiKey,
    });

    async function summarizeMessages(messages: BaseMessage[]) {
      const summaryPrompt = [
        { role: 'system', content: 'Summarize the following conversation:' },
        { role: 'user', content: JSON.stringify(messages) },
      ];
      const res = await llm.invoke(summaryPrompt);
      return res.content;
    }

    const tools: Tool[] = [];
    this.memory = new MemorySaver();
    this.agent = await createReactAgent({
      llm,
      tools,
      checkpointSaver: this.memory,
      preModelHook: async (state) => {
        const maxMessages = 20;
        if (state.messages.length > maxMessages) {
          const oldMessages = state.messages.slice(
            0,
            state.messages.length - maxMessages,
          );
          const recentMessages = state.messages.slice(-maxMessages);

          const summary = await summarizeMessages(oldMessages);

          return {
            messages: [
              { role: 'system', content: `Conversation so far: ${summary}` },
              ...recentMessages,
            ],
          };
        }

        return {}; // no changes if under the limit
      },
    });
  }

  clearMemory() {
    this.memory?.deleteThread(DEFAULT_THREAD_ID);
  }

  getAgentResponseStream(userMessage: string): Observable<BotMessage> {
    if (!this.agent) {
      return throwError(() => new Error('Agent executor not initialized yet'));
    }

    return new Observable<BotMessage>((observer) => {
      (async () => {
        try {
          const stream = await this.agent!.streamEvents(
            {
              messages: [{ role: 'user', content: userMessage }],
            },
            {
              version: 'v2',
              configurable: {
                thread_id: DEFAULT_THREAD_ID,
              },
            },
          );

          let content = '';
          const reasoning: BotMessageReasoning[] = [];
          for await (const event of stream) {
            switch (event.event) {
              case 'on_chain_end':
              case 'on_chat_model_end':
              case 'on_tool_end':
              case 'on_on_llm_end':
              case 'on_prompt_end':
              case 'on_retriever_end':
                reasoning.push({
                  id: event.run_id,
                  content: `Called ${event.event}: ${event.name}`,
                });
                break;
              case 'on_chat_model_stream':
                content += event.data.chunk.content;
                break;
            }
            observer.next({ content, reasoning: [...reasoning] });
          }

          observer.complete();
        } catch (error) {
          observer.error(error);
        }
      })();
    });
  }
}
