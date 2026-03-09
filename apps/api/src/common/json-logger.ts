import { WinstonModule } from 'nest-winston';
import * as winston from 'winston';
import { traceStorage } from './trace';

export function createJsonLogger() {
  return WinstonModule.createLogger({
    transports: [
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.timestamp({ format: () => new Date().toISOString() }),
          winston.format.printf((info) => {
            const { timestamp, level, message, context, ms, ...rest } = info;
            const trace = traceStorage.getStore();
            const log: Record<string, unknown> = {
              timestamp,
              level,
              service: 'nestjs-api',
              context: context ?? 'App',
              message,
            };
            if (trace?.traceId) log['trace_id'] = trace.traceId;
            if (trace?.userId) log['user_id'] = trace.userId;
            if (ms !== undefined) log['ms'] = ms;
            Object.assign(log, rest);
            return JSON.stringify(log);
          }),
        ),
      }),
    ],
  });
}
