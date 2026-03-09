# Claude Development Guide

This repository contains a backend portfolio project demonstrating a modern AI-integrated backend architecture.

Project name

AI Habit Platform

Goal

Build a production-style backend system integrating:

- Node.js backend API (NestJS)
- Python AI service
- OCR processing
- LLM text structuring
- PostgreSQL for application data
- MongoDB for AI processing logs
- Google Calendar integration
- Firebase Cloud Messaging (FCM)

Repository structure

apps/api  
NestJS backend service

apps/ai  
Python FastAPI AI service

apps/demo  
Simple frontend for testing APIs

docs  
Architecture and development phases

Development must follow the phases defined in the docs directory.

Implementation order

Phase 0 → Project Setup
Phase 1 → Backend API
Phase 1.5 → Demo Client
Phase 2 → AI Service
Phase 3 → LLM Processing
Phase 4 → External Integration
Phase 5 → Elasticsearch
Phase 6 → Filebeat
Phase 7 → Logstash
Phase 8 → Kibana

Development principles

- clean architecture
- modular design
- containerized environment
- API documentation
- maintainable code

Testing and verification

Claude must follow a TDD-based verification process for every phase.

Rules:

1. Write or update the verification script in `scripts/verify/test_phaseN.py` alongside the implementation — not after.
2. A phase is not complete until all tests in `./scripts/verify/run.sh N` pass.
3. Do not proceed to the next phase until the current phase verification passes.
4. After verification passes, update `docs/phase-status.md` to mark the phase complete with the date.
5. After verification passes, update the `## Development Progress` table in `README.md` to reflect the latest status.

Verification coverage checklist (apply to every phase):

- [ ] Service health check — each service responds on its port
- [ ] Functional test — actual endpoints called with real input, not just health
- [ ] Integration test — cross-service flow verified end-to-end (e.g. NestJS → FastAPI → DB)
- [ ] Timing / retry — async pipelines (Filebeat, Logstash) polled with timeout, not assumed instant
- [ ] Compose readiness — all required containers running/healthy before tests run

Verification scripts:

- Location: `scripts/verify/`
- Runner: `./scripts/verify/run.sh [phase]`
- Compose check: `./scripts/verify/check_compose.sh`
- Full run with LLM: `./scripts/verify/run.sh --all`
- Dependencies: `pip3 install -r scripts/verify/requirements.txt`
- Reference: `docs/phase-verification-template.md`

Test file responsibilities:

- `test_phase1.py` — NestJS /health, FastAPI /health, Swagger
- `test_phase2.py` — FastAPI OCR: real image upload, text extraction
- `test_phase3.py` — Integration: POST /records/ocr → OCR → LLM → DB (slow, ~120s)
- `test_phase4.py` — Phase 4 endpoints registered: /auth/google, /calendar/events, /notifications/send
- `test_phase5.py` — Elasticsearch cluster health
- `test_phase6.py` — Filebeat → ES ingestion with retry (60s timeout)
- `test_phase7.py` — Logstash JSON field structure with retry (60s timeout)
- `test_phase8.py` — Kibana status and Data Views

Claude should implement the project **phase by phase**, and each phase must pass verification before the next begins.

Documentation before commit

Before every commit or commit & push, Claude must verify that all related documentation is up to date.

Rules:

1. Identify which docs are affected by the change (README.md, docs/*.md, scripts/*/README.md, etc.).
2. Update every affected document to reflect the actual behavior — not the intended behavior.
3. Documentation must be updated in the **same commit** as the code change, not in a follow-up commit.
4. If a new feature, option, or behavior is added, the following must be present in the docs before committing:
   - What it does (purpose)
   - How to use it (CLI options, config fields, examples)
   - How to verify it works (test steps and expected output)
5. Do not commit with a placeholder like "TODO: update docs". Docs must be complete at commit time.

Memory management

After completing any meaningful work (new feature, bug fix, design decision, config change), always update `/home/node/.claude/projects/-workspace/memory/MEMORY.md` to reflect the latest state.
