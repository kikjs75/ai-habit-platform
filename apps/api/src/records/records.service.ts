import { Injectable, Logger } from '@nestjs/common';
import { AiProxyService } from '../ai-proxy/ai-proxy.service';
import { MongoService } from '../mongo/mongo.service';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class RecordsService {
  private readonly logger = new Logger(RecordsService.name);

  constructor(
    private aiProxy: AiProxyService,
    private prisma: PrismaService,
    private mongo: MongoService,
  ) {}

  async processOcr(
    file: Express.Multer.File,
  ): Promise<{ text: string; recordId: string }> {
    // 1. Run OCR via AI service
    const ocrResult = await this.aiProxy.runOcr(file);
    const { text } = ocrResult;

    // 2. Resolve demo user
    const user = await this.prisma.user.upsert({
      where: { email: 'demo@local' },
      update: {},
      create: { email: 'demo@local' },
    });

    // 3. Store normalized record in Postgres
    const record = await this.prisma.foodRecord.create({
      data: {
        userId: user.id,
        rawText: text,
      },
    });

    // 4. Store log document in Mongo
    await this.mongo.insertOcrLog({
      userId: user.id,
      rawText: text,
      source: 'ocr',
    });

    this.logger.log(`Created food_record ${record.id}`);

    return { text, recordId: record.id };
  }
}
