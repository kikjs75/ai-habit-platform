# Phase 3 — LLM Processing

Goal

Convert OCR text into structured data.

Example OCR text

Milk  
Calories 120  
Protein 6g

LLM structured output

{
 "product_name": "Milk",
 "calories": 120,
 "protein": "6g"
}

AI Processing Pipeline

Image Upload  
↓  
OCR Extraction  
↓  
LLM Structuring  
↓  
Store Result (PostgreSQL)  
↓  
Store Logs (MongoDB)

Data Storage Strategy

PostgreSQL

Stores normalized application data.

table

food_records

fields

- id
- user_id
- product_name
- calories
- protein
- created_at

MongoDB

Stores AI processing logs.

collections

ocr_logs

llm_results

Example Mongo document

{
 "raw_text": "...",
 "structured_output": {...},
 "timestamp": "..."
}

Purpose

PostgreSQL stores final application data.

MongoDB stores AI processing history and debugging logs.
