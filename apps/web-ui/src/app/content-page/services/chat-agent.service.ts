import { Injectable } from '@angular/core';
import type { PromptTemplate } from '@langchain/core/prompts';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { AgentExecutor, createReactAgent } from 'langchain/agents';
import { pull } from 'langchain/hub';
import type { Tool } from 'langchain/tools';
import { from, Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface BotMessage {
  content: string;
  reasoning?: string[];
}

@Injectable({ providedIn: 'root' })
export class ChatAgentService {
  private agentExecutor?: AgentExecutor;

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

    const agent = await createReactAgent({ llm, tools, prompt });

    this.agentExecutor = new AgentExecutor({
      agent,
      tools,
    });
  }

  getAgentResponse(userMessage: string): Observable<BotMessage> {
    console.log('getAgentResponse', userMessage);
    if (!this.agentExecutor) {
      console.log('I am here');
      return from(Promise.reject('Agent not initialized yet'));
    }
    return from<Promise<BotMessage>>(
      this.agentExecutor
        .invoke({ input: userMessage })
        .then((result: any) => {
          console.log('I am here', userMessage, result);

          // Typical agent output
          const content =
            result.output ?? (typeof result === 'string' ? result : '');
          const reasoning: string[] = [];

          // Try to get reasoning chain from agent output
          // This depends on the agent; often intermediateSteps or similar.
          if (Array.isArray(result.intermediateSteps)) {
            // Convert each step to a string or just extract relevant fields
            reasoning.push(
              ...result.intermediateSteps.map(
                (step: any) =>
                  step.observation ?? step.actionLog ?? String(step),
              ),
            );
          } else if (result.reasoning) {
            reasoning.push(...result.reasoning);
          }

          const botMessage: BotMessage = { content, reasoning };
          console.log(botMessage);
          return botMessage;
        })
        .catch((err: Error) => {
          console.error('invoke() failed:', err);
          return { content: 'Error from agent', reasoning: [String(err)] };
        }),
    );
  }
}
