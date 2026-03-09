# Kibana 대시보드 가이드

## 개요

4개 대시보드를 통해 AI Habit Platform의 API 성능, AI 처리 성능, E2E 요청 추적, 에러 탐지를 시각화합니다.

- Kibana URL: http://localhost:5601/app/dashboards
- 프로비저닝 스크립트: `scripts/provision_kibana.py`

## 프로비저닝

```bash
# 전체 4개 한 번에 생성
python3 scripts/provision_kibana.py

# 특정 대시보드만 생성
python3 scripts/provision_kibana.py --only 1   # API 요청 모니터링
python3 scripts/provision_kibana.py --only 2   # AI 처리 성능
python3 scripts/provision_kibana.py --only 3   # E2E 요청 추적
python3 scripts/provision_kibana.py --only 4   # 에러 & 이상 탐지

# Kibana URL 지정
python3 scripts/provision_kibana.py --kb-url http://localhost:5601
```

> 스크립트는 결정론적 UUID를 사용하므로 재실행해도 동일한 ID로 덮어씁니다 (idempotent).

---

## 대시보드 1 — API 요청 모니터링

> 인덱스: `ai-habit-api-logs-*`

NestJS API의 전체 요청 현황을 모니터링합니다.

| # | 패널 | 시각화 | 설명 |
|---|------|--------|------|
| ① | 시간대별 요청 수 | 꺾은선 | `@timestamp` 기준 요청 수 추이 |
| ② | 엔드포인트별 평균 응답시간 | 수평 막대 | `url` 기준 `duration_ms` 평균 |
| ③ | HTTP 상태 코드 분포 | 파이 | `status_code` 비율 |
| ④ | p95 응답시간 | 단일 지표 | `duration_ms` 95th percentile |
| ⑤ | 에러 요청 목록 | 데이터 테이블 | `level: error` 필터 → URL, 상태 코드, trace_id |

**활용 예시**
- 특정 시간대 트래픽 급증 확인
- 느린 엔드포인트 식별 (② 패널)
- 에러 발생 시 trace_id로 FastAPI 로그 연계 조회

---

## 대시보드 2 — AI 처리 성능

> 인덱스: `ai-habit-ai-logs-*`

FastAPI OCR/LLM 처리 성능을 모니터링합니다.

| # | 패널 | 시각화 | 설명 |
|---|------|--------|------|
| ① | OCR vs LLM 평균 처리시간 | 수평 막대 | 두 작업의 `duration_ms` 평균 비교 |
| ② | OCR 평균 처리시간 | 단일 지표 | OCR `duration_ms` 평균 |
| ③ | LLM 평균 추론시간 | 단일 지표 | LLM `duration_ms` 평균 |
| ④ | OCR 요청 건수 추이 | 꺾은선 | 시간대별 OCR 처리 건수 |
| ⑤ | AI 에러 목록 | 데이터 테이블 | `level: error` → 메시지, trace_id, user_id |

**활용 예시**
- LLM 추론 시간 이상 증가 감지 (① 패널)
- OCR 요청 패턴 파악 (④ 패널)
- AI 에러 발생 시 trace_id로 NestJS 로그 연계 조회

---

## 대시보드 3 — E2E 요청 추적

> 인덱스: `ai-habit-api-logs-*`, `ai-habit-ai-logs-*`

`trace_id` / `span_id` / `user_id` 기반으로 전체 요청 흐름을 추적합니다.

| # | 패널 | 시각화 | 설명 |
|---|------|--------|------|
| ① | HTTP 평균 응답시간 | 단일 지표 | NestJS 전체 요청 `duration_ms` 평균 |
| ② | OCR 평균 처리시간 | 단일 지표 | FastAPI OCR `duration_ms` 평균 |
| ③ | LLM 평균 추론시간 | 단일 지표 | FastAPI LLM `duration_ms` 평균 |
| ④ | 느린 요청 목록 (1초 초과) | 데이터 테이블 | `duration_ms > 1000` → URL, trace_id, user_id |
| ⑤ | 사용자별 평균 응답시간 | 수평 막대 | `user_id` 기준 `duration_ms` 평균 |

**trace_id 활용 흐름**
```
① Kibana Discover → trace_id 검색
② 해당 trace_id의 NestJS 로그 (span_id: HTTP span)
③ 같은 trace_id의 FastAPI OCR 로그 (span_id: OCR span)
④ 같은 trace_id의 FastAPI LLM 로그 (span_id: LLM span)
→ 전 구간 지연 원인 파악
```

**활용 예시**
- 특정 요청의 OCR vs LLM 구간 지연 비교 (①②③ 비교)
- 느린 요청에서 trace_id 추출 후 Discover에서 전 구간 조회
- 사용자별 응답시간 편차 분석 (⑤ 패널)

---

## 대시보드 4 — 에러 & 이상 탐지

> 인덱스: `ai-habit-api-logs-*`, `ai-habit-ai-logs-*`

에러 발생 패턴과 성능 이상을 탐지합니다.

| # | 패널 | 시각화 | 설명 |
|---|------|--------|------|
| ① | 시간대별 에러 발생 추이 | 막대 | `level: error` 시간대별 건수 |
| ② | 에러 발생 위치 (context) | 파이 | NestJS 모듈별 에러 비율 |
| ③ | LLM 느린 추론 (10초 초과) | 데이터 테이블 | `duration_ms > 10000` → trace_id, user_id |
| ④ | 5xx 에러 목록 | 데이터 테이블 | `status_code >= 500` → URL, 상태 코드, trace_id |

**활용 예시**
- 에러가 특정 모듈(RecordsService 등)에 집중되는지 확인 (② 패널)
- LLM 타임아웃 전조 증상 조기 감지 (③ 패널)
- 5xx 에러 발생 시 trace_id로 원인 추적 (④ 패널)

---

## 로그 필드 참조

| 필드 | 타입 | 출처 | 설명 |
|------|------|------|------|
| `@timestamp` | date | Filebeat | 로그 수집 시각 |
| `trace_id` | keyword | NestJS + FastAPI | 요청 단위 고유 ID (E2E 추적) |
| `span_id` | keyword | NestJS + FastAPI | 작업 단위 고유 ID |
| `user_id` | keyword | NestJS + FastAPI | 요청 사용자 (X-User-Id 헤더) |
| `service` | keyword | 양쪽 | `nestjs-api` / `fastapi-ai` |
| `level` | keyword | 양쪽 | `info` / `warn` / `error` |
| `context` | keyword | NestJS | 모듈명 (HTTP, RecordsService 등) |
| `duration_ms` | number | 양쪽 | 처리 소요 시간 (ms) |
| `method` | keyword | NestJS | HTTP 메서드 |
| `url` | keyword | NestJS | 요청 URL |
| `status_code` | number | NestJS | HTTP 응답 코드 |
| `chars` | number | FastAPI | OCR 추출 문자 수 |
