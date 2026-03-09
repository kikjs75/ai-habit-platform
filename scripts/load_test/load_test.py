#!/usr/bin/env python3
"""
AI Habit Platform — OCR Load Test

Usage:
    python3 scripts/load_test/load_test.py                        # config.yaml 기준
    python3 scripts/load_test/load_test.py --mode sequential      # 순차 실행
    python3 scripts/load_test/load_test.py --mode concurrent      # 동시 실행
    python3 scripts/load_test/load_test.py --requests 10          # 요청 10건
    python3 scripts/load_test/load_test.py --delay 5              # 요청 간 5초 대기
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

logger = logging.getLogger("load_test")


# ─── 로깅 설정 ───────────────────────────────────────────────────────────────

class _SizedTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """일별 로테이션 + 100MB 크기 초과 시 즉시 로테이션."""

    def __init__(self, filename, max_bytes=0, **kwargs):
        super().__init__(filename, **kwargs)
        self.max_bytes = max_bytes

    def shouldRollover(self, record) -> bool:
        if self.max_bytes > 0 and self.stream:
            self.stream.seek(0, 2)
            if self.stream.tell() >= self.max_bytes:
                return 1
        return super().shouldRollover(record)


def setup_logging(log_cfg: dict) -> None:
    log_file = log_cfg.get("file", "scripts/load_test/logs/load_test.log")
    p = Path(log_file)
    p.parent.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
    rotate_mb = log_cfg.get("rotate_mb", 100)

    logger.setLevel(level)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = _SizedTimedRotatingFileHandler(
        log_file,
        max_bytes=rotate_mb * 1024 * 1024,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.info(f"로그 파일: {p.resolve()}")


# ─── 샘플 데이터 풀 ──────────────────────────────────────────────────────────

PRODUCT_POOL = [
    {"name": "Whole Milk",     "calories": 150, "fat": "8g",   "protein": "8g",   "carb": "12g", "sodium": "120mg"},
    {"name": "Greek Yogurt",   "calories": 100, "fat": "0g",   "protein": "17g",  "carb": "6g",  "sodium": "65mg"},
    {"name": "Chicken Breast", "calories": 165, "fat": "3.6g", "protein": "31g",  "carb": "0g",  "sodium": "74mg"},
    {"name": "Brown Rice",     "calories": 216, "fat": "1.8g", "protein": "5g",   "carb": "45g", "sodium": "10mg"},
    {"name": "Salmon Fillet",  "calories": 208, "fat": "13g",  "protein": "20g",  "carb": "0g",  "sodium": "59mg"},
    {"name": "Almond Butter",  "calories": 190, "fat": "17g",  "protein": "7g",   "carb": "7g",  "sodium": "0mg"},
    {"name": "Banana",         "calories": 105, "fat": "0.4g", "protein": "1.3g", "carb": "27g", "sodium": "1mg"},
    {"name": "Cheddar Cheese", "calories": 113, "fat": "9g",   "protein": "7g",   "carb": "0.4g","sodium": "174mg"},
    {"name": "Oatmeal",        "calories": 166, "fat": "3.6g", "protein": "5.9g", "carb": "28g", "sodium": "9mg"},
    {"name": "Avocado",        "calories": 114, "fat": "10g",  "protein": "1.3g", "carb": "6g",  "sodium": "5mg"},
    {"name": "Egg",            "calories": 78,  "fat": "5g",   "protein": "6g",   "carb": "0.6g","sodium": "62mg"},
    {"name": "Sweet Potato",   "calories": 103, "fat": "0.1g", "protein": "2.3g", "carb": "24g", "sodium": "41mg"},
    {"name": "Tuna Can",       "calories": 109, "fat": "2.5g", "protein": "20g",  "carb": "0g",  "sodium": "287mg"},
    {"name": "Cottage Cheese", "calories": 206, "fat": "9g",   "protein": "25g",  "carb": "8g",  "sodium": "764mg"},
    {"name": "Peanut Butter",  "calories": 188, "fat": "16g",  "protein": "8g",   "carb": "6g",  "sodium": "147mg"},
]

SERVING_SIZES = [
    "100g", "150g", "200g", "1 cup (240ml)", "1 oz (28g)",
    "2 tbsp (32g)", "1 medium (118g)", "1/2 fruit (68g)",
]


# ─── 이미지 생성 ──────────────────────────────────────────────────────────────

def generate_image(output_dir: Path, width: int, height: int) -> Path:
    product = random.choice(PRODUCT_POOL)
    serving = random.choice(SERVING_SIZES)
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
    url = cfg["api"]["base_url"].rstrip("/") + cfg["api"]["endpoint"]
    timeout = cfg["api"]["timeout"]
    user_id = cfg["api"]["user_id"]

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
        if cfg["images"]["delete_after_send"]:
            try:
                image_path.unlink()
            except FileNotFoundError:
                pass

    return {
        "duration_ms": duration_ms,
        "status": status,
        "error": error,
        "success": status in (200, 201),
    }


# ─── 통계 ────────────────────────────────────────────────────────────────────

def calc_stats(results: list) -> dict:
    if not results:
        return {}
    durations = sorted(r["duration_ms"] for r in results)
    n = len(durations)
    successes = sum(1 for r in results if r["success"])
    errors = list(set(r["error"] for r in results if r["error"]))

    def pct(lst, p):
        return lst[max(0, int(n * p / 100) - 1)]

    return {
        "total": n,
        "success": successes,
        "error": n - successes,
        "success_pct": round(successes / n * 100, 1),
        "duration_ms": {
            "avg": round(sum(durations) / n),
            "min": durations[0],
            "p50": pct(durations, 50),
            "p95": pct(durations, 95),
            "p99": pct(durations, 99),
            "max": durations[-1],
        },
        "errors": errors[:5],
    }


def print_stats(stats: dict, elapsed: float):
    dm = stats.get("duration_ms", {})
    logger.info(
        f"[누계 {round(elapsed)}s] "
        f"요청={stats['total']}  성공={stats['success']}  실패={stats['error']}  "
        f"성공률={stats['success_pct']}%  "
        f"avg={dm.get('avg','-')}ms  p95={dm.get('p95','-')}ms"
    )
    if stats.get("errors"):
        logger.warning(f"에러 유형: {stats['errors']}")


# ─── Sequential 모드 ─────────────────────────────────────────────────────────

def _next_delay(load_cfg: dict) -> float:
    """요청 간 대기 시간 결정: delay_min/max 둘 다 있으면 랜덤, 아니면 delay_sec 고정."""
    d_min = load_cfg.get("delay_min")
    d_max = load_cfg.get("delay_max")
    if d_min is not None and d_max is not None:
        return random.uniform(d_min, d_max)
    return load_cfg.get("delay_sec", 2)


def run_sequential(cfg: dict):
    load_cfg = cfg["load"]
    duration_sec = load_cfg.get("duration_sec")          # 시간 기준 종료 (우선)
    max_requests = load_cfg.get("max_requests", 20)       # 건수 기준 종료 (기본)
    output_dir = Path(cfg["images"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # 대기 방식 판단
    d_min = load_cfg.get("delay_min")
    d_max = load_cfg.get("delay_max")
    if d_min is not None and d_max is not None:
        delay_desc = f"랜덤 {d_min}~{d_max}s"
    else:
        delay_desc = f"고정 {load_cfg.get('delay_sec', 2)}s"

    # 종료 조건 판단
    stop_desc = f"{duration_sec}s 동안" if duration_sec else f"{max_requests}건"

    logger.info("=" * 55)
    logger.info("모드: Sequential (응답 후 다음 요청)")
    logger.info(f"종료 조건: {stop_desc}  요청 간 대기: {delay_desc}")
    logger.info(f"Target: {cfg['api']['base_url']}{cfg['api']['endpoint']}")
    logger.info("=" * 55)

    results = []
    start_time = time.monotonic()
    i = 0

    while True:
        i += 1
        elapsed = time.monotonic() - start_time

        # 종료 조건 확인
        if duration_sec is not None:
            if elapsed >= duration_sec:
                break
            label = f"[{i}  경과{round(elapsed)}s/{duration_sec}s]"
        else:
            if i > max_requests:
                break
            label = f"[{i}/{max_requests}]"

        # 이미지 생성
        try:
            image_path = generate_image(
                output_dir, cfg["images"]["width"], cfg["images"]["height"])
        except Exception as e:
            logger.error(f"{label} 이미지 생성 실패: {e}")
            continue

        # 요청 전송
        logger.info(f"{label} 요청 시작...")
        result = send_request(cfg, image_path)
        results.append(result)
        elapsed = time.monotonic() - start_time

        # 즉시 결과 로그
        status_str = f"HTTP {result['status']}" if result["success"] else f"FAIL({result['error']})"
        logger.info(
            f"{label} {status_str}  "
            f"duration={result['duration_ms']}ms  "
            f"경과={round(elapsed)}s"
        )

        # 중간 누계 (5건마다)
        if i % 5 == 0:
            s = calc_stats(results)
            print_stats(s, elapsed)

        # 다음 요청 전 대기 (종료 직전이면 스킵)
        delay = _next_delay(load_cfg)
        if duration_sec is not None:
            remaining = duration_sec - (time.monotonic() - start_time)
            if remaining <= 0:
                break
            delay = min(delay, remaining)
        if delay > 0:
            logger.info(f"  → {round(delay, 1)}s 대기 후 다음 요청...")
            time.sleep(delay)

    return results, time.monotonic() - start_time


# ─── Concurrent 모드 ─────────────────────────────────────────────────────────

def run_concurrent(cfg: dict):
    tps = cfg["load"]["tps"]
    duration = cfg["load"]["duration"]
    max_workers = cfg["load"]["max_workers"]
    max_pending = cfg["load"].get("max_pending", max_workers * 2)
    output_dir = Path(cfg["images"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    interval = 1.0 / tps

    logger.info("=" * 55)
    logger.info("모드: Concurrent (TPS 기반 동시 요청)")
    logger.info(f"TPS={tps}  Duration={duration}s  Workers={max_workers}")
    logger.info(f"Target: {cfg['api']['base_url']}{cfg['api']['endpoint']}")
    logger.info(f"※ LLM 포함 최대 TPS ≈ 0.033 초과 시 타임아웃 발생")
    logger.info("=" * 55)

    results = []
    results_lock = threading.Lock()
    start_time = time.monotonic()
    end_time = start_time + duration
    next_print = start_time + 30

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        while time.monotonic() < end_time:
            loop_start = time.monotonic()

            pending = len([f for f in futures if not f.done()])
            if pending >= max_pending:
                time.sleep(0.5)
                continue

            try:
                image_path = generate_image(
                    output_dir, cfg["images"]["width"], cfg["images"]["height"])
            except Exception as e:
                logger.error(f"이미지 생성 실패: {e}")
                time.sleep(interval)
                continue

            future = executor.submit(send_request, cfg, image_path)
            futures.append(future)

            done = [f for f in futures if f.done()]
            for f in done:
                with results_lock:
                    results.append(f.result())
            futures = [f for f in futures if not f.done()]

            now = time.monotonic()
            if now >= next_print and results:
                s = calc_stats(results)
                print_stats(s, now - start_time)
                next_print += 30

            elapsed_loop = time.monotonic() - loop_start
            sleep_time = interval - elapsed_loop
            if sleep_time > 0:
                time.sleep(sleep_time)

        if futures:
            request_timeout = cfg["api"]["timeout"]
            logger.info(f"진행 중인 요청 {len(futures)}개 완료 대기 (최대 {request_timeout}s)...")
            for f in futures:
                try:
                    results.append(f.result(timeout=request_timeout))
                except Exception:
                    results.append({"duration_ms": request_timeout * 1000,
                                    "status": 0, "error": "timeout", "success": False})

    return results, time.monotonic() - start_time


# ─── 최종 리포트 ──────────────────────────────────────────────────────────────

def print_final_report(results: list, elapsed: float, cfg: dict):
    s = calc_stats(results)
    if not s:
        logger.warning("완료된 요청 없음")
        return

    dm = s.get("duration_ms", {})
    actual_tps = round(s["total"] / max(elapsed, 1), 3)

    logger.info("=" * 55)
    logger.info("최종 결과")
    logger.info("=" * 55)
    logger.info(f"총 요청수   : {s['total']}")
    logger.info(f"성공        : {s['success']}")
    logger.info(f"실패        : {s['error']}")
    logger.info(f"성공률      : {s['success_pct']}%")
    logger.info(f"실제 TPS    : {actual_tps}")
    logger.info(f"경과 시간   : {round(elapsed)}s")
    logger.info(f"응답시간(ms): "
                f"avg={dm.get('avg','-')}  min={dm.get('min','-')}  "
                f"p50={dm.get('p50','-')}  p95={dm.get('p95','-')}  "
                f"p99={dm.get('p99','-')}  max={dm.get('max','-')}")
    if s.get("errors"):
        logger.warning(f"에러 유형   : {s['errors']}")
    logger.info("=" * 55)

    reports_dir = Path(cfg["report"].get("output_dir", "scripts/load_test/reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = reports_dir / f"load_test_result_{ts}.json"

    s["actual_tps"] = actual_tps
    s["elapsed"] = round(elapsed)
    s["config"] = {
        "mode": cfg["load"]["mode"],
        "api": cfg["api"]["base_url"] + cfg["api"]["endpoint"],
    }
    s["timestamp"] = datetime.now().isoformat()
    with open(output_file, "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
    logger.info(f"결과 저장: {output_file.resolve()}")


# ─── 설정 로드 + Main ────────────────────────────────────────────────────────

def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="AI Habit Load Test")
    parser.add_argument("--config", default="scripts/load_test/config.yaml")
    parser.add_argument("--mode", choices=["sequential", "concurrent"],
                        help="실행 모드 오버라이드")
    parser.add_argument("--requests", type=int, dest="max_requests",
                        help="총 요청 수 (sequential 건수 기준)")
    parser.add_argument("--duration-sec", type=int, dest="duration_sec",
                        help="실행 시간 초 (sequential 시간 기준, --requests 대신 사용)")
    parser.add_argument("--delay", type=float,
                        help="고정 대기 시간 초 (sequential)")
    parser.add_argument("--delay-min", type=float, dest="delay_min",
                        help="랜덤 대기 최솟값 초 (sequential)")
    parser.add_argument("--delay-max", type=float, dest="delay_max",
                        help="랜덤 대기 최댓값 초 (sequential)")
    parser.add_argument("--tps", type=float, help="TPS (concurrent)")
    parser.add_argument("--duration", type=int, help="실행 시간 초 (concurrent)")
    parser.add_argument("--no-delete", action="store_true",
                        help="이미지 삭제 안 함")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"설정 파일 없음: {args.config}")
        sys.exit(1)

    cfg = load_config(args.config)
    setup_logging(cfg.get("log", {}))

    # CLI 오버라이드
    if args.mode:
        cfg["load"]["mode"] = args.mode
    if args.max_requests:
        cfg["load"]["max_requests"] = args.max_requests
    if args.duration_sec:
        cfg["load"]["duration_sec"] = args.duration_sec
    if args.delay is not None:
        cfg["load"]["delay_sec"] = args.delay
    if args.delay_min is not None:
        cfg["load"]["delay_min"] = args.delay_min
    if args.delay_max is not None:
        cfg["load"]["delay_max"] = args.delay_max
    if args.tps:
        cfg["load"]["tps"] = args.tps
    if args.duration:
        cfg["load"]["duration"] = args.duration
    if args.no_delete:
        cfg["images"]["delete_after_send"] = False

    mode = cfg["load"].get("mode", "sequential")

    if mode == "sequential":
        results, elapsed = run_sequential(cfg)
    else:
        results, elapsed = run_concurrent(cfg)

    print_final_report(results, elapsed, cfg)


if __name__ == "__main__":
    main()
