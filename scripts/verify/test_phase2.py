"""
Phase 2 — FastAPI OCR 직접 검증
대상: http://localhost:8000/ocr
완료 조건:
  - POST /ocr 이미지 업로드 → 200
  - 응답에 text 필드 존재
  - OCR 추출 텍스트 비어있지 않음
"""

import requests
import pytest
from conftest import AI_URL


class TestFastAPIOcr:
    def test_ocr_returns_200(self, sample_image_bytes):
        """POST /ocr → 200"""
        res = requests.post(
            f"{AI_URL}/ocr",
            files={"file": ("sample.png", sample_image_bytes, "image/png")},
            timeout=30,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    def test_ocr_response_has_text_field(self, sample_image_bytes):
        """응답에 text 필드 존재"""
        res = requests.post(
            f"{AI_URL}/ocr",
            files={"file": ("sample.png", sample_image_bytes, "image/png")},
            timeout=30,
        )
        data = res.json()
        assert "text" in data, f"Missing 'text' field: {data}"

    def test_ocr_text_not_empty(self, sample_image_bytes):
        """OCR 추출 텍스트가 비어있지 않음"""
        res = requests.post(
            f"{AI_URL}/ocr",
            files={"file": ("sample.png", sample_image_bytes, "image/png")},
            timeout=30,
        )
        text = res.json().get("text", "")
        assert len(text.strip()) > 0, "OCR returned empty text"

    def test_ocr_response_has_engine_field(self, sample_image_bytes):
        """응답에 engine 필드 존재 (tesseract)"""
        res = requests.post(
            f"{AI_URL}/ocr",
            files={"file": ("sample.png", sample_image_bytes, "image/png")},
            timeout=30,
        )
        data = res.json()
        assert "engine" in data, f"Missing 'engine' field: {data}"
        assert data["engine"] == "tesseract"
