import { AsyncLocalStorage } from 'async_hooks';
import { randomUUID } from 'crypto';

export interface TraceContext {
  traceId: string;
  userId: string;
}

export const traceStorage = new AsyncLocalStorage<TraceContext>();

export function newId(): string {
  return randomUUID();
}
