import { NextFunction, Request, Response } from 'express';

/** Adds the abort controller to the request object. */
export function addRequestAbortController() {
  return async (req: Request, _res: Response, next: NextFunction) => {
    const controller = new AbortController();

    req.on('close', () => {
      controller.abort();
    });

    req.abortController = controller;

    next();
  };
}
