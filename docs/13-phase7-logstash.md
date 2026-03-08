# Phase 7 — Logstash

## 목표

Logstash 파이프라인을 추가하여 Filebeat로부터 로그를 받아
JSON 파싱 후 Elasticsearch에 저장한다.

> **설계 결정**: grok 패턴 방식 대신 JSON 구조화 로깅 방식을 채택한다.
> 상세 배경은 `docs/15-logging-strategy.md` 참조.

## 작업 내용

### 1. 디렉토리 구조

```
apps/logstash/
  pipeline/
    logstash.conf    # 메인 파이프라인
  config/
    logstash.yml     # Logstash 설정
```

### 2. logstash.yml

`apps/logstash/config/logstash.yml`

```yaml
http.host: "0.0.0.0"
xpack.monitoring.enabled: false
```

### 3. 파이프라인 설정

`apps/logstash/pipeline/logstash.conf`

앱이 JSON을 직접 출력하므로 grok 없이 `json` 필터만 사용한다.
JSON이 아닌 로그(ELK 컴포넌트 자체 로그 등)는 드롭하여 재귀 루프를 방지한다.

```
input {
  beats {
    port => 5044
  }
}

filter {
  # JSON 형식이 아닌 이벤트 드롭 (ELK 자체 로그, 기타 컨테이너 로그 등)
  if [message] !~ /^\s*\{/ {
    drop {}
  }

  # message 필드의 JSON 파싱
  json {
    source => "message"
  }

  # JSON 파싱 실패 이벤트 드롭
  if "_jsonparsefailure" in [tags] {
    drop {}
  }

  # ELK 컴포넌트 자체 로그 드롭 (ECS 포맷 — service.name 필드 존재)
  if [service.name] {
    drop {}
  }
}

output {
  if [service] == "nestjs-api" {
    elasticsearch {
      hosts => ["http://elasticsearch:9200"]
      index => "ai-habit-api-logs-%{+yyyy.MM.dd}"
    }
  } else if [service] == "fastapi-ai" {
    elasticsearch {
      hosts => ["http://elasticsearch:9200"]
      index => "ai-habit-ai-logs-%{+yyyy.MM.dd}"
    }
  } else {
    elasticsearch {
      hosts => ["http://elasticsearch:9200"]
      index => "ai-habit-other-logs-%{+yyyy.MM.dd}"
    }
  }
}
```

### 4. docker-compose 추가

```yaml
logstash:
  image: docker.elastic.co/logstash/logstash:8.13.0
  container_name: ai-habit-logstash
  environment:
    - TZ=Asia/Seoul
    - LS_JAVA_OPTS=-Xms256m -Xmx256m
  ports:
    - "5044:5044"
    - "9600:9600"
  volumes:
    - ./apps/logstash/pipeline:/usr/share/logstash/pipeline:ro
    - ./apps/logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
  depends_on:
    elasticsearch:
      condition: service_healthy
  networks:
    - appnet
```

### 5. Filebeat output 확인

`apps/filebeat/filebeat.yml`의 output이 Logstash로 설정되어 있는지 확인:

```yaml
output.logstash:
  hosts: ["logstash:5044"]
```

## 기대 로그 포맷

### NestJS API

```json
{"timestamp": "2026-03-08T19:00:00.123+09:00", "level": "info", "service": "nestjs-api", "context": "HTTP", "message": "POST /records/ocr 200 1243ms"}
```

### FastAPI AI

```json
{"timestamp": "2026-03-08T19:00:00.456+09:00", "level": "INFO", "service": "fastapi-ai", "logger": "main", "message": "OCR completed, extracted 42 chars"}
```

## 검증 방법

```bash
# Logstash 상태 확인
curl http://localhost:9600/?pretty

# 파이프라인 통계
curl http://localhost:9600/_node/stats/pipelines?pretty

# 인덱스별 도큐먼트 수 확인
curl http://localhost:9200/ai-habit-api-logs-*/_count
curl http://localhost:9200/ai-habit-ai-logs-*/_count

# 실제 도큐먼트 확인
curl "http://localhost:9200/ai-habit-api-logs-*/_search?pretty&size=3"
```

## 완료 조건

- [ ] Logstash 컨테이너 정상 구동
- [ ] Filebeat → Logstash Beats 연결 확인
- [ ] NestJS JSON 로그 파싱 후 `ai-habit-api-logs-*` 인덱스 적재 확인
- [ ] FastAPI JSON 로그 파싱 후 `ai-habit-ai-logs-*` 인덱스 적재 확인
- [ ] `service`, `level`, `context`, `timestamp` 필드 구조화 확인
