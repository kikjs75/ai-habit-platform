# AI Habit Platform

AI-integrated backend portfolio project demonstrating a modern backend architecture.

This project showcases how to integrate:

- NestJS backend API
- Python FastAPI AI service
- OCR processing (Tesseract)
- PostgreSQL application database
- MongoDB AI processing logs
- Docker-based development environment
- React demo client

---

# System Architecture

```mermaid
graph TD

Client[User Browser]
Demo[React Demo Client]
API[NestJS Backend API]
AI[FastAPI AI Service]
OCR[Tesseract OCR Engine]
PG[(PostgreSQL)]
Mongo[(MongoDB)]

Client --> Demo
Demo --> API
API --> AI
AI --> OCR
API --> PG
API --> Mongo

Image Upload
↓
Demo Client
↓
NestJS API
↓
AI Service (OCR)
↓
OCR Text Returned
↓
Store Result (PostgreSQL)
↓
Store Logs (MongoDB)

# Project README

## Development Environment Structure

devcontainer.json
- development tools
- editor environment
- node / python / pnpm / git

docker-compose.yml
- postgres
- mongo
- api
- ai
- demo

apps/ai/Dockerfile
- tesseract

## Running the Project

Start all services with Docker Compose.

```bash
docker compose up --build
```

After startup the following services will be available.

| Service | URL |
|---|---|
| Demo Client | http://localhost:5173 |
| API Server | http://localhost:3000 |
| Swagger API Docs | http://localhost:3000/docs |
| AI Service | http://localhost:8000 |

---

## Phase 0,1,1.5 - Execution / Verification Checklist

Once generated from this prompt, it is considered a success if the following conditions are met locally.

Run
bashdocker compose up --build

Success Criteria
1. Demo Client

 Confirm image upload and result display at http://localhost:5173 (or 3001, etc.)

2. NestJS Swagger

 Confirm access to http://localhost:3000/docs

3. Health Check

 GET http://localhost:3000/health
 GET http://localhost:8000/health

4. Upload Call Verification

 Upload API call is processed successfully, and

 Confirm row created in PostgreSQL food_records table
 Confirm document created in MongoDB ocr_logs collection


## Phase 0 — Project Setup

Prepare the monorepo development environment.

### Infrastructure Components

- NestJS API container
- FastAPI AI container
- PostgreSQL database
- MongoDB database
- React demo client

### Service Ports

| Service | Port |
|---|---|
| API | 3000 |
| AI Service | 8000 |
| Demo Client | 5173 |
| PostgreSQL | 5432 |
| MongoDB | 27017 |

> The entire development environment runs through Docker Compose.

---

## Phase 1 — Backend API

The backend server is implemented using NestJS.

### Core API Endpoints

| Endpoint | Description |
|---|---|
| `POST /records/ocr` | Upload image and run OCR |
| `GET /health` | API health check |

### Swagger Documentation

```
http://localhost:3000/docs
```

### Database Storage

**PostgreSQL Tables**

```
users
habits
food_records
```

**MongoDB Collections**

```
ocr_logs
```

- PostgreSQL stores normalized application data.
- MongoDB stores AI processing logs.

---

## Phase 1.5 — Demo Client

A simple React application is provided to test the backend.

### Demo URL

```
http://localhost:5173
```

### Features

- Image upload
- Run OCR API request
- Display extracted OCR text
- Display created record ID

### Purpose

Allow reviewers and interviewers to easily test the backend system.

---

## Future Phases

### Phase 2 — AI Service Improvements

- OCR accuracy improvements
- Image preprocessing
- Asynchronous processing

### Phase 3 — LLM Data Structuring

Convert OCR text into structured JSON.

**Example**

```json
{
  "product_name": "Milk",
  "calories": 120,
  "protein": "6g"
}
```

- Structured data will be stored in PostgreSQL.
- AI processing logs will be stored in MongoDB.

### Phase 4 — External Integration

- Google Calendar API integration
- Firebase Cloud Messaging
- Reminder notifications

---

## Portfolio Purpose

This project demonstrates the following engineering capabilities.

- Backend API architecture
- AI service integration
- OCR processing pipelines
- Database modeling
- Containerized development
- External API integration
- Modular backend design

---

## License

This repository is provided for portfolio demonstration purposes only.  
Unauthorized copying, modification, or commercial use of the code is prohibited.

© 2026 Jinsu Kim
