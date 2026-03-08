# Phase 8 — Kibana

## 목표

Kibana를 추가하여 Elasticsearch에 저장된 로그를 시각화한다.
Index Pattern 설정, Discover 로그 탐색, 대시보드 구성을 완료한다.

## 작업 내용

### 1. docker-compose 추가

```yaml
kibana:
  image: docker.elastic.co/kibana/kibana:8.13.0
  container_name: ai-habit-kibana
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    - TZ=Asia/Seoul
  ports:
    - "5601:5601"
  depends_on:
    elasticsearch:
      condition: service_healthy
  healthcheck:
    test: ["CMD-SHELL", "curl -s http://localhost:5601/api/status | grep -q '\"level\":\"available\"'"]
    interval: 10s
    timeout: 5s
    retries: 20
  networks:
    - appnet
```

### 2. Index Pattern 설정

Kibana 접속 후 순서:

1. `http://localhost:5601` 접속
2. **Stack Management → Index Patterns → Create index pattern**
3. 아래 패턴 등록

| Index Pattern | 설명 |
|---------------|------|
| `ai-habit-api-logs-*` | NestJS API 로그 |
| `ai-habit-ai-logs-*` | FastAPI AI 로그 |

Time field: `@timestamp`

### 3. 구성할 대시보드

#### 대시보드 1 — API 요청 모니터링

| 패널 | 시각화 유형 | 내용 |
|------|-------------|------|
| 시간대별 요청 수 | Line chart | `@timestamp` 기준 요청 추이 |
| 엔드포인트별 호출 수 | Bar chart | `context` 필드 기준 집계 |
| 로그 레벨 분포 | Pie chart | INFO / WARN / ERROR 비율 |
| 최근 에러 로그 | Data table | `log_level: ERROR` 필터 |

#### 대시보드 2 — AI 처리 모니터링

| 패널 | 시각화 유형 | 내용 |
|------|-------------|------|
| OCR 요청 추이 | Line chart | `/ocr` 경로 요청 수 |
| LLM 요청 추이 | Line chart | `/llm` 경로 요청 수 |
| HTTP 상태 코드 분포 | Pie chart | `status_code` 필드 집계 |
| 처리 현황 테이블 | Data table | 최근 요청 목록 |

## 검증 방법

```bash
# Kibana 상태 확인
curl http://localhost:5601/api/status | python3 -m json.tool | grep level
```

브라우저에서:
1. `http://localhost:5601` 접속
2. **Discover** → Index Pattern 선택 → 로그 확인
3. **Dashboard** → 구성한 대시보드 확인

## 완료 조건

- [ ] Kibana 컨테이너 정상 구동
- [ ] Index Pattern 2개 등록 완료
- [ ] Discover에서 NestJS, FastAPI 로그 탐색 가능
- [ ] API 요청 모니터링 대시보드 구성
- [ ] AI 처리 모니터링 대시보드 구성

## 최종 서비스 포트 현황

| 서비스 | 포트 |
|--------|------|
| Demo (React) | 5173 |
| NestJS API | 3000 |
| FastAPI AI | 8000 |
| PostgreSQL | 5432 |
| MongoDB | 27017 |
| Elasticsearch | 9200 |
| Logstash (Beats) | 5044 |
| Logstash (API) | 9600 |
| Kibana | 5601 |
