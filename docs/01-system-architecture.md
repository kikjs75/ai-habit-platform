# System Architecture

High-level architecture

Client
↓
NestJS Backend API
↓
Python AI Service
↓
OCR / LLM processing

Databases

PostgreSQL

stores application data

tables

- users
- habits
- food_records

MongoDB

stores AI processing logs

collections

- ocr_logs
- llm_results

External integrations

Google Calendar API
Firebase Cloud Messaging

Log monitoring (ELK Stack)

Filebeat

collects Docker container logs from NestJS API and FastAPI AI service

Logstash

parses and transforms logs, routes to Elasticsearch

- pipeline: Filebeat → Logstash → Elasticsearch
- NestJS grok filter: pid, timestamp, log_level, context
- FastAPI grok filter: method, path, status_code

Elasticsearch

stores structured logs

indices

- ai-habit-api-logs-* (NestJS API logs)
- ai-habit-ai-logs-* (FastAPI AI logs)

Kibana

visualizes logs via dashboards

- API 요청 모니터링 대시보드
- AI 처리 모니터링 대시보드
