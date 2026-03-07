import { Body, Controller, Post } from '@nestjs/common';
import { ApiBody, ApiOperation, ApiTags } from '@nestjs/swagger';
import { CalendarService } from './calendar.service';

class CreateEventDto {
  type: 'meal' | 'water';
  time: string; // ISO 8601 datetime string
}

@ApiTags('Calendar')
@Controller('calendar')
export class CalendarController {
  constructor(private readonly calendarService: CalendarService) {}

  @Post('events')
  @ApiOperation({ summary: 'Google Calendar 리마인더 이벤트 생성' })
  @ApiBody({
    schema: {
      example: { type: 'meal', time: '2026-03-08T12:00:00+09:00' },
    },
  })
  createEvent(@Body() body: CreateEventDto) {
    return this.calendarService.createEvent(body.type, body.time);
  }
}
