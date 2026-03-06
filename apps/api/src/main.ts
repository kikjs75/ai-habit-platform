import { Logger } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app.module';
import { PrismaService } from './prisma/prisma.service';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    logger: ['error', 'warn', 'log'],
  });

  app.enableCors();

  // Swagger
  const swaggerConfig = new DocumentBuilder()
    .setTitle('AI Habit Platform API')
    .setDescription('Backend API for AI Habit Platform — Phase 1')
    .setVersion('1.0')
    .build();
  const document = SwaggerModule.createDocument(app, swaggerConfig);
  SwaggerModule.setup('docs', app, document);

  // Seed demo user
  const prisma = app.get(PrismaService);
  await prisma.user.upsert({
    where: { email: 'demo@local' },
    update: {},
    create: { email: 'demo@local' },
  });
  Logger.log('Demo user ensured: demo@local', 'Bootstrap');

  await app.listen(3000);
  Logger.log('API running at http://localhost:3000', 'Bootstrap');
  Logger.log('Swagger docs at http://localhost:3000/docs', 'Bootstrap');
}

bootstrap();
