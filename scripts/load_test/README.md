# Load Test 가이드

## 사전 준비

```bash
pip3 install pyyaml Pillow requests
```

## 실행 모드

### Sequential 모드 (기본값, LLM 포함 권장)

응답을 받은 후 다음 요청을 전송합니다. 큐 누적 없이 안정적으로 테스트할 수 있습니다.

```bash
# 기본 실행 (config.yaml 기준, sequential 20건)
python3 scripts/load_test/load_test.py

# 요청 수 / 대기 시간 오버라이드
python3 scripts/load_test/load_test.py --requests 10 --delay 5

# 이미지 삭제 안 하고 확인
python3 scripts/load_test/load_test.py --requests 3 --no-delete

# 백그라운드 실행
nohup python3 scripts/load_test/load_test.py > /dev/null 2>&1 &
```

### Concurrent 모드 (OCR only 권장)

TPS 기반 동시 요청을 전송합니다. LLM 포함 시 0.033 TPS 초과 시 타임아웃이 연쇄 발생합니다.

```bash
# concurrent 모드로 전환
python3 scripts/load_test/load_test.py --mode concurrent --tps 0.03 --duration 300

# OCR only (LLM 비활성화 시) 높은 TPS 테스트
python3 scripts/load_test/load_test.py --mode concurrent --tps 1 --duration 60
```

## CLI 옵션

| 옵션 | 설명 |
|------|------|
| `--mode sequential\|concurrent` | 실행 모드 (config.yaml 오버라이드) |
| `--requests N` | 총 요청 수 (sequential) |
| `--delay N` | 요청 간 대기 시간 초 (sequential) |
| `--tps N` | 초당 요청 수 (concurrent) |
| `--duration N` | 실행 시간 초 (concurrent) |
| `--no-delete` | 전송 후 이미지 삭제 안 함 |
| `--config PATH` | config 파일 경로 지정 |

## 설정 파일 (config.yaml)

| 항목 | 설명 | 기본값 |
|------|------|--------|
| `load.mode` | 실행 모드 (`sequential` / `concurrent`) | `sequential` |
| `load.max_requests` | 총 요청 수 (sequential) | `20` |
| `load.delay_sec` | 요청 간 대기 시간 초 (sequential) | `2` |
| `load.tps` | 초당 요청 수 (concurrent) | `0.03` |
| `load.duration` | 테스트 실행 시간 초 (concurrent) | `300` |
| `load.max_workers` | 최대 동시 스레드 수 (concurrent) | `4` |
| `load.max_pending` | 최대 대기 요청 수 (concurrent) | `2` |
| `api.base_url` | API 서버 주소 | `http://localhost:3000` |
| `api.timeout` | 요청 타임아웃 초 | `120` |
| `images.delete_after_send` | 전송 후 이미지 삭제 여부 | `true` |
| `report.output_dir` | 결과 JSON 저장 디렉토리 | `scripts/load_test/reports` |
| `log.file` | 로그 파일 경로 (고정명) | `scripts/load_test/logs/load_test.log` |
| `log.level` | 로그 레벨 (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `log.rotate_mb` | 로그 파일 최대 크기 MB (초과 시 즉시 로테이션) | `100` |

### 로그 로테이션 방식

두 가지 조건 중 **먼저 발생하는 쪽**에서 로테이션됩니다:

| 조건 | 동작 |
|------|------|
| 파일 크기 100MB 초과 | 즉시 로테이션 |
| 자정(00:00) 도달 | 날짜별 로테이션 |

로테이션된 파일은 날짜 접미사로 보관됩니다 (`load_test.log.2026-03-09`), 최대 30일 보관.

---

## LLM 처리량 한계와 모드 선택

FastAPI의 LLM 엔드포인트는 **PyTorch 추론이 동기식**으로 실행되어 한 번에 1개 요청만 처리할 수 있습니다.

```
req1 (t=0s)  → LLM 30s → 완료 ✓
req2 (t=10s) → LLM 대기 20s + 추론 30s = 50s → 완료 ✓
req3 (t=20s) → LLM 대기 40s + 추론 30s = 70s → 완료 ✓
req4 (t=30s) → LLM 대기 60s + 추론 30s = 90s → TIMEOUT ✗
```

**LLM 최대 처리량 = 1건 ÷ 30s = 0.033 TPS**

| 시나리오 | 권장 모드 | 권장 TPS / 요청 수 | timeout |
|---------|---------|----------------|---------|
| LLM 포함 (기본) | **sequential** | max_requests=20 | 120s |
| LLM 포함 concurrent | concurrent | tps=0.02~0.03, max_workers=1 | 120s |
| OCR only | concurrent | tps=0.5~2.0, max_workers=4 | 30s |

---

## 워밍업(Warmup) 구간이 필요한 이유

LLM 모델의 **첫 번째 추론이 특히 느리기** 때문입니다.

```
요청 #1 (콜드 스타트): 35,000ms  ← 모델 캐시 로딩, JIT 컴파일 등
요청 #2             : 27,000ms
요청 #3             : 26,500ms
요청 #4~            : 25,000~28,000ms  ← 안정 구간
```

워밍업 없이 통계를 내면 #1의 이상값이 평균/p95를 왜곡합니다.

```
워밍업 없음:  avg=29,500ms  p95=34,800ms  ← 콜드 스타트 이상값 포함
워밍업 있음:  avg=26,200ms  p95=28,100ms  ← 실제 안정 성능
```

sequential 모드에서는 **첫 1~2건을 제외하고 통계를 해석**하거나, 서버가 이미 웜업된 상태에서 테스트하는 것을 권장합니다.

| 구성 요소 | 콜드 스타트 영향 |
|----------|----------------|
| LLM 모델 (Qwen 1.5B) | 첫 추론 시 CPU 캐시 미스 → 유독 느림 |
| NestJS | DB 커넥션 풀 초기화 |
| PostgreSQL | 쿼리 플랜 캐시 미적재 |

---

## 로그 확인 (grep 예제)

> 로그 파일 이름은 실행마다 다릅니다. 최신 파일을 먼저 확인하세요:
> ```bash
> ls -t scripts/load_test/logs/ | head -1
> ```

이하 예제에서 `LOG=scripts/load_test/logs/load_test_*.log` 형태로 파일을 지정하거나, 최신 파일을 변수로 사용하세요:

```bash
LOG=$(ls -t scripts/load_test/logs/load_test_*.log | head -1)
```

### 기본 모니터링

```bash
# 실시간 전체 로그 추적
tail -f $LOG

# 최근 50줄
tail -50 $LOG

# 특정 줄 수부터 실시간
tail -n 0 -f $LOG
```

### 진행 상황 (Sequential 모드)

```bash
# 각 요청 결과 확인 (sequential: [N/M] 형태)
grep "\[.*\/.*\]" $LOG

# 누계 통계 (5건마다 출력)
grep "\[누계" $LOG

# 테스트 시작/종료 확인
grep "모드: Sequential\|최종 결과\|결과 저장" $LOG

# 실패 요청만
grep "FAIL" $LOG
```

### 진행 상황 (Concurrent 모드)

```bash
# 누계 통계 (30초마다 출력)
grep "\[누계" $LOG

# 테스트 시작/종료 확인
grep "모드: Concurrent\|최종 결과\|결과 저장" $LOG

# TPS 설정값 확인
grep "TPS=" $LOG
```

### 성능 지표

```bash
# p95 응답시간만 추출
grep "\[누계" $LOG | grep -o "p95=[0-9]*ms"

# 평균 응답시간 추이
grep "\[누계" $LOG | grep -o "avg=[0-9]*ms"

# 최종 응답시간 통계
grep "응답시간(ms)" $LOG

# 실제 TPS
grep "실제 TPS" $LOG
```

### 에러 탐지

```bash
# 에러/경고만 필터
grep "WARNING\|ERROR" $LOG

# 에러 유형 확인
grep "에러 유형" $LOG

# timeout 에러만
grep "timeout" $LOG

# connection 에러만
grep "connection_error" $LOG

# 이미지 생성 실패
grep "이미지 생성 실패" $LOG
```

### 성공률

```bash
# 성공률 추이 (누계 통계에서)
grep "\[누계" $LOG | grep -o "성공률=[0-9.]*%"

# 100% 미만인 구간만
grep "\[누계" $LOG | grep -v "성공률=100%"

# 최종 성공/실패 건수
grep "성공 \+:\|실패 \+:" $LOG
```

### 완료 확인

```bash
# 테스트 완료 여부 (결과 파일 저장 시점)
grep "결과 저장" $LOG

# 최종 결과 요약
grep -A 10 "최종 결과" $LOG
```

### 복합 활용

```bash
# 타임스탬프 포함 에러만
grep "WARNING\|ERROR" $LOG | grep -v "^$"

# 특정 시간대 로그 (예: 15:10 ~ 15:15)
grep "15:1[0-5]" $LOG

# sequential 모드: 요청별 duration만 추출
grep "\[.*\/.*\] HTTP" $LOG | grep -o "duration=[0-9]*ms"

# sequential 모드: 요청별 결과를 CSV 형태로
grep "\[.*\/.*\] HTTP" $LOG \
  | sed 's/.*\[\([0-9]*\)\/[0-9]*\] HTTP \([0-9]*\).*duration=\([0-9]*\)ms.*경과=\([0-9]*\)s/\1,\2,\3,\4/' \
  | awk 'BEGIN{print "seq,status,duration_ms,elapsed_s"} {print}'
```

---

## 로그 파일 관리

```bash
# 로그 디렉토리 확인
ls -lh scripts/load_test/logs/

# 최신 로그 파일 확인
ls -t scripts/load_test/logs/ | head -5

# 이전 실행 결과 비교
grep "최종 결과" -A 10 scripts/load_test/logs/load_test_20260309_151045.log
```

## 결과 파일 (scripts/load_test/reports/)

결과 파일은 실행마다 타임스탬프로 구분됩니다:
```
scripts/load_test/reports/load_test_result_20260309_151045.json
```

```bash
# 최신 결과 파일 확인
REPORT=$(ls -t scripts/load_test/reports/load_test_result_*.json | head -1)

# 전체 결과 확인
cat $REPORT | python3 -m json.tool

# 특정 지표만
cat $REPORT | python3 -c "
import json, sys
d = json.load(sys.stdin)
dm = d.get('duration_ms', {})
print(f\"모드: {d['config']['mode']}, 총 요청: {d['total']}, 성공률: {d['success_pct']}%\")
print(f\"avg: {dm.get('avg')}ms, p95: {dm.get('p95')}ms, p99: {dm.get('p99')}ms\")
print(f\"실제 TPS: {d['actual_tps']}, 경과: {d['elapsed']}s\")
"

# 모든 실행 결과 목록
ls -lh scripts/load_test/reports/

# 특정 날짜 결과만
ls scripts/load_test/reports/load_test_result_20260309_*.json
```
