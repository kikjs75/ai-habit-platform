#!/usr/bin/env bash
# Phase 검증 실행 스크립트
# 사용법:
#   ./run.sh          → 전체 실행
#   ./run.sh 5        → Phase 5만 실행
#   ./run.sh 5 6      → Phase 5, 6 실행

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 의존성 설치 확인
if ! python -c "import pytest, requests" 2>/dev/null; then
  echo "[setup] Installing dependencies..."
  pip install -r requirements.txt -q
fi

if [ $# -eq 0 ]; then
  # 전체 실행
  echo "=== Running all phase verifications ==="
  pytest test_phase1.py test_phase5.py test_phase6.py test_phase7.py test_phase8.py -v
else
  # 지정 Phase만 실행
  FILES=""
  for phase in "$@"; do
    FILES="$FILES test_phase${phase}.py"
  done
  echo "=== Running Phase $* verification ==="
  pytest $FILES -v
fi
