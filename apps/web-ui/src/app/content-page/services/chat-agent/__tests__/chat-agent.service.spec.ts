import { TestBed } from '@angular/core/testing';
import { AIMessageChunk } from '@langchain/core/messages';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { MemorySaver } from '@langchain/langgraph/web';

import { environment } from '../../../../../environments/environment';
import { CHAT_MODEL, MEMORY_SAVER } from '../../../content-page.tokens';
import { BotMessage, ChatAgentService } from '../chat-agent.service';

class MockRunnable {
  streamEvents = jasmine.createSpy('streamEvents');
}

describe('ChatAgentService', () => {
  let service: ChatAgentService;
  let mockMemorySaver: MemorySaver;
  let mockLLM: ChatGoogleGenerativeAI;

  beforeEach(async () => {
    mockMemorySaver = new MemorySaver();
    spyOn(mockMemorySaver, 'deleteThread').and.callThrough();

    mockLLM = new ChatGoogleGenerativeAI({
      model: environment.geminiModel,
      temperature: 0.7,
      apiKey: environment.geminiApiKey,
    });
    spyOn(mockLLM, 'invoke').and.resolveTo(
      new AIMessageChunk({ content: 'content' }),
    );

    TestBed.configureTestingModule({
      providers: [
        ChatAgentService,
        { provide: MEMORY_SAVER, useValue: mockMemorySaver },
        { provide: CHAT_MODEL, useValue: mockLLM },
      ],
    });

    service = TestBed.inject(ChatAgentService);

    // Wait for async loadAgent() to complete
    await service.loadAgent();
  });

  it('clearMemory should call deleteThread with default thread id', () => {
    service.clearMemory();

    expect(mockMemorySaver.deleteThread).toHaveBeenCalledWith('default_thread');
  });

  it('getAgentResponseStream should error if agent is not initialized', (done) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (service as any).agent = undefined;

    service.getAgentResponseStream('hi').subscribe({
      next: () => fail('should not emit'),
      error: (err) => {
        expect(err.message).toBe('Agent executor not initialized yet');
        done();
      },
    });
  });

  it('getAgentResponseStream should emit content and reasoning and complete', (done) => {
    async function* fakeStream() {
      yield {
        event: 'on_chat_model_stream',
        data: { chunk: { content: 'hello' } },
      };
      yield { event: 'on_chain_end', run_id: 'run123', name: 'chainName' };
    }

    const mockRunnable = new MockRunnable();
    mockRunnable.streamEvents.and.returnValue(Promise.resolve(fakeStream()));
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (service as any).agent = mockRunnable;

    const emitted: BotMessage[] = [];
    service.getAgentResponseStream('hello').subscribe({
      next: (msg) => emitted.push(msg),
      complete: () => {
        expect(emitted.length).toBeGreaterThan(0);
        expect(emitted[0].content).toContain('hello');
        expect(
          emitted.some((m) => m.reasoning?.some((r) => r.id === 'run123')),
        ).toBeTrue();
        done();
      },
      error: (err) => fail(err),
    });
  });

  it('getAgentResponseStream should emit error when fake stream throws an error', (done) => {
    const mockRunnable = new MockRunnable();
    mockRunnable.streamEvents.and.returnValue(
      Promise.reject(new Error('Random error')),
    );
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (service as any).agent = mockRunnable;

    service.getAgentResponseStream('hello').subscribe({
      error: () => {
        done();
      },
    });
  });
});
