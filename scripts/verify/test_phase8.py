"""
Phase 8 — Kibana 구동 검증
대상: http://localhost:5601
완료 조건:
  - Kibana 컨테이너 정상 구동
  - 상태 API green
  - Index Pattern 생성 확인
"""

import requests
import pytest
from conftest import KB_URL

HEADERS = {"kbn-xsrf": "true", "Content-Type": "application/json"}


class TestKibanaHealth:
    def test_kibana_reachable(self):
        """포트 5601 접근 가능"""
        res = requests.get(f"{KB_URL}/api/status", timeout=15)
        assert res.status_code == 200

    def test_kibana_status_available(self):
        """Kibana 상태 available"""
        res = requests.get(f"{KB_URL}/api/status", timeout=15)
        data = res.json()
        overall = data.get("status", {}).get("overall", {})
        state = overall.get("state", "")
        assert state in ("green", "available"), f"Kibana state: {state}"


class TestKibanaIndexPattern:
    def test_index_pattern_api_logs(self):
        """ai-habit-api-logs-* Data View 존재"""
        res = requests.get(
            f"{KB_URL}/api/data_views/data_view",
            headers=HEADERS,
            timeout=10,
        )
        assert res.status_code == 200
        views = res.json().get("data_view", [])
        titles = [v.get("title", "") for v in views]
        assert any("ai-habit-api-logs" in t for t in titles), \
            f"ai-habit-api-logs data view not found. Existing: {titles}"

    def test_index_pattern_ai_logs(self):
        """ai-habit-ai-logs-* Data View 존재"""
        res = requests.get(
            f"{KB_URL}/api/data_views/data_view",
            headers=HEADERS,
            timeout=10,
        )
        assert res.status_code == 200
        views = res.json().get("data_view", [])
        titles = [v.get("title", "") for v in views]
        assert any("ai-habit-ai-logs" in t for t in titles), \
            f"ai-habit-ai-logs data view not found. Existing: {titles}"
