"""
Phase 6 — Filebeat 로그 수집 검증
대상: http://localhost:9200 (Filebeat → ES 직접 또는 Logstash 경유 후)
완료 조건:
  - ai-habit-* 인덱스 존재
  - 인덱스에 도큐먼트 1개 이상 적재

주의: Filebeat → ES 적재까지 최대 60초 소요될 수 있습니다.
"""

import time
import requests
import pytest
from conftest import ES_URL

INDEX_PATTERN = "ai-habit-*"
WAIT_TIMEOUT  = 60   # seconds
WAIT_INTERVAL = 5    # seconds


def _poll(condition_fn, timeout=WAIT_TIMEOUT, interval=WAIT_INTERVAL):
    """condition_fn이 AssertionError 없이 통과할 때까지 폴링"""
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            condition_fn()
            return
        except AssertionError as e:
            last_exc = e
            time.sleep(interval)
    raise last_exc


class TestFilebeatIngestion:
    def test_aihabit_index_exists(self):
        """ai-habit-* 인덱스 1개 이상 존재 (최대 60초 대기)"""
        def check():
            res = requests.get(
                f"{ES_URL}/_cat/indices/{INDEX_PATTERN}?h=index", timeout=10
            )
            assert res.status_code == 200
            indices = [l.strip() for l in res.text.strip().splitlines() if l.strip()]
            assert len(indices) >= 1, f"No ai-habit-* indices found yet"
        _poll(check)

    def test_documents_ingested(self):
        """ai-habit-* 인덱스에 도큐먼트 적재 확인 (최대 60초 대기)"""
        def check():
            res = requests.get(f"{ES_URL}/{INDEX_PATTERN}/_count", timeout=10)
            assert res.status_code == 200
            count = res.json().get("count", 0)
            assert count >= 1, f"No documents yet (count={count})"
        _poll(check)

    def test_api_logs_index_exists(self):
        """ai-habit-api-logs-* 인덱스 존재 (최대 60초 대기)"""
        def check():
            res = requests.get(
                f"{ES_URL}/_cat/indices/ai-habit-api-logs-*?h=index", timeout=10
            )
            assert res.status_code == 200
            indices = [l.strip() for l in res.text.strip().splitlines() if l.strip()]
            assert len(indices) >= 1, "ai-habit-api-logs-* index not found yet"
        _poll(check)

    def test_ai_logs_index_exists(self):
        """ai-habit-ai-logs-* 인덱스 존재 (최대 60초 대기)"""
        def check():
            res = requests.get(
                f"{ES_URL}/_cat/indices/ai-habit-ai-logs-*?h=index", timeout=10
            )
            assert res.status_code == 200
            indices = [l.strip() for l in res.text.strip().splitlines() if l.strip()]
            assert len(indices) >= 1, "ai-habit-ai-logs-* index not found yet"
        _poll(check)
