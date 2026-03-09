import io
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timezone, timedelta

import pytesseract
import torch
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from pythonjsonlogger import jsonlogger
from transformers import AutoModelForCausalLM, AutoTokenizer

KST = timezone(timedelta(hours=9))

_trace_id: ContextVar[str] = ContextVar('trace_id', default='')
_user_id: ContextVar[str] = ContextVar('user_id', default='anonymous')

_STDLIB_ATTRS = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "message", "module",
    "msecs", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
})


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(KST).isoformat(timespec="milliseconds")
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["service"] = "fastapi-ai"
        for key, value in record.__dict__.items():
            if key not in _STDLIB_ATTRS and key not in log_record:
                log_record[key] = value
        if record.exc_info:
            log_record["traceback"] = self.formatException(record.exc_info)
            record.exc_info = None
            record.exc_text = None


_handler = logging.StreamHandler()
_handler.setFormatter(CustomJsonFormatter())
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(_handler)
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


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    _trace_id.set(request.headers.get("x-trace-id", ""))
    _user_id.set(request.headers.get("x-user-id", "anonymous"))
    return await call_next(request)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    span_id = str(uuid.uuid4())
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        t0 = time.monotonic()
        text = pytesseract.image_to_string(image)
        duration_ms = int((time.monotonic() - t0) * 1000)
        text = text.strip()
        logger.info("OCR completed", extra={
            "trace_id": _trace_id.get(),
            "span_id": span_id,
            "user_id": _user_id.get(),
            "chars": len(text),
            "duration_ms": duration_ms,
        })
        return {"text": text, "engine": "tesseract"}
    except Exception as e:
        logger.error("OCR failed: %s", e, extra={
            "trace_id": _trace_id.get(),
            "span_id": span_id,
            "user_id": _user_id.get(),
        })
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


class LlmRequest(BaseModel):
    text: str


@app.post("/llm")
async def llm_structure(body: LlmRequest):
    span_id = str(uuid.uuid4())
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

        t0 = time.monotonic()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        duration_ms = int((time.monotonic() - t0) * 1000)

        generated = outputs[0][inputs.input_ids.shape[1]:]
        response_text = tokenizer.decode(generated, skip_special_tokens=True).strip()
        logger.info("LLM inference completed", extra={
            "trace_id": _trace_id.get(),
            "span_id": span_id,
            "user_id": _user_id.get(),
            "duration_ms": duration_ms,
            "response": response_text,
        })

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
        logger.error("LLM processing failed: %s", e, extra={
            "trace_id": _trace_id.get(),
            "span_id": span_id,
            "user_id": _user_id.get(),
        })
        raise HTTPException(status_code=500, detail=f"LLM processing failed: {str(e)}")
