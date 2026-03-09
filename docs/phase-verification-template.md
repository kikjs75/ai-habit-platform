# Phase 검증 템플릿

각 Phase 완료 시 이 템플릿을 복사해 결과를 기록한다.

## 검증 실행 방법

### 사전 준비 (최초 1회)

```bash
cd scripts/verify
pip3 install -r requirements.txt
```

### Phase별 실행

```bash
# 특정 Phase만
./scripts/verify/run.sh 5

# 여러 Phase
./scripts/verify/run.sh 5 6

# 전체
./scripts/verify/run.sh
```

### 직접 실행 (pytest)

```bash
cd scripts/verify
python3 -m pytest test_phase5.py -v
```

---

## 검증 결과 기록 양식

```
Phase N — [Phase 명칭]
검증일: YYYY-MM-DD
검증자: (본인)
실행 명령: ./scripts/verify/run.sh N

결과:
  test_phaseN.py::ClassName::test_xxx   PASSED
  test_phaseN.py::ClassName::test_yyy   PASSED
  ...

완료 조건 체크:
  - [x] 조건 1
  - [x] 조건 2
  - [ ] 조건 3 (미완료 시 사유 기재)

비고:
  (특이사항 자유 기재)
```

---

## 검증 파일 목록

| 파일 | 대상 Phase | 검증 항목 |
|------|-----------|-----------|
| `test_phase1.py` | Phase 1 | NestJS /health, FastAPI /health, Swagger |
| `test_phase2.py` | Phase 2 | FastAPI OCR: 실제 이미지 업로드, text 추출 |
| `test_phase3.py` | Phase 3 | 통합: POST /records/ocr → OCR → LLM → DB (느림, ~120s) |
| `test_phase4.py` | Phase 4 | /auth/google 302, /calendar/events, /notifications/send 등록 확인 |
| `test_phase5.py` | Phase 5 | ES 클러스터 상태, 포트 9200 |
| `test_phase6.py` | Phase 6 | ai-habit-* 인덱스 존재, 도큐먼트 적재 (retry 60s) |
| `test_phase7.py` | Phase 7 | Logstash 구동, JSON 필드 구조화 확인 (retry 60s) |
| `test_phase8.py` | Phase 8 | Kibana 상태, Data View 존재 |

## 검증 커버리지 체크리스트

각 Phase 완료 시 아래 항목이 모두 커버되는지 확인:

- [ ] 서비스 health check — 포트 응답 확인
- [ ] 기능 테스트 — 실제 입력으로 엔드포인트 호출
- [ ] 통합 테스트 — 서비스 간 연동 흐름 검증
- [ ] 타이밍/retry — 비동기 파이프라인은 폴링으로 대기
- [ ] Compose 준비 — 필수 컨테이너 정상 구동 확인

## 전체 실행 옵션

```bash
# 기본 전체 (Phase 3 LLM 제외)
./scripts/verify/run.sh

# LLM 포함 전체 (~2분 이상 소요)
./scripts/verify/run.sh --all

# docker compose 상태 확인 후 전체 실행
./scripts/verify/run.sh --compose
```

---

## 참고 — 서비스 포트 (HostOS 기준)

| 서비스 | 포트 |
|--------|------|
| NestJS API | 3000 |
| FastAPI AI | 8000 |
| Elasticsearch | 9200 |
| Logstash API | 9600 |
| Kibana | 5601 |
