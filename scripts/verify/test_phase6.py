"""
Phase 6 — Filebeat 로그 수집 검증
대상: http://localhost:9200 (Filebeat → ES 직접 또는 Logstash 경유 후)
완료 조건:
  - ai-habit-* 인덱스 존재
  - 인덱스에 도큐먼트 1개 이상 적재
"""

import requests
import pytest
from conftest import ES_URL

INDEX_PATTERN = "ai-habit-*"


class TestFilebeatIngestion:
    def test_aihabit_index_exists(self):
        """ai-habit-* 인덱스 1개 이상 존재"""
        res = requests.get(f"{ES_URL}/_cat/indices/{INDEX_PATTERN}?h=index", timeout=10)
        assert res.status_code == 200
        indices = [line.strip() for line in res.text.strip().splitlines() if line.strip()]
        assert len(indices) >= 1, f"No ai-habit-* indices found"

    def test_documents_ingested(self):
        """ai-habit-* 인덱스에 도큐먼트 적재 확인"""
        res = requests.get(f"{ES_URL}/{INDEX_PATTERN}/_count", timeout=10)
        assert res.status_code == 200
        count = res.json().get("count", 0)
        assert count >= 1, f"No documents found in {INDEX_PATTERN} (count={count})"

    def test_api_logs_index_exists(self):
        """ai-habit-api-logs-* 인덱스 존재"""
        res = requests.get(f"{ES_URL}/_cat/indices/ai-habit-api-logs-*?h=index", timeout=10)
        assert res.status_code == 200
        indices = [line.strip() for line in res.text.strip().splitlines() if line.strip()]
        assert len(indices) >= 1, "ai-habit-api-logs-* index not found"

    def test_ai_logs_index_exists(self):
        """ai-habit-ai-logs-* 인덱스 존재"""
        res = requests.get(f"{ES_URL}/_cat/indices/ai-habit-ai-logs-*?h=index", timeout=10)
        assert res.status_code == 200
        indices = [line.strip() for line in res.text.strip().splitlines() if line.strip()]
        assert len(indices) >= 1, "ai-habit-ai-logs-* index not found"
