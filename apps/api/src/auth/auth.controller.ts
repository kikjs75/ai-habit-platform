import { Controller, Get, Query, Redirect, Res } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { Response } from 'express';
import { AuthService } from './auth.service';

@ApiTags('Auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Get('google')
  @ApiOperation({ summary: 'Google OAuth 인증 페이지로 리다이렉트' })
  @Redirect()
  redirectToGoogle() {
    const url = this.authService.getAuthUrl();
    return { url };
  }

  @Get('google/callback')
  @ApiOperation({ summary: 'Google OAuth 콜백 처리' })
  async googleCallback(@Query('code') code: string, @Res() res: Response) {
    await this.authService.handleCallback(code);
    res.send(`
      <html><body style="font-family:sans-serif;text-align:center;padding:60px">
        <h2>Google Calendar 인증 완료!</h2>
        <p>이 창을 닫고 데모 페이지로 돌아가세요.</p>
        <script>setTimeout(() => window.close(), 2000);</script>
      </body></html>
    `);
  }
}
