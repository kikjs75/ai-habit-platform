"""
Phase 8 — Kibana 구동 검증
대상: http://localhost:5601
완료 조건:
  - Kibana 컨테이너 정상 구동
  - 상태 API available
  - Index Pattern(Data View) 2개 자동 생성 및 확인
"""

import requests
import pytest
from conftest import KB_URL

HEADERS = {"kbn-xsrf": "true", "Content-Type": "application/json"}

DATA_VIEWS = [
    ("ai-habit-api-logs-*", "ai-habit-api-logs"),
    ("ai-habit-ai-logs-*", "ai-habit-ai-logs"),
]


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
        level = overall.get("level", overall.get("state", ""))
        assert level in ("green", "available"), f"Kibana level: {level}"


class TestKibanaIndexPattern:
    @classmethod
    def setup_class(cls):
        """Data View가 없으면 Kibana API로 자동 생성"""
        for pattern, _ in DATA_VIEWS:
            requests.post(
                f"{KB_URL}/api/data_views/data_view",
                headers=HEADERS,
                json={"data_view": {"title": pattern, "timeFieldName": "@timestamp"}},
                timeout=15,
            )
            # 409 Conflict = already exists → 무시

    def _get_titles(self):
        res = requests.get(
            f"{KB_URL}/api/data_views",
            headers=HEADERS,
            timeout=10,
        )
        assert res.status_code == 200, f"Data Views API error: {res.status_code}"
        return [v.get("title", "") for v in res.json().get("data_view", [])]

    def test_index_pattern_api_logs(self):
        """ai-habit-api-logs-* Data View 존재"""
        titles = self._get_titles()
        assert any("ai-habit-api-logs" in t for t in titles), \
            f"ai-habit-api-logs data view not found. Existing: {titles}"

    def test_index_pattern_ai_logs(self):
        """ai-habit-ai-logs-* Data View 존재"""
        titles = self._get_titles()
        assert any("ai-habit-ai-logs" in t for t in titles), \
            f"ai-habit-ai-logs data view not found. Existing: {titles}"
