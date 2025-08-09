import { Injectable } from '@angular/core';
import type { PromptTemplate } from '@langchain/core/prompts';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import {
  AgentAction,
  AgentExecutor,
  AgentFinish,
  AgentRunnableSequence,
  AgentStep,
  createReactAgent,
} from 'langchain/agents';
import { pull } from 'langchain/hub';
import type { Tool } from 'langchain/tools';
import { Observable, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';

type Agent = AgentRunnableSequence<
  { steps: AgentStep[] },
  AgentAction | AgentFinish
>;

export interface BotMessage {
  content: string;
  reasoning?: string[];
}

@Injectable({ providedIn: 'root' })
export class ChatAgentService {
  private agentExecutor?: AgentExecutor;
  private agent?: Agent;

  constructor() {
    this.loadAgent();
  }

  async loadAgent() {
    const llm = new ChatGoogleGenerativeAI({
      model: 'gemini-2.5-flash',
      temperature: 0.7,
      apiKey: environment.geminiApiKey,
    });

    // const dummyTool = new Tool({
    //   name: 'dummy',
    //   description: 'A dummy tool that does nothing',
    //   func: async () => 'No operation',
    // });

    const tools: Tool[] = [];

    const prompt: PromptTemplate =
      await pull<PromptTemplate>('hwchase17/react');

    this.agent = await createReactAgent({ llm, tools, prompt });
    this.agentExecutor = new AgentExecutor({
      agent: this.agent,
      tools,
    });
  }

  getAgentResponseStream(userMessage: string): Observable<BotMessage> {
    if (!this.agentExecutor) {
      return throwError(() => new Error('Agent executor not initialized yet'));
    }

    return new Observable<BotMessage>((observer) => {
      (async () => {
        try {
          let content = '';
          const reasoning: string[] = [];

          for await (const logPatch of this.agentExecutor!.streamLog({
            input: userMessage,
          })) {
            for (const op of logPatch.ops) {
              if (op.op === 'add' && op.value?.content) {
                content += op.value.content;
                observer.next({ content, reasoning });
              }
            }
          }

          observer.complete();
        } catch (error) {
          observer.error(error);
        }
      })();
    });
  }
}
