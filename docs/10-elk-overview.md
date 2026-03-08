# ELK Stack 연동 개요

## 목적

AI Habit Platform의 NestJS API, FastAPI AI 서비스에서 발생하는 로그를 수집·가공·저장·시각화한다.

## 파이프라인

```
NestJS API (stdout)  ─┐
                       ├─► Filebeat ─► Logstash ─► Elasticsearch ─► Kibana
FastAPI AI (stdout)  ─┘
```

## 구성 요소 및 역할

| 컴포넌트 | 역할 | Phase |
|----------|------|-------|
| Elasticsearch | 로그 저장 및 검색 엔진 | Phase 5 |
| Filebeat | Docker 컨테이너 로그 수집 및 전달 | Phase 6 |
| Logstash | 로그 파싱 및 구조화 파이프라인 | Phase 7 |
| Kibana | 대시보드 및 시각화 | Phase 8 |

## 포트 할당

| 서비스 | 포트 |
|--------|------|
| Elasticsearch | 9200 |
| Logstash (Beats input) | 5044 |
| Logstash (HTTP API) | 9600 |
| Kibana | 5601 |

## 수집 대상 로그

| 서비스 | 로그 내용 |
|--------|-----------|
| NestJS API | HTTP 요청/응답, OCR 처리, LLM 처리, 에러 |
| FastAPI AI | OCR 요청, LLM 추론 요청, 모델 로딩 |

## 개발 순서

```
Phase 5 → Elasticsearch 단독 구성 및 검증
Phase 6 → Filebeat 추가, 로그 수집 확인
Phase 7 → Logstash 추가, 파이프라인 파싱 구성
Phase 8 → Kibana 추가, 대시보드 구성
```

## 버전

| 컴포넌트 | 버전 |
|----------|------|
| Elasticsearch | 8.13.0 |
| Logstash | 8.13.0 |
| Filebeat | 8.13.0 |
| Kibana | 8.13.0 |

> ELK 스택은 동일 버전을 사용해야 한다.
