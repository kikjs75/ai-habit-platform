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

Verification scripts:

- Location: `scripts/verify/`
- Runner: `./scripts/verify/run.sh [phase]`
- Dependencies: `pip install -r scripts/verify/requirements.txt`
- Reference: `docs/phase-verification-template.md`

Claude should implement the project **phase by phase**, and each phase must pass verification before the next begins.

Memory management

After completing any meaningful work (new feature, bug fix, design decision, config change), always update `/home/node/.claude/projects/-workspace/memory/MEMORY.md` to reflect the latest state.
