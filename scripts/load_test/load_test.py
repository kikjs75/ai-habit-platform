#!/usr/bin/env python3
"""
AI Habit Platform — OCR Load Test

이미지를 동적으로 생성하고 POST /records/ocr 에 부하를 발생시킵니다.
TPS(Transactions Per Second) 기반으로 요청 속도를 제어합니다.

Usage:
    python3 scripts/load_test/load_test.py
    python3 scripts/load_test/load_test.py --config scripts/load_test/config.yaml
    python3 scripts/load_test/load_test.py --tps 2 --duration 30
"""

import argparse
import json
import logging
import logging.handlers
import os
import random
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import requests
import yaml
from PIL import Image, ImageDraw

# 모듈 레벨 logger — setup_logging() 호출 후 활성화
logger = logging.getLogger("load_test")

# ─── 로깅 설정 ───────────────────────────────────────────────────────────────

def setup_logging(log_cfg: dict) -> None:
    """콘솔 + 파일(rotating) 동시 출력"""
    log_file = log_cfg.get("file", "scripts/load_test/logs/load_test.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    level_str = log_cfg.get("level", "INFO").upper()
    rotate_mb = log_cfg.get("rotate_mb", 10)
    level = getattr(logging, level_str, logging.INFO)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.setLevel(level)

    # 콘솔 핸들러
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 파일 핸들러 (rotating)
    fh = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=rotate_mb * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.info(f"로그 파일: {Path(log_file).resolve()}")


# ─── 샘플 데이터 풀 ──────────────────────────────────────────────────────────

PRODUCT_POOL = [
    {"name": "Whole Milk",      "calories": 150, "fat": "8g",   "protein": "8g",   "carb": "12g", "sodium": "120mg"},
    {"name": "Greek Yogurt",    "calories": 100, "fat": "0g",   "protein": "17g",  "carb": "6g",  "sodium": "65mg"},
    {"name": "Chicken Breast",  "calories": 165, "fat": "3.6g", "protein": "31g",  "carb": "0g",  "sodium": "74mg"},
    {"name": "Brown Rice",      "calories": 216, "fat": "1.8g", "protein": "5g",   "carb": "45g", "sodium": "10mg"},
    {"name": "Salmon Fillet",   "calories": 208, "fat": "13g",  "protein": "20g",  "carb": "0g",  "sodium": "59mg"},
    {"name": "Almond Butter",   "calories": 190, "fat": "17g",  "protein": "7g",   "carb": "7g",  "sodium": "0mg"},
    {"name": "Banana",          "calories": 105, "fat": "0.4g", "protein": "1.3g", "carb": "27g", "sodium": "1mg"},
    {"name": "Cheddar Cheese",  "calories": 113, "fat": "9g",   "protein": "7g",   "carb": "0.4g","sodium": "174mg"},
    {"name": "Oatmeal",         "calories": 166, "fat": "3.6g", "protein": "5.9g", "carb": "28g", "sodium": "9mg"},
    {"name": "Avocado",         "calories": 114, "fat": "10g",  "protein": "1.3g", "carb": "6g",  "sodium": "5mg"},
    {"name": "Egg",             "calories": 78,  "fat": "5g",   "protein": "6g",   "carb": "0.6g","sodium": "62mg"},
    {"name": "Sweet Potato",    "calories": 103, "fat": "0.1g", "protein": "2.3g", "carb": "24g", "sodium": "41mg"},
    {"name": "Tuna Can",        "calories": 109, "fat": "2.5g", "protein": "20g",  "carb": "0g",  "sodium": "287mg"},
    {"name": "Cottage Cheese",  "calories": 206, "fat": "9g",   "protein": "25g",  "carb": "8g",  "sodium": "764mg"},
    {"name": "Peanut Butter",   "calories": 188, "fat": "16g",  "protein": "8g",   "carb": "6g",  "sodium": "147mg"},
]

SERVING_SIZES = [
    "100g", "150g", "200g", "1 cup (240ml)", "1 oz (28g)",
    "2 tbsp (32g)", "1 medium (118g)", "1/2 fruit (68g)",
]


# ─── 이미지 생성 ──────────────────────────────────────────────────────────────

def generate_image(output_dir: Path, width: int, height: int) -> Path:
    """랜덤 영양성분 데이터로 이미지 생성"""
    product = random.choice(PRODUCT_POOL)
    serving = random.choice(SERVING_SIZES)

    # 값에 약간의 랜덤 변이를 주어 다양한 데이터 생성
    calories = product["calories"] + random.randint(-20, 20)

    lines = [
        "Nutrition Facts",
        f"Product: {product['name']}",
        f"Serving Size {serving}",
        "",
        f"Calories {calories}",
        f"Total Fat {product['fat']}",
        f"Protein {product['protein']}",
        f"Total Carbohydrate {product['carb']}",
        f"Sodium {product['sodium']}",
        "",
        f"Generated: {datetime.now().strftime('%H:%M:%S')}",
    ]

    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    y = 20
    for line in lines:
        draw.text((20, y), line, fill="black")
        y += 28

    filename = output_dir / f"load_{uuid.uuid4().hex[:8]}.png"
    img.save(filename)
    return filename


# ─── 단일 요청 실행 ───────────────────────────────────────────────────────────

def send_request(cfg: dict, image_path: Path) -> dict:
    """이미지 파일로 OCR 요청 전송, 결과 반환"""
    url = cfg["api"]["base_url"].rstrip("/") + cfg["api"]["endpoint"]
    user_id = cfg["api"]["user_id"]
    timeout = cfg["api"]["timeout"]

    start = time.monotonic()
    status = 0
    error = None

    try:
        with open(image_path, "rb") as f:
            res = requests.post(
                url,
                files={"image": (image_path.name, f, "image/png")},
                headers={"X-User-Id": user_id},
                timeout=timeout,
            )
        status = res.status_code
    except requests.exceptions.Timeout:
        error = "timeout"
    except requests.exceptions.ConnectionError:
        error = "connection_error"
    except Exception as e:
        error = str(e)
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        # 이미지 삭제
        if cfg["images"]["delete_after_send"]:
            try:
                image_path.unlink()
            except FileNotFoundError:
                pass

    return {
        "duration_ms": duration_ms,
        "status": status,
        "error": error,
        "success": (status == 200 or status == 201),
    }


# ─── 통계 집계 ────────────────────────────────────────────────────────────────

class Stats:
    def __init__(self):
        self._lock = threading.Lock()
        self.results: list[dict] = []
        self.start_time: float = 0.0

    def add(self, result: dict):
        with self._lock:
            self.results.append(result)

    def summary(self, warmup: int = 0) -> dict:
        with self._lock:
            data = self.results[:]

        elapsed = time.monotonic() - self.start_time
        # 워밍업 제외: 시작 후 warmup 초 이내 결과 제거
        effective = [r for r in data if r.get("ts", 0) >= warmup]

        if not effective:
            return {"total": 0, "elapsed": round(elapsed, 1)}

        durations = [r["duration_ms"] for r in effective]
        durations_sorted = sorted(durations)
        n = len(durations_sorted)
        successes = sum(1 for r in effective if r["success"])
        errors = [r["error"] for r in effective if r["error"]]

        def percentile(lst, p):
            idx = max(0, int(len(lst) * p / 100) - 1)
            return lst[idx]

        effective_duration = max(elapsed - warmup, 1)

        return {
            "total":       len(effective),
            "success":     successes,
            "error":       len(effective) - successes,
            "success_pct": round(successes / len(effective) * 100, 1),
            "actual_tps":  round(len(effective) / effective_duration, 2),
            "elapsed":     round(elapsed, 1),
            "duration_ms": {
                "avg":  round(sum(durations) / n),
                "min":  durations_sorted[0],
                "max":  durations_sorted[-1],
                "p50":  percentile(durations_sorted, 50),
                "p95":  percentile(durations_sorted, 95),
                "p99":  percentile(durations_sorted, 99),
            },
            "errors": list(set(errors))[:5],
        }


# ─── 부하 테스트 실행 ────────────────────────────────────────────────────────

def run(cfg: dict):
    tps = cfg["load"]["tps"]
    duration = cfg["load"]["duration"]
    warmup = cfg["load"]["warmup"]
    max_workers = cfg["load"]["max_workers"]
    print_interval = cfg["report"]["print_interval"]

    output_dir = Path(cfg["images"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    img_width = cfg["images"]["width"]
    img_height = cfg["images"]["height"]

    stats = Stats()
    interval = 1.0 / tps  # 요청 간격 (초)

    logger.info("=" * 55)
    logger.info("AI Habit Load Test 시작")
    logger.info(f"TPS={tps}  Duration={duration}s  Warmup={warmup}s  Workers={max_workers}")
    logger.info(f"Target: {cfg['api']['base_url']}{cfg['api']['endpoint']}")
    logger.info("=" * 55)
    if warmup > 0:
        logger.info(f"워밍업 {warmup}초 진행 중...")

    stats.start_time = time.monotonic()
    end_time = stats.start_time + duration + warmup
    # 워밍업 직후 첫 출력, 이후 print_interval 주기
    next_print = stats.start_time + warmup + min(print_interval, duration)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        while time.monotonic() < end_time:
            loop_start = time.monotonic()
            ts = loop_start - stats.start_time  # 경과 시간

            # 이미지 생성 및 요청 제출
            try:
                image_path = generate_image(output_dir, img_width, img_height)
            except Exception as e:
                logger.error(f"이미지 생성 실패: {e}")
                time.sleep(interval)
                continue

            future = executor.submit(send_request, cfg, image_path)
            future._ts = ts  # 타임스탬프 첨부
            futures.append(future)

            # 완료된 futures 수집
            done = [f for f in futures if f.done()]
            for f in done:
                result = f.result()
                result["ts"] = f._ts
                stats.add(result)
            futures = [f for f in futures if not f.done()]

            # 중간 통계 출력
            now = time.monotonic()
            if now >= next_print and (now - stats.start_time) > warmup:
                s = stats.summary(warmup)
                dm = s.get("duration_ms", {})
                logger.info(
                    f"[진행 {s['elapsed']}s] "
                    f"요청={s['total']}  "
                    f"성공률={s.get('success_pct', 0)}%  "
                    f"실제TPS={s.get('actual_tps', 0)}  "
                    f"avg={dm.get('avg', '-')}ms  "
                    f"p95={dm.get('p95', '-')}ms"
                )
                if s.get("errors"):
                    logger.warning(f"에러 유형: {s['errors']}")
                next_print += print_interval

            # TPS 속도 조절
            elapsed_loop = time.monotonic() - loop_start
            sleep_time = interval - elapsed_loop
            if sleep_time > 0:
                time.sleep(sleep_time)

        # 남은 futures 수집 (요청 타임아웃 내에서 대기)
        if futures:
            request_timeout = cfg["api"]["timeout"]
            logger.info(f"진행 중인 요청 {len(futures)}개 완료 대기 (최대 {request_timeout}s)...")
            for f in futures:
                try:
                    result = f.result(timeout=request_timeout)
                    result["ts"] = getattr(f, "_ts", 0)
                    stats.add(result)
                except Exception:
                    stats.add({"duration_ms": request_timeout * 1000,
                               "status": 0, "error": "timeout", "success": False,
                               "ts": getattr(f, "_ts", 0)})

    # ─── 최종 리포트 ──────────────────────────────────────────────────────────
    s = stats.summary(warmup)
    dm = s.get("duration_ms", {})

    logger.info("=" * 55)
    logger.info(f"최종 결과 (워밍업 {warmup}s 제외)")
    logger.info("=" * 55)
    logger.info(f"총 요청수   : {s.get('total', 0)}")
    logger.info(f"성공        : {s.get('success', 0)}")
    logger.info(f"실패        : {s.get('error', 0)}")
    logger.info(f"성공률      : {s.get('success_pct', 0)}%")
    logger.info(f"실제 TPS    : {s.get('actual_tps', 0)}")
    logger.info(f"경과 시간   : {s.get('elapsed', 0)}s")
    if dm:
        logger.info(f"응답시간(ms): avg={dm.get('avg','-')}  min={dm.get('min','-')}  "
                    f"p50={dm.get('p50','-')}  p95={dm.get('p95','-')}  "
                    f"p99={dm.get('p99','-')}  max={dm.get('max','-')}")
    if s.get("errors"):
        logger.warning(f"에러 유형   : {s['errors']}")
    logger.info("=" * 55)

    # 결과 파일 저장
    output_file = cfg["report"]["output_file"]
    s["config"] = {"tps": tps, "duration": duration, "warmup": warmup}
    s["timestamp"] = datetime.now().isoformat()
    with open(output_file, "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
    logger.info(f"결과 저장: {Path(output_file).resolve()}")


# ─── 설정 로드 ────────────────────────────────────────────────────────────────

def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="AI Habit Load Test")
    parser.add_argument("--config", default="scripts/load_test/config.yaml",
                        help="설정 파일 경로")
    parser.add_argument("--tps", type=float, help="TPS 오버라이드")
    parser.add_argument("--duration", type=int, help="실행 시간(초) 오버라이드")
    parser.add_argument("--warmup", type=int, help="워밍업 시간(초) 오버라이드")
    parser.add_argument("--no-delete", action="store_true",
                        help="이미지 삭제 안 함")
    args = parser.parse_args()

    config_path = args.config
    if not os.path.exists(config_path):
        print(f"설정 파일 없음: {config_path}")
        sys.exit(1)

    cfg = load_config(config_path)
    setup_logging(cfg.get("log", {}))

    # CLI 오버라이드
    if args.tps:
        cfg["load"]["tps"] = args.tps
    if args.duration:
        cfg["load"]["duration"] = args.duration
    if args.warmup is not None:
        cfg["load"]["warmup"] = args.warmup
    if args.no_delete:
        cfg["images"]["delete_after_send"] = False

    run(cfg)


if __name__ == "__main__":
    main()
