"""
Phase 4 — External Integration 엔드포인트 검증
대상: http://localhost:3000
완료 조건:
  - GET  /auth/google          → 302 redirect (Google OAuth URL 생성)
  - POST /calendar/events      → 엔드포인트 존재 (OAuth 미인증 시 500 허용, 404는 불가)
  - POST /notifications/send   → 엔드포인트 존재 (FCM 설정 무관, 404는 불가)

주의: 실제 OAuth 인증 및 FCM 전송은 수동 검증 대상입니다.
      이 테스트는 엔드포인트 등록 여부만 확인합니다.
"""

import requests
import pytest
from conftest import API_URL


class TestAuthEndpoint:
    def test_google_auth_redirects(self):
        """GET /auth/google → 302 redirect (Google OAuth URL)"""
        res = requests.get(
            f"{API_URL}/auth/google",
            allow_redirects=False,
            timeout=5,
        )
        assert res.status_code == 302, \
            f"Expected 302 redirect, got {res.status_code}"
        location = res.headers.get("Location", "")
        assert "accounts.google.com" in location, \
            f"Redirect target is not Google: {location}"


class TestCalendarEndpoint:
    def test_calendar_events_endpoint_exists(self):
        """POST /calendar/events → 엔드포인트 등록 확인 (404 아님)"""
        res = requests.post(
            f"{API_URL}/calendar/events",
            json={"type": "meal", "time": "2026-03-09T12:00:00+09:00"},
            timeout=10,
        )
        assert res.status_code != 404, \
            f"Endpoint not found (404) — route may not be registered"


class TestNotificationEndpoint:
    def test_notification_send_endpoint_exists(self):
        """POST /notifications/send → 엔드포인트 등록 확인 (404 아님)"""
        res = requests.post(
            f"{API_URL}/notifications/send",
            json={"message": "verify test"},
            timeout=10,
        )
        assert res.status_code != 404, \
            f"Endpoint not found (404) — route may not be registered"
