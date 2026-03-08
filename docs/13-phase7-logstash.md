# Phase 7 — Logstash

## 목표

Logstash 파이프라인을 추가하여 Filebeat로부터 로그를 받아
NestJS, FastAPI 로그를 각각 파싱하고 구조화된 형태로 Elasticsearch에 저장한다.

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

```
input {
  beats {
    port => 5044
  }
}

filter {
  # NestJS API 로그 파싱
  if [container][name] == "ai-habit-api" {
    grok {
      match => {
        "message" => "\[Nest\] %{NUMBER:pid}\s+- %{DATA:timestamp}\s+%{LOGLEVEL:log_level} \[%{DATA:context}\] %{GREEDYDATA:log_message}"
      }
    }
    mutate {
      add_field => { "service" => "nestjs-api" }
    }
  }

  # FastAPI AI 서비스 로그 파싱
  if [container][name] == "ai-habit-ai" {
    grok {
      match => {
        "message" => "%{LOGLEVEL:log_level}:%{SPACE}%{IPORHOST:client_ip}:%{NUMBER:client_port} - \"%{WORD:method} %{URIPATHPARAM:path} HTTP/%{NUMBER:http_version}\" %{NUMBER:status_code}"
      }
    }
    mutate {
      add_field => { "service" => "fastapi-ai" }
      convert => { "status_code" => "integer" }
    }
  }

  # 파싱 실패한 태그 제거
  if "_grokparsefailure" in [tags] {
    mutate {
      remove_tag => ["_grokparsefailure"]
    }
  }

  # 타임스탬프 정리
  date {
    match => ["timestamp", "MM/dd/yyyy, hh:mm:ss a"]
    target => "@timestamp"
    timezone => "Asia/Seoul"
  }
}

output {
  if [service] == "nestjs-api" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "ai-habit-api-logs-%{+yyyy.MM.dd}"
    }
  } else if [service] == "fastapi-ai" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "ai-habit-ai-logs-%{+yyyy.MM.dd}"
    }
  } else {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
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

### 5. Filebeat output 변경

`apps/filebeat/filebeat.yml`의 output을 Logstash로 전환:

```yaml
output.logstash:
  hosts: ["logstash:5044"]
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
curl http://localhost:9200/ai-habit-api-logs-*/_search?pretty&size=3
```

## 완료 조건

- [ ] Logstash 컨테이너 정상 구동
- [ ] Filebeat → Logstash Beats 연결 확인
- [ ] NestJS 로그 파싱 후 `ai-habit-api-logs-*` 인덱스 적재 확인
- [ ] FastAPI 로그 파싱 후 `ai-habit-ai-logs-*` 인덱스 적재 확인
- [ ] `service`, `log_level`, `context` 필드 구조화 확인
