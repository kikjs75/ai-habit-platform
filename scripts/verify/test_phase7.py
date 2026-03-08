"""
Phase 7 — Logstash JSON 파이프라인 검증
대상: http://localhost:9200, http://localhost:9600
완료 조건:
  - Logstash 정상 구동 (포트 9600)
  - ai-habit-api-logs-* 도큐먼트에 service, level, context 필드 존재
  - ai-habit-ai-logs-* 도큐먼트에 service, level 필드 존재
"""

import requests
import pytest
from conftest import ES_URL

LS_URL = "http://localhost:9600"
API_INDEX = "ai-habit-api-logs-*"
AI_INDEX  = "ai-habit-ai-logs-*"


class TestLogstashHealth:
    def test_logstash_reachable(self):
        """포트 9600 접근 가능"""
        res = requests.get(LS_URL, timeout=10)
        assert res.status_code == 200

    def test_logstash_pipeline_running(self):
        """파이프라인 통계 조회 가능"""
        res = requests.get(f"{LS_URL}/_node/stats/pipelines", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "pipelines" in data


class TestApiLogStructure:
    def _get_sample_doc(self) -> dict:
        res = requests.get(
            f"{ES_URL}/{API_INDEX}/_search",
            params={"size": 1},
            timeout=10,
        )
        assert res.status_code == 200, "Failed to query api-logs index"
        hits = res.json().get("hits", {}).get("hits", [])
        assert len(hits) >= 1, f"No documents in {API_INDEX}"
        return hits[0].get("_source", {})

    def test_api_log_has_service_field(self):
        """service 필드 존재 및 값 확인"""
        doc = self._get_sample_doc()
        assert "service" in doc, f"Missing 'service' field: {doc}"
        assert doc["service"] == "nestjs-api"

    def test_api_log_has_level_field(self):
        """level 필드 존재"""
        doc = self._get_sample_doc()
        assert "level" in doc, f"Missing 'level' field: {doc}"

    def test_api_log_has_context_field(self):
        """context 필드 존재"""
        doc = self._get_sample_doc()
        assert "context" in doc, f"Missing 'context' field: {doc}"

    def test_api_log_has_timestamp_field(self):
        """timestamp 필드 존재"""
        doc = self._get_sample_doc()
        assert "timestamp" in doc, f"Missing 'timestamp' field: {doc}"


class TestAiLogStructure:
    def _get_sample_doc(self) -> dict:
        res = requests.get(
            f"{ES_URL}/{AI_INDEX}/_search",
            params={"size": 1},
            timeout=10,
        )
        assert res.status_code == 200, "Failed to query ai-logs index"
        hits = res.json().get("hits", {}).get("hits", [])
        assert len(hits) >= 1, f"No documents in {AI_INDEX}"
        return hits[0].get("_source", {})

    def test_ai_log_has_service_field(self):
        """service 필드 존재 및 값 확인"""
        doc = self._get_sample_doc()
        assert "service" in doc, f"Missing 'service' field: {doc}"
        assert doc["service"] == "fastapi-ai"

    def test_ai_log_has_level_field(self):
        """level 필드 존재"""
        doc = self._get_sample_doc()
        assert "level" in doc, f"Missing 'level' field: {doc}"

    def test_ai_log_has_timestamp_field(self):
        """timestamp 필드 존재"""
        doc = self._get_sample_doc()
        assert "timestamp" in doc, f"Missing 'timestamp' field: {doc}"
