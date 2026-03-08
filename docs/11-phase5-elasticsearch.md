# Phase 5 — Elasticsearch

## 목표

Elasticsearch를 docker-compose에 추가하고 단독으로 정상 동작을 확인한다.
이 단계에서는 로그 수집 없이 Elasticsearch 자체의 구동과 인덱스 구성만 검증한다.

## 작업 내용

### 1. docker-compose 추가

`elasticsearch` 서비스를 추가한다.

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.13.0
  container_name: ai-habit-elasticsearch
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
    - ES_JAVA_OPTS=-Xms512m -Xmx512m
    - TZ=Asia/Seoul
  ports:
    - "9200:9200"
  volumes:
    - es_data:/usr/share/elasticsearch/data
  healthcheck:
    test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -q '\"status\":\"green\"\\|\"status\":\"yellow\"'"]
    interval: 10s
    timeout: 5s
    retries: 20
  networks:
    - appnet
```

volumes에 `es_data` 추가:
```yaml
volumes:
  es_data:
```

### 2. 인덱스 템플릿 설계

수집할 로그 인덱스:

| 인덱스 이름 | 용도 |
|-------------|------|
| `ai-habit-api-logs` | NestJS API 요청/응답 로그 |
| `ai-habit-ai-logs` | FastAPI OCR/LLM 처리 로그 |

### 3. .env 추가

```env
# Elasticsearch (Phase 5)
ELASTICSEARCH_HOST=http://elasticsearch:9200
```

## 검증 방법

```bash
# 클러스터 상태 확인
curl http://localhost:9200/_cluster/health?pretty

# 기대 응답
{
  "cluster_name" : "docker-cluster",
  "status" : "green",
  ...
}

# 인덱스 목록 확인
curl http://localhost:9200/_cat/indices?v
```

## 완료 조건

- [ ] Elasticsearch 컨테이너 정상 구동
- [ ] `_cluster/health` 응답 status: yellow 이상
- [ ] 포트 9200 접근 가능
