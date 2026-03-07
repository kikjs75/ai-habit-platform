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

Development principles

- clean architecture
- modular design
- containerized environment
- API documentation
- maintainable code

Claude should implement the project **phase by phase**.

Memory management

After completing any meaningful work (new feature, bug fix, design decision, config change), always update `/home/node/.claude/projects/-workspace/memory/MEMORY.md` to reflect the latest state.
