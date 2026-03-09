#!/usr/bin/env python3
"""
Kibana 대시보드 프로비저닝 스크립트

Usage:
    python3 scripts/provision_kibana.py            # 전체 4개 대시보드
    python3 scripts/provision_kibana.py --only 1   # 특정 대시보드만
    python3 scripts/provision_kibana.py --kb-url http://localhost:5601
"""

import argparse
import json
import sys
import uuid

import requests

DEFAULT_KB_URL = "http://localhost:5601"
HEADERS = {"kbn-xsrf": "true", "Content-Type": "application/json"}
NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def mid(name: str) -> str:
    """이름 기반 결정론적 UUID — 재실행해도 같은 ID"""
    return str(uuid.uuid5(NS, name))


# ─── Data View ────────────────────────────────────────────────────────────────

def get_or_create_data_view(kb_url: str, pattern: str) -> str:
    res = requests.get(f"{kb_url}/api/data_views", headers=HEADERS, timeout=10)
    for dv in res.json().get("data_view", []):
        if dv["title"] == pattern:
            return dv["id"]
    res = requests.post(
        f"{kb_url}/api/data_views/data_view",
        headers=HEADERS,
        json={"data_view": {"title": pattern, "timeFieldName": "@timestamp"}},
        timeout=10,
    )
    return res.json()["data_view"]["id"]


# ─── Column Helpers ───────────────────────────────────────────────────────────

def col_date() -> dict:
    return {
        "label": "@timestamp", "dataType": "date",
        "operationType": "date_histogram", "sourceField": "@timestamp",
        "isBucketed": True, "scale": "interval",
        "params": {"interval": "auto", "includeEmptyRows": True, "dropPartials": False},
    }


def col_count(label: str = "요청 수") -> dict:
    return {
        "label": label, "dataType": "number",
        "operationType": "count", "isBucketed": False,
        "scale": "ratio", "sourceField": "___records___",
    }


def col_avg(field: str, label: str) -> dict:
    return {
        "label": label, "dataType": "number",
        "operationType": "average", "sourceField": field,
        "isBucketed": False, "scale": "ratio", "params": {},
    }


def col_pct(field: str, pct: int, label: str) -> dict:
    return {
        "label": label, "dataType": "number",
        "operationType": "percentile", "sourceField": field,
        "isBucketed": False, "scale": "ratio",
        "params": {"percentile": pct},
    }


def col_terms_str(field: str, label: str, order_col: str, size: int = 10) -> dict:
    return {
        "label": label, "dataType": "string",
        "operationType": "terms", "sourceField": field,
        "isBucketed": True, "scale": "ordinal",
        "params": {
            "size": size,
            "orderBy": {"type": "column", "columnId": order_col},
            "orderDirection": "desc",
            "otherBucket": True, "missingBucket": False,
            "parentFormat": {"id": "terms"},
            "include": [], "exclude": [],
            "includeIsRegex": False, "excludeIsRegex": False,
        },
    }


def col_terms_num(field: str, label: str, order_col: str, size: int = 10) -> dict:
    return {
        "label": label, "dataType": "number",
        "operationType": "terms", "sourceField": field,
        "isBucketed": True, "scale": "ordinal",
        "params": {
            "size": size,
            "orderBy": {"type": "column", "columnId": order_col},
            "orderDirection": "desc",
            "otherBucket": False, "missingBucket": False,
            "parentFormat": {"id": "terms"},
            "include": [], "exclude": [],
            "includeIsRegex": False, "excludeIsRegex": False,
        },
    }


# ─── Lens Attribute Builder ───────────────────────────────────────────────────

def lens_attrs(title: str, viz_type: str, layer_id: str, dv_id: str,
               columns: dict, col_order: list, viz_cfg: dict,
               query: str = "") -> dict:
    return {
        "title": title, "visualizationType": viz_type, "type": "lens",
        "references": [{
            "id": dv_id,
            "name": f"indexpattern-datasource-layer-{layer_id}",
            "type": "index-pattern",
        }],
        "state": {
            "datasourceStates": {
                "formBased": {
                    "layers": {
                        layer_id: {
                            "columnOrder": col_order,
                            "columns": columns,
                            "indexPatternId": dv_id,
                        }
                    }
                }
            },
            "visualization": viz_cfg,
            "filters": [],
            "query": {"language": "kuery", "query": query},
            "internalReferences": [],
            "adHocDataViews": {},
        },
    }


# ─── Visualization Templates ──────────────────────────────────────────────────

def viz_line_count(title: str, lid: str, dv_id: str, query: str = "") -> dict:
    """시간대별 요청 수 (꺾은선 그래프)"""
    dc, cc = mid(f"{lid}-d"), mid(f"{lid}-c")
    return lens_attrs(title, "lnsXY", lid, dv_id,
        columns={dc: col_date(), cc: col_count()},
        col_order=[dc, cc],
        viz_cfg={
            "legend": {"isVisible": True, "position": "right"},
            "valueLabels": "hide", "preferredSeriesType": "line",
            "layers": [{"layerId": lid, "accessors": [cc], "position": "top",
                        "seriesType": "line", "showGridlines": False,
                        "xAccessor": dc, "layerType": "data"}],
        }, query=query)


def viz_hbar_avg(title: str, lid: str, dv_id: str,
                 terms_field: str, terms_label: str,
                 avg_field: str, avg_label: str,
                 is_num_terms: bool = False, query: str = "") -> dict:
    """terms별 평균값 수평 막대 그래프"""
    tc, ac = mid(f"{lid}-t"), mid(f"{lid}-a")
    terms_col = (col_terms_num(terms_field, terms_label, ac)
                 if is_num_terms
                 else col_terms_str(terms_field, terms_label, ac))
    return lens_attrs(title, "lnsXY", lid, dv_id,
        columns={tc: terms_col, ac: col_avg(avg_field, avg_label)},
        col_order=[tc, ac],
        viz_cfg={
            "legend": {"isVisible": True, "position": "right"},
            "valueLabels": "hide", "preferredSeriesType": "bar_horizontal",
            "layers": [{"layerId": lid, "accessors": [ac], "position": "top",
                        "seriesType": "bar_horizontal", "showGridlines": False,
                        "xAccessor": tc, "layerType": "data"}],
        }, query=query)


def viz_pie(title: str, lid: str, dv_id: str,
            terms_field: str, terms_label: str,
            is_num_terms: bool = False, query: str = "") -> dict:
    """terms 분포 파이 차트"""
    tc, cc = mid(f"{lid}-t"), mid(f"{lid}-c")
    terms_col = (col_terms_num(terms_field, terms_label, cc)
                 if is_num_terms
                 else col_terms_str(terms_field, terms_label, cc))
    return lens_attrs(title, "lnsPie", lid, dv_id,
        columns={tc: terms_col, cc: col_count("건수")},
        col_order=[tc, cc],
        viz_cfg={
            "shape": "pie",
            "layers": [{"layerId": lid,
                        "primaryGroups": [tc], "metrics": [cc],
                        "layerType": "data", "numberDisplay": "percent",
                        "categoryDisplay": "default", "legendDisplay": "default",
                        "legendPosition": "right"}],
        }, query=query)


def viz_metric_pct(title: str, lid: str, dv_id: str,
                   field: str, pct: int, label: str, query: str = "") -> dict:
    """Percentile 단일 지표"""
    mc = mid(f"{lid}-m")
    return lens_attrs(title, "lnsMetric", lid, dv_id,
        columns={mc: col_pct(field, pct, label)},
        col_order=[mc],
        viz_cfg={"layerId": lid, "layerType": "data", "metricAccessor": mc},
        query=query)


def viz_metric_avg(title: str, lid: str, dv_id: str,
                   field: str, label: str, query: str = "") -> dict:
    """Average 단일 지표"""
    mc = mid(f"{lid}-m")
    return lens_attrs(title, "lnsMetric", lid, dv_id,
        columns={mc: col_avg(field, label)},
        col_order=[mc],
        viz_cfg={"layerId": lid, "layerType": "data", "metricAccessor": mc},
        query=query)


def viz_datatable(title: str, lid: str, dv_id: str,
                  group_fields: list, query: str = "") -> dict:
    """집계 데이터 테이블 — group_fields: [(field, label, is_numeric), ...]"""
    cc = mid(f"{lid}-c")
    columns = {cc: col_count("건수")}
    col_order = []
    for i, (field, label, is_num) in enumerate(group_fields):
        cid = mid(f"{lid}-g{i}")
        columns[cid] = (col_terms_num(field, label, cc, size=20)
                        if is_num
                        else col_terms_str(field, label, cc, size=20))
        col_order.append(cid)
    col_order.append(cc)
    return lens_attrs(title, "lnsDatatable", lid, dv_id,
        columns=columns, col_order=col_order,
        viz_cfg={
            "columns": [{"columnId": c} for c in col_order],
            "layerId": lid, "layerType": "data",
            "rowHeight": "auto", "rowHeightLines": 1,
            "headerRowHeight": "auto", "headerRowHeightLines": 1,
            "paginationSize": 25,
            "sorting": {"columnId": cc, "direction": "desc"},
        }, query=query)


# ─── Dashboard Panel + Save ───────────────────────────────────────────────────

def panel(name: str, attrs: dict,
          x: int, y: int, w: int, h: int) -> dict:
    pid = mid(name)
    return {
        "panelIndex": pid,
        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": pid},
        "type": "lens",
        "embeddableConfig": {"attributes": attrs, "enhancements": {}},
    }


def save_dashboard(kb_url: str, dash_id: str, title: str,
                   panels: list, description: str = "") -> requests.Response:
    body = {
        "attributes": {
            "title": title,
            "description": description,
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "syncColors": False,
                                       "hidePanelTitles": False}),
            "version": 1,
            "timeRestore": False,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"language": "kuery", "query": ""}, "filter": []
                })
            },
        },
        "references": [],
    }
    return requests.post(
        f"{kb_url}/api/saved_objects/dashboard/{dash_id}?overwrite=true",
        headers=HEADERS, json=body, timeout=15,
    )


# ─── 4개 대시보드 정의 ────────────────────────────────────────────────────────

def dashboard_1_api(api_dv: str) -> tuple:
    """대시보드 1 — API 요청 모니터링 (5개 패널)"""
    panels = [
        # 패널 1: 시간대별 요청 수 (전체 너비)
        panel("d1-p1",
              viz_line_count("① 시간대별 요청 수", mid("d1-l1"), api_dv),
              x=0, y=0, w=48, h=15),

        # 패널 2: 엔드포인트별 평균 응답시간
        panel("d1-p2",
              viz_hbar_avg("② 엔드포인트별 평균 응답시간 (ms)", mid("d1-l2"), api_dv,
                           "url.keyword", "URL", "duration_ms", "평균 duration_ms"),
              x=0, y=15, w=24, h=15),

        # 패널 3: HTTP 상태 코드 분포
        panel("d1-p3",
              viz_pie("③ HTTP 상태 코드 분포", mid("d1-l3"), api_dv,
                      "status_code", "상태 코드", is_num_terms=True),
              x=24, y=15, w=24, h=15),

        # 패널 4: p95 응답시간
        panel("d1-p4",
              viz_metric_pct("④ p95 응답시간 (ms)", mid("d1-l4"), api_dv,
                             "duration_ms", 95, "p95 duration_ms"),
              x=0, y=30, w=12, h=10),

        # 패널 5: 에러 요청 목록
        panel("d1-p5",
              viz_datatable("⑤ 에러 요청 목록", mid("d1-l5"), api_dv,
                            [("url.keyword", "URL", False),
                             ("status_code", "상태 코드", True),
                             ("trace_id.keyword", "trace_id", False)],
                            query="level: error OR level: ERROR"),
              x=12, y=30, w=36, h=10),
    ]
    return (mid("dashboard-1"),
            "AI Habit — API 요청 모니터링",
            panels,
            "NestJS API 요청 현황: 요청 수 추이, 엔드포인트별 응답시간, 상태 코드 분포, p95, 에러 목록")


def dashboard_2_ai(ai_dv: str) -> tuple:
    """대시보드 2 — AI 처리 성능 (5개 패널)"""
    panels = [
        panel("d2-p1",
              viz_hbar_avg("① OCR vs LLM 평균 처리시간 (ms)", mid("d2-l1"), ai_dv,
                           "message.keyword", "작업 유형", "duration_ms", "평균 duration_ms",
                           query='message: "OCR completed" OR message: "LLM inference completed"'),
              x=0, y=0, w=48, h=15),
        panel("d2-p2",
              viz_metric_avg("② OCR 평균 처리시간 (ms)", mid("d2-l2"), ai_dv,
                             "duration_ms", "평균 duration_ms",
                             query='message: "OCR completed"'),
              x=0, y=15, w=16, h=10),
        panel("d2-p3",
              viz_metric_avg("③ LLM 평균 추론시간 (ms)", mid("d2-l3"), ai_dv,
                             "duration_ms", "평균 duration_ms",
                             query='message: "LLM inference completed"'),
              x=16, y=15, w=16, h=10),
        panel("d2-p4",
              viz_line_count("④ OCR 요청 건수 추이", mid("d2-l4"), ai_dv,
                             query='message: "OCR completed"'),
              x=32, y=15, w=16, h=10),
        panel("d2-p5",
              viz_datatable("⑤ AI 에러 목록", mid("d2-l5"), ai_dv,
                            [("message.keyword", "메시지", False),
                             ("trace_id.keyword", "trace_id", False),
                             ("user_id.keyword", "user_id", False)],
                            query="level: error OR level: ERROR"),
              x=0, y=25, w=48, h=15),
    ]
    return (mid("dashboard-2"),
            "AI Habit — AI 처리 성능",
            panels,
            "FastAPI OCR/LLM 처리 성능: 구간 처리시간, OCR vs LLM 비교, 에러 목록")


def dashboard_3_e2e(api_dv: str, ai_dv: str) -> tuple:
    """대시보드 3 — E2E 요청 추적 (5개 패널)"""
    panels = [
        panel("d3-p1",
              viz_metric_avg("① HTTP 평균 응답시간 (ms)", mid("d3-l1"), api_dv,
                             "duration_ms", "평균 duration_ms"),
              x=0, y=0, w=16, h=10),
        panel("d3-p2",
              viz_metric_avg("② OCR 평균 처리시간 (ms)", mid("d3-l2"), ai_dv,
                             "duration_ms", "평균 duration_ms",
                             query='message: "OCR completed"'),
              x=16, y=0, w=16, h=10),
        panel("d3-p3",
              viz_metric_avg("③ LLM 평균 추론시간 (ms)", mid("d3-l3"), ai_dv,
                             "duration_ms", "평균 duration_ms",
                             query='message: "LLM inference completed"'),
              x=32, y=0, w=16, h=10),
        panel("d3-p4",
              viz_datatable("④ 느린 요청 목록 (1초 초과)", mid("d3-l4"), api_dv,
                            [("url.keyword", "URL", False),
                             ("trace_id.keyword", "trace_id", False),
                             ("user_id.keyword", "user_id", False)],
                            query="duration_ms > 1000"),
              x=0, y=10, w=48, h=15),
        panel("d3-p5",
              viz_hbar_avg("⑤ 사용자별 평균 응답시간 (ms)", mid("d3-l5"), api_dv,
                           "user_id.keyword", "user_id", "duration_ms", "평균 duration_ms"),
              x=0, y=25, w=48, h=15),
    ]
    return (mid("dashboard-3"),
            "AI Habit — E2E 요청 추적",
            panels,
            "trace_id 기반 전 구간 지연 분석: HTTP/OCR/LLM 평균, 느린 요청 목록, 사용자별 현황")


def dashboard_4_errors(api_dv: str, ai_dv: str) -> tuple:
    """대시보드 4 — 에러 & 이상 탐지 (4개 패널)"""
    panels = [
        panel("d4-p1",
              viz_line_count("① 시간대별 에러 발생 추이", mid("d4-l1"), api_dv,
                             query="level: error OR level: ERROR"),
              x=0, y=0, w=48, h=15),
        panel("d4-p2",
              viz_pie("② 에러 발생 위치 (context)", mid("d4-l2"), api_dv,
                      "context.keyword", "context",
                      query="level: error OR level: ERROR"),
              x=0, y=15, w=24, h=15),
        panel("d4-p3",
              viz_datatable("③ LLM 느린 추론 (10초 초과)", mid("d4-l3"), ai_dv,
                            [("trace_id.keyword", "trace_id", False),
                             ("user_id.keyword", "user_id", False)],
                            query='message: "LLM inference completed" AND duration_ms > 10000'),
              x=24, y=15, w=24, h=15),
        panel("d4-p4",
              viz_datatable("④ 5xx 에러 목록", mid("d4-l4"), api_dv,
                            [("url.keyword", "URL", False),
                             ("status_code", "상태 코드", True),
                             ("trace_id.keyword", "trace_id", False)],
                            query="status_code >= 500"),
              x=0, y=30, w=48, h=15),
    ]
    return (mid("dashboard-4"),
            "AI Habit — 에러 & 이상 탐지",
            panels,
            "에러율 추이, 에러 발생 위치, LLM 느린 추론, 5xx 에러 목록")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb-url", default=DEFAULT_KB_URL)
    parser.add_argument("--only", type=int, choices=[1, 2, 3, 4],
                        help="특정 대시보드만 생성 (1~4)")
    args = parser.parse_args()
    kb_url = args.kb_url.rstrip("/")

    print(f"Kibana: {kb_url}")
    print("Data View 확인 중...")
    api_dv = get_or_create_data_view(kb_url, "ai-habit-api-logs-*")
    ai_dv = get_or_create_data_view(kb_url, "ai-habit-ai-logs-*")
    print(f"  api-logs: {api_dv}")
    print(f"  ai-logs:  {ai_dv}\n")

    all_dashboards = {
        1: dashboard_1_api(api_dv),
        2: dashboard_2_ai(ai_dv),
        3: dashboard_3_e2e(api_dv, ai_dv),
        4: dashboard_4_errors(api_dv, ai_dv),
    }

    targets = [args.only] if args.only else [1, 2, 3, 4]
    failed = False

    for num in targets:
        dash_id, title, panels, desc = all_dashboards[num]
        print(f"[{num}] {title} ...")
        res = save_dashboard(kb_url, dash_id, title, panels, desc)
        if res.status_code in (200, 201):
            print(f"  ✓ 완료")
        else:
            print(f"  ✗ 실패 [{res.status_code}]: {res.text[:300]}")
            failed = True

    print()
    if failed:
        sys.exit(1)
    print("완료!")
    print(f"  → {kb_url}/app/dashboards")


if __name__ == "__main__":
    main()
