import { inject, Injectable } from '@angular/core';
import { Runnable } from '@langchain/core/runnables';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { createReactAgent } from '@langchain/langgraph/prebuilt';
import { MemorySaver } from '@langchain/langgraph/web';
import { Observable, throwError } from 'rxjs';

import { CurrentTimeTool } from './tools/get-current-time';

/** The response from the LLM */
export interface BotMessage {
  content: string;
  reasoning?: BotMessageReasoning[];
}

/** The reasoning message of the Bot message */
export interface BotMessageReasoning {
  id: string;
  content: string;
}

/** The default thread ID */
const DEFAULT_THREAD_ID = 'default_thread';

/** The chat agent used to interface with the UI */
@Injectable({ providedIn: 'root' })
export class ChatAgentService {
  private agent?: Runnable;

  private readonly memorySaver = inject(MemorySaver);
  private readonly chatGoogleGenerativeAI = inject(ChatGoogleGenerativeAI);
  private readonly getCurrentTimeTool = inject(CurrentTimeTool);

  constructor() {
    this.loadAgent();
  }

  async loadAgent() {
    this.agent = await createReactAgent({
      llm: this.chatGoogleGenerativeAI,
      tools: [this.getCurrentTimeTool],
      checkpointSaver: this.memorySaver,
    });
  }

  clearMemory() {
    this.memorySaver.deleteThread(DEFAULT_THREAD_ID);
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
