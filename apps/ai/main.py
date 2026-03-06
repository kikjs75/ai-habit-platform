import io
import json
import logging
import os
from contextlib import asynccontextmanager

import pytesseract
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")

tokenizer = None
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global tokenizer, model
    logger.info("Loading LLM model: %s", MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )
    model.eval()
    logger.info("LLM model loaded successfully")
    yield


app = FastAPI(
    title="AI Habit Platform - AI Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        text = pytesseract.image_to_string(image)
        text = text.strip()
        logger.info("OCR completed, extracted %d chars", len(text))
        return {"text": text, "engine": "tesseract"}
    except Exception as e:
        logger.error("OCR failed: %s", e)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


class LlmRequest(BaseModel):
    text: str


@app.post("/llm")
async def llm_structure(body: LlmRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="LLM model not loaded yet")
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a nutrition data extractor. "
                    "Extract product_name (string), calories (integer), protein (string, e.g. '6g') "
                    "from the given OCR text. "
                    "Respond with valid JSON only. Use null for missing fields."
                ),
            },
            {"role": "user", "content": f"OCR text:\n{body.text}"},
        ]

        text_input = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text_input, return_tensors="pt")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated = outputs[0][inputs.input_ids.shape[1]:]
        response_text = tokenizer.decode(generated, skip_special_tokens=True).strip()
        logger.info("LLM raw response: %s", response_text)

        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in LLM response")

        result = json.loads(response_text[start:end])
        return {
            "product_name": result.get("product_name"),
            "calories": result.get("calories"),
            "protein": result.get("protein"),
        }
    except Exception as e:
        logger.error("LLM processing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM processing failed: {str(e)}")
