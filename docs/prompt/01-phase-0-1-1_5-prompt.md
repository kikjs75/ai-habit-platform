You are Claude Code working inside a new repository.

Read CLAUDE.md and docs/* first. Then implement Phase 0 and Phase 1 and Phase 1.5.

Goal:
Create a monorepo backend portfolio project "AI Habit Platform" with:
- NestJS (TypeScript) backend API (apps/api)
- Python FastAPI AI service (apps/ai)
- React demo client (apps/demo)
- PostgreSQL for application data
- MongoDB for AI processing logs
- Docker Compose for local dev

Hard requirements:
1) Everything must run locally with ONE command:
   docker compose up --build
2) Provide clear environment variables via .env.example and per-app .env.example
3) Provide Swagger/OpenAPI for API (NestJS)
4) Provide health endpoints:
   - apps/api: GET /health
   - apps/ai:  GET /health
5) Provide a minimal end-to-end flow (even if LLM is stubbed):
   - Demo uploads an image -> calls NestJS -> NestJS forwards to AI service OCR -> returns extracted text -> NestJS stores:
     - Postgres: normalized record row (user_id can be a fixed demo user)
     - Mongo: log document containing raw text + timestamps
   - Demo shows the OCR text result on screen

Monorepo structure:
- CLAUDE.md (already exists)
- docs/* (already exists)
- apps/api (NestJS)
- apps/ai (FastAPI)
- apps/demo (React)
- docker-compose.yml
- README.md

Implementation details:

A) apps/api (NestJS)
- Use NestJS with modules:
  - HealthModule (GET /health)
  - RecordsModule
  - AiProxyModule (client to apps/ai)
- Endpoints:
  - POST /records/ocr
    multipart/form-data with file "image"
    behavior:
      1) send image to AI service POST /ocr
      2) receive { text: "...", confidence?: number }
      3) store normalized record to Postgres table food_records
      4) store log document to Mongo collection ocr_logs
      5) return response { text, recordId }
- DB layer:
  - Use Prisma (recommended) or TypeORM, choose ONE and implement cleanly.
  - Postgres schema:
    users(id, email, created_at)
    food_records(id, user_id, raw_text, created_at)
    Optionally store structured fields later.
  - For demo, create a single seed user (email: demo@local) automatically on startup if not exists.
- Mongo:
  - Connect using official Mongo driver or Mongoose; choose ONE.
  - Store ocr_logs:
    { userId, rawText, createdAt, source:"ocr" }
- Config:
  - Use @nestjs/config
  - Validate env vars
- Swagger:
  - Enable Swagger at /docs
- Logging:
  - Add structured JSON logging (simple pino is ok)

B) apps/ai (FastAPI)
- Endpoints:
  - GET /health -> { status:"ok" }
  - POST /ocr -> accept image file -> run OCR
- OCR:
  - Use Tesseract.
  - If OCR dependencies are missing in container, add them in Dockerfile.
  - Return JSON: { text: "...", engine:"tesseract" }
- Add a sample image under apps/ai/samples and a short doc on how to test.

C) apps/demo (React)
- Simple page:
  - file input
  - button "Run OCR"
  - calls POST http://localhost:3000/records/ocr (or whatever port mapping you choose)
  - show extracted text and recordId
- Minimal styling ok.
- Provide .env.example for API base URL

D) docker-compose.yml
- Services:
  - api (port 3000)
  - ai  (port 8000)
  - postgres (port 5432)
  - mongo (port 27017)
- Set up networks and depends_on
- Provide volumes for DB persistence
- Provide healthchecks if easy

E) README.md
Must include:
- Architecture overview (ASCII diagram)
- How to run (docker compose up --build)
- How to test:
  - Demo UI URL
  - Swagger URL
  - curl examples
- Environment variables table

F) Quality gates
- Ensure consistent formatting (prettier for TS, black/ruff for Python)
- Provide basic lint/test scripts in package.json and pyproject or requirements
- Avoid overly complex features; focus on working end-to-end.

Deliverables:
- Commit-ready repository state with all code and docs updated.
- Ensure Phase 0/1/1.5 are satisfied.

Start now: generate all files and code.
