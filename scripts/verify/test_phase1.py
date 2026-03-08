"""
Phase 1 — NestJS API 기본 검증
대상: http://localhost:3000
"""

import requests
import pytest
from conftest import API_URL, AI_URL


class TestNestJSHealth:
    def test_api_health(self):
        """GET /health → 200, status ok"""
        res = requests.get(f"{API_URL}/health", timeout=5)
        assert res.status_code == 200
        assert res.json().get("status") == "ok"

    def test_swagger_docs_accessible(self):
        """GET /docs → 200 (Swagger UI)"""
        res = requests.get(f"{API_URL}/docs", timeout=5)
        assert res.status_code == 200


class TestFastAPIHealth:
    def test_ai_health(self):
        """GET /health → 200, status ok"""
        res = requests.get(f"{AI_URL}/health", timeout=5)
        assert res.status_code == 200
        assert res.json().get("status") == "ok"


class TestJsonLogging:
    def test_api_returns_json_content_type(self):
        """API 응답이 JSON 형식인지 확인"""
        res = requests.get(f"{API_URL}/health", timeout=5)
        assert "application/json" in res.headers.get("Content-Type", "")
