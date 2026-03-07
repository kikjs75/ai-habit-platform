import { BadRequestException, Injectable, Logger } from '@nestjs/common';
import { google, Auth } from 'googleapis';
import { AuthService } from '../auth/auth.service';

@Injectable()
export class CalendarService {
  private readonly logger = new Logger(CalendarService.name);

  constructor(private readonly authService: AuthService) {}

  async createEvent(type: 'meal' | 'water', time: string): Promise<{ eventId: string; htmlLink: string }> {
    if (!this.authService.isAuthenticated()) {
      throw new BadRequestException(
        'Google Calendar 인증이 필요합니다. GET /auth/google 로 먼저 인증하세요.',
      );
    }

    const calendar = google.calendar({ version: 'v3', auth: this.authService.getClient() });

    const title = type === 'meal' ? '식사 리마인더' : '물 마시기 리마인더';
    const description =
      type === 'meal'
        ? '식사 시간입니다! 음식을 기록해보세요.'
        : '물을 마실 시간입니다! 수분을 보충하세요.';

    const startTime = new Date(time);
    const endTime = new Date(startTime.getTime() + 30 * 60 * 1000);

    const result = await calendar.events.insert({
      calendarId: 'primary',
      requestBody: {
        summary: title,
        description,
        start: { dateTime: startTime.toISOString(), timeZone: 'Asia/Seoul' },
        end: { dateTime: endTime.toISOString(), timeZone: 'Asia/Seoul' },
      },
    });

    this.logger.log(`Calendar event created: ${result.data.htmlLink}`);
    return { eventId: result.data.id!, htmlLink: result.data.htmlLink! };
  }
}
