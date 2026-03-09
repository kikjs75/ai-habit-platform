#!/usr/bin/env bash
# Phase 검증 실행 스크립트
# 사용법:
#   ./run.sh              → 전체 실행 (Phase 1~8, test_phase3 제외 — LLM 느림)
#   ./run.sh 5            → Phase 5만 실행
#   ./run.sh 1 2 3        → Phase 1, 2, 3 실행
#   ./run.sh --all        → LLM 통합 테스트(Phase 3) 포함 전체 실행
#   ./run.sh --compose    → docker compose 상태 확인 후 전체 실행

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 의존성 설치 확인
if ! python3 -c "import pytest, requests, PIL" 2>/dev/null; then
  echo "[setup] Installing dependencies..."
  pip3 install -r requirements.txt -q
fi

# --compose 옵션 처리
if [ "$1" = "--compose" ]; then
  bash "$SCRIPT_DIR/check_compose.sh"
  shift
fi

# --all 옵션 처리 (LLM 포함 전체)
if [ "$1" = "--all" ]; then
  echo "=== Running ALL phase verifications (including LLM integration — may take 2+ min) ==="
  python3 -m pytest \
    test_phase1.py test_phase2.py test_phase3.py test_phase4.py \
    test_phase5.py test_phase6.py test_phase7.py test_phase8.py \
    -v
  exit 0
fi

if [ $# -eq 0 ]; then
  # 기본 전체 실행 (Phase 3 제외 — LLM 느림)
  echo "=== Running phase verifications (skip Phase 3 LLM — use --all to include) ==="
  python3 -m pytest \
    test_phase1.py test_phase2.py test_phase4.py \
    test_phase5.py test_phase6.py test_phase7.py test_phase8.py \
    -v
else
  # 지정 Phase만 실행
  FILES=""
  for phase in "$@"; do
    FILES="$FILES test_phase${phase}.py"
  done
  echo "=== Running Phase $* verification ==="
  python3 -m pytest $FILES -v
fi
