import type { Request } from 'express';
import { ipKeyGenerator } from 'express-rate-limit';

export function rateLimitKey(req: Request): string {
  return ipKeyGenerator(req.ip || 'unknown', 64);
}
