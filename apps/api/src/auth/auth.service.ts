import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { google, Auth } from 'googleapis';

@Injectable()
export class AuthService {
  private readonly logger = new Logger(AuthService.name);
  private readonly oauth2Client: Auth.OAuth2Client;
  private tokens: Auth.Credentials | null = null;

  constructor(private config: ConfigService) {
    this.oauth2Client = new google.auth.OAuth2(
      config.get('GOOGLE_CLIENT_ID'),
      config.get('GOOGLE_CLIENT_SECRET'),
      config.get('GOOGLE_REDIRECT_URI'),
    );
  }

  getAuthUrl(): string {
    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: ['https://www.googleapis.com/auth/calendar.events'],
    });
  }

  async handleCallback(code: string): Promise<void> {
    const { tokens } = await this.oauth2Client.getToken(code);
    this.oauth2Client.setCredentials(tokens);
    this.tokens = tokens;
    this.logger.log('Google OAuth tokens stored in memory');
  }

  getClient(): Auth.OAuth2Client {
    return this.oauth2Client;
  }

  isAuthenticated(): boolean {
    return !!this.tokens;
  }
}
