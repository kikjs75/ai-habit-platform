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
| `test_phase5.py` | Phase 5 | ES 클러스터 상태, 포트 9200 |
| `test_phase6.py` | Phase 6 | ai-habit-* 인덱스 존재, 도큐먼트 적재 |
| `test_phase7.py` | Phase 7 | Logstash 구동, JSON 필드 구조화 확인 |
| `test_phase8.py` | Phase 8 | Kibana 상태, Data View 존재 |

---

## 참고 — 서비스 포트 (HostOS 기준)

| 서비스 | 포트 |
|--------|------|
| NestJS API | 3000 |
| FastAPI AI | 8000 |
| Elasticsearch | 9200 |
| Logstash API | 9600 |
| Kibana | 5601 |
