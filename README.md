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

### Root / Docker Compose

| Variable           | Default                                | Description                    |
|--------------------|----------------------------------------|--------------------------------|
| `POSTGRES_USER`    | `app`                                  | PostgreSQL user                |
| `POSTGRES_PASSWORD`| `app`                                  | PostgreSQL password            |
| `POSTGRES_DB`      | `app`                                  | PostgreSQL database name       |

### apps/api

| Variable       | Default                              | Description                      |
|----------------|--------------------------------------|----------------------------------|
| `DATABASE_URL` | `postgresql://app:app@postgres:5432/app` | Prisma connection string     |
| `MONGO_URL`    | `mongodb://mongo:27017`              | MongoDB connection string        |
| `AI_BASE_URL`  | `http://ai:8000`                     | AI service base URL              |

### apps/demo

| Variable            | Default                   | Description                               |
|---------------------|---------------------------|-------------------------------------------|
| `VITE_API_BASE_URL` | `http://localhost:3000`   | API URL (browser-side, use `localhost`)   |

## Project Structure

```
.
├── apps/
│   ├── api/          # NestJS backend (Phase 1)
│   │   ├── prisma/   # Prisma schema
│   │   └── src/
│   │       ├── health/     # GET /health
│   │       ├── records/    # POST /records/ocr
│   │       ├── ai-proxy/   # AI service client
│   │       ├── prisma/     # Prisma service
│   │       └── mongo/      # MongoDB service
│   ├── ai/           # FastAPI AI service (Phase 2)
│   │   └── samples/  # Sample images for testing
│   └── demo/         # React demo client (Phase 1.5)
├── docs/             # Architecture & phase docs
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

## License

Portfolio demonstration purposes only.
© 2026 Jinsu Kim
