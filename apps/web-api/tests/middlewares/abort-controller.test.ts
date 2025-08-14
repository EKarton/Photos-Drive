import { EventEmitter } from 'events';
import { NextFunction, Request, Response } from 'express';
import { addRequestAbortController } from '../../src/middlewares/abort-controller';

describe('addRequestAbortController middleware', () => {
  let req: Request & { abortController?: AbortController };
  let res: Response;
  let next: NextFunction;

  beforeEach(() => {
    // Use EventEmitter to simulate req.on('close')
    req = new EventEmitter() as never;
    res = {} as Response;
    next = jest.fn();
  });

  it('should attach an AbortController to req', async () => {
    const middleware = addRequestAbortController();
    await middleware(req, res, next);

    expect(req.abortController).toBeDefined();
    expect(req.abortController).toBeInstanceOf(AbortController);
  });

  it('should call next()', async () => {
    const middleware = addRequestAbortController();
    await middleware(req, res, next);

    expect(next).toHaveBeenCalledTimes(1);
  });

  it('should abort controller when req closes', async () => {
    const middleware = addRequestAbortController();
    await middleware(req, res, next);

    const abortSpy = jest.spyOn(req.abortController!, 'abort');

    // Simulate client disconnect
    req.emit('close');

    expect(abortSpy).toHaveBeenCalledTimes(1);
  });
});
