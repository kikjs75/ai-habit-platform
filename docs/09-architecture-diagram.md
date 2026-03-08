# Architecture Diagram

System architecture

Client
↓
Demo Web UI
↓
NestJS API Server
↓
Python AI Service

AI processing

Image Upload  
↓  
OCR Extraction  
↓  
LLM Structuring

Databases

PostgreSQL

application data

MongoDB

AI logs

External services

Google Calendar API

Firebase Cloud Messaging

Log pipeline (ELK Stack)

NestJS API (stdout)  ─┐
                       ├─► Filebeat ─► Logstash ─► Elasticsearch ─► Kibana
FastAPI AI (stdout)  ─┘

Ports

| Service | Port |
|---------|------|
| Demo (React) | 5173 |
| NestJS API | 3000 |
| FastAPI AI | 8000 |
| PostgreSQL | 5432 |
| MongoDB | 27017 |
| Elasticsearch | 9200 |
| Logstash Beats | 5044 |
| Logstash API | 9600 |
| Kibana | 5601 |
