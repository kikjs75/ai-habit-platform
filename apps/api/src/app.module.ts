import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AiProxyModule } from './ai-proxy/ai-proxy.module';
import { AuthModule } from './auth/auth.module';
import { CalendarModule } from './calendar/calendar.module';
import { HealthModule } from './health/health.module';
import { MongoModule } from './mongo/mongo.module';
import { NotificationModule } from './notification/notification.module';
import { PrismaModule } from './prisma/prisma.module';
import { RecordsModule } from './records/records.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    PrismaModule,
    MongoModule,
    HealthModule,
    AiProxyModule,
    RecordsModule,
    AuthModule,
    CalendarModule,
    NotificationModule,
  ],
})
export class AppModule {}
