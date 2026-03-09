import {
  CallHandler,
  ExecutionContext,
  Injectable,
  Logger,
  NestInterceptor,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { newId, traceStorage } from './trace';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const req = context.switchToHttp().getRequest();
    const { method, url } = req;
    const traceId = (req.headers['x-trace-id'] as string) || newId();
    const userId = (req.headers['x-user-id'] as string) || 'anonymous';
    const spanId = newId();
    const start = Date.now();

    return new Observable((subscriber) => {
      traceStorage.run({ traceId, userId }, () => {
        next
          .handle()
          .pipe(
            tap({
              next: () => {
                const res = context.switchToHttp().getResponse();
                const duration_ms = Date.now() - start;
                this.logger.log({
                  message: `${method} ${url} ${res.statusCode}`,
                  method,
                  url,
                  status_code: res.statusCode,
                  duration_ms,
                  trace_id: traceId,
                  span_id: spanId,
                  user_id: userId,
                });
              },
              error: (err: { status?: number }) => {
                const status = err?.status ?? 500;
                const duration_ms = Date.now() - start;
                this.logger.error({
                  message: `${method} ${url} ${status}`,
                  method,
                  url,
                  status_code: status,
                  duration_ms,
                  trace_id: traceId,
                  span_id: spanId,
                  user_id: userId,
                });
              },
            }),
          )
          .subscribe(subscriber);
      });
    });
  }
}
