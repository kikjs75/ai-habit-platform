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
