# Load Test 가이드

## 실행 방법

```bash
# 기본 실행 (config.yaml 기준)
python3 scripts/load_test/load_test.py

# 설정 오버라이드
python3 scripts/load_test/load_test.py --tps 2 --duration 30
python3 scripts/load_test/load_test.py --tps 0.5 --duration 120 --warmup 10

# 이미지 삭제 안 하고 확인
python3 scripts/load_test/load_test.py --tps 1 --duration 10 --no-delete

# 백그라운드 실행
nohup python3 scripts/load_test/load_test.py --tps 1 --duration 60 > /dev/null 2>&1 &
```

## 설정 파일 (config.yaml)

| 항목 | 설명 | 기본값 |
|------|------|--------|
| `api.base_url` | API 서버 주소 | `http://localhost:3000` |
| `api.timeout` | 요청 타임아웃 (초) | `90` |
| `load.tps` | 초당 요청 수 | `1` |
| `load.duration` | 테스트 실행 시간 (초) | `60` |
| `load.warmup` | 워밍업 구간 (초, 통계 제외) | `5` |
| `load.max_workers` | 최대 동시 요청 스레드 수 | `4` |
| `images.delete_after_send` | 전송 후 이미지 삭제 여부 | `true` |
| `report.print_interval` | 중간 통계 출력 주기 (초) | `10` |
| `log.file` | 로그 파일 경로 | `load_test.log` |
| `log.level` | 로그 레벨 (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `log.rotate_mb` | 로그 파일 최대 크기 (MB) | `10` |

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

### 이 프로젝트에서 특히 중요한 이유

| 구성 요소 | 콜드 스타트 영향 |
|----------|----------------|
| LLM 모델 (Qwen 1.5B) | 첫 추론 시 CPU 캐시 미스 → 유독 느림 |
| NestJS | DB 커넥션 풀 초기화 |
| PostgreSQL | 쿼리 플랜 캐시 미적재 |

**워밍업 구간 = "실제 운영 상태"가 되기까지의 준비 시간**
요청은 정상적으로 전송하되, 통계 집계에서만 제외합니다.

> 서버가 이미 충분히 동작 중인 상태라면 `config.yaml`에서 `warmup: 0`으로 설정하면 됩니다.

---

## 로그 확인 (grep 예제)

### 기본 모니터링

```bash
# 실시간 전체 로그 추적
tail -f load_test.log

# 최근 50줄
tail -50 load_test.log

# 특정 줄 수부터 실시간
tail -n 0 -f load_test.log
```

### 진행 상황

```bash
# 중간 통계만 (10초 주기 요약)
grep "\[진행" load_test.log

# 테스트 시작/종료 확인
grep "Load Test 시작\|최종 결과\|결과 저장" load_test.log

# 설정값 확인 (TPS, Duration)
grep "TPS=" load_test.log

# 워밍업 완료 시점 확인
grep "워밍업" load_test.log
```

### 성능 지표

```bash
# TPS와 응답시간만 추출
grep "\[진행" load_test.log | awk '{print $1, $2, $5, $6, $7}'

# p95 응답시간만 추출
grep "\[진행" load_test.log | grep -o "p95=[0-9]*ms"

# 평균 응답시간 추이
grep "\[진행" load_test.log | grep -o "avg=[0-9]*ms"

# 최종 응답시간 통계
grep "응답시간(ms)" load_test.log
```

### 에러 탐지

```bash
# 에러/경고만 필터
grep "WARNING\|ERROR" load_test.log

# 에러 유형 확인
grep "에러 유형" load_test.log

# timeout 에러만
grep "timeout" load_test.log

# connection 에러만
grep "connection_error" load_test.log

# 이미지 생성 실패
grep "이미지 생성 실패" load_test.log
```

### 성공률

```bash
# 성공률 추이
grep "\[진행" load_test.log | grep -o "성공률=[0-9.]*%"

# 100% 미만인 구간만
grep "\[진행" load_test.log | grep -v "성공률=100%"

# 최종 성공/실패 건수
grep "성공\s*:\|실패\s*:" load_test.log
```

### 완료 확인

```bash
# 테스트 완료 여부 (결과 파일 저장 시점)
grep "결과 저장" load_test.log

# 최종 결과 요약 (마지막 5줄)
grep -A 10 "최종 결과" load_test.log

# 실제 TPS 달성 여부
grep "실제 TPS" load_test.log
```

### 복합 활용

```bash
# 타임스탬프 포함 에러만
grep "WARNING\|ERROR" load_test.log | grep -v "^$"

# 특정 시간대 로그 (예: 12:05 ~ 12:10)
grep "12:0[5-9]" load_test.log

# 진행 요약을 CSV 형태로 보기
grep "\[진행" load_test.log \
  | sed 's/.*\[진행 \([0-9.]*\)s\] 요청=\([0-9]*\).*성공률=\([0-9.]*\)%.*실제TPS=\([0-9.]*\).*avg=\([0-9-]*\)ms.*/\1,\2,\3,\4,\5/' \
  | awk 'BEGIN{print "elapsed,requests,success_pct,tps,avg_ms"} {print}'
```

---

## 로그 파일 관리

```bash
# 현재 로그 파일 크기 확인
ls -lh load_test.log*

# rotate된 파일 목록
ls load_test.log*

# 이전 실행 결과 비교 (rotate 파일 포함)
cat load_test.log.1 | grep "최종 결과" -A 10

# 로그 파일 초기화 (다음 실행 전)
> load_test.log
```

## 결과 파일 (load_test_result.json)

```bash
# 전체 결과 확인
cat load_test_result.json | python3 -m json.tool

# 특정 지표만
cat load_test_result.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
dm = d.get('duration_ms', {})
print(f\"총 요청: {d['total']}, 성공률: {d['success_pct']}%\")
print(f\"avg: {dm.get('avg')}ms, p95: {dm.get('p95')}ms, p99: {dm.get('p99')}ms\")
"
```
