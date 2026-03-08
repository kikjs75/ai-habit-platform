# Logging Strategy — JSON 구조화 로깅 설계 결정

## 배경

Phase 5~8 ELK Stack 연동을 준비하면서 NestJS API와 FastAPI AI 서비스의 로그를
Logstash에서 어떻게 파싱할지 검토가 필요했다.

초기 설계(`docs/13-phase7-logstash.md`)는 grok 패턴 기반 파싱 방식이었으나,
참조 프로젝트 분석을 통해 JSON 구조화 로깅 방식으로 전환을 결정했다.

## 참조 프로젝트 분석

- **참조**: https://github.com/kikjs75/etl-public-data/tree/main/etl-public-data
- **분석일**: 2026-03-08

### 참조 프로젝트의 구성

**FastAPI 로깅**

`python-json-logger` 라이브러리 + 커스텀 포매터(`CustomJsonFormatter`)를 사용해
모든 로그를 JSON으로 stdout 출력.

```python
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(KST).isoformat(timespec="milliseconds")
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["service"] = "etl-backend"
```

출력 예시:
```json
{"timestamp": "2026-03-08T19:00:00.123+09:00", "level": "INFO", "logger": "__main__", "service": "etl-backend", "message": "OCR completed, extracted 42 chars"}
```

**Logstash 파이프라인**

grok 패턴 없이 JSON 파싱만으로 구성. JSON이 아닌 로그는 드롭.

```
filter {
  if [message] !~ /^\s*\{/ {
    drop {}
  }
  json {
    source => "message"
  }
  if "_jsonparsefailure" in [tags] {
    drop {}
  }
}
```

**Filebeat**

컨테이너 로그 전체 수집 후 Logstash로 전달. 컨테이너 필터링은 Logstash에서 처리.

## 방식 비교

| 항목 | grok 방식 (초기 설계) | JSON 방식 (참조 적용) |
|------|----------------------|----------------------|
| Logstash 설정 | grok 패턴 2개 (복잡, 깨지기 쉬움) | `json { source => "message" }` 1줄 |
| 로그 포맷 | 텍스트 파싱 의존 | 구조화된 필드 직접 접근 |
| 필드 확장 | grok 패턴 수정 필요 | 코드에서 필드 추가만 하면 됨 |
| Kibana 활용 | 파싱 성공 여부에 따라 제한적 | 필드별 필터/시각화 즉시 가능 |
| 유지보수 | 포맷 변경 시 grok 함께 수정 | 독립적 |
| 파싱 실패 리스크 | 로그 포맷 변경 시 전체 파싱 실패 | 없음 |

## 결정

**JSON 구조화 로깅 방식으로 전환한다.**

grok 방식은 텍스트 포맷에 의존하기 때문에 포맷이 조금만 바뀌어도 파이프라인 전체가
영향을 받는다. JSON 방식은 앱이 직접 구조화된 데이터를 출력하므로 Logstash 설정이
단순해지고, Kibana에서도 필드를 즉시 활용할 수 있다.

## 구현 계획

### FastAPI (`apps/ai/main.py`)

- `python-json-logger==2.0.7` 추가 (`requirements.txt`)
- `CustomJsonFormatter` 구현 (참조 프로젝트 기준)
- 공통 필드: `timestamp`, `level`, `logger`, `service`, `message`

출력 예시:
```json
{"timestamp": "2026-03-08T19:00:00.123+09:00", "level": "INFO", "logger": "main", "service": "fastapi-ai", "message": "POST /ocr HTTP/1.1 200"}
```

### NestJS (`apps/api`)

- `winston` + `nest-winston` 패키지 설치
- 기본 NestJS Logger를 JSON 출력 커스텀 로거로 교체
- 기존 `LoggingInterceptor`와 연동

출력 예시:
```json
{"timestamp": "2026-03-08T19:00:00.123+09:00", "level": "info", "context": "HTTP", "service": "nestjs-api", "message": "POST /records/ocr 200 1243ms"}
```

### Logstash (`apps/logstash/pipeline/logstash.conf`)

grok 방식 → JSON 파싱 방식으로 교체.
`docs/13-phase7-logstash.md`도 함께 업데이트 예정.

```
filter {
  if [message] !~ /^\s*\{/ { drop {} }
  json { source => "message" }
  if "_jsonparsefailure" in [tags] { drop {} }
}
```

## 영향 범위

| 파일 | 변경 내용 |
|------|-----------|
| `apps/ai/requirements.txt` | `python-json-logger` 추가 |
| `apps/ai/main.py` | `CustomJsonFormatter` 적용 |
| `apps/api/package.json` | `winston`, `nest-winston` 추가 |
| `apps/api/src/main.ts` | 커스텀 JSON 로거 등록 |
| `apps/logstash/pipeline/logstash.conf` | grok → json 파싱으로 교체 |
| `docs/13-phase7-logstash.md` | 파이프라인 설명 업데이트 |
