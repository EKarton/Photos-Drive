import type { Request } from 'express';
import { ipKeyGenerator } from 'express-rate-limit';

export function normalizedIp(ip: string): string {
  return ip.replace(/:\d+[^:]*$/, '');
}

export function rateLimitKey(req: Request): string {
  const ip = req.ip!.includes('.') ? normalizedIp(req.ip!) : req.ip!;
  return ipKeyGenerator(ip, 64);
}
