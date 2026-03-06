# 외부 API 준비 가이드

이 문서는 **AI Habit Platform**에서 나중에 Phase 4를 진행할 때 필요한 외부 API 준비 작업을 정리한 문서입니다.

대상 외부 API

- Google Calendar API
- Firebase Cloud Messaging (FCM)

---

 1. 개요

현재 프로젝트의 **Phase 0 ~ 1.5** 에서는 외부 API 없이도 개발과 시연이 가능합니다.  
하지만 **Phase 4 — External Integration** 에서 실제로 동작하는 캘린더 등록과 푸시 알림을 구현하려면, Google Cloud / Firebase 콘솔에서 사전 설정이 필요합니다. Google Calendar API는 먼저 Google Cloud 프로젝트에서 API를 활성화하고, OAuth 동의 화면과 OAuth 클라이언트 자격 증명을 구성해야 합니다. FCM은 Firebase 프로젝트를 만들고, 서버 환경에서 메시지를 보내기 위해 FCM HTTP v1 API 또는 Admin SDK 기반의 인증 구성이 필요합니다. :contentReference[oaicite:0]{index=0}

---

# 2. 준비 대상 정리

## 2.1 Google Calendar API에서 필요한 것

- Google Cloud Project
- Google Calendar API 활성화
- OAuth consent screen 설정
- OAuth 2.0 Client ID 생성
- Redirect URI 설정
- 테스트용 Google 계정

Google의 공식 Quickstart 기준으로, Calendar API를 사용하려면 먼저 프로젝트에서 API를 켜고, Google Auth platform의 Branding/Audience 설정으로 OAuth 동의 화면을 구성한 뒤, OAuth 2.0 Client ID를 만들어야 합니다. 서버 애플리케이션은 일반적으로 OAuth 2.0 웹 서버 흐름을 사용해 access token과 refresh token을 발급받습니다. :contentReference[oaicite:1]{index=1}

## 2.2 Firebase Cloud Messaging에서 필요한 것

- Firebase Project
- 앱 등록(Android / iOS / Web 중 최소 1개)
- Cloud Messaging 사용 설정
- 서버 인증 방식 결정
  - Firebase Admin SDK
  - FCM HTTP v1 API
- 서비스 계정 또는 Google Cloud 기반 인증 정보
- 테스트용 디바이스 토큰

Firebase 공식 문서에 따르면, 서버에서 FCM을 호출하려면 **Admin SDK** 또는 **FCM HTTP v1 API** 중 하나를 사용해야 하며, HTTP v1 API를 사용할 경우 서비스 계정 기반 OAuth 2.0 access token이 필요합니다. 또한 실제 푸시를 보내려면 클라이언트 앱에서 발급받은 registration token이 필요합니다. :contentReference[oaicite:2]{index=2}

---

# 3. Google Calendar API 준비 절차

## 3.1 Google Cloud Project 생성

1. Google Cloud Console에 로그인합니다.
2. 새 프로젝트를 생성합니다.
3. 프로젝트 이름 예시:
   - `ai-habit-platform-dev`
   - `ai-habit-platform-portfolio`

이후 모든 Calendar API 설정은 이 프로젝트 기준으로 진행합니다.

---

## 3.2 Google Calendar API 활성화

1. Google Cloud Console에서 해당 프로젝트를 선택합니다.
2. API Library로 이동합니다.
3. `Google Calendar API`를 검색합니다.
4. `Enable`을 클릭합니다.

Google 공식 Quickstart는 Calendar API 사용 전에 해당 API를 프로젝트에서 활성화해야 한다고 안내합니다. :contentReference[oaicite:3]{index=3}

---

## 3.3 OAuth Consent Screen 설정

1. Google Cloud Console에서  
   `Google Auth platform > Branding` 으로 이동합니다.
2. 앱 이름 입력
3. 사용자 지원 이메일 입력
4. Audience 선택
   - 개인 테스트면 일반적으로 `External`
   - Google Workspace 내부 조직 전용이면 `Internal`
5. 개발자 연락 이메일 입력
6. 저장

Google 공식 문서 기준으로 새 프로젝트에서는 OAuth 동의 화면(Branding, Audience, Data Access)을 먼저 구성해야 OAuth Client를 생성할 수 있습니다. :contentReference[oaicite:4]{index=4}

---

## 3.4 OAuth Client 생성

NestJS 백엔드에서 사용하려면 보통 **Web application** 타입의 OAuth Client ID를 생성합니다.

절차:

1. `Google Auth platform > Clients` 이동
2. `Create Client`
3. Application Type 선택
   - `Web application`
4. 이름 입력
   - 예: `ai-habit-platform-web`
5. Authorized redirect URIs 추가
   - 로컬 개발 예시:
     - `http://localhost:3000/auth/google/callback`
6. 생성 후 `client_id` 와 `client_secret` 확보

Google OAuth 2.0 웹 서버 앱은 redirect URI를 포함한 OAuth 클라이언트 구성이 필요하며, 승인 후 authorization code를 받아 token으로 교환하는 흐름을 사용합니다. :contentReference[oaicite:5]{index=5}

---

## 3.5 필요한 Scope 결정

처음에는 최소 권한으로 시작하는 것이 좋습니다.

추천 scope 예시:

- `https://www.googleapis.com/auth/calendar.events`

의미:

- 사용자의 캘린더 이벤트 생성/수정 가능

Scope는 앱이 요청하는 접근 범위를 의미하며, 필요한 범위만 요청할수록 동의율과 보안성이 좋아집니다. :contentReference[oaicite:6]{index=6}

---

## 3.6 애플리케이션에 저장할 환경 변수

NestJS에서 사용할 `.env` 예시:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
GOOGLE_CALENDAR_SCOPES=https://www.googleapis.com/auth/calendar.events

## 3.7 pre-implementation checklist
- [ ] Google Cloud 프로젝트 생성
- [ ] Google Calendar API 활성화
- [ ] OAuth consent screen 구성
- [ ] OAuth Client ID 생성
- [ ] Redirect URI 등록
- [ ] 테스트용 Google 계정 준비
- [ ] NestJS .env에 값 등록

#
