"""
Phase 6 — Filebeat 로그 수집 검증
대상: http://localhost:9200 (Filebeat → ES 직접 출력, Phase 6)
완료 조건:
  - ai-habit-logs-* 인덱스 생성 확인
  - 인덱스에 도큐먼트 1개 이상 적재 확인

주의:
  - Phase 6 output: ES 직접 (index: ai-habit-logs-*)
  - Phase 7에서 Logstash 경유로 전환되면 ai-habit-api-logs-*, ai-habit-ai-logs-* 로 분리
  - Filebeat 수집 지연으로 최대 60초 폴링
"""

import time
import requests
import pytest
from conftest import ES_URL

INDEX_PATTERN = "ai-habit-logs-*"
WAIT_TIMEOUT  = 60
WAIT_INTERVAL = 5


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
    def test_aihabit_logs_index_exists(self):
        """ai-habit-logs-* 인덱스 생성 확인 (최대 60초 대기)"""
        def check():
            res = requests.get(
                f"{ES_URL}/_cat/indices/{INDEX_PATTERN}?h=index", timeout=10
            )
            assert res.status_code == 200
            indices = [l.strip() for l in res.text.strip().splitlines() if l.strip()]
            assert len(indices) >= 1, f"No {INDEX_PATTERN} indices found yet"
        _poll(check)

    def test_documents_ingested(self):
        """ai-habit-logs-* 인덱스에 도큐먼트 적재 확인 (최대 60초 대기)"""
        def check():
            res = requests.get(f"{ES_URL}/{INDEX_PATTERN}/_count", timeout=10)
            assert res.status_code == 200
            count = res.json().get("count", 0)
            assert count >= 1, f"No documents yet in {INDEX_PATTERN} (count={count})"
        _poll(check)

    def test_document_has_container_metadata(self):
        """도큐먼트에 container 메타데이터 포함 (Filebeat docker metadata)"""
        def check():
            res = requests.get(
                f"{ES_URL}/{INDEX_PATTERN}/_search",
                params={"size": 1},
                timeout=10,
            )
            assert res.status_code == 200
            hits = res.json().get("hits", {}).get("hits", [])
            assert len(hits) >= 1, "No documents yet"
            source = hits[0].get("_source", {})
            assert "container" in source or "docker" in source, \
                f"No container metadata in document: {list(source.keys())}"
        _poll(check)
