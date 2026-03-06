# Phase 1 — Backend API

Goal

Create the main backend service.

Technology

Node.js  
TypeScript  
NestJS  
PostgreSQL

Core APIs

User API

POST /users  
create user

POST /auth/login  
login user

Habit API

POST /habits  
create habit

GET /habits  
list habits

Food Record API

POST /records  
create food record

GET /records  
get user records

Database

PostgreSQL

tables

users

food_records

food_records fields

- id
- user_id
- raw_text
- product_name
- calories
- protein
- created_at

Requirements

REST API design  
Swagger documentation  
PostgreSQL integration

Deliverables

Working NestJS API server
