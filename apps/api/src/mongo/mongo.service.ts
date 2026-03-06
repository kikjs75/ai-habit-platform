import {
  Injectable,
  Logger,
  OnModuleDestroy,
  OnModuleInit,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Db, MongoClient } from 'mongodb';

@Injectable()
export class MongoService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(MongoService.name);
  private client: MongoClient;
  private db: Db;

  constructor(private config: ConfigService) {}

  async onModuleInit() {
    const url = this.config.get<string>('MONGO_URL', 'mongodb://mongo:27017');
    this.client = new MongoClient(url);
    await this.client.connect();
    this.db = this.client.db('ai_habit');
    this.logger.log('MongoDB connected');
  }

  async onModuleDestroy() {
    await this.client.close();
  }

  async insertOcrLog(data: {
    userId: string;
    rawText: string;
    source: string;
  }): Promise<string> {
    const collection = this.db.collection('ocr_logs');
    const result = await collection.insertOne({
      ...data,
      createdAt: new Date(),
    });
    return result.insertedId.toString();
  }

  async insertLlmResult(data: {
    userId: string;
    rawText: string;
    structuredOutput: Record<string, unknown>;
  }): Promise<string> {
    const collection = this.db.collection('llm_results');
    const result = await collection.insertOne({
      ...data,
      timestamp: new Date(),
    });
    return result.insertedId.toString();
  }
}
