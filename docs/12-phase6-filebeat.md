# Phase 6 — Filebeat

## 목표

Filebeat를 추가하여 NestJS API, FastAPI AI 서비스의 Docker 컨테이너 로그를 수집하고
Logstash(또는 임시로 Elasticsearch 직접)로 전달한다.

## 작업 내용

### 1. Filebeat 설정 파일 작성

`apps/filebeat/filebeat.yml`

```yaml
filebeat.inputs:
  - type: container
    paths:
      - /var/lib/docker/containers/*/*.log
    processors:
      - add_docker_metadata:
          host: "unix:///var/run/docker.sock"

processors:
  - drop_event:
      when:
        not:
          or:
            - equals:
                container.name: "ai-habit-api"
            - equals:
                container.name: "ai-habit-ai"

output.logstash:
  hosts: ["logstash:5044"]

# Phase 6 임시 — Logstash 없이 직접 ES로 보낼 경우
# output.elasticsearch:
#   hosts: ["elasticsearch:9200"]
#   index: "ai-habit-logs-%{+yyyy.MM.dd}"

logging.level: info
```

### 2. docker-compose 추가

```yaml
filebeat:
  image: docker.elastic.co/beats/filebeat:8.13.0
  container_name: ai-habit-filebeat
  user: root
  environment:
    - TZ=Asia/Seoul
  volumes:
    - ./apps/filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/run/docker.sock:/var/run/docker.sock:ro
  depends_on:
    elasticsearch:
      condition: service_healthy
  networks:
    - appnet
```

### 3. NestJS 로그 포맷 확인

NestJS 기본 로그 포맷:
```
[Nest] 1  - 03/08/2026, 7:00:00 PM   LOG [Bootstrap] Application is running on: http://[::1]:3000
[Nest] 1  - 03/08/2026, 7:00:01 PM   LOG [RecordsController] POST /records/ocr
```

FastAPI (uvicorn) 로그 포맷:
```
INFO:     172.18.0.1:12345 - "POST /ocr HTTP/1.1" 200 OK
INFO:     172.18.0.1:12345 - "POST /llm HTTP/1.1" 200 OK
```

## 검증 방법

```bash
# Filebeat 로그 확인
docker compose logs filebeat --tail=30

# Elasticsearch에 데이터 수신 여부 확인
curl http://localhost:9200/_cat/indices?v

# 인덱스에 실제 도큐먼트 확인
curl http://localhost:9200/ai-habit-logs-*/_count
```

## 완료 조건

- [ ] Filebeat 컨테이너 정상 구동
- [ ] `ai-habit-api`, `ai-habit-ai` 컨테이너 로그 수집 확인
- [ ] Elasticsearch 인덱스에 로그 도큐먼트 적재 확인
