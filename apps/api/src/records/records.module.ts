import { Module } from '@nestjs/common';
import { AiProxyModule } from '../ai-proxy/ai-proxy.module';
import { RecordsController } from './records.controller';
import { RecordsService } from './records.service';

@Module({
  imports: [AiProxyModule],
  controllers: [RecordsController],
  providers: [RecordsService],
})
export class RecordsModule {}
