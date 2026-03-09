#!/usr/bin/env bash
# docker compose 전체 서비스 구동 상태 확인
# 사용법: ./check_compose.sh
# 종료 코드: 0 = 모두 정상, 1 = 비정상 서비스 존재

set -e

# 프로젝트 루트 찾기 (docker-compose.yml 위치)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== Docker Compose 서비스 상태 확인 ==="
cd "$ROOT"

# 전체 서비스 상태 출력
docker compose ps

echo ""
echo "=== 헬스체크 결과 ==="

REQUIRED_SERVICES=(
  "ai-habit-postgres"
  "ai-habit-mongo"
  "ai-habit-ai"
  "ai-habit-api"
  "ai-habit-elasticsearch"
  "ai-habit-logstash"
  "ai-habit-filebeat"
)

FAILED=0
for SERVICE in "${REQUIRED_SERVICES[@]}"; do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$SERVICE" 2>/dev/null || echo "no-healthcheck")
  STATE=$(docker inspect --format='{{.State.Status}}' "$SERVICE" 2>/dev/null || echo "not-found")

  if [ "$STATE" != "running" ]; then
    echo "  FAIL  $SERVICE — State: $STATE"
    FAILED=1
  elif [ "$STATUS" = "unhealthy" ]; then
    echo "  FAIL  $SERVICE — Health: unhealthy"
    FAILED=1
  else
    echo "  OK    $SERVICE — State: $STATE, Health: $STATUS"
  fi
done

echo ""
if [ $FAILED -eq 0 ]; then
  echo "모든 필수 서비스 정상 구동 중 ✓"
else
  echo "비정상 서비스가 있습니다. docker compose logs <service> 로 확인하세요."
  exit 1
fi
