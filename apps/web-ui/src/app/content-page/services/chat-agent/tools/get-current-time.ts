import { Injectable } from '@angular/core';
import { DynamicStructuredTool } from 'langchain/tools';
import { z } from 'zod';

export const CurrentTimeInputSchema = z.object({});

export const CurrentTimeOutputSchema = z.object({
  timestamp: z.string().describe('The timestamp in ISO format'),
});

export type CurrentTimeOutput = z.infer<typeof CurrentTimeOutputSchema>;

@Injectable({ providedIn: 'root' })
export class CurrentTimeTool extends DynamicStructuredTool {
  constructor() {
    super({
      name: 'CurrentTimeTool',
      description: 'Tool that returns the current time',
      schema: CurrentTimeInputSchema,
      func: async (): Promise<CurrentTimeOutput> => {
        return { timestamp: new Date().toISOString() };
      },
    });
  }
}
