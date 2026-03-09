"""
Phase 3 — NestJS → FastAPI → DB 전체 통합 검증
대상: http://localhost:3000/records/ocr
완료 조건:
  - POST /records/ocr 이미지 업로드 → 200
  - 응답에 text, recordId, productName, calories, protein 필드 존재
  - text 비어있지 않음 (OCR 동작)
  - recordId 존재 (PostgreSQL 저장)
  - productName/calories/protein 중 하나 이상 non-null (LLM 동작)

주의: LLM 추론으로 인해 최대 120초 소요됩니다.
"""

import requests
import pytest
from conftest import API_URL

TIMEOUT = 150  # LLM 추론 최대 대기


class TestOcrIntegration:
    @pytest.fixture(scope="class")
    def ocr_response(self, sample_image_bytes):
        """POST /records/ocr 응답 (class 전체 공유)"""
        res = requests.post(
            f"{API_URL}/records/ocr",
            files={"image": ("sample.png", sample_image_bytes, "image/png")},
            timeout=TIMEOUT,
        )
        return res

    def test_ocr_endpoint_returns_200(self, ocr_response):
        """POST /records/ocr → 200"""
        assert ocr_response.status_code == 200, \
            f"Expected 200, got {ocr_response.status_code}: {ocr_response.text}"

    def test_response_has_required_fields(self, ocr_response):
        """응답에 필수 필드 존재: text, recordId, productName, calories, protein"""
        data = ocr_response.json()
        for field in ("text", "recordId", "productName", "calories", "protein"):
            assert field in data, f"Missing field '{field}' in response: {data}"

    def test_ocr_text_not_empty(self, ocr_response):
        """OCR text 비어있지 않음"""
        text = ocr_response.json().get("text", "")
        assert len(text.strip()) > 0, "OCR returned empty text"

    def test_record_id_saved_to_db(self, ocr_response):
        """recordId 존재 → PostgreSQL 저장 확인"""
        record_id = ocr_response.json().get("recordId")
        assert record_id is not None, "recordId is None — DB save may have failed"
        assert isinstance(record_id, str) and len(record_id) > 0

    def test_llm_extracted_at_least_one_field(self, ocr_response):
        """LLM이 productName / calories / protein 중 하나 이상 추출"""
        data = ocr_response.json()
        extracted = [
            data.get("productName"),
            data.get("calories"),
            data.get("protein"),
        ]
        assert any(v is not None for v in extracted), \
            f"LLM extracted nothing — all fields are null: {data}"
