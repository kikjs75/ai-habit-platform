"""
Phase 5 — Elasticsearch 단독 구동 검증
대상: http://localhost:9200
완료 조건:
  - Elasticsearch 컨테이너 정상 구동
  - _cluster/health status: yellow 이상
  - 포트 9200 접근 가능
"""

import requests
import pytest
from conftest import ES_URL


class TestElasticsearchHealth:
    def test_es_reachable(self):
        """포트 9200 접근 가능"""
        res = requests.get(ES_URL, timeout=10)
        assert res.status_code == 200

    def test_cluster_health_status(self):
        """클러스터 상태 yellow 이상"""
        res = requests.get(f"{ES_URL}/_cluster/health", timeout=10)
        assert res.status_code == 200
        status = res.json().get("status")
        assert status in ("yellow", "green"), f"Unexpected cluster status: {status}"

    def test_cluster_name(self):
        """클러스터 이름 확인"""
        res = requests.get(f"{ES_URL}/_cluster/health", timeout=10)
        data = res.json()
        assert "cluster_name" in data

    def test_node_count(self):
        """노드 1개 이상 활성"""
        res = requests.get(f"{ES_URL}/_cluster/health", timeout=10)
        data = res.json()
        assert data.get("number_of_nodes", 0) >= 1
