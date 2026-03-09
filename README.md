# AI Habit Platform

A production-style backend portfolio project demonstrating a modern AI-integrated architecture.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │         Demo Client  (React / Vite  :5173)               │  │
│   └─────────────────────────┬────────────────────────────────┘  │
└─────────────────────────────┼───────────────────────────────────┘
                              │ POST /records/ocr (multipart)
                              ▼
              ┌───────────────────────────────┐
              │   NestJS API  (:3000)         │
              │                               │
              │  HealthModule   GET /health   │
              │  RecordsModule  POST /records/ocr
              │  AiProxyModule  → AI service  │
              └──────┬────────────────┬───────┘
                     │                │
          POST /ocr  │                │ store
                     ▼                ├─────────────────────────┐
         ┌───────────────────┐        ▼                         ▼
         │  FastAPI AI (:8000)│  ┌──────────────┐  ┌─────────────────────┐
         │                   │  │  PostgreSQL   │  │    MongoDB          │
         │  GET  /health     │  │  :5432        │  │    :27017           │
         │  POST /ocr        │  │               │  │                     │
         │  Tesseract OCR    │  │  users        │  │  ocr_logs           │
         └───────────────────┘  │  food_records │  │  (raw text + meta)  │
                                └──────────────┘  └─────────────────────┘
```

## Quick Start

```bash
docker compose up --build
```

All five services start automatically. On first run, Docker pulls base images and builds containers — this takes a few minutes. Subsequent runs are much faster.

## Service URLs

| Service        | URL                           |
|----------------|-------------------------------|
| Demo Client    | http://localhost:5173         |
| API Server     | http://localhost:3000         |
| Swagger Docs   | http://localhost:3000/docs    |
| AI Service     | http://localhost:8000         |
| PostgreSQL     | localhost:5432                |
| MongoDB        | localhost:27017               |

## How to Test

### 1. Demo UI

Open http://localhost:5173, select any image file containing text (e.g. a nutrition label photo), and click **Run OCR**. The extracted text and record ID are displayed on screen.

### 2. Health checks

```bash
curl http://localhost:3000/health
# {"status":"ok"}

curl http://localhost:8000/health
# {"status":"ok"}
```

### 3. OCR via curl

```bash
# Using the NestJS API (end-to-end)
curl -X POST http://localhost:3000/records/ocr \
  -F "image=@/path/to/your/image.png"

# Direct AI service call
curl -X POST http://localhost:8000/ocr \
  -F "file=@/path/to/your/image.png"
```

Expected response:
```json
{
  "text": "Nutrition Facts\nCalories 150\n...",
  "recordId": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 4. Generate a test image

```bash
cd apps/ai/samples
pip install Pillow
python create_sample.py
# -> creates sample.png with nutrition label text

curl -X POST http://localhost:3000/records/ocr \
  -F "image=@apps/ai/samples/sample.png"
```

### 5. Swagger UI

Browse and test all endpoints at http://localhost:3000/docs.

### 6. Query the databases directly

**PostgreSQL**

```bash
# Open an interactive psql session
docker exec -it ai-habit-postgres psql -U app -d app

# Useful queries
SELECT * FROM users;
SELECT id, user_id, product_name, calories, protein, created_at FROM food_records ORDER BY created_at DESC;

# Exit
\q
```

Run a one-off query without entering the shell:
```bash
docker exec ai-habit-postgres psql -U app -d app \
  -c "SELECT * FROM food_records ORDER BY created_at DESC LIMIT 10;"
```

**MongoDB**

```bash
# Open an interactive mongosh session
docker exec -it ai-habit-mongo mongosh

# Useful queries
use ai_habit
db.ocr_logs.find().sort({ createdAt: -1 }).pretty()
db.ocr_logs.countDocuments()

# Exit
exit
```

Run a one-off query without entering the shell:
```bash
docker exec ai-habit-mongo mongosh \
  --eval "db.getSiblingDB('ai_habit').ocr_logs.find().sort({ createdAt: -1 }).pretty()"
```

**GUI tools**

| Database   | Tool                | Connection                                              |
|------------|---------------------|---------------------------------------------------------|
| PostgreSQL | TablePlus / DBeaver | host `localhost:5432`, user `app`, password `app`, db `app` |
| MongoDB    | MongoDB Compass     | `mongodb://localhost:27017`                             |

## Environment Variables

모든 환경변수는 루트의 `.env`에서 관리합니다. `.env.example`을 복사해서 사용하세요.

```bash
cp .env.example .env
```

> `.env`는 `.gitignore`에 등록되어 있어 git에 커밋되지 않습니다.
> `docker-compose.yml`은 `.env`의 값을 `${VAR}` 형태로 참조합니다.

### 기본 인프라

| Variable            | Default                                   | Description                             |
|---------------------|-------------------------------------------|-----------------------------------------|
| `POSTGRES_USER`     | `app`                                     | PostgreSQL user                         |
| `POSTGRES_PASSWORD` | `app`                                     | PostgreSQL password                     |
| `POSTGRES_DB`       | `app`                                     | PostgreSQL database name                |
| `DATABASE_URL`      | `postgresql://app:app@postgres:5432/app`  | Prisma connection string                |
| `MONGO_URL`         | `mongodb://mongo:27017`                   | MongoDB connection string               |
| `AI_BASE_URL`       | `http://ai:8000`                          | AI service base URL                     |
| `VITE_API_BASE_URL` | `http://localhost:3000`                   | API URL (브라우저용, localhost 사용)     |

### Google Calendar (Phase 4)

| Variable                | Description                                                        |
|-------------------------|--------------------------------------------------------------------|
| `GOOGLE_CLIENT_ID`      | Google OAuth Client ID (`client_secret_*.json`의 `client_id`)      |
| `GOOGLE_CLIENT_SECRET`  | Google OAuth Client Secret (`client_secret_*.json`의 `client_secret`) |
| `GOOGLE_REDIRECT_URI`   | OAuth 콜백 URI (`http://localhost:3000/auth/google/callback`)       |

> `client_secret_*.json` 파일의 내용을 직접 로드하지 않고, 필요한 세 값만 환경변수로 분리해서 사용합니다.

### Firebase Cloud Messaging (Phase 4)

| Variable         | Description                                             |
|------------------|---------------------------------------------------------|
| `FCM_TEST_TOKEN` | 테스트 디바이스의 FCM Registration Token                |

> FCM 서비스 계정 인증은 `docs/etc/fcm/fcm-sender.json`을 Docker 볼륨으로 마운트합니다 (`/secrets/fcm-sender.json`).
> 이 파일도 `.gitignore`에 등록되어 있습니다.

## Project Structure

```
.
├── apps/
│   ├── api/          # NestJS backend
│   │   ├── prisma/   # Prisma schema
│   │   └── src/
│   │       ├── health/       # GET /health
│   │       ├── records/      # POST /records/ocr
│   │       ├── ai-proxy/     # AI service client
│   │       ├── prisma/       # Prisma service
│   │       ├── mongo/        # MongoDB service
│   │       ├── auth/         # Google OAuth2 (Phase 4)
│   │       ├── calendar/     # Google Calendar (Phase 4)
│   │       └── notification/ # FCM push (Phase 4)
│   ├── ai/           # FastAPI AI service (Phase 2/3)
│   │   └── samples/  # Sample images for testing
│   └── demo/         # React demo client (Phase 1.5)
├── docs/             # Architecture & phase docs
├── .env.example      # 환경변수 템플릿 (민감한 값은 .env에만 보관)
├── docker-compose.yml
└── README.md
```

## Database Schema

### PostgreSQL (Prisma)

```sql
users        (id, email, created_at)
food_records (id, user_id, raw_text, product_name, calories, protein, created_at)
```

### MongoDB

```
ocr_logs: { userId, rawText, source, createdAt }
```

A demo user (`demo@local`) is created automatically on API startup.

## Development (without Docker)

```bash
# API
cd apps/api
cp .env.example .env   # edit DATABASE_URL, MONGO_URL, AI_BASE_URL
npm install
npx prisma db push
npm run start:dev

# AI service
cd apps/ai
pip install -r requirements.txt
uvicorn main:app --reload

# Demo
cd apps/demo
cp .env.example .env
npm install
npm run dev
```

## Resetting the Database

To clear all data from both databases:

**PostgreSQL** — truncate `food_records` and `users` together:

```bash
docker exec ai-habit-postgres psql -U app -d app \
  -c "TRUNCATE food_records, users RESTART IDENTITY CASCADE;"
```

**MongoDB** — delete all documents from `ocr_logs`:

```bash
docker exec ai-habit-mongo mongosh \
  --eval "db.getSiblingDB('ai_habit').ocr_logs.deleteMany({})"
```

**Both at once:**

```bash
docker exec ai-habit-postgres psql -U app -d app \
  -c "TRUNCATE food_records, users RESTART IDENTITY CASCADE;" && \
docker exec ai-habit-mongo mongosh \
  --eval "db.getSiblingDB('ai_habit').ocr_logs.deleteMany({})"
```

> The demo user (`demo@local`) is automatically re-created on the next API request.

## Development Progress

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Project Setup — monorepo, Docker Compose | ✅ Done |
| 1 | Backend API — NestJS, PostgreSQL, MongoDB | ✅ Done |
| 1.5 | Demo Client — React image upload + OCR result | ✅ Done |
| 2 | AI Service — FastAPI + Tesseract OCR | ✅ Done |
| 3 | LLM Processing — structured data extraction | ✅ Done |
| 4 | External Integration — Google Calendar + FCM | ✅ Done |
| 5 | Elasticsearch — log storage | ✅ Done |
| 6 | Filebeat — log collection | ✅ Done |
| 7 | Logstash — log parsing pipeline | ✅ Done |
| 8 | Kibana — dashboard & visualization | ✅ Done |

### Phase 4 구현 내용

**Google Calendar 연동**
- Google OAuth 2.0 웹 서버 플로우 구현 (`GET /auth/google` → 콜백 → 토큰 인메모리 저장)
- 식사/물 마시기 리마인더 이벤트 생성 (`POST /calendar/events`)
- 스코프: `https://www.googleapis.com/auth/calendar.events`

**Firebase Cloud Messaging (FCM) 연동**
- Firebase Admin SDK 기반 서버 푸시 전송 (`POST /notifications/send`)
- 서비스 계정 JSON을 Docker 볼륨으로 마운트하여 인증
- 테스트 디바이스 토큰은 환경변수(`FCM_TEST_TOKEN`)로 관리

**Demo UI 업데이트**
- Google Calendar 인증 버튼 + 이벤트 생성 폼 추가
- FCM 알림 전송 폼 추가

**새 API 엔드포인트**

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/auth/google` | Google OAuth 인증 페이지 리다이렉트 |
| `GET` | `/auth/google/callback` | OAuth 콜백 처리 (토큰 저장) |
| `POST` | `/calendar/events` | 캘린더 리마인더 이벤트 생성 |
| `POST` | `/notifications/send` | FCM 푸시 알림 전송 |

### Phase 4 사용 흐름

```bash
# 1. Google Calendar 인증 (브라우저에서)
open http://localhost:3000/auth/google

# 2. 캘린더 이벤트 생성
curl -X POST http://localhost:3000/calendar/events \
  -H "Content-Type: application/json" \
  -d '{"type":"meal","time":"2026-03-08T12:00:00+09:00"}'

# 3. FCM 푸시 전송
curl -X POST http://localhost:3000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{"message":"Don'\''t forget to log your meal!"}'
```

### Phase 4 동작 확인 (2026-03-08)

**Google Calendar OAuth2 흐름**

| 단계 | 화면 |
|------|------|
| ① 미확인 앱 경고 (테스트 모드) | ![oauth1](images/oauth2_capture_1.jpg) |
| ② 캘린더 권한 동의 | ![oauth2](images/oauth2_capture_2.jpg) |
| ③ 인증 완료 콜백 | ![oauth3](images/oauth2_capture_3.jpg) |

**Google Calendar 이벤트 생성**

| 단계 | 화면 |
|------|------|
| API 응답 (eventId 반환) | ![cal1](images/fcm_capture_1.jpg) |
| Google Calendar 등록 확인 | ![cal2](images/fcm_capture_2.jpg) |

**FCM 푸시 알림**

| 단계 | 화면 |
|------|------|
| API 응답 (messageId 반환) | ![fcm1](images/fcm_capture_3.jpg) |
| 알림 권한 요청 (Android) | ![fcm2](images/fcm_capture_4.jpg) |
| 알림 수신 확인 (Android 에뮬레이터) | ![fcm3](images/fcm_capture_5.jpg) |

### Phase 4 환경변수 설정 방법

민감한 값은 `.env`에만 보관합니다 (gitignore 처리). `docker-compose.yml`은 `${VAR}` 참조만 사용합니다.

```bash
# .env 에 아래 항목 추가
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
FCM_TEST_TOKEN=...
```

FCM 서비스 계정 JSON(`fcm-sender.json`)은 Docker 볼륨으로 마운트합니다 — 별도 환경변수 불필요.

> 자세한 항목은 [환경변수 섹션](#environment-variables)을 참고하세요.

## License

Portfolio demonstration purposes only.
© 2026 Jinsu Kim
