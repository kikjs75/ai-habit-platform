import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as admin from 'firebase-admin';
import * as fs from 'fs';

@Injectable()
export class NotificationService implements OnModuleInit {
  private readonly logger = new Logger(NotificationService.name);

  constructor(private readonly config: ConfigService) {}

  onModuleInit() {
    if (!admin.apps.length) {
      const keyPath = this.config.get<string>('FCM_KEY_PATH', '/secrets/fcm-sender.json');
      const serviceAccount = JSON.parse(fs.readFileSync(keyPath, 'utf-8'));
      admin.initializeApp({
        credential: admin.credential.cert(serviceAccount),
      });
      this.logger.log('Firebase Admin SDK initialized');
    }
  }

  async sendPush(token: string, message: string): Promise<string> {
    const messageId = await admin.messaging().send({
      token,
      notification: {
        title: 'AI Habit Reminder',
        body: message,
      },
    });
    this.logger.log(`FCM message sent: ${messageId}`);
    return messageId;
  }

  getTestToken(): string {
    return this.config.get<string>('FCM_TEST_TOKEN', '');
  }
}
