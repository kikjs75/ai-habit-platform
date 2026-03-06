# Phase 3 — LLM Processing

## Goal

Convert OCR text into structured data.

---

## Example OCR Text

```
Milk
Calories 120
Protein 6g
```

## LLM Structured Output

```json
{
  "product_name": "Milk",
  "calories": 120,
  "protein": "6g"
}
```

---

## Technology

* Python
* Hugging Face Transformers
* PyTorch
* Optional: TensorFlow-compatible model support

---

## LLM Tooling

The LLM processing layer uses open-source model tooling.

Recommended stack:

* Hugging Face Transformers for model loading and inference
* PyTorch as the primary inference backend
* TensorFlow support can be considered optionally if needed by the selected model

---

## Implementation Direction

The system should support the following flow:

1. Receive OCR raw text
2. Send raw text to the LLM processing layer
3. Convert the text into structured JSON
4. Validate and normalize output fields
5. Store normalized data in PostgreSQL
6. Store processing logs in MongoDB

---

## AI Processing Pipeline

```
Image Upload
     ↓
OCR Extraction
     ↓
LLM Structuring
     ↓
Store Result (PostgreSQL)
     ↓
Store Logs (MongoDB)
```

---

## Data Storage Strategy

### PostgreSQL

Stores normalized application data.

| Field | Description |
|------------|-------------------------------|
| `id` | Primary key |
| `user_id` | Reference to user |
| `product_name` | Name of food product |
| `calories` | Caloric value |
| `protein` | Protein content |
| `created_at` | Record creation timestamp |

### MongoDB

Stores AI processing logs.

**Collections:**

* `ocr_logs`
* `llm_results`

**Example Mongo Document:**

```json
{
  "raw_text": "...",
  "structured_output": {
    "product_name": "Milk",
    "calories": 120,
    "protein": "6g"
  },
  "timestamp": "..."
}
```

---

## Purpose

| Storage | Role |
|-------------|--------------------------------------|
| PostgreSQL | Stores final application data |
| MongoDB | Stores AI processing history and debugging logs |