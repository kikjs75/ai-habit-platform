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

  async processOcr(file: Express.Multer.File): Promise<{
    text: string;
    recordId: string;
    productName: string | null;
    calories: number | null;
    protein: string | null;
  }> {
    // 1. Run OCR via AI service
    const ocrResult = await this.aiProxy.runOcr(file);
    const { text } = ocrResult;

    // 2. Resolve demo user
    const user = await this.prisma.user.upsert({
      where: { email: 'demo@local' },
      update: {},
      create: { email: 'demo@local' },
    });

    // 3. Store raw record in PostgreSQL
    const record = await this.prisma.foodRecord.create({
      data: { userId: user.id, rawText: text },
    });

    // 4. Store OCR log in MongoDB
    await this.mongo.insertOcrLog({
      userId: user.id,
      rawText: text,
      source: 'ocr',
    });

    this.logger.log(`Created food_record ${record.id}, running LLM structuring`);

    // 5. Run LLM structuring via AI service
    const llmResult = await this.aiProxy.runLlm(text);

    // 6. Update food_record with structured fields
    await this.prisma.foodRecord.update({
      where: { id: record.id },
      data: {
        productName: llmResult.product_name ?? null,
        calories: llmResult.calories ?? null,
        protein: llmResult.protein ?? null,
      },
    });

    // 7. Store LLM result log in MongoDB
    await this.mongo.insertLlmResult({
      userId: user.id,
      rawText: text,
      structuredOutput: llmResult as unknown as Record<string, unknown>,
    });

    this.logger.log(`food_record ${record.id} updated with LLM structured data`);

    return {
      text,
      recordId: record.id,
      productName: llmResult.product_name ?? null,
      calories: llmResult.calories ?? null,
      protein: llmResult.protein ?? null,
    };
  }
}
