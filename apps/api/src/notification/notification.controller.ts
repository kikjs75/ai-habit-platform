import { Body, Controller, Post } from '@nestjs/common';
import { ApiBody, ApiOperation, ApiTags } from '@nestjs/swagger';
import { NotificationService } from './notification.service';

class SendNotificationDto {
  token?: string;
  message: string;
}

@ApiTags('Notification')
@Controller('notifications')
export class NotificationController {
  constructor(private readonly notificationService: NotificationService) {}

  @Post('send')
  @ApiOperation({ summary: 'FCM 푸시 알림 전송' })
  @ApiBody({
    schema: {
      example: { message: "Don't forget to log your meal!" },
    },
  })
  async send(@Body() body: SendNotificationDto) {
    const token = body.token ?? this.notificationService.getTestToken();
    const messageId = await this.notificationService.sendPush(token, body.message);
    return { messageId, token };
  }
}
