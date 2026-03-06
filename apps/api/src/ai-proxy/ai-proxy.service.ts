import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';
import FormData = require('form-data');

export interface OcrResult {
  text: string;
  engine: string;
}

@Injectable()
export class AiProxyService {
  private readonly logger = new Logger(AiProxyService.name);

  constructor(private config: ConfigService) {}

  async runOcr(file: Express.Multer.File): Promise<OcrResult> {
    const aiBaseUrl = this.config.get<string>('AI_BASE_URL', 'http://ai:8000');

    const formData = new FormData();
    formData.append('file', file.buffer, {
      filename: file.originalname || 'upload.png',
      contentType: file.mimetype || 'image/png',
    });

    this.logger.log(`Forwarding OCR request to ${aiBaseUrl}/ocr`);

    const response = await axios.post<OcrResult>(`${aiBaseUrl}/ocr`, formData, {
      headers: formData.getHeaders(),
      timeout: 30000,
    });

    return response.data;
  }
}
